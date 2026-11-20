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
    rows.append(dict(page=page.number+1,words=len(words),ink_fraction=round(ink,4),review=ink<.025))
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
print("Sparse pages for review:",[r["page"] for r in rows if r["review"]])
