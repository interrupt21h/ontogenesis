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


def composite_2d(scene, meta):
    """Artistic field map of one authentic 2D slice (or documented projection)."""
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


def composite(volume, meta, depth):
    """Gaussian depth composite across the observed z axis (not a true slice)."""
    n = volume.shape[-1]
    z = np.arange(n, dtype=np.float32)
    distance = np.minimum((z-depth) % n, (depth-z) % n)
    weights = np.exp(-.5*(distance / max(1.5, n/5.5))**2)
    weights /= weights.sum()
    scene = np.tensordot(weights, volume, axes=(0, 1))
    return composite_2d(scene, meta)


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


def voxel_cloud(volume, shape, progress):
    """Rotating projected 3D voxel glyphs, all sourced from observed lattice values.

    Camera rotation and adaptive intensity exposure are *presentation*, not
    field transport. Optional fine edges join genuinely adjacent grid voxels.
    """
    width,height=shape
    n=volume.shape[-1]
    grid=np.indices((n,n,n),dtype=np.float32).reshape(3,-1).T
    grid-=(n-1)/2.0
    z,y,x=grid.T
    phi=2*math.pi*progress*1.45+.3
    theta=.46+.12*math.sin(2*math.pi*progress)
    xr=x*math.cos(phi)-z*math.sin(phi)
    zr=x*math.sin(phi)+z*math.cos(phi)
    yr=y*math.cos(theta)-zr*math.sin(theta)
    depth=y*math.sin(theta)+zr*math.cos(theta)
    perspective=2.0/(2.2-depth/n)
    sx=width/2+xr*(width/n)*.67*perspective
    sy=height/2+yr*(height/n)*.78*perspective

    strength=np.zeros(n**3,dtype=np.float32)
    rgb=np.zeros((n**3,3),dtype=np.float32)
    colors=((1,.70,.33),(1,.31,.72),(.27,.91,.85),(.46,.59,1.))
    matrix_strength=None
    for channel,amplitude,weight,color in (
        (0,.004,.76,colors[0]),
        (1,.02,.50,colors[1]),
        (2,.02,.52,colors[2]),
        (3,.08,.58,colors[3])
    ):
        raw=volume[channel].ravel()
        low,high=np.percentile(raw,(54,98.5))
        exposure=np.clip((raw-low)/max(high-low,1e-9),0,1)
        # Do not magnify numerical extinction into fictitious chemistry.
        exposure*=min(1.,float(np.max(raw))/amplitude)
        exposure*=weight
        rgb+=exposure[:,None]*np.asarray(color,dtype=np.float32)
        strength+=exposure
        if channel==0:
            matrix_strength=exposure
    # Only a *measured* resource deficit may generate a red scar.
    deficit=np.clip((1-volume[4].ravel()-.003)/.12,0,1)*.6
    strength+=deficit
    rgb+=deficit[:,None]*np.asarray((1.,.13,.09),dtype=np.float32)
    significant=max(float(np.percentile(strength,61)),.07)
    pixels=np.where(strength>significant)[0]
    canvas=Image.new("RGB",(width,height),INK)
    if len(pixels)==0:
        return canvas
    glow=Image.new("RGBA",(width,height),(0,0,0,0))
    fine=Image.new("RGBA",(width,height),(0,0,0,0))
    g=ImageDraw.Draw(glow,"RGBA")
    d=ImageDraw.Draw(fine,"RGBA")

    # A restrained mesh is a visualization of *grid-neighbor adjacency*,
    # not biological fibers or an inferred transport network.
    structural=(matrix_strength.reshape(n,n,n)>.45)
    if np.any(structural):
        lines=Image.new("RGBA",(width,height),(0,0,0,0))
        pen=ImageDraw.Draw(lines,"RGBA")
        for axis in range(3):
            a=structural.copy()
            b=np.roll(structural,-1,axis=axis)
            a&=b
            ix=np.where(a)
            if not ix[0].size:
                continue
            src=np.ravel_multi_index(ix,(n,n,n))
            neighbor=list(ix)
            neighbor[axis]=(neighbor[axis]+1)%n
            dst=np.ravel_multi_index(tuple(neighbor),(n,n,n))
            for u,v in zip(src[::3],dst[::3]):
                if abs(sx[u]-sx[v])>width*.16 or abs(sy[u]-sy[v])>height*.16:
                    continue
                pen.line((float(sx[u]),float(sy[u]),float(sx[v]),float(sy[v])),
                         fill=(196,136,79,35),width=1)
        canvas=Image.alpha_composite(canvas.convert("RGBA"),lines).convert("RGB")

    # Painter's algorithm for correctly layered luminous voxel glyphs.
    for k in pixels[np.argsort(depth[pixels])]:
        power=float(np.clip(strength[k],0,2))
        shade=np.clip(rgb[k]/max(strength[k],.08),0,1)
        color=tuple(int(c*255) for c in shade)
        xx,yy=float(sx[k]),float(sy[k])
        size=(1.5+1.3*power)*float(perspective[k])
        g.ellipse((xx-size*3,yy-size*3,xx+size*3,yy+size*3),
                  fill=color+(min(180,int(20+38*power)),))
        d.ellipse((xx-size,yy-size,xx+size,yy+size),
                  fill=color+(min(255,int(65+90*power)),))
    cloud=Image.alpha_composite(canvas.convert("RGBA"),
                                glow.filter(ImageFilter.GaussianBlur(max(3,width//90))))
    return Image.alpha_composite(cloud,fine).convert("RGB")


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
    """Immersive full-bleed art: the measured 3D world is the entire frame."""
    if width<640 or height<360 or width%2 or height%2:
        raise ValueError("Even frame dimensions of at least 640x360 required")
    event=meta["event_step"]
    total=meta["steps"]
    frac=float(step)/total
    n=volume.shape[-1]
    depth=((n*.5)+(n*.88)*math.sin(2*math.pi*(frac*.67+.08)))%n

    fog=camera_frame(composite(volume,meta,depth),(width,height),frac)
    cloud=voxel_cloud(volume,(width,height),frac)
    image=Image.blend(fog,cloud,.94)

    # Inset spatial evidence is used only briefly so diagnostic graphics
    # never dominate the cinematic composition.
    idx=int(round(depth))%n
    if (.28<=frac<=.42) or (.77<=frac<=.87):
        size=min(int(width*.20),int(height*.32))
        section=composite_2d(volume[:,idx,:,:],meta)
        section=section.resize((size,size),Image.Resampling.BICUBIC)
        x=width-size-int(width*.055)
        y=int(height*.18)
        image.paste(section,(x,y))
        pane=ImageDraw.Draw(image)
        pane.rectangle((x-2,y-2,x+size+2,y+size+2),
                       outline=TEAL,width=2)
        pane.text((x,y+size+13),f"MEASURED z={idx:02d} / ω={meta['recording']['omega_index']:02d}",
                  font=font(max(10,int(height*.019)),bold=True),fill=WHITE)

    # Legibility gradients are a graphic overlay, not a simulated field.
    veil=Image.new("RGBA",(width,height),(0,0,0,0))
    vd=ImageDraw.Draw(veil,"RGBA")
    vd.rectangle((0,0,width,int(height*.16)),fill=(5,11,25,156))
    vd.rectangle((0,int(height*.85),width,height),fill=(5,11,25,168))
    image=Image.alpha_composite(image.convert("RGBA"),veil).convert("RGB")
    d=ImageDraw.Draw(image)
    pad=int(width*.038)
    d.text((pad,int(height*.038)),"ONTOGENESIS  /  0028",
           font=font(max(20,int(height*.038)),bold=True),fill=WHITE)
    d.text((pad,int(height*.103)),phase(step,event,total),
           font=font(max(12,int(height*.022)),bold=True),
           fill=TEAL if step<event else AMBER)
    d.text((width-int(width*.31),int(height*.064)),
           "A FIELD OF ARTIFICIAL LIFE",
           font=font(max(10,int(height*.019))),fill=MUTED)

    # Explicit symbolic annotation: not a physical wavefront.
    if event<=step<=event+total*.045:
        age=(step-event)/max(total*.045,1)
        radius=int((.10+.25*age)*min(width,height))
        cx,cy=width//2,height//2
        d.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),
                  outline=AMBER,width=max(2,int(6*(1-age))))
        d.text((pad,int(height*.77)),"EXTERNAL DISTURBANCE  /  EVENT MARKER",
               font=font(max(11,int(height*.022)),bold=True),fill=AMBER)

    # Playback progress is intentionally subordinate to the changing world.
    info_y=int(height*.885)
    d.text((pad,info_y),f"STEP {step:04.0f} / {total:04d}",
           font=font(max(12,int(height*.025)),bold=True),fill=WHITE)
    d.text((pad,int(height*.945)),caption,
           font=font(max(9,int(height*.014))),fill=MUTED)
    x0=int(width*.40);x1=width-pad;line_y=int(height*.907)
    d.line((x0,line_y,x1,line_y),fill=(48,75,92),width=4)
    d.line((x0,line_y,x0+int((x1-x0)*frac),line_y),fill=TEAL,width=4)
    cut=x0+int((x1-x0)*event/total)
    d.line((cut,line_y-12,cut,line_y+12),fill=AMBER,width=3)
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
    caption="OBSERVED VOXELS  /  ROTATING PROJECTION + VISUAL TEMPORAL BLENDING (NOT EXTRA SIMULATION STEPS)"
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
