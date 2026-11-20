"""G0028 cinematic renderer: depth-traversed artificial-life fields.

Scientific values are read exclusively from the recorded NPZ archive.
Spatial reconstruction, temporal blending, color mixing, bloom and camera
motion are artistic operations, not additional numerical simulation steps.
"""
import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

CHANNELS = ("matrix", "species_v", "species_w", "pulse", "energy")
INK = (7, 14, 27)
MUTED = (144, 174, 191)
WHITE = (230, 240, 247)
TEAL = (74, 229, 219)
AMBER = (254, 181, 94)
PINK = (243, 93, 156)
BLUE = (112, 149, 249)


def font(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    path = Path("/usr/share/fonts/truetype/dejavu") / name
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def read_archive(archive, metadata):
    meta = json.loads(Path(metadata).read_text())
    if meta["generation"] != "0028" or meta["recording"]["channel_order"] != list(CHANNELS):
        raise ValueError("Wrong generation or field order")
    expected = meta["archive"]["sha256"]
    actual = hashlib.sha256(Path(archive).read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError("Archive SHA-256 mismatch; refuse to render unverified fields")
    with np.load(archive, allow_pickle=False) as payload:
        data = payload["states"]
        steps = payload["steps"]
    if list(data.shape) != meta["recording"]["shape"]:
        raise ValueError("Archive shape mismatch")
    if data.ndim != 5 or data.shape[1] != len(CHANNELS):
        raise ValueError("Expected time,field,z,y,x archive")
    if data.shape[-1] != data.shape[-2] or data.shape[-1] != data.shape[-3]:
        raise ValueError("Spatial sampling is not cubic")
    if steps[0] != 0 or steps[-1] != meta["steps"] or not np.all(np.diff(steps)>0):
        raise ValueError("Missing or nonmonotonic numerical samples")
    if not np.isfinite(data).all():
        raise ValueError("Nonfinite numerical archive")
    return data, steps, meta


def normalize(a, meta, field, contrast=1.0):
    spans = meta["recording"]["fixed_exposure_percentiles"][field]
    lo, hi = spans["p02"], spans["p995"]
    minimum_span = .025 if field == "energy" else 1e-4
    scaled = np.clip((a.astype(np.float32) - lo) / max(hi-lo, minimum_span), 0, 1)
    return np.clip(scaled ** contrast, 0, 1)


def composite(volume, meta, depth):
    """Depth-weighted (z) luminosity from a fixed-omega observed 3D volume."""
    n = volume.shape[-1]
    z = np.arange(n, dtype=np.float32)
    distance = np.minimum((z-depth) % n, (depth-z) % n)
    weights = np.exp(-.5*(distance / max(1.5, n/5.5))**2)
    weights /= weights.sum()
    scene = np.tensordot(weights, volume, axes=(0, 1))
    # scene indices: matrix, V, W, pulse, energy.
    matrix = normalize(scene[0], meta, "matrix", .78)
    v = normalize(scene[1], meta, "species_v", .68)
    w = normalize(scene[2], meta, "species_w", .68)
    pulse = normalize(scene[3], meta, "pulse", .75)
    energy = normalize(scene[4], meta, "energy", .85)
    deficit = np.clip(1 - energy, 0, 1)
    contour = np.hypot(np.roll(matrix,1,axis=0)-np.roll(matrix,-1,axis=0),
                       np.roll(matrix,1,axis=1)-np.roll(matrix,-1,axis=1))
    contour = np.clip(contour*1.35,0,1)
    # The palette is an artistic encoding of *recorded* numerical fields.
    rgb = np.stack((
        .032 + .61*matrix + .39*v + .18*deficit,
        .052 + .55*w + .37*matrix + .21*pulse,
        .090 + .64*pulse + .48*v + .43*contour + .12*w
    ),axis=-1)
    rgb = np.clip(np.power(rgb,.83), 0, 1)
    return Image.fromarray(np.uint8(np.round(255*rgb)), "RGB")


def camera_frame(lowres, shape, progress):
    w,h = shape
    # Bicubic is a DISPLAY reconstruction of measured lattice cells.
    scene = lowres.resize((w,h), Image.Resampling.BICUBIC)
    # Continuous camera movement within the reconstructed field.
    angle = 3.1 * math.sin(progress * 2*math.pi*2.3)
    zoom = 1.065 + .020*math.sin(progress*math.pi*3)
    enlarged = scene.resize((int(w*zoom)+2,int(h*zoom)+2),Image.Resampling.BICUBIC)
    scene = enlarged.crop(((enlarged.width-w)//2,(enlarged.height-h)//2,
                           (enlarged.width+w)//2,(enlarged.height+h)//2))
    scene = scene.rotate(angle,resample=Image.Resampling.BICUBIC,
                         expand=False,fillcolor=INK)
    # A low-energy glow reveals chemical interfaces rather than masking them.
    glow=scene.filter(ImageFilter.GaussianBlur(max(3, w//70)))
    return Image.blend(glow,scene,.76)


def phase(step, event, total):
    if step < event*.55:
        return "I  /  EMERGENCE"
    if step < event:
        return "II  /  A LIVING FIELD"
    if step < event + total*.045:
        return "III  /  DISTURBANCE"
    if step < total*.91:
        return "IV  /  RESPONSE"
    return "V  /  AFTERMATH"


def draw_movie_frame(volume, meta, *, step, frame_number, total_frames,
                     width, height, caption):
    if width<640 or height<360 or width%2 or height%2:
        raise ValueError("Even frame dimensions of at least 640x360 required")
    event=meta["event_step"]
    total=meta["steps"]
    frac=float(step)/total
    n=volume.shape[-1]
    depth=((n*.5)+(n*.88)*math.sin(2*math.pi*(frac*.67+.08)))%n
    hero_w=int(width*.77)
    side_w=width-hero_w
    top=int(height*.17)
    bottom=int(height*.115)
    world_h=height-top-bottom
    image=Image.new("RGB",(width,height),INK)
    d=ImageDraw.Draw(image)
    d.rectangle((0,0,width,5),fill=TEAL if step<event else AMBER)
    d.text((int(width*.04),int(height*.036)),"ONTOGENESIS  /  0028",
           font=font(max(17,int(height*.040)),bold=True),fill=WHITE)
    d.text((int(width*.04),int(height*.103)),phase(step,event,total),
           font=font(max(13,int(height*.025)),bold=True),
           fill=TEAL if step<event else AMBER)
    d.text((width-int(width*.25),int(height*.055)),"AN ARTIFICIAL UNIVERSE",
           font=font(max(10,int(height*.018))),fill=MUTED)

    margin=int(width*.036)
    hw=hero_w-margin-12
    hh=world_h-8
    hero=camera_frame(composite(volume,meta,depth),(hw,hh),frac)
    image.paste(hero,(margin,top))
    d=ImageDraw.Draw(image)
    d.rounded_rectangle((margin,top,margin+hw,top+hh),radius=6,
                        outline=(54,106,127),width=2)
    d.text((margin+18,top+16),"DEPTH-COMPOSITE   /   FIXED ω",
           font=font(max(10,int(height*.019)),bold=True),fill=WHITE)

    # The inset shows a real z section from the same recorded omega hyperplane.
    idx=int(round(depth))%n
    inset=composite(volume,meta,float(idx))
    inset_size=min(int(side_w*.72),int(world_h*.43))
    inset=inset.resize((inset_size,inset_size),Image.Resampling.BICUBIC)
    inset_x=hero_w+int(side_w*.12)
    inset_y=top+int(world_h*.07)
    image.paste(inset,(inset_x,inset_y))
    d=ImageDraw.Draw(image)
    d.rectangle((inset_x-2,inset_y-2,inset_x+inset_size+2,inset_y+inset_size+2),
                outline=TEAL,width=2)
    label_sz=max(10,int(height*.019))
    d.text((inset_x,inset_y+inset_size+13),f"VOLUME SECTION  z={idx:02d}",
           font=font(label_sz,bold=True),fill=WHITE)
    d.text((inset_x,inset_y+inset_size+43),f"ω={meta['recording']['omega_index']:02d}  /  N={n}",
           font=font(label_sz),fill=MUTED)
    legend_y=top+int(world_h*.73)
    for i,(color,label) in enumerate(((AMBER,"MATRIX"),(PINK,"SPECIES V"),
                                     (TEAL,"SPECIES W"),(BLUE,"EXCITATION"))):
        y=legend_y+i*max(20,int(height*.035))
        d.ellipse((inset_x,y,inset_x+9,y+9),fill=color)
        d.text((inset_x+18,y-3),label,font=font(label_sz),fill=MUTED)

    # The outline is an EXPLICIT symbolic annotation, not a physical wave.
    if event <= step <= event+total*.045:
        age=(step-event)/max(total*.045,1)
        cx=margin+hw//2;cy=top+hh//2
        radius=int((.1+.22*age)*min(hw,hh))
        d.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),
                  outline=AMBER,width=max(2,int(5*(1-age))))
        d.text((margin+18,top+hh-34),"EXTERNAL SHOCK / EVENT MARKER",
               fill=AMBER,font=font(label_sz,bold=True))

    y=height-int(height*.078)
    d.text((margin,y-6),f"STEP {step:04.0f} / {total:04d}",
           fill=WHITE,font=font(max(12,int(height*.023)),bold=True))
    bar_x=int(width*.35);bar_end=width-margin
    d.line((bar_x,y+7,bar_end,y+7),fill=(53,78,94),width=4)
    d.line((bar_x,y+7,bar_x+int((bar_end-bar_x)*frac),y+7),fill=TEAL,width=4)
    event_x=bar_x+int((bar_end-bar_x)*event/total)
    d.line((event_x,y-4,event_x,y+19),fill=AMBER,width=3)
    d.text((margin,height-24),caption,
           fill=MUTED,font=font(max(9,int(height*.014))))
    return image


def render(archive, metadata, movie, poster, *, seconds=60, fps=24,
           width=1280, height=720):
    data, steps, meta = read_archive(archive,metadata)
    if not (6 <= seconds <= 180 and 12 <= fps <= 60):
        raise ValueError("seconds in [6,180], fps in [12,60]")
    total=int(round(seconds*fps))
    out=Path(movie);out.parent.mkdir(parents=True,exist_ok=True)
    poster=Path(poster);poster.parent.mkdir(parents=True,exist_ok=True)
    ffmpeg=[
        "ffmpeg","-hide_banner","-loglevel","error","-y",
        "-f","rawvideo","-pix_fmt","rgb24","-s",f"{width}x{height}",
        "-r",str(fps),"-i","pipe:0",
        "-an","-c:v","libx264","-preset","veryfast","-crf","18",
        "-pix_fmt","yuv420p","-movflags","+faststart",str(out)
    ]
    written=set()
    caption="RECORDED NUMERICAL VOLUMES  /  SPATIAL RECONSTRUCTION + VISUAL TEMPORAL BLENDING"
    proc=subprocess.Popen(ffmpeg,stdin=subprocess.PIPE)
    try:
        for i in range(total):
            t=meta["steps"]*i/max(total-1,1)
            upper=min(int(np.searchsorted(steps,t,side="right")),len(steps)-1)
            lower=max(0,upper-1)
            delta=float(steps[upper]-steps[lower])
            f=(t-float(steps[lower]))/delta if delta>0 else 0.
            volume=((1-f)*data[lower].astype(np.float32)
                    +f*data[upper].astype(np.float32))
            frame=draw_movie_frame(volume,meta,step=t,frame_number=i,
                                   total_frames=total,width=width,height=height,
                                   caption=caption)
            if i==round(total*.70):
                frame.save(poster,optimize=True)
            if i%max(1,total//9)==0:
                written.add(hashlib.sha256(frame.tobytes()).hexdigest())
                print(f"Rendered {i}/{total}  /  step {t:.1f}",flush=True)
            proc.stdin.write(frame.tobytes())
        proc.stdin.close()
        code=proc.wait()
        if code!=0:
            raise RuntimeError(f"FFmpeg failed with exit code {code}")
    except Exception:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        raise
    if len(written)<5:
        raise AssertionError("Cinematic render has insufficient frame variation")
    if not poster.is_file() or not out.is_file() or out.stat().st_size<4096:
        raise AssertionError("Missing cinematic film or poster")
    print(json.dumps({"movie":str(out),"bytes":out.stat().st_size,
                      "samples":int(len(steps)),"rendered_frames":total,
                      "unique_sampled_visual_frames":len(written),
                      "poster":str(poster)},indent=2),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--metadata",type=Path,required=True)
    p.add_argument("--movie",type=Path,required=True)
    p.add_argument("--poster",type=Path,required=True)
    p.add_argument("--seconds",type=int,default=60)
    p.add_argument("--fps",type=int,default=24)
    p.add_argument("--width",type=int,default=1280)
    p.add_argument("--height",type=int,default=720)
    a=p.parse_args()
    render(a.input,a.metadata,a.movie,a.poster,seconds=a.seconds,
           fps=a.fps,width=a.width,height=a.height)


if __name__=="__main__":
    main()
