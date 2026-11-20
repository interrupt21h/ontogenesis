"""Topology dashboard for native and archived observatory frames."""
from PIL import ImageFont

def topology_panel(draw, rows, steps, cells):
    if not rows: raise ValueError("No observation rows")
    font=ImageFont.load_default(size=13)
    small=ImageFont.load_default(size=12)
    fg=(200,220,240); teal=(80,220,160)
    colors=((239,165,74),(60,190,235),(180,145,235))
    left=664
    draw.rectangle((left,586,1279,719),fill=(8,13,23))
    draw.text((left,590),"MATRIX COVERAGE / THRESHOLD",font=font,fill=fg)
    draw.rectangle((left,614,left+300,680),outline=(75,90,110))
    for threshold,color in zip(("0.1","0.15","0.2"),colors):
        points=[(left+300*h["step"]/steps,680-66*h["matrix_threshold_coverage"][threshold]) for h in rows]
        if len(points)>1: draw.line(points,fill=color,width=2)
        else: draw.point(points[0],fill=color)
    for k,(label,color) in enumerate(zip(("M > .10","M > .15","M > .20"),colors)):
        draw.text((left+k*98,684),label,font=small,fill=color)
    h=rows[-1]
    x=980
    draw.text((x,590),"SECONDARY COMPLEMENT / CELLS",font=font,fill=fg)
    count=h["cavity_candidates"]
    total=round(h["cavity_fraction"]*cells)
    draw.text((x,610),f"{count} regions | {total:,} cells",font=font,fill=teal)
    draw.text((x,628),f"Largest: {h['largest_cavity']:,} | Components: {h['complement_components']}",font=small,fill=fg)
    draw.text((x,646),f"Coverage: {100*h['cavity_fraction']:.5f}% | Euler: {h['euler_characteristic']}",font=small,fill=fg)
    peak=max(round(a["cavity_fraction"]*cells) for a in rows)
    if peak:
        draw.rectangle((x,666,x+280,690),outline=(75,90,110))
        points=[(x+280*a["step"]/steps,690-24*round(a["cavity_fraction"]*cells)/peak) for a in rows]
        if len(points)>1: draw.line(points,fill=teal,width=2)
        draw.text((x,696),f"Adaptive scale: 0–{peak:,} cells",font=small,fill=teal)
    else:
        draw.text((x,671),"No qualifying regions observed",font=small,fill=teal)
