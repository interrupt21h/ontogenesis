"""G0035 Morphogenic Tide — two distinct films from archived native 4D fields.

This is a *derived visualization experiment*, not a new integration.
The material is an authentic z-max projection of each stored omega hyperplane
onto the native 16x16 y/x lattice. Smooth iso-ribbons and bloom are explicitly
artistic resampling; original numerical samples never interpolate in time.
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
from niche_spatial_render import load_fields

WIDTH, HEIGHT = 1280, 720
PLANE = 16
TIMES = list(range(0, 241, 24))
ARMS = ("separated_070", "near_transition")
COLORS = {"v": (57, 234, 209), "w": (250, 156, 109),
          "m": (154, 136, 226)}
LEVELS = (.12, .24, .42, .64)


def validate(data, info):
    if (info.get("seed"), info.get("n"), info.get("steps"),
        info.get("sample_steps")) != (73, 16, 240, TIMES):
        raise ValueError("Requires exact G0033 seed-73, 16^4, 240-step native archive")
    for arm in ARMS:
        for kind in ("v", "w", "m"):
            src = data.get(f"{arm}_{kind}")
            if src is None or src.dtype != np.float32 or src.shape != (11,16,16,16,16):
                raise ValueError("Missing original numerical field")
    return data, info


def projection(v, w, m):
    """Recorded 3D omega slice -> exact 2D z-maximum arrays, y/x orientation."""
    if any(a.shape != (PLANE,)*3 for a in (v,w,m)):
        raise ValueError("Projection expects original 16x16x16 float arrays")
    if not all(np.isfinite(a).all() and np.min(a) >= 0 for a in (v,w,m)):
        raise ValueError("Nonfinite or negative field")
    return {
        "v": np.max(v, axis=0).astype(np.float32),
        "w": np.max(w, axis=0).astype(np.float32),
        "m": np.max(m, axis=0).astype(np.float32),
        "native_v_active": int(np.count_nonzero(v > .1)),
        "native_w_active": int(np.count_nonzero(w > .1)),
        "native_joint": int(np.count_nonzero((v > .1) & (w > .1))),
    }


def native_contours(field, levels=LEVELS):
    """Grid-exact numerical isoband masks, without smoothing."""
    a = np.asarray(field, dtype=np.float32)
    if a.shape != (PLANE,PLANE):
        raise ValueError("Native contour grid must be 16x16")
    return np.stack([a >= x for x in levels]).astype(np.uint8)


def artistic_field(field, size):
    """Bicubic image-space interpolation ONLY; not a solver field or timestep."""
    a = np.uint8(np.clip(field,0,1)*255)
    return np.asarray(Image.fromarray(a,"L").resize(size,
                      Image.Resampling.BICUBIC), dtype=np.float32)/255.


def make_plate(projected, size=(480,480), *, light_phase=0.0):
    """Art-directed *visual isocontours* anchored to the measured z-max plane.

    The broad fields, thin luminous ridges and optical halo are presentation
    transforms; unlike the evidence edition these are not native cells.
    """
    from scipy.ndimage import gaussian_filter

    width,height=size
    y,x=np.mgrid[0:height,0:width].astype(np.float32)
    background=np.zeros((height,width,3),np.float32)
    background[:]=[3,12,22]
    halo=np.exp(-((x-width*.52)**2/(width*.80)**2+
                   (y-height*.53)**2/(height*.80)**2))
    background+=halo[...,None]*[7,12,21]
    luminous=np.zeros_like(background)
    levels=(.10,.145,.19,.235,.28,.325,.37,.415)
    for kind in ("m","v","w"):
        field=artistic_field(projected[kind],size)
        field=gaussian_filter(field,1.2)
        color=np.asarray(COLORS[kind],np.float32)
        if kind=="m":
            ridges=sum(np.exp(-((field-level)/.003)**2)
                       for level in (.12,.16,.20,.24))
            region=np.clip((field-.06)*.7,0,.18)
            edges=np.clip(ridges*.17,0,.8)
        else:
            # Genuine numerical contour levels, presented as glowing bands.
            # Each concentration is from a real, recorded z-max plane.
            ridges=sum(np.exp(-((field-level)/.0044)**2)
                       for level in levels)
            region=np.clip((field-.08)*.44,0,.22)
            edges=np.clip(ridges*.95,0,1.4)
        background+=(region+edges)[...,None]*color
        luminous+=np.clip(edges*.38,0,1)[...,None]*color
    # Ambient flicker is display-only and must never move numerical contours.
    background+=halo[...,None]*(.5+.5*math.cos(light_phase))*[.8,1.,1.4]
    plate=Image.fromarray(np.uint8(np.clip(background,0,255)),"RGB")
    bloom=Image.fromarray(np.uint8(np.clip(luminous,0,255)),"RGB")
    bloom=bloom.filter(ImageFilter.GaussianBlur(12))
    from PIL import ImageChops
    return ImageChops.add(plate,bloom)

def scene_state(data, arm, t, omega):
    if arm not in ARMS or not 0<=t<11 or not 0<=omega<16:
        raise ValueError("Selected view is not a stored numerical state")
    values=[data[f"{arm}_{k}"][t,omega] for k in ("v","w","m")]
    return projection(*values)


def state_at(index,count):
    if count<2 or not 0<=index<count:
        raise ValueError("Invalid film frame")
    progress=index/(count-1)
    act=min(2,int(progress*3))
    local=min(1.,max(0.,progress*3-act))
    t=min(10,int(local*11)) if act<2 else 10
    omega=min(15,int(local*16))
    return progress,act,t,omega


def gradient_background():
    y,x=np.mgrid[0:HEIGHT,0:WIDTH].astype(np.float32)
    bloom=np.exp(-((x-640)**2/600**2+(y-400)**2/500**2))
    colors=np.stack([5+7*bloom,12+11*bloom,23+16*bloom],axis=-1)
    return Image.fromarray(np.uint8(np.clip(colors,0,255)),"RGB")


def art_frame(data, info, index, count, backdrop, tile):
    progress,act,t,omega=state_at(index,count)
    image=backdrop.copy()
    d=ImageDraw.Draw(image)
    phase=progress*math.tau*2
    if act<2:
        arm=ARMS[act]
        plate=tile(arm,t,omega)
        # At full-frame scale the 16x16 numerical plane becomes an
        # extraordinary landscape of visual iso-surfaces, not a tiny map.
        display=plate.resize((690,514),Image.Resampling.BICUBIC)
        image.paste(display,(295,155))
        caption="A HABITAT OF COMPLEMENTARY NICHES" if act==0 else "THE MATCHED WORLD WITHOUT NICHES"
    else:
        left=tile(ARMS[0],t,omega).resize((516,427),Image.Resampling.BICUBIC)
        right=tile(ARMS[1],t,omega).resize((516,427),Image.Resampling.BICUBIC)
        image.paste(left,(100,199))
        image.paste(right,(666,199))
        caption="TWO ENVIRONMENTS / ONE INITIALIZATION"
    d=ImageDraw.Draw(image)
    d.text((43,20),"ONTOGENESIS   /   G0035   /   NATIVE FOUR-DIMENSIONAL FIELD ART",
           fill="#9fe5dc",font=font(17,True))
    d.text((42,58),"MORPHOGENIC TIDE",fill="#f1f7fc",font=font(49,True))
    d.text((44,118),caption,fill="#cbdfec",font=font(17))
    d.text((44,677),f"SEED 73  •  STORED STEP {info['sample_steps'][t]:03d} / 240  •  OMEGA {omega:02d}",
           fill="#bdd5e2",font=font(13))
    if act==2:
        d.text((104,629),"COMPLEMENTARY NICHE 0.70",fill="#7be6d9",font=font(14,True))
        d.text((671,629),"NO-NICHE CONTROL",fill="#f5bb93",font=font(14,True))
    d.rectangle((0,713,round(WIDTH*progress),720),fill="#74e5d8")
    return image,{"act":act,"step":info["sample_steps"][t],"omega":omega,
                  "arms":list(ARMS) if act==2 else [ARMS[act]]}


def evidence_frame(data, info, index,count,backdrop,projected):
    progress,_,t,omega=state_at(index,count)
    # Evidence edition always compares the same two arms at the same
    # stored sample, with exact native 16x16 cells.
    image=backdrop.copy()
    d=ImageDraw.Draw(image)
    d.text((42,20),"ONTOGENESIS / G0035 / REPRODUCIBLE NUMERICAL PLANE STUDY",
           font=font(17,True),fill="#80ded3")
    d.text((42,60),"THE EVIDENCE BELOW THE TIDE",font=font(38,True),fill="#f0f7fb")
    d.text((44,116),
           f"Seed 73  ·  actual recorded step {info['sample_steps'][t]}  ·  omega plane {omega}",
           font=font(17),fill="#bdd2df")
    for arm,x,label in ((ARMS[0],95,"COMPLEMENTARY NICHE 0.70"),
                        (ARMS[1],690,"NO-NICHE CONTROL")):
        p=projected(arm,t,omega)
        # Exact cell occupancy: no bicubic drawing, glow, or fabricated contours.
        v=(p["v"]>.1).astype(np.uint8)
        w=(p["w"]>.1).astype(np.uint8)
        m=(p["m"]>.2).astype(np.uint8)
        raster=np.empty((16,16,3),np.uint8)
        raster[:]=[9,24,34]
        raster=np.clip(raster.astype(np.int16)+
               v[...,None]*[49,170,151]+w[...,None]*[169,101,55]+
               m[...,None]*[43,39,83],0,255).astype(np.uint8)
        native=Image.fromarray(raster,"RGB").resize((480,480),
                                     Image.Resampling.NEAREST)
        image.paste(native,(x,171))
        d=ImageDraw.Draw(image)
        d.text((x,145),label,font=font(15,True),fill="#e1ecf5")
        d.text((x,659),
               f"Native z-max active columns: V {int(v.sum())}   W {int(w.sum())}   joint {int((v&w).sum())}",
               font=font(12),fill="#b7cfdb")
    d.rectangle((0,713,round(WIDTH*progress),720),fill="#76e6d4")
    return image,{"step":info["sample_steps"][t],"omega":omega,"arms":list(ARMS)}


def encode(output,images,fps):
    import imageio_ffmpeg
    output=Path(output)
    cmd=[imageio_ffmpeg.get_ffmpeg_exe(),"-hide_banner","-loglevel","error",
         "-y","-f","rawvideo","-pix_fmt","rgb24","-s","1280x720",
         "-r",str(fps),"-i","-","-an","-c:v","libx264","-preset","fast",
         "-crf","20","-pix_fmt","yuv420p","-movflags","+faststart",str(output)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for image in images:
            proc.stdin.write(image.tobytes())
    finally:
        if proc.stdin:
            proc.stdin.close()
    if proc.wait()!=0 or not output.is_file() or output.stat().st_size<8192:
        raise RuntimeError(f"Film encoding failed: {output}")
    return output


def render(archive,metadata,out,*,seconds=24,fps=24):
    if seconds not in (2,24,36) or fps not in (8,24):
        raise ValueError("Invalid bounded production parameters")
    data,info,source_sha=load_fields(archive,metadata)
    validate(data,info)
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    base=gradient_background()
    @lru_cache(maxsize=384)
    def projection_cache(arm,t,omega):
        return scene_state(data,arm,t,omega)
    @lru_cache(maxsize=384)
    def tile_cache(arm,t,omega):
        return make_plate(projection_cache(arm,t,omega),size=(480,480))
    count=seconds*fps
    records={}
    for edition in ("art","evidence"):
        basename=out/f"ontogenesis-0035-morphogenic-tide-{edition}"
        movie=basename.with_suffix(".mp4")
        poster=basename.with_suffix(".png")
        shots=[]
        def frames():
            for i in range(count):
                if edition=="art":
                    im,stamp=art_frame(data,info,i,count,base,tile_cache)
                else:
                    im,stamp=evidence_frame(data,info,i,count,base,projection_cache)
                if i in (0,count//3,2*count//3,count-1):
                    shots.append({"index":i,**stamp,
                                  "frame_sha256":hashlib.sha256(im.tobytes()).hexdigest()})
                if i==int(count*.75):
                    im.save(poster)
                yield im
        encode(movie,frames(),fps)
        if len({s["frame_sha256"] for s in shots})!=4 or poster.stat().st_size<4096:
            raise RuntimeError("Cinematic lacks temporal variation or poster")
        manifest={
            "generation":"0035","edition":edition,
            "project_type":"derived art-directed visualization, not a new solver run",
            "source_generation":"0033","seed":73,
            "source_archive_sha256":source_sha,
            "original_sample_steps":TIMES,"n":16,"steps":240,
            "arms":list(ARMS),"frames":count,"fps":fps,"seconds":seconds,
            "width":WIDTH,"height":HEIGHT,"review_samples":shots,
            "native_projection":"z-axis maximum of actual 3D omega hyperplane, 16x16 y/x",
            "numerical_interpolation":False,
            "artistic_transforms":(
                ["bicubic presentation resampling","visual isobands",
                 "light scattering / bloom","cinematic composition","editorial camera"]
                if edition=="art" else ["nearest-neighbor 16x16 grid display"]),
            "does_not_demonstrate":"new artificial organisms, autonomous ecology, or additional solver timesteps",
            "render_revision":os.getenv("GITHUB_SHA","unversioned")
        }
        basename.with_suffix(".render.json").write_text(json.dumps(manifest,indent=2)+"\n")
        records[edition]=manifest
    return records


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive",type=Path,required=True)
    parser.add_argument("--metadata",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--seconds",type=int,default=24)
    parser.add_argument("--fps",type=int,default=24)
    a=parser.parse_args()
    print(json.dumps(render(a.archive,a.metadata,a.out,
                            seconds=a.seconds,fps=a.fps),indent=2))


if __name__=="__main__":
    main()
