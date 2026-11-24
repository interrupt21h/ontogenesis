"""G0034 Lineage Ribbons — animated diagram of *recorded* 4D components.

Nodes are top-size-filtered connected components; edges are observed shared
voxels at consecutive recorded steps. Curves, camera focus and particles are
presentation only, not reconstructed topology or biological lineage.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw
from ecological_diagnostic_render import background, font

SEEDS = ("42", "73")
ARMS = ("near_transition", "separated_070")
SPECIES = ("v_only", "w_only")
PALETTE = {"v_only": (89, 230, 205), "w_only": (252, 169, 105)}
PLOT_X0, PLOT_X1 = 110, 1208
PLOT_Y = {"42": {"v_only": (194, 290), "w_only": (311, 408)},
          "73": {"v_only": (441, 534), "w_only": (557, 651)}}


def validate_report(report):
    if (report.get("generation"), report.get("edition"), report.get("n"),
        report.get("steps"), report.get("seeds"), report.get("arms"),
        report.get("species")) != (
            "0034", "periodic-four-dimensional-component-genealogy-pilot-v1",
            16, 240, [42, 73], list(ARMS), list(SPECIES)):
        raise ValueError("Unexpected G0034 numerical evidence")
    if report.get("times") != list(range(0, 241, 24)):
        raise ValueError("G0034 recorded timeline missing")
    for seed in SEEDS:
        for arm in ARMS:
            for species in SPECIES:
                records = report["source"][seed]["arms"][arm][species]
                if len(records) != 11:
                    raise ValueError("G0034 component timeline incomplete")
                for i, rec in enumerate(records):
                    if rec["sample_index"] != i:
                        raise ValueError("Changed component sample index")
                    if sum(r["sites"] for r in rec["featured"]) > rec["active_sites"]:
                        raise ValueError("Featured components exceed the actual lattice")
                    if (rec["component_count"] < len(rec["featured"])
                        or rec["largest_component"] > rec["active_sites"]):
                        raise ValueError("Invalid component count")
                    prev = records[i-1] if i else None
                    ids = set(r["id"] for r in rec["featured"])
                    prior = set(r["id"] for r in prev["featured"]) if prev else set()
                    for edge in rec["featured_edges_from_previous"]:
                        if edge["from"] not in prior or edge["to"] not in ids:
                            raise ValueError("Visual lineage references an untracked component")
                        if edge["sites"] <= 0:
                            raise ValueError("Lineage overlap not positive")
    return report


def layout(records, seed, species):
    low, high = PLOT_Y[seed][species]
    placement = {}
    for i, rec in enumerate(records):
        featured = rec["featured"][:12]
        if not featured:
            continue
        total = sum(math.sqrt(x["sites"]) for x in featured)
        cursor = low + (high-low) * .06
        space = (high-low) * .88
        for node in featured:
            height = max(4, space*math.sqrt(node["sites"])/max(1e-9,total))
            mid = cursor + height/2
            placement[(i, node["id"])] = (
                PLOT_X0+(PLOT_X1-PLOT_X0)*i/10, mid, node["sites"])
            cursor += height
    return placement


def diagram(report, *, arm):
    validate_report(report)
    if arm not in ARMS:
        raise ValueError("Unknown model treatment")
    im = background()
    d = ImageDraw.Draw(im)
    d.rectangle((0,0,1280,7), fill="#5DE4D3")
    d.text((37,22),"ONTOGENESIS / G0034 / OBSERVED FOUR-DIMENSIONAL STRUCTURAL GENEALOGY",
           font=font(16, True),fill="#76E8D5")
    d.text((37,59),"THE LINEAGE RIBBONS",font=font(44,True),fill="#F2F8FC")
    d.text((40,117),f"Treatment: {arm}  ·  16⁴ periodic topology  ·  threshold >0.10",
           font=font(16),fill="#BFD7E4")
    for seed in SEEDS:
        upper = 185 if seed=="42" else 434
        bottom = 416 if seed=="42" else 658
        d.rounded_rectangle((34,upper,1242,bottom),radius=13,
                            fill="#10283A",outline="#416176",width=2)
        d.text((45,upper+9),f"SEED {seed}",font=font(13,True),fill="#E8F2F9")
        d.text((940,upper+10),"TEAL / V-ONLY     AMBER / W-ONLY",
               font=font(11,True),fill="#C1D7DF")
        for species in SPECIES:
            records = report["source"][seed]["arms"][arm][species]
            color = PALETTE[species]
            placements = layout(records,seed,species)
            # Only actual nonzero overlap edges are drawn.
            for i,record in enumerate(records):
                if not i:
                    continue
                for edge in record["featured_edges_from_previous"]:
                    src=placements.get((i-1,edge["from"]))
                    dest=placements.get((i,edge["to"]))
                    if src is None or dest is None:
                        continue
                    x0,y0,_=src;x1,y1,_=dest
                    strength=min(1.,math.sqrt(edge["sites"])/75)
                    edge_color=tuple(round(v*(.24+.58*strength)) for v in color)
                    # Polyline bends are graphical routing only.
                    xm=(x0+x1)/2
                    d.line([(x0,y0),(xm,y0),(xm,y1),(x1,y1)],
                           fill=edge_color,width=1+round(5*strength),joint="curve")
            for (i,_), (x,y,size) in placements.items():
                radius=2+min(8,round(2*math.log1p(size)/math.log(10)))
                d.ellipse((x-radius,y-radius,x+radius,y+radius),
                          fill=color,outline="#EFFAFF",width=1)
    for i,step in enumerate(report["times"]):
        x=PLOT_X0+(PLOT_X1-PLOT_X0)*i/10
        if i%2==0:
            d.text((x-12,665),str(step),font=font(11),fill="#B1C9D8")
    d.text((44,692),"NODES = ACTUAL 4D CONNECTED COMPONENTS   /   CURVES = MEASURED SHARED SITES IN ADJACENT RECORDED STATES",
           font=font(11),fill="#BED5E1")
    return im


def frame(report, plate, index, count, *, arm):
    if count<2 or not 0<=index<count:
        raise ValueError("Invalid render frame")
    pct=index/(count-1)
    ti=min(10,int(pct*11))
    im=plate.copy().convert("RGBA")
    x=PLOT_X0+(PLOT_X1-PLOT_X0)*ti/10
    # Future ribbons are already archived, but remain shaded until the
    # display cursor reaches their actual recorded time.
    shade=Image.new("RGBA",im.size,(0,0,0,0))
    sh=ImageDraw.Draw(shade)
    if x+2<PLOT_X1:
        for top,bottom in ((185,416),(434,658)):
            sh.rectangle((int(x)+3,top+2,PLOT_X1,bottom-2),
                         fill=(7,20,31,170))
    im=Image.alpha_composite(im,shade)
    d=ImageDraw.Draw(im)
    d.line((x,182,x,659),fill="#FCECB7",width=3)
    d.rounded_rectangle((510,136,865,178),radius=10,fill="#29495B")
    d.text((523,144),f"RECORDED STEP {report['times'][ti]:03d} / 240",
           font=font(18,True),fill="#FAF8E5")
    # Highlight actual components in the current sampled state; pulse size is
    # an editorial signal only, never a numerical growth interpolation.
    pulse=1.5+1.4*(.5+.5*math.sin(pct*math.tau*6))
    for seed in SEEDS:
        for species in SPECIES:
            records=report["source"][seed]["arms"][arm][species]
            points=layout(records,seed,species)
            color=PALETTE[species]
            for node in records[ti]["featured"][:12]:
                pos=points.get((ti,node["id"]))
                if pos is None:
                    continue
                cx,cy,_=pos
                rad=4+pulse
                d.ellipse((cx-rad,cy-rad,cx+rad,cy+rad),
                          outline=(*color,215),width=2)
    # Semantic counters tied to the current discrete snapshot.
    for seed,y in (("42",395),("73",637)):
        a=report["source"][seed]["arms"][arm]
        v=a["v_only"][ti]["component_count"]
        w=a["w_only"][ti]["component_count"]
        d.rounded_rectangle((885,y-28,1197,y-5),radius=6,
                            fill=(24,52,67,225))
        d.text((897,y-25),f"STEP {report['times'][ti]}  ·  V {v:,} regions  /  W {w:,} regions",
               font=font(11,True),fill="#E6F3F9")
    d.rectangle((0,712,round(pct*1280),720),fill="#67E5CF")
    return im.convert("RGB")


def render(report, movie, poster, *, arm="separated_070", seconds=24, fps=24):
    validate_report(report)
    if seconds not in (2,24,36) or fps not in (8,24):
        raise ValueError("Exceeded bounded cinematic budget")
    import imageio_ffmpeg
    movie,poster=Path(movie),Path(poster)
    movie.parent.mkdir(parents=True,exist_ok=True)
    poster.parent.mkdir(parents=True,exist_ok=True)
    plate=diagram(report,arm=arm)
    command=[imageio_ffmpeg.get_ffmpeg_exe(),"-hide_banner","-loglevel","error",
             "-y","-f","rawvideo","-pix_fmt","rgb24","-s","1280x720",
             "-r",str(fps),"-i","-","-an","-c:v","libx264","-preset","fast",
             "-crf","21","-pix_fmt","yuv420p","-movflags","+faststart",str(movie)]
    proc=subprocess.Popen(command,stdin=subprocess.PIPE)
    count=seconds*fps
    fingerprints=[]
    try:
        for i in range(count):
            img=frame(report,plate,i,count,arm=arm)
            if i in (0,count//3,2*count//3,count-1):
                fingerprints.append(hashlib.sha256(img.tobytes()).hexdigest())
            if i==int(count*.75):
                img.save(poster)
            proc.stdin.write(img.tobytes())
    finally:
        if proc.stdin:
            proc.stdin.close()
    if proc.wait()!=0 or not movie.exists() or movie.stat().st_size<8192:
        raise RuntimeError("Lineage ribbon encoder failed")
    if len(set(fingerprints))!=4 or poster.stat().st_size<4096:
        raise RuntimeError("Lineage film did not advance")
    info={
        "generation":"0034","edition":"native-4d-overlap-genealogy-ribbon-cinematic-v1",
        "model_arm":arm,"seeds":report["seeds"],
        "source_archive_sha256_by_seed":{
            k:v["source_archive_sha256"] for k,v in report["source"].items()},
        "times":report["times"],"n":16,"steps":240,
        "threshold":report["threshold"],
        "visualization":"Recorded component size nodes and exact voxel-overlap edges",
        "interpolated_numerical_states":False,
        "biological_lineages_inferred":False,
        "frames":count,"fps":fps,"seconds":seconds,"width":1280,"height":720,
        "revision":os.getenv("GITHUB_SHA","unversioned"),
    }
    movie.with_suffix(".render.json").write_text(json.dumps(info,indent=2)+"\n")
    return info


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data",required=True,type=Path)
    p.add_argument("--movie",required=True,type=Path)
    p.add_argument("--poster",required=True,type=Path)
    p.add_argument("--arm",choices=ARMS,default="separated_070")
    p.add_argument("--seconds",type=int,default=24)
    p.add_argument("--fps",type=int,default=24)
    args=p.parse_args()
    report=json.loads(args.data.read_text())
    print(json.dumps(render(report,args.movie,args.poster,arm=args.arm,
                            seconds=args.seconds,fps=args.fps),indent=2))


if __name__=="__main__":
    main()
