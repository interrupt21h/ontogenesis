"""Flag sparse pages for editorial review; not a substitute for visual inspection."""
from pathlib import Path
import json
import re
import fitz
from PIL import Image, ImageDraw

out = Path(__file__).resolve().parent / "build"
doc = fitz.open(out / "ontogenesis.pdf")
rows = []
thumbs = []
for page in doc:
    pix = page.get_pixmap(matrix=fitz.Matrix(.36,.36), alpha=False)
    im = Image.frombytes("RGB", (pix.width,pix.height), pix.samples)
    gray = im.convert("L")
    region = gray.crop((0,int(im.height*.10),im.width,int(im.height*.90)))
    hist = region.histogram()
    ink = sum(hist[:220])/max(1,region.width*region.height)
    words = page.get_text("words")
    content=page.get_text()
    plate=("Development sequence" in content or "Final frame detail" in content) and "Source animation artifact" in content
    images=page.get_image_info()
    width=max((i["bbox"][2]-i["bbox"][0] for i in images),default=0)
    fraction=width/max(1,page.rect.width-2*25/25.4*72)
    undersized=plate and fraction<.85
    rows.append(dict(page=page.number+1,words=len(words),ink_fraction=round(ink,4),simulation_plate=plate,image_width_fraction=round(fraction,3),undersized=undersized,review=ink<.025 or undersized))
    thumbs.append(im)
w,h=thumbs[0].size
cols=6
sheet=Image.new("RGB",(cols*(w+12),((len(thumbs)+cols-1)//cols)*(h+24)),"#dce4e8")
draw=ImageDraw.Draw(sheet)
for i,im in enumerate(thumbs):
    x=i%cols*(w+12); y=i//cols*(h+24)
    sheet.paste(im,(x,y))
    draw.text((x+4,y+h+2),str(i+1),fill="black")
sheet.save(out/"contact-sheet.jpg",quality=88)
(out/"layout-audit.json").write_text(json.dumps(rows,indent=2))
print("Pages for review:",[r["page"] for r in rows if r["review"]])
if any(r["undersized"] for r in rows):
    raise SystemExit("Simulation plate width below 85% of text area")

# The historical source claims precisely one chapter for each implemented
# experiment. This audit compares them to *actual PDF page text*; the TOC
# alone is not accepted as evidence of a generated chapter.
root=Path(__file__).resolve().parents[1]
history=(root/"docs/HISTORY.md").read_text()
generations=[int(x) for x in re.findall(r"^## Generation (\d{4})",history,re.M)]
if generations!=list(range(1,29)):
    raise SystemExit(f"Experiment-history record missing, duplicated or unordered: {generations}")
chapter_pages={}
for n in generations:
    target=f"Generation {n:04d} "
    matches=[]
    for page in doc:
        if page.number<20:  # exclude the early table of contents
            continue
        lines=page.get_text().splitlines()
        if any(line.startswith(target) and ("—" in line or line.endswith("—"))
               for line in lines):
            matches.append(page.number+1)
    if not matches:
        raise SystemExit(f"Missing rendered Generation {n:04d} chapter")
    chapter_pages[f"{n:04d}"]=matches[0]
if list(chapter_pages.values())!=sorted(chapter_pages.values()):
    raise SystemExit("Experimental chapters are out of chronological order")

text_pages=[p.get_text() for p in doc]
alltext="\n".join(text_pages)
must_find=[
    "The genealogy of the investigation",
    "The late-experiment branch structure",
    "Final renders and visualization fidelity",
    "Synthesis and research directions",
    "About the artist",
    "Localized disturbance: matched pilot measurements",
]
for heading in must_find:
    if heading not in alltext:
        raise SystemExit("Required editorial chapter/diagram missing: "+heading)
gallery={}
for g in ("0024","0025","0028"):
    matches=[i+1 for i,t in enumerate(text_pages)
             if re.search(r"FINAL RENDERS\s*/\s*GENERATION\s*"+g,t)]
    if len(matches)!=1:
        raise SystemExit(f"Expected one explicit final-renders gallery plate for {g}, got {matches}")
    gallery[g]=matches[0]
if chapter_pages["0028"]>=gallery["0024"]:
    raise SystemExit("Final gallery must follow all numbered experiments")
synthesis=next(i+1 for i,t in enumerate(text_pages)
               if i+1>gallery["0028"] and "Synthesis and research directions" in t)
if gallery["0028"]>=synthesis:
    raise SystemExit("Synthesis must follow the curated final gallery")
if not ("About the artist" in text_pages[-1] or "About the artist" in text_pages[-2]):
    raise SystemExit("Final author page missing or shifted away from the end")
for fig in ("research-finale.pdf","0028-evidence.pdf"):
    file=out/"atlas"/fig
    if not file.exists() or file.stat().st_size<1000:
        raise SystemExit("Required evidence/model-ancestry figure missing: "+fig)
if not (out/"mechanisms/0028.pdf").is_file():
    raise SystemExit("G0028 paired-treatment schematic not included")
summary={
    "source_revision_chapter_count":len(generations),
    "pages":len(doc),
    "generation_chapter_pages":chapter_pages,
    "final_renders_gallery_pages":gallery,
    "synthesis_page":synthesis,
    "author_page":len(doc),
    "diagram_semantics":{
        "research-finale":"Software/model ancestry, not a single linear model chain",
        "0028":"Conceptual paired control vs treated arm; no simulated pixels",
        "0028-evidence":"Native numerical matched-control pilot measurements",
    },
    "sparse_pages_requiring_visual_review":[r["page"] for r in rows if r["review"]],
    "status":"chapter coverage, gallery ordering, and required diagrams checked",
}
(out/"experiment-figure-audit.json").write_text(json.dumps(summary,indent=2)+"\n")
print("Verified scientific chapters:",len(generations),
      "Final gallery pages:",gallery,"Author page:",len(doc))

