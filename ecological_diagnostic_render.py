"""G0030: two-chapter cinematic diagnostic of *measured* numerical time series.

Scene I shows the bounded early-viability screen (180 steps, no-change and
three early supply inversions). Scene II shows the four-arm ecological
factorial study (1200 steps, shared intervention at 600). The connected
lines are visual guides through sampled values, not interpolated organisms,
spatial field frames or newly calculated numerical simulation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ARMS_VIABILITY = ("unchanged", "invert_12", "invert_24", "invert_48")
ARMS_FACTORIAL = ("neither", "w_to_v_only", "v_to_w_only", "both")
PALETTE = ("#B8CBDF", "#50D5C4", "#F6AB70", "#D98CEA")
BACKGROUND = "#101D2C"
PANEL = "#192D40"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SOURCE_LABELS = {
    "viability": ("EARLY VIABILITY", "No change vs. early spatial supply inversions", 180),
    "factorial": ("FOUR-ARM ECOLOGY", "Cross-feeding controls · common reversal at step 600", 1200),
}


def validate(pilot, viability):
    for name, data, expected_steps, expected_arms in (
        ("factorial", pilot, 1200, ARMS_FACTORIAL),
        ("viability", viability, 180, ARMS_VIABILITY),
    ):
        if (data.get("generation"), data.get("steps"), data.get("n"),
            data.get("seeds")) != ("0030", expected_steps, 16, [42, 73]):
            raise ValueError(f"Unexpected verified G0030 {name} numerical scope")
        times = data.get("times", [])
        if not isinstance(times, list) or len(times) < 30 or times[0] != 0 or times[-1] != expected_steps:
            raise ValueError(f"{name}: invalid time series")
        for seed in ("42", "73"):
            arms = data.get("observations", {}).get(seed, {})
            if set(arms) != set(expected_arms):
                raise ValueError(f"{name}: missing/extra arms for seed {seed}")
            for arm, rows in arms.items():
                if [r["step"] for r in rows] != times:
                    raise ValueError(f"{name}: mismatched sampling for {seed} {arm}")
                if any(not 0 <= r["v_active"] <= 1 or not 0 <= r["w_active"] <= 1
                       or not math.isfinite(r["v_active"]) or not math.isfinite(r["w_active"])
                       for r in rows):
                    raise ValueError(f"{name}: invalid measured coverage")
    if pilot.get("season_switch") != 600:
        raise ValueError("Unexpected factorial intervention time")
    if viability.get("cases") != {"unchanged": None, "invert_12": 12,
                                  "invert_24": 24, "invert_48": 48}:
        raise ValueError("Unexpected viability intervention schedule")


def font(size, bold=False):
    file=FONT_BOLD if bold else FONT
    if not Path(file).is_file():
        # Pinned matplotlib includes verified DejaVu fonts on minimal runners.
        from matplotlib import get_data_path
        file=str(Path(get_data_path())/"fonts"/"ttf"/
                 ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"))
    return ImageFont.truetype(file, size)


def background():
    img = Image.new("RGB", (1280, 720), BACKGROUND)
    p = img.load()
    for y in range(720):
        for x in range(1280):
            glow = max(0.0, 1.0-math.hypot((x-1130)/1200, (y-80)/850))
            p[x,y] = (int(16 + 8*glow), int(29+18*glow), int(44+20*glow))
    return img


def line_plot(draw, rows_by_arm, metric, available, max_step, box, ymax, interventions):
    x0, y0, x1, y1 = box
    pad_left, pad_top, pad_right, pad_bottom = 42, 32, 18, 25
    cx0, cy0, cx1, cy1 = x0+pad_left, y0+pad_top, x1-pad_right, y1-pad_bottom
    w, h = cx1-cx0, cy1-cy0
    for value in (0, .5, 1):
        yy = int(cy1 - value*h)
        draw.line([(cx0,yy),(cx1,yy)], fill="#30465A", width=1)
        draw.text((x0+7,yy-7),f"{ymax*value:.1f}",font=font(12),fill="#9FB5C6")
    for moment in interventions:
        xp=int(cx0 + w*moment/max_step)
        if xp >= cx0 and xp<=cx1:
            for y in range(cy0,cy1,9):
                draw.line([(xp,y),(xp,min(y+4,cy1))],fill="#7E7A69",width=1)
    clock_x = int(cx0+w*max(0,min(available,max_step))/max_step)
    draw.line([(clock_x,cy0),(clock_x,cy1)],fill="#55738C",width=1)
    draw.text((cx0,cy1+6),"0",font=font(12),fill="#B2C4D3")
    half=max_step//2
    draw.text((cx0+w//2-11,cy1+6),str(half),font=font(12),fill="#B2C4D3")
    draw.text((cx1-35,cy1+6),str(max_step),font=font(12),fill="#B2C4D3")
    for index, (arm, rows) in enumerate(rows_by_arm.items()):
        points=[(int(cx0+w*r["step"]/max_step),
                 int(cy1-h*min(1.0,max(0.0,(r[metric]*100)/ymax))))
                for r in rows if r["step"]<=available]
        if len(points)>1:
            draw.line(points,fill=PALETTE[index],width=3,joint="curve")
        if points:
            x,y=points[-1]
            draw.ellipse((x-4,y-4,x+4,y+4),fill=PALETTE[index])
    # All values labeled are percentages of cells, not concentration density.
    draw.text((x0+13,y0+9),"ACTIVE CELL COVERAGE (%)",font=font(12,True),fill="#C1D6E7")


def panel(draw, dataset, seed, metric, box, step, max_step, title, ymax, intervention_times):
    x0,y0,x1,y1=box
    draw.rounded_rectangle(box,radius=13,fill=PANEL,outline="#34536B",width=2)
    draw.text((x0+16,y0+8),title,font=font(21,True),fill="#EAF3F8")
    hist=dataset["observations"][str(seed)]
    line_plot(draw,hist,metric,step,max_step,box,ymax,intervention_times)


def draw_frame(pilot,viability,t,seconds,base=None):
    if seconds<=0:
        raise ValueError("Render duration must be positive")
    transition=seconds*.42
    if t<transition:
        mode="viability"
        source=viability
        progress=min(1.0,t/transition)
        clock=int(progress*source["steps"])
        moments=(12,24,48)
        conclusion="V loses active coverage even without changing the environment"
    else:
        mode="factorial"
        source=pilot
        progress=min(1.0,(t-transition)/max(seconds-transition,1e-6))
        clock=int(progress*source["steps"])
        moments=(600,)
        conclusion="No sustained active coexistence was observed in the pilot"
    title,subtitle,limit=SOURCE_LABELS[mode]
    img=base.copy() if base is not None else background()
    d=ImageDraw.Draw(img)
    d.rectangle((0,0,1280,8),fill="#49CFBF")
    d.text((42,29),"ONTOGENESIS    /    GENERATION 0030",font=font(22,True),fill="#54D5C7")
    d.text((40,64),"WHEN COEXISTENCE FADES",font=font(43,True),fill="#F1F6FB")
    d.text((43,124),subtitle,font=font(18),fill="#B9CADA")
    d.rounded_rectangle((1027,35,1235,108),radius=13,outline="#536D81",width=2,fill="#203648")
    d.text((1044,48),"NUMERICAL STEP",font=font(12,True),fill="#A7C0D2")
    d.text((1045,65),f"{clock:04d} / {limit}",font=font(26,True),fill="#E8F2F8")
    labels=ARMS_VIABILITY if mode=="viability" else ARMS_FACTORIAL
    shown={"unchanged":"No change","invert_12":"Invert at 12",
           "invert_24":"Invert at 24","invert_48":"Invert at 48",
           "neither":"Neither","w_to_v_only":"W → V only",
           "v_to_w_only":"V → W only","both":"Both"}
    for i,label in enumerate(labels):
        x=43+i*305
        d.rounded_rectangle((x,163,x+18,179),radius=4,fill=PALETTE[i])
        d.text((x+29,159),shown[label],font=font(17),fill="#DCEAF3")
    v_max=max(1.0,max(100*r["v_active"] for arm in source["observations"].values()
                               for rows in arm.values() for r in rows)*1.15)
    v_max=min(100.0,math.ceil(v_max*10)/10)
    for r,seed in enumerate((42,73)):
        y=200+r*197
        panel(d,source,seed,"v_active",(41,y,625,y+179),clock,limit,
              f"SEED {seed}   /   SPECIES V",v_max,moments)
        panel(d,source,seed,"w_active",(652,y,1237,y+179),clock,limit,
              f"SEED {seed}   /   SPECIES W",100.0,moments)
    d.rounded_rectangle((41,599,1238,663),radius=11,fill="#22394C",outline="#365971",width=1)
    d.text((57,605),title,font=font(17,True),fill="#53D7C8")
    d.text((56,626),conclusion,font=font(16),fill="#EDF4F8")
    d.text((43,682),"MEASURED TIME-SERIES / LINES CONNECT SAVED SAMPLES / NOT SPATIAL SIMULATION FOOTAGE",
           font=font(12),fill="#B0C4D4")
    d.rectangle((0,713,round(1280*min(1,t/seconds)),720),fill="#54D6C7")
    return img


def render(pilot_path,viability_path,movie,poster,*,seconds=30,fps=24):
    if not 2<=seconds<=90 or fps not in (8,12,24,30):
        raise ValueError("Unsupported bounded render duration/fps")
    raw_a=Path(pilot_path).read_bytes()
    raw_b=Path(viability_path).read_bytes()
    pilot=json.loads(raw_a);viability=json.loads(raw_b)
    validate(pilot,viability)
    movie=Path(movie);poster=Path(poster)
    movie.parent.mkdir(parents=True,exist_ok=True)
    poster.parent.mkdir(parents=True,exist_ok=True)
    n=int(seconds*fps)
    base=background()
    import imageio_ffmpeg
    command=[imageio_ffmpeg.get_ffmpeg_exe(),"-hide_banner","-loglevel","error","-y",
             "-f","rawvideo","-pix_fmt","rgb24","-s","1280x720",
             "-r",str(fps),"-i","-","-an","-c:v","libx264",
             "-preset","fast","-crf","20","-pix_fmt","yuv420p",
             "-movflags","+faststart",str(movie)]
    sampled=[]
    proc=subprocess.Popen(command,stdin=subprocess.PIPE)
    try:
        for i in range(n):
            image=draw_frame(pilot,viability,i/fps,seconds,base)
            if i in (0,round(n*.35),round(n*.70),n-1):
                sampled.append(hashlib.sha256(image.tobytes()).hexdigest())
            if i==min(n-1,round(n*.78)):
                image.save(poster)
            proc.stdin.write(image.tobytes())
    finally:
        if proc.stdin:
            proc.stdin.close()
    if proc.wait()!=0 or not movie.exists() or movie.stat().st_size<8192:
        raise RuntimeError("Cinematic evidence encoding failed")
    if not poster.exists() or poster.stat().st_size<4096:
        raise RuntimeError("Diagnostic poster missing")
    if len(set(sampled))!=len(sampled):
        raise RuntimeError("Repeated/unchanged keyframes, failed animation")
    metadata={
        "generation":"0030","edition":"measured-ecology-diagnostic-1",
        "kind":"time-series animation, not spatial simulation footage",
        "width":1280,"height":720,"fps":fps,"seconds":seconds,
        "frames":n,"source_archive_sha256":{
            "g0030-pilot.json":hashlib.sha256(raw_a).hexdigest(),
            "g0030-viability.json":hashlib.sha256(raw_b).hexdigest()},
        "source_simulation_revisions":{
            "factorial":pilot.get("source_sha"),
            "viability":viability.get("source_sha")},
        "render_commit":os.getenv("GITHUB_SHA","unversioned"),
        "presentation":{
            "early_viability":"No-change control and early inversions at 12, 24, 48",
            "factorial":"Neither / W-to-V / V-to-W / both; common step-600 inversion",
            "curve_semantics":"Lines connect recorded discrete samples; clocks mark numerical step",
            "camera_or_spatial_voxels":False,"reported_measure":"cells with species mass above 0.1",
            "scientific_conclusion":"No sustained active coexistence demonstrated at tested scopes"},
        "selected_featured_film":False,
        "distinct_keyframe_hashes":len(set(sampled)),
    }
    movie.with_suffix(".render.json").write_text(json.dumps(metadata,indent=2)+"\n")
    return metadata


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--factorial",type=Path,required=True)
    p.add_argument("--viability",type=Path,required=True)
    p.add_argument("--movie",type=Path,required=True)
    p.add_argument("--poster",type=Path,required=True)
    p.add_argument("--seconds",type=int,default=30)
    p.add_argument("--fps",type=int,default=24)
    args=p.parse_args()
    print(json.dumps(render(args.factorial,args.viability,args.movie,args.poster,
                            seconds=args.seconds,fps=args.fps),indent=2))


if __name__=="__main__":
    main()
