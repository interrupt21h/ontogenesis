"""G0037 Memory Strata — art-directed recorded-field cinema + exact-grid film.

Visual language: layered topographic ribbons made from native 4D matrix and
V/W concentration profiles. Each ribbon comes from one *actual recorded*
24-step snapshot; perspective, layered placement, glow and color are artistic.
The evidence edition shows exact pixelated 12x12 z-maximum projected cells.
Neither film synthesizes numerical timesteps, organisms, or adaptive memory.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
import subprocess
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from ecological_diagnostic_render import font

SEEDS=(42,73)
ARMS=("control","low","high")
CLOCK=(0,24,48,72,96,120)
WIDTH,HEIGHT=1280,720
PALETTE={"v":(91,234,209),"w":(249,170,112),"m":(155,139,245)}


def load(items):
    if len(items)!=2:raise ValueError("Two independently seeded sources required")
    sources={}
    for archive,metadata in items:
        info=json.loads(Path(metadata).read_text())
        digest=hashlib.sha256(Path(archive).read_bytes()).hexdigest()
        seed=info.get("seed")
        if seed not in SEEDS or seed in sources:raise ValueError("Seed mismatch")
        if (info.get("generation"),info.get("n"),info.get("steps"),
            info.get("sample_steps"),info.get("archive_sha256"))!=(
            "0037",12,120,list(CLOCK),digest):raise ValueError("Invalid recorded numerical scope")
        if info.get("arms")!=list(ARMS):raise ValueError("Missing prescribed control")
        with np.load(archive,allow_pickle=False) as f:
            fields={key:np.asarray(f[key]).copy() for key in f.files}
        for arm in ARMS:
            for channel in ("v","w","m"):
                a=fields.get(f"{arm}_{channel}")
                if a is None or a.shape!=(6,12,12,12,12) or a.dtype!=np.float32:
                    raise ValueError("Native 4D channel changed")
                if not np.isfinite(a).all() or a.min()< -1e-6:
                    raise ValueError("Invalid native concentration field")
        if not all(np.array_equal(fields["control_m"][0],fields[f"{arm}_m"][0])
                   for arm in ARMS):raise ValueError("Unmatched initial states")
        sources[seed]={"fields":fields,"meta":info,"sha":digest}
    return sources


def projected(source,arm,t,omega):
    if arm not in ARMS or not 0<=t<len(CLOCK) or not 0<=omega<12:
        raise ValueError("Unrecorded source state")
    f=source["fields"]
    return {k:np.max(f[f"{arm}_{k}"][t,omega],axis=0)
            for k in ("v","w","m")}


def read_clock(index,count):
    if count<2 or not 0<=index<count:raise ValueError("Invalid film frame")
    fraction=index/(count-1)
    act=min(2,int(fraction*3))
    part=min(1.,max(0.,fraction*3-act))
    step=min(5,int(part*6)) if act<2 else 5
    omega=min(11,int(part*12))
    return fraction,act,step,omega


def backdrop():
    y,x=np.mgrid[:HEIGHT,:WIDTH].astype(np.float32)
    radial=np.exp(-((x-640)**2/680**2+(y-360)**2/470**2))
    a=np.stack((4+7*radial,12+12*radial,26+19*radial),axis=-1)
    return Image.fromarray(a.astype(np.uint8),"RGB")


def strata(d,glow,source,arm,step,omega,x0,x1,upper,lower):
    """Native 2D concentration sheets as sculptural time-layered mesh terrain.

    Each surface comes from one actual 12x12 z-max projected 4D omega plane,
    at one authentic recorded numerical time. The arrangement in perspective,
    vertical exaggeration, translucent fill and optical bloom are artistic.
    No additional sampled field, velocity or agent is simulated.
    """
    layers=step+1
    is_wide=(x1-x0)>600
    amplitude=260 if is_wide else 118
    spacing=2.4 if is_wide else 1.35
    row_ids=(0,2,4,6,8,10,11)
    for t in range(layers):
        level=upper+(lower-upper)*(t+.75)/(layers+1)
        age=.27+.73*(t+1)/layers
        planes=projected(source,arm,t,omega)
        for kind,offset in (("m",8),("w",18),("v",-13)):
            grid=np.asarray(planes[kind],dtype=np.float64)
            if float(grid.max())<=.0001:
                continue
            color=PALETTE[kind]
            rows=[]
            for yidx in row_ids:
                row=[]
                for col in range(12):
                    # The height is directly proportional to authentic
                    # concentration. Global gain is a *display* exaggeration.
                    px=x0+(x1-x0)*col/11+(yidx-5.5)*(1.2 if is_wide else .6)
                    py=level+(yidx-5.5)*spacing+offset-amplitude*float(grid[yidx,col])
                    row.append((px,py))
                rows.append(row)
            # A sequence of actual 4D numerical lattice samples defines
            # each small mesh quadrilateral. Polygon opacity is art only.
            if kind!="m":
                for i in range(len(rows)-1):
                    for j in range(11):
                        quad=(rows[i][j],rows[i][j+1],
                              rows[i+1][j+1],rows[i+1][j])
                        d.polygon(quad,fill=(*color,int(7+10*age)))
            alpha=int((105 if kind=="m" else 135)*age)
            for i,row in enumerate(rows):
                if kind=="m" and i not in (0,2,4,6):
                    continue
                d.line(row,fill=(*color,alpha),width=2 if is_wide else 1,
                       joint="curve")
                if i in (0,3,6) and kind!="m":
                    glow.line([(px/2,py/2) for px,py in row],
                              fill=(*color,int(100*age)),width=2)
            for j in (0,3,6,9,11):
                d.line([row[j] for row in rows],
                       fill=(*color,int(42*age)),width=1)
            # Every spark is located at a native active projected cell.
            if kind!="m":
                for yidx in (2,6,10):
                    i=row_ids.index(yidx)
                    for j in (0,3,6,9,11):
                        if grid[yidx,j]>.1:
                            px,py=rows[i][j]
                            radius=1.5+1.3*age
                            d.ellipse((px-radius,py-radius,px+radius,py+radius),
                                      fill=(*color,int(245*age)))
    return layers


def art_frame(sources,index,count,base):
    fraction,act,step,omega=read_clock(index,count)
    image=base.copy()
    d=ImageDraw.Draw(image)
    gimg=Image.new("RGBA",(640,360),(0,0,0,0))
    g=ImageDraw.Draw(gimg,"RGBA")
    if act<2:
        seed=SEEDS[act]
        arm="high"
        strata(d,g,sources[seed],arm,step,omega,110,1170,212,605)
        subtitle=f"SEED {seed} / THE ACCUMULATING STRUCTURAL TRACE"
    else:
        seed=73
        for arm,x0,x1 in (("control",65,435),("low",455,825),("high",845,1215)):
            strata(d,g,sources[seed],arm,step,omega,x0,x1,252,587)
            d.text((x0+5,608),f"{arm.upper()}  /  {sources[seed]['meta']['feedback_gains'][arm]:.4f}",
                   font=font(14,True),fill="#c9dee8")
        subtitle="ONE INITIAL WORLD / THREE CAUSALLY DIFFERENT TRANSPORT RULES"
    glow=gimg.filter(ImageFilter.GaussianBlur(10)).resize((WIDTH,HEIGHT),Image.Resampling.BILINEAR)
    image=Image.alpha_composite(image.convert("RGBA"),glow).convert("RGB")
    d=ImageDraw.Draw(image)
    d.text((43,23),"ONTOGENESIS / G0037 / RECORDED FOUR-DIMENSIONAL MORPHOLOGY",
           font=font(16,True),fill="#8de2d6")
    d.text((40,58),"MEMORY STRATA",font=font(49,True),fill="#f0f9fc")
    d.text((43,119),subtitle,font=font(17),fill="#c2d7e2")
    d.text((43,676),f"ACTUAL RECORDED STEP {CLOCK[step]:03d} / 120   ·   OMEGA {omega:02d}   ·   NATIVE 4D FIELD",
           font=font(14),fill="#bdd1dd")
    d.rectangle((0,714,round(1280*fraction),720),fill="#73e5d2")
    return image,{"act":act,"seed":seed,"step":CLOCK[step],"omega":omega}


def evidence_frame(sources,index,count,base):
    fraction,act,step,omega=read_clock(index,count)
    seed=SEEDS[act] if act<2 else 73
    image=base.copy()
    d=ImageDraw.Draw(image)
    d.text((43,23),"ONTOGENESIS / G0037 / EXACT RECORDED NUMERICAL EVIDENCE",
           font=font(17,True),fill="#8de2d6")
    d.text((41,61),"STRUCTURAL PERSISTENCE",font=font(42,True),fill="#f2f9fc")
    d.text((44,121),f"Seed {seed} · step {CLOCK[step]} · omega {omega} · exact 12×12 z-max matrix cells",
           font=font(17),fill="#c0d4e2")
    for arm,x in (("control",75),("low",480),("high",885)):
        p=projected(sources[seed],arm,step,omega)["m"]
        raster=np.empty((12,12,3),np.uint8)
        raster[:]=[9,21,33]
        intensity=np.clip(p,0,1)
        raster[:]=np.uint8(np.clip(np.asarray([9,21,33])+
                           intensity[...,None]*np.asarray([156,131,210]),0,255))
        view=Image.fromarray(raster,"RGB").resize((320,400),Image.Resampling.NEAREST)
        image.paste(view,(x,191))
        d.text((x,159),f"{arm.upper()} / g={sources[seed]['meta']['feedback_gains'][arm]:.4f}",
               font=font(15,True),fill="#d0e4ee")
        sample=sources[seed]["meta"]["results"][arm]["observations"][step]
        score=sample["matrix_persistence"]
        value="n/a" if score is None or score["jaccard"] is None else f"{score['jaccard']:.4f}"
        d.text((x,599),f"Native 4D Jaccard: {value}",font=font(13),fill="#d2dfeb")
        d.text((x,623),f"Matrix mean: {sample['matrix_mean']:.5f}",
               font=font(13),fill="#bbd1df")
    d.text((44,679),"BOTH-EMPTY JACCARD IS UNDEFINED   ·   ACTUAL STORED STATES ONLY, NO SYNTHETIC INTERMEDIATE FIELDS",
           font=font(12),fill="#b6cfdd")
    d.rectangle((0,714,round(1280*fraction),720),fill="#73e5d2")
    return image,{"seed":seed,"step":CLOCK[step],"omega":omega}


def render(items,out,*,seconds=24,fps=24):
    if seconds not in (2,24) or fps not in (8,24):raise ValueError("Render out of CI budget")
    import imageio_ffmpeg
    sources=load(items);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    base=backdrop();count=seconds*fps
    summaries={}
    for edition in ("art","evidence"):
        stem=out/f"ontogenesis-0037-memory-strata-{edition}"
        cmd=[imageio_ffmpeg.get_ffmpeg_exe(),"-hide_banner","-loglevel","error",
             "-y","-f","rawvideo","-pix_fmt","rgb24","-s","1280x720",
             "-r",str(fps),"-i","-","-an","-c:v","libx264","-preset","fast",
             "-crf","20","-pix_fmt","yuv420p","-movflags","+faststart",str(stem.with_suffix(".mp4"))]
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
        shots=[]
        try:
            for i in range(count):
                img,mark=(art_frame(sources,i,count,base)
                          if edition=="art" else evidence_frame(sources,i,count,base))
                if i in (0,count//3,2*count//3,count-1):
                    shots.append({"frame":i,**mark,"sha256":hashlib.sha256(img.tobytes()).hexdigest()})
                if i==count*3//4:img.save(stem.with_suffix(".png"))
                proc.stdin.write(img.tobytes())
        finally:
            if proc.stdin:proc.stdin.close()
        if proc.wait()!=0 or not stem.with_suffix(".mp4").is_file():
            raise RuntimeError("Failed to encode H264: "+edition)
        if len({x["sha256"] for x in shots})!=4 or stem.with_suffix(".png").stat().st_size<4096:
            raise RuntimeError("No distinct cinematic temporal progression")
        manifest={"generation":"0037","edition":edition,
                  "source_archive_sha256_by_seed":{str(s):sources[s]["sha"] for s in SEEDS},
                  "source_gains":sources[42]["meta"]["feedback_gains"],
                  "recorded_times":list(CLOCK),"n":12,"steps":120,
                  "numerical_interpolation":False,"biological_memory_inferred":False,
                  "projection":"actual z-max hyperplane, profile averages only in art edition",
                  "artistic_treatment":(
                      ["stacked actual sampled-time strata","perspective arrangement","optical glow"]
                      if edition=="art" else ["nearest-neighbor measured matrix-grid cells"]),
                  "frames":count,"fps":fps,"seconds":seconds,"width":WIDTH,"height":HEIGHT,
                  "keyframes":shots,"revision":os.getenv("GITHUB_SHA","unversioned")}
        stem.with_suffix(".render.json").write_text(json.dumps(manifest,indent=2)+"\n")
        summaries[edition]=manifest
    return summaries


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("a","am","b","bm","out"):p.add_argument("--"+key,required=True,type=Path)
    p.add_argument("--seconds",type=int,default=24)
    p.add_argument("--fps",type=int,default=24)
    q=p.parse_args()
    print(json.dumps(render(((q.a,q.am),(q.b,q.bm)),q.out,seconds=q.seconds,fps=q.fps),indent=2))
