"""G0036 Feedback Aurora: art and evidence films of actual matched runs.

The artwork maps authentic control/feedback concentration differences from
native 12^4 fields. Curved illuminated difference contours are artistic image
resampling; the exact 12x12 evidence companion uses nearest-neighbor cells.
Each frame selects one of eleven real recorded numerical steps and a real
fourth-axis hyperplane. No interpolated chemistry or imagined organisms.
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
from PIL import Image, ImageDraw, ImageFilter
from ecological_diagnostic_render import font

SEEDS=(42,73)
ARMS=("control","feedback")
TIMES=tuple(range(0,121,12))
SIZE=(1280,720)
COLORS=((85,231,211),(255,170,122),(159,139,244))


def load_sources(items):
    if len(items)!=2:
        raise ValueError("Expected two independently matched seed field archives")
    sources={}
    for path,meta in items:
        info=json.loads(Path(meta).read_text())
        digest=hashlib.sha256(Path(path).read_bytes()).hexdigest()
        seed=info.get("seed")
        if (info.get("generation"),info.get("n"),info.get("steps"),
            info.get("sample_steps"),info.get("archive_sha256"))!=(
                "0036",12,120,list(TIMES),digest):
            raise ValueError("Invalid G0036 archive provenance or numerical clock")
        if seed not in SEEDS or seed in sources:
            raise ValueError("Missing or repeated matched seed")
        with np.load(path,allow_pickle=False) as npz:
            fields={key:np.asarray(npz[key]).copy() for key in npz.files}
        for arm in ARMS:
            for kind in ("v","w","m","e"):
                arr=fields.get(f"{arm}_{kind}")
                if arr is None or arr.dtype!=np.float32 or arr.shape!=(11,12,12,12,12):
                    raise ValueError("Changed numerical field layout")
                if not np.isfinite(arr).all() or arr.min()< -1e-6:
                    raise ValueError("Invalid source field")
        if info["numerical"]["control"]["hashes"]["0"]!=info["numerical"]["feedback"]["hashes"]["0"]:
            raise ValueError("Initial numeric states are not matched")
        sources[seed]={"fields":fields,"meta":info,"sha":digest}
    return sources


def projection(a):
    if a.shape!=(12,12,12):
        raise ValueError("Requires one actual 12^3 omega hyperplane")
    return np.max(a,axis=0).astype(np.float32)


def observation(source,step_index,omega):
    if not 0<=step_index<11 or not 0<=omega<12:
        raise ValueError("Unrecorded numerical state")
    values=source["fields"]
    p={}
    for arm in ARMS:
        for kind in ("v","w","m"):
            p[f"{arm}_{kind}"]=projection(values[f"{arm}_{kind}"][step_index,omega])
    for kind in ("v","w","m"):
        p[f"delta_{kind}"]=p[f"feedback_{kind}"]-p[f"control_{kind}"]
    return p


def background():
    y,x=np.mgrid[0:720,0:1280].astype(np.float32)
    left=np.exp(-((x-350)**2/(630**2)+(y-385)**2/(470**2)))
    right=np.exp(-((x-1010)**2/(650**2)+(y-430)**2/(480**2)))
    rgb=np.stack([5+8*right+3*left,11+11*left+5*right,
                  24+14*left+8*right],axis=-1)
    return Image.fromarray(np.uint8(np.clip(rgb,0,255)),"RGB")


def film_state(index,count):
    if not 0<=index<count or count<2:
        raise ValueError("Invalid film frame")
    progress=index/(count-1)
    act=min(2,int(progress*3))
    local=min(1.,progress*3-act)
    step=min(10,int(local*11)) if act<2 else 10
    omega=min(11,int(local*12))
    return progress,act,step,omega


def palette_plate(obs, mode, scale, *, width=500,height=455):
    """Artistic contour plate; normalizer is fixed for the entire evidence set."""
    def resample(kind):
        a=obs[kind]
        source=np.uint8(np.clip(a,0,1)*255)
        return np.asarray(Image.fromarray(source,"L").resize((width,height),
                          Image.Resampling.BICUBIC),dtype=np.float32)/255.
    from scipy.ndimage import gaussian_filter
    y,x=np.mgrid[0:height,0:width].astype(np.float32)
    rgb=np.zeros((height,width,3),np.float32);rgb[:]=[5,15,27]
    radial=np.exp(-((x-width*.53)**2/(width*.68)**2+
                    (y-height*.48)**2/(height*.70)**2))
    rgb+=radial[...,None]*[8,13,24]
    for kind,color in zip(("v","w","m"),COLORS):
        if mode=="control":
            arr=resample("control_"+kind)
        elif mode=="feedback":
            arr=resample("feedback_"+kind)
        else:
            delta=obs["delta_"+kind]
            # Map the common fixed global maximum into image-space intensity.
            a=np.clip(np.abs(delta)/max(scale[kind],1e-9),0,1)
            arr=np.asarray(Image.fromarray(np.uint8(a*255),"L").resize(
                       (width,height),Image.Resampling.BICUBIC),np.float32)/255.
        arr=gaussian_filter(arr,1.0)
        yy,xx=np.gradient(arr)
        grad=np.clip(np.hypot(xx,yy)*7,0,1)
        if mode=="delta":
            bands=sum(np.exp(-((arr-t)/.012)**2)
                      for t in (.13,.23,.34,.45,.58,.72))
            intensity=np.clip(bands*.8,0,1.4)+arr*.21
        else:
            bands=sum(np.exp(-((arr-t)/.006)**2)
                      for t in (.12,.20,.29,.39,.51,.64))
            intensity=np.clip(bands*.67,0,1.3)+arr*.14
        rgb+=(intensity+grad*.14)[...,None]*np.asarray(color,np.float32)
    plate=Image.fromarray(np.uint8(np.clip(rgb,0,255)),"RGB")
    return Image.blend(plate,plate.filter(ImageFilter.GaussianBlur(9)),.13)


def art_frame(sources,index,count,base,plate,scale):
    pct,act,step,omega=film_state(index,count)
    img=base.copy()
    draw=ImageDraw.Draw(img)
    if act==0:
        seed=42;mode="delta"
        p=plate(seed,step,omega,mode)
        img.paste(p.resize((700,495),Image.Resampling.BICUBIC),(291,171))
        subtitle="THE INTERVENTION LEAVES A TRACE"
    elif act==1:
        seed=73;mode="delta"
        p=plate(seed,step,omega,mode)
        img.paste(p.resize((700,495),Image.Resampling.BICUBIC),(291,171))
        subtitle="THE SAME RULE / A DIFFERENT BEGINNING"
    else:
        seed=73
        a=plate(seed,step,omega,"control")
        b=plate(seed,step,omega,"feedback")
        img.paste(a.resize((532,425)),(99,203))
        img.paste(b.resize((532,425)),(651,203))
        subtitle="ONE INITIAL STATE / TWO TRANSPORT HISTORIES"
    draw=ImageDraw.Draw(img)
    draw.text((42,20),"ONTOGENESIS / G0036 / COUPLED FOUR-DIMENSIONAL EXPERIMENT",
              fill="#91e3d8",font=font(16,True))
    draw.text((41,56),"FEEDBACK AURORA",fill="#f1f8fb",font=font(50,True))
    draw.text((44,121),subtitle,fill="#c4d9e6",font=font(18))
    draw.text((44,675),f"SEED {seed}  ·  RECORDED STEP {TIMES[step]:03d} / 120  ·  OMEGA PLANE {omega:02d}",
              fill="#b9d4df",font=font(14))
    if act==2:
        draw.text((113,634),"ORIGINAL CONTROL",fill="#ebbfa4",font=font(15,True))
        draw.text((665,634),"STRUCTURAL FEEDBACK",fill="#7ce8d7",font=font(15,True))
    draw.rectangle((0,713,round(1280*pct),720),fill="#6de7d6")
    return img,{"act":act,"seed":seed,"step":TIMES[step],"omega":omega}


def evidence_frame(sources,index,count,base):
    pct,act,step,omega=film_state(index,count)
    seed=SEEDS[0] if act==0 else SEEDS[1]
    obs=observation(sources[seed],step,omega)
    img=base.copy()
    d=ImageDraw.Draw(img)
    d.text((43,22),"ONTOGENESIS / G0036 / ORIGINAL NUMERICAL EVIDENCE",
           font=font(17,True),fill="#8ce6d8")
    d.text((42,60),"THE CAUSAL COMPARISON",font=font(41,True),fill="#f0f7fb")
    d.text((44,121),f"Seed {seed} · step {TIMES[step]} · omega {omega} · 12×12 z-max columns",
           font=font(17),fill="#c3d8e3")
    for arm,x in (("control",91),("feedback",683)):
        v,w,m=(obs[f"{arm}_{kind}"] for kind in ("v","w","m"))
        vv=(v>.1).astype(np.uint8);ww=(w>.1).astype(np.uint8)
        mm=(m>.2).astype(np.uint8)
        rgb=np.zeros((12,12,3),np.int16)
        rgb[:]=[11,23,36]
        rgb+=vv[...,None]*[45,181,157]
        rgb+=ww[...,None]*[176,111,65]
        rgb+=mm[...,None]*[36,38,84]
        view=Image.fromarray(np.uint8(np.clip(rgb,0,255)),"RGB")
        img.paste(view.resize((500,440),Image.Resampling.NEAREST),(x,182))
        d=ImageDraw.Draw(img)
        d.text((x,151),arm.upper(),font=font(17,True),fill="#eaf3f6")
        counts=f"V columns {int(vv.sum())} · W columns {int(ww.sum())} · shared {int((vv&ww).sum())}"
        d.text((x,630),counts,font=font(13),fill="#c1d5de")
    d.text((44,680),"EXACT SAMPLED NUMERICAL COLUMNS — NO INTERPOLATED FIELDS, CONTOURS OR GLOW",
           font=font(12),fill="#bcd4df")
    d.rectangle((0,713,round(1280*pct),720),fill="#6de7d6")
    return img,{"seed":seed,"step":TIMES[step],"omega":omega}


def render(inputs,out,*,seconds=24,fps=24):
    if seconds not in (2,24) or fps not in (8,24):
        raise ValueError("Exceeds bounded two-film rendering budget")
    sources=load_sources(inputs)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    scales={}
    for kind in ("v","w","m"):
        maximum=0.
        for seed in SEEDS:
            f=sources[seed]["fields"]
            delta=np.abs(f[f"feedback_{kind}"]-f[f"control_{kind}"])
            maximum=max(maximum,float(delta.max()))
        scales[kind]=maximum
    @lru_cache(maxsize=120)
    def plate(seed,t,omega,mode):
        return palette_plate(observation(sources[seed],t,omega),mode,scales)
    base=background()
    import imageio_ffmpeg
    count=seconds*fps; manifests={}
    for edition in ("art","evidence"):
        prefix=out/f"ontogenesis-0036-feedback-aurora-{edition}"
        cmd=[imageio_ffmpeg.get_ffmpeg_exe(),"-hide_banner","-loglevel","error",
             "-y","-f","rawvideo","-pix_fmt","rgb24","-s","1280x720",
             "-r",str(fps),"-i","-","-an","-c:v","libx264","-preset","fast",
             "-crf","20","-pix_fmt","yuv420p","-movflags","+faststart",
             str(prefix.with_suffix(".mp4"))]
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
        shots=[]
        try:
            for i in range(count):
                image,clock=(art_frame(sources,i,count,base,plate,scales)
                             if edition=="art" else evidence_frame(sources,i,count,base))
                if i in (0,count//3,2*count//3,count-1):
                    shots.append({"frame":i,"clock":clock,
                                  "sha256":hashlib.sha256(image.tobytes()).hexdigest()})
                if i==count*3//4:
                    image.save(prefix.with_suffix(".png"))
                proc.stdin.write(image.tobytes())
        finally:
            if proc.stdin:
                proc.stdin.close()
        movie=prefix.with_suffix(".mp4")
        if proc.wait()!=0 or not movie.is_file() or movie.stat().st_size<8192:
            raise RuntimeError("Failed cinematic encode: "+str(movie))
        if len({r["sha256"] for r in shots})!=4 or prefix.with_suffix(".png").stat().st_size<4096:
            raise RuntimeError("Duplicate cinematic keyframes or missing poster")
        manifest={
            "generation":"0036","edition":edition,
            "source_archive_sha256_by_seed":{str(s):sources[s]["sha"] for s in SEEDS},
            "seeds":list(SEEDS),"arms":list(ARMS),"sample_steps":list(TIMES),
            "n":12,"steps":120,"frames":count,"fps":fps,"seconds":seconds,
            "width":1280,"height":720,"numerical_interpolation":False,
            "global_difference_color_scales":scales,
            "projection":"actual z-max native 12^3 omega hyperplane",
            "artistic_treatments":(
                ["bloom","fixed-scale numerical-difference isocontours",
                 "image-space resampling","three-act comparison"]
                if edition=="art" else ["nearest-neighbor original 12x12 display"]),
            "keyframes":shots,
            "revision":os.getenv("GITHUB_SHA","unversioned"),
            "limits":"Finite prescribed numerical feedback, not evidence of evolved artificial life"
        }
        prefix.with_suffix(".render.json").write_text(json.dumps(manifest,indent=2)+"\n")
        manifests[edition]=manifest
    return manifests


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("a","am","b","bm","out"):
        p.add_argument("--"+key,required=True,type=Path)
    p.add_argument("--seconds",type=int,default=24)
    p.add_argument("--fps",type=int,default=24)
    v=p.parse_args()
    print(json.dumps(render(((v.a,v.am),(v.b,v.bm)),v.out,
                            seconds=v.seconds,fps=v.fps),indent=2))


if __name__=="__main__":
    main()
