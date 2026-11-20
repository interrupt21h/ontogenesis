"""Flag sparse pages for editorial review; not a substitute for visual inspection."""
from pathlib import Path
import json
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
