"""G0034 / Luminous Habitat — art-directed film from real recorded 4D fields.

Three editorial acts: seed-73 complementary habitat, the matched control, and
a final diptych. The dark volumetric glass, bloom, camera and light falloff are
art direction. Every bright feature and filament is anchored to an actual
concentration sample or a real adjacent pair in a stored 3D hyperplane of the
native 4D state. No simulated states or organisms are invented.
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
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from ecological_diagnostic_render import font
from niche_spatial_render import load_fields

ARMS = ("separated_070", "near_transition")
KINDS = ("v", "w", "m")
COLORS = {"v": (68, 241, 211), "w": (255, 165, 110),
          "m": (119, 112, 194)}
LIMITS = {"v": 750, "w": 750, "m": 260}
EDGE_LIMIT = 480
WIDTH, HEIGHT = 1280, 720
SMALL = (640, 360)


def validate(data, info):
    if info.get("seed") != 73 or info.get("steps") != 240 or info.get("n") != 16:
        raise ValueError("Luminous Habitat requires G0033 seed 73 at 16^4 / 240 steps")
    if info["sample_steps"] != list(range(0, 241, 24)):
        raise ValueError("The eleven original discrete sample times are required")
    if set(info["treatments"]) != set(ARMS):
        raise ValueError("Both original matched habitat treatments required")
    for arm in ARMS:
        for kind in KINDS:
            if data[f"{arm}_{kind}"].shape != (11, 16, 16, 16, 16):
                raise ValueError("Changed native 4D numerical scope")
    return data, info


def geometry(v, w, m):
    """Produce exact slice coordinates and direct 3D face edges.

    A 4D hyperplane fixes omega; these segment edges are actual neighboring
    voxel pairs inside that hyperplane, not an inferred surface or streamline.
    """
    if v.shape != w.shape or v.shape != m.shape or v.shape != (16,)*3:
        raise ValueError("Expected one native 16^3 four-dimensional hyperplane")
    exclusive_v = (v > .1) & ~(w > .1)
    exclusive_w = (w > .1) & ~(v > .1)
    masks = {"v": exclusive_v, "w": exclusive_w, "m": m > .22}
    values = {"v": v, "w": w, "m": m}
    out = {}
    for kind in KINDS:
        indices = np.argwhere(masks[kind])
        strengths = values[kind][masks[kind]]
        if indices.size:
            chosen = np.argsort(-strengths, kind="stable")[:LIMITS[kind]]
            selected = indices[chosen].astype(np.float32)
            intensities = strengths[chosen].astype(np.float32)
        else:
            selected = np.zeros((0, 3), np.float32)
            intensities = np.zeros(0, np.float32)
        out[kind] = (selected, intensities)
    edges = {}
    for kind in ("v", "w"):
        links = []
        mask = masks[kind]
        for axis in range(3):
            # Neighbor j+1 in this 3D plane (nonwrapped, so boundaries are not
            # connected visually across the outside of the frame).
            slices_a = [slice(None)]*3
            slices_b = [slice(None)]*3
            slices_a[axis], slices_b[axis] = slice(0, -1), slice(1, None)
            shared = mask[tuple(slices_a)] & mask[tuple(slices_b)]
            coords = np.argwhere(shared)
            if coords.size:
                nxt = coords.copy()
                nxt[:, axis] += 1
                strengths = np.minimum(values[kind][tuple(coords.T)],
                                       values[kind][tuple(nxt.T)])
                for k in np.argsort(-strengths, kind="stable")[:EDGE_LIMIT]:
                    links.append((coords[k].astype(np.float32),
                                  nxt[k].astype(np.float32),
                                  float(strengths[k])))
        links.sort(key=lambda e: -e[2])
        edges[kind] = links[:EDGE_LIMIT]
    return out, edges


def project(points, angle, xcenter, ycenter, scale):
    if len(points) == 0:
        return np.empty((0, 2), np.float32), np.empty(0, np.float32)
    p = np.asarray(points, dtype=np.float32)
    z = p[:, 0]-7.5
    y = p[:, 1]-7.5
    x = p[:, 2]-7.5
    c,s = math.cos(angle),math.sin(angle)
    horiz = x*c - y*s
    depth = x*s + y*c
    # A camera-induced depth transform; numerical voxel positions unchanged.
    persp = 1 / (1 + depth/58)
    return np.column_stack((xcenter+horiz*scale*persp,
                            ycenter+(depth*.44-z*.91)*scale*persp)),depth


def studio_background():
    # Shared image throughout all frames, softly illuminated like a stage
    # rather than a second independent population.
    y, x = np.mgrid[0:HEIGHT, 0:WIDTH].astype(np.float32)
    warm = np.exp(-((x-285)**2/(470**2)+(y-410)**2/(430**2)))
    cool = np.exp(-((x-965)**2/(490**2)+(y-260)**2/(410**2)))
    arr = np.stack((7+9*warm+2*cool, 15+8*warm+10*cool,
                    25+11*warm+19*cool), axis=-1)
    return Image.fromarray(np.clip(arr,0,255).astype(np.uint8),"RGB")


def scene(draw, soft, fields, edges, *, center, scale, angle):
    # All emitted pixels are anchored to native 3D data points or same-species
    # nearest-neighbor pairs. The glow and scale do not change the solver.
    cx, cy = center
    output = []
    for kind in ("m", "v", "w"):
        pts, strength = fields[kind]
        coords, depth = project(pts,angle,cx,cy,scale)
        order = np.argsort(depth)
        color = COLORS[kind]
        for i in order:
            xx,yy = map(float,coords[i])
            if not (15 < xx < WIDTH-15 and 130 < yy < 685):
                continue
            amount = float(np.clip(strength[i],0,1))
            if kind == "m":
                radius = 1.3
                alpha = int(75+85*amount)
            else:
                radius = 1.3 + 2.2*amount
                alpha = int(140+115*amount)
            soft.ellipse((xx*.5-radius*1.9,yy*.5-radius*1.9,
                          xx*.5+radius*1.9,yy*.5+radius*1.9),
                         fill=tuple(int(channel*.6) for channel in color)+(180,))
            draw.ellipse((xx-radius,yy-radius,xx+radius,yy+radius),
                         fill=color+(alpha,))
        output.append(len(coords))
        if kind in ("v", "w"):
            # Filaments require a genuine adjacent pair from the same native
            # concentration mask. There are no fake connecting trajectories.
            for a,b,amount in edges[kind]:
                endpoints,_=project(np.stack((a,b)),angle,cx,cy,scale)
                p0,p1=endpoints
                if min(p0[0],p1[0])<15 or max(p0[0],p1[0])>WIDTH-15:
                    continue
                if min(p0[1],p1[1])<130 or max(p0[1],p1[1])>685:
                    continue
                intensity = float(np.clip(amount,0,1))
                draw.line((tuple(map(float,p0)),tuple(map(float,p1))),
                          fill=color+(int(70+135*intensity),),
                          width=1 if intensity < .5 else 2)
                soft.line((tuple(p0*.5),tuple(p1*.5)),
                          fill=color+(int(70+110*intensity),),width=2)
    return output


def frame(data, info, index, count, base, prepared):
    if count<2 or not 0<=index<count:
        raise ValueError("Invalid frame index")
    progress=index/(count-1)
    # Act I: complementary habitat; Act II: no-niche matched control;
    # Act III: true same-time diptych of the two recorded worlds.
    act = min(2,int(progress*3))
    local = progress*3-act
    if act < 2:
        arm=ARMS[act]
        time_index=min(10,int(local*11))
        omega=min(15,int(local*16))
        panels=((arm,(640,390),23.8),)
    else:
        time_index=10
        omega=min(15,int(local*16))
        panels=((ARMS[0],(342,393),17.3),(ARMS[1],(943,393),17.3))
    angle=.24+math.tau*(.20+.64*progress)
    img=base.copy().convert("RGBA")
    d=ImageDraw.Draw(img,"RGBA")
    bloom=Image.new("RGBA",SMALL,(0,0,0,0))
    glow=ImageDraw.Draw(bloom,"RGBA")
    for arm,center,scale in panels:
        field, links=prepared(arm,time_index,omega)
        scene(d,glow,field,links,center=center,scale=scale,angle=angle)
    # Optical light is created only from existing luminous field features.
    light=bloom.filter(ImageFilter.GaussianBlur(12)).resize((WIDTH,HEIGHT),
                                                 Image.Resampling.BILINEAR)
    img=Image.alpha_composite(img,light)
    d=ImageDraw.Draw(img,"RGBA")
    # Gallery-like typography occupies a quiet top strip, never used as
    # artificial geometry or as an extra visual population.
    d.text((44,22),"ONTOGENESIS  /  FOUR-DIMENSIONAL ARTIFICIAL-LIFE-INSPIRED WORLDS",
           font=font(16,True),fill=(179,221,228,245))
    title=("THE LUMINOUS HABITAT" if act==0 else
           "A WORLD WITHOUT THE NICHE" if act==1 else
           "SAME BEGINNING  /  TWO FATES")
    d.text((42,58),title,font=font(42,True),fill=(242,249,251,255))
    d.text((44,113),
           f"Seed 73  ·  recorded state {info['sample_steps'][time_index]}/240  ·  4D omega plane {omega:02d}",
           font=font(16),fill=(191,216,227,245))
    if act==2:
        d.text((179,590),"PRESCRIBED NICHE 0.70",font=font(14,True),
               fill=(91,233,213,255))
        d.text((787,590),"NO SPATIAL PREFERENCE",font=font(14,True),
               fill=(255,183,122,255))
        d.line((640,165,640,613),fill=(80,112,132,95),width=2)
    d.rounded_rectangle((43,637,1238,673),radius=10,fill=(14,34,49,220))
    d.text((60,644),"CYAN  /  EXCLUSIVE V     AMBER  /  EXCLUSIVE W     VIOLET  /  MATRIX",
           font=font(13),fill=(218,233,241,255))
    d.text((44,686),
           "ACTUAL RECORDED 4D FIELD · REAL ADJACENT-VOXEL FILAMENTS · LIGHT AND CAMERA ARE ARTISTIC",
           font=font(11),fill=(179,206,220,240))
    d.rectangle((0,711,round(WIDTH*progress),720),
                fill=(91,236,215,255))
    return img.convert("RGB"), {"act":act,"step":info["sample_steps"][time_index],
                                "omega":omega,"arms":[x[0] for x in panels]}


def render(archive,metadata,movie,poster,*,seconds=24,fps=24):
    if seconds not in (2,24,36) or fps not in (8,24):
        raise ValueError("Outside bounded Luminous Habitat rendering budget")
    data,info,sha=load_fields(archive,metadata)
    validate(data,info)
    @lru_cache(maxsize=64)
    def prepared(arm,t,omega):
        return geometry(*(data[f"{arm}_{kind}"][t,omega] for kind in KINDS))
    base=studio_background()
    import imageio_ffmpeg
    movie,poster=Path(movie),Path(poster)
    movie.parent.mkdir(parents=True,exist_ok=True)
    poster.parent.mkdir(parents=True,exist_ok=True)
    command=[imageio_ffmpeg.get_ffmpeg_exe(),"-hide_banner","-loglevel","error",
             "-y","-f","rawvideo","-pix_fmt","rgb24","-s","1280x720",
             "-r",str(fps),"-i","-","-an","-c:v","libx264","-preset","fast",
             "-crf","20","-pix_fmt","yuv420p","-movflags","+faststart",str(movie)]
    proc=subprocess.Popen(command,stdin=subprocess.PIPE)
    count=seconds*fps
    hashes=[];shots=[]
    try:
        for i in range(count):
            img,shot=frame(data,info,i,count,base,prepared)
            if i in (0,count//3,2*count//3,count-1):
                hashes.append(hashlib.sha256(img.tobytes()).hexdigest())
                shots.append({"frame":i,**shot})
            if i==count*3//4:
                img.save(poster)
            proc.stdin.write(img.tobytes())
    finally:
        if proc.stdin:
            proc.stdin.close()
    if proc.wait()!=0 or not movie.is_file() or movie.stat().st_size<8192:
        raise RuntimeError("Luminous Habitat H264 encoding failed")
    if len(set(hashes))!=4 or poster.stat().st_size<4096:
        raise RuntimeError("Luminous Habitat failed temporal / poster checks")
    output={
        "generation":"0034","edition":"luminous-habitat-native-field-cinema-v1",
        "source_generation":"0033","seed":73,
        "source_archive_sha256":sha,
        "n":16,"steps":240,"times":info["sample_steps"],
        "arms":list(ARMS),"w_threshold":0.1,"v_threshold":0.1,
        "matrix_threshold":0.22,
        "visual_geometry":"Actual 3D hyperplane voxel locations and genuine same-mask nearest-neighbor voxel pairs",
        "artistic_transforms":["studio lighting","optical bloom","depth perspective",
                                "cinematic camera orbit","recorded-state focus",
                                "color materialization","editorial split-screen"],
        "interpolated_numerical_states":False,
        "organisms_inferred":False,
        "frames":count,"seconds":seconds,"fps":fps,"width":1280,"height":720,
        "review_samples":shots,"revision":os.getenv("GITHUB_SHA","unversioned"),
    }
    movie.with_suffix(".render.json").write_text(json.dumps(output,indent=2)+"\n")
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ("archive","metadata","movie","poster"):
        parser.add_argument("--"+key,required=True,type=Path)
    parser.add_argument("--seconds",type=int,default=24)
    parser.add_argument("--fps",type=int,default=24)
    a=parser.parse_args()
    print(json.dumps(render(a.archive,a.metadata,a.movie,a.poster,
                            seconds=a.seconds,fps=a.fps),indent=2))


if __name__=="__main__":
    main()
