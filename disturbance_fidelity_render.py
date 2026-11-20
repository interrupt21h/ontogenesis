"""Fidelity edition of G0028: G0025-class volumetric ray integration.

The ray field is rendered from real numerical hyperplanes. Orbiting camera,
omega/temporal interpolation, exposure mapping and glow are VISUAL DISPLAY
operations, not additional model steps or physical flow measurements.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.ndimage import map_coordinates

from disturbance_cinematic_fidelity import CHANNELS, digest_file

DARK=(5,12,23)
INK=(227,242,252)
SOFT=(147,182,201)
COPPER=(252,171,82)
CYAN=(66,231,215)


def font(size,bold=False):
    name="DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    path=Path("/usr/share/fonts/truetype/dejavu")/name
    return ImageFont.truetype(str(path),size) if path.exists() else ImageFont.load_default()


def read_fidelity_archive(path,manifest):
    manifest=json.loads(Path(manifest).read_text())
    if manifest["generation"]!="0028" or manifest["edition"]!="cinematic-fidelity-2":
        raise ValueError("Not a G0028 fidelity archive")
    if manifest["recording"]["channel_order"]!=list(CHANNELS):
        raise ValueError("Wrong numerical channel order")
    if digest_file(Path(path))!=manifest["archive"]["sha256"]:
        raise ValueError("SHA-256 provenance mismatch")
    with np.load(path,allow_pickle=False) as archive:
        states=archive["states"]
        steps=archive["steps"]
        omega=archive["omega_indices"]
        dense_steps=archive["dense_steps"]
        dense_states=archive["dense_states"]
    if states.ndim!=6 or states.shape[2]!=len(CHANNELS):
        raise ValueError("Expected samples,omega,channel,z,y,x")
    if list(states.shape)!=manifest["recording"]["shape"]:
        raise ValueError("Incorrect native lattice shape")
    if list(map(int,omega))!=manifest["recording"]["omega_indices"]:
        raise ValueError("Mismatched omega indexing")
    if list(map(int,dense_steps))!=manifest["recording"]["dense_steps"]:
        raise ValueError("Mismatched keyframe steps")
    if list(dense_states.shape)!=manifest["recording"]["dense_shape"]:
        raise ValueError("Inconsistent dense float32 keyframes")
    if states.dtype!=np.float16 or dense_states.dtype!=np.float32:
        raise ValueError("Incorrect numerical archive precision")
    if not np.all(np.diff(steps)>0) or steps[0]!=0 or steps[-1]!=manifest["steps"]:
        raise ValueError("Missing or unordered sample times")
    if not np.isfinite(states).all() or not np.isfinite(dense_states).all():
        raise ValueError("Nonfinite native field samples")
    if not np.array_equal(dense_states[:,0,omega[0]],np.array([
        dense_states[i,0,int(omega[0])] for i in range(len(dense_steps))
    ])):
        raise ValueError("Malformed dense checkpoint indexing")
    return states,steps,omega,manifest


def observed_volume(states,steps,omega,step,omega_pos):
    """Interpolation for display only; all vertices have measured provenance."""
    upper=int(np.searchsorted(steps,step,side="right"))
    upper=min(len(steps)-1,max(1,upper))
    lower=upper-1
    dt=float(steps[upper]-steps[lower])
    fraction=np.clip((step-float(steps[lower]))/dt,0,1) if dt else 0
    # Parameter omega_pos runs over the ordered measured hyperplanes. The
    # periodic 4D grid is intrinsically cyclic, but the between-plane
    # imagery is interpolated, not independently simulated.
    p0=int(math.floor(omega_pos))%len(omega)
    p1=(p0+1)%len(omega)
    q=omega_pos-math.floor(omega_pos)
    a=states[lower,p0].astype(np.float32)
    b=states[upper,p0].astype(np.float32)
    mix=(1-fraction)*a+fraction*b
    if p0!=p1 and q>1e-8:
        c=states[lower,p1].astype(np.float32)
        d=states[upper,p1].astype(np.float32)
        mix=(1-q)*mix+q*((1-fraction)*c+fraction*d)
    return mix,{"time_lower":int(steps[lower]),"time_upper":int(steps[upper]),
                "omega_lower":int(omega[p0]),"omega_upper":int(omega[p1]),
                "temporal_alpha":float(fraction),"omega_alpha":float(q)}


def scale_field(field,metadata,channel,floor):
    # A fixed across-time exposure. When the whole species becomes
    # numerically extinct, it is not artificially normalized to full light.
    p995=metadata["recording"]["fixed_exposure_percentiles"][channel]["p995"]
    return np.clip(field/max(p995,floor),0,1)


def volumetric_ray(volume,metadata,progress,rays=96):
    """Orthographic emission/absorption from 3D measured fields, as in G0025."""
    if rays<24 or rays>160:
        raise ValueError("Ray sampling must lie between 24 and 160")
    n=volume.shape[-1]
    if volume.shape!=(len(CHANNELS),n,n,n):
        raise ValueError("Invalid volume")
    a=np.linspace(-n*.88,n*.88,rays,dtype=np.float32)
    z,y,x=np.meshgrid(a,a,a,indexing="ij")
    spin=progress*math.pi*3.1+.24
    elevation=.28+.17*math.sin(progress*2*math.pi)
    ce,se=np.cos(elevation),np.sin(elevation)
    yy=ce*y-se*z
    zz=se*y+ce*z
    c,s=np.cos(spin),np.sin(spin)
    coords=np.array((-s*x+c*zz, yy, c*x+s*zz),dtype=np.float32)+(n-1)/2
    inside=np.all((coords>=0)&(coords<n-1),axis=0)
    fields=[map_coordinates(volume[i],coords,order=1,
                             mode="constant",cval=0,prefilter=False)
            for i in range(len(CHANNELS))]
    matrix,v,w,pulse,energy,trait,recovery=fields
    # A near-uniform, chemically extinct world must NOT be rendered as a
    # luminous opaque box. Relative matrix contrast preserves measured
    # spatial differences, then an absolute concentration gate suppresses
    # numeric ghosts when all concentrations diminish.
    matrix_native=volume[0].astype(np.float32)
    lower,upper=np.percentile(matrix_native,(35,99.5))
    m=np.clip((matrix-lower)/max(upper-lower,.002),0,1)
    m*=min(1.,float(upper)/.005)
    # Use the actual discrete matrix gradient to illuminate interfaces.
    gradients=np.gradient(matrix_native)
    edge_native=np.sqrt(sum(g*g for g in gradients))
    edge=map_coordinates(edge_native,coords,order=1,mode="constant",
                         cval=0,prefilter=False)
    edge/=max(float(np.percentile(edge_native,99.0)),.001)
    edge=np.clip(edge,0,1)*min(1.,float(matrix_native.max())/.012)
    a=scale_field(v,metadata,"species_v",.012)
    b=scale_field(w,metadata,"species_w",.012)
    p=scale_field(pulse,metadata,"pulse",.05)
    t=np.clip(np.abs(trait-.5)/.25,0,1)*inside
    r=scale_field(recovery,metadata,"recovery",.05)
    scar=np.clip((1-energy-.003)/.20,0,1)*inside
    energy=np.clip(energy,0,1)

    rgb=np.zeros((rays,rays,3),np.float32)
    trans=np.ones((rays,rays),np.float32)
    palette=np.array(((.96,.47,.73), (1.,.32,.08), (.07,.71,1.),
                      (.32,1.,.48), (.96,.24,.25),(.56,.38,1.),
                      (1.,.13,.05),(.22,.92,.91)),dtype=np.float32)
    for k in range(rays):
        # Uses measured concentrations, after documented artistic exposure.
        # Per-step alpha is bounded so a uniformly faint field does not
        # completely conceal the internal volume.
        components=np.stack((
            .42*m[k], .96*a[k], .96*b[k], .35*p[k],
            .23*r[k], .18*t[k], .93*scar[k], .63*edge[k]))
        density=components.sum(axis=0)
        opacity=(1-np.exp(-.11*density))*inside[k]
        weight=np.maximum(density,1e-7)
        light=np.tensordot(components.transpose(1,2,0),
                            palette,axes=([2],[0]))/weight[...,None]
        light*=.35+.65*energy[k,:,:,None]
        light+=scar[k,:,:,None]*np.array((.18,.01,0),np.float32)
        rgb+=trans[:,:,None]*opacity[:,:,None]*light
        trans*=1-opacity
    rgb=np.clip(rgb*1.7,0,1)**.78
    return Image.fromarray(np.uint8(np.clip(rgb*255,0,255)),"RGB")


def phase(step,event,total):
    if step<event*.40:return "I  /  PRIMORDIAL ORGANIZATION"
    if step<event:return "II  /  CHEMICAL LANDSCAPES"
    if step<event+total*.05:return "III  /  LOCALIZED DISTURBANCE"
    if step<total*.90:return "IV  /  INTERVENTION RESPONSE"
    return "V  /  RESIDUAL STRUCTURE"


def compose(vol,metadata,step,omega_position,width,height,ray_samples):
    progress=step/max(metadata["steps"],1)
    ray=volumetric_ray(vol,metadata,progress,ray_samples)
    background=ray.resize((width,height),Image.Resampling.BICUBIC).filter(
        ImageFilter.GaussianBlur(max(14,width//45)))
    canvas=Image.blend(Image.new("RGB",(width,height),DARK),background,.22)
    side=int(height*.94)
    primary=ray.resize((side,side),Image.Resampling.BICUBIC)
    canvas.paste(primary,((width-side)//2,(height-side)//2))
    # Overlaid blocks are artistic HUD, never evidence diagrams.
    overlay=Image.new("RGBA",(width,height),(0,0,0,0))
    d=ImageDraw.Draw(overlay,"RGBA")
    top=int(height*.135);bottom=int(height*.85)
    d.rectangle((0,0,width,top),fill=(4,10,19,162))
    d.rectangle((0,bottom,width,height),fill=(4,10,19,175))
    event=metadata["event_step"]
    if event<=step<event+metadata["steps"]*.05:
        age=(step-event)/(metadata["steps"]*.05)
        radius=int((.07+.33*age)*side)
        cx,cy=width//2,height//2
        d.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),
                  outline=(255,176,96,int(205*(1-age))),width=3)
    image=Image.alpha_composite(canvas.convert("RGBA"),overlay).convert("RGB")
    draw=ImageDraw.Draw(image)
    inset=int(width*.045)
    draw.text((inset,int(height*.030)),"ONTOGENESIS  /  G0028",
              font=font(max(21,height//28),True),fill=INK)
    draw.text((inset,int(height*.095)),phase(step,event,metadata["steps"]),
              font=font(max(11,height//52),True),fill=CYAN if step<event else COPPER)
    draw.text((width-int(width*.28),int(height*.063)),
              "VOLUMETRIC ARTIFICIAL UNIVERSE",
              font=font(max(10,height//65)),fill=SOFT)
    draw.text((inset,int(height*.885)),f"t = {step:.1f} / {metadata['steps']}",
              font=font(max(11,height//38),True),fill=INK)
    draw.text((inset,int(height*.950)),
              "MEASURED 3D HYPERPLANES  /  RAY INTEGRATION  /  DISPLAY INTERPOLATION",
              font=font(max(10,height//78)),fill=SOFT)
    x0=int(width*.43);x1=width-inset;yb=int(height*.922)
    draw.line((x0,yb,x1,yb),fill=(52,80,99),width=4)
    draw.line((x0,yb,x0+int((x1-x0)*progress),yb),fill=CYAN,width=4)
    ev=x0+int((x1-x0)*event/metadata["steps"])
    draw.line((ev,yb-10,ev,yb+10),fill=COPPER,width=3)
    return image


def render(archive,manifest,movie,poster,*,seconds=60,fps=24,
           width=1280,height=720,ray_samples=96):
    if width%2 or height%2 or width<640 or height<360:
        raise ValueError("Even HD video dimensions required")
    if not 6<=seconds<=180 or not 12<=fps<=60:
        raise ValueError("Invalid playback duration or frame rate")
    states,steps,omega,meta=read_fidelity_archive(archive,manifest)
    total=round(seconds*fps)
    movie=Path(movie)
    poster=Path(poster)
    movie.parent.mkdir(parents=True,exist_ok=True)
    poster.parent.mkdir(parents=True,exist_ok=True)
    ffmpeg=[
        "ffmpeg","-hide_banner","-loglevel","error","-y",
        "-f","rawvideo","-pix_fmt","rgb24",
        "-s",f"{width}x{height}","-r",str(fps),"-i","pipe:0",
        "-an","-c:v","libx264","-preset","veryfast","-crf","18",
        "-pix_fmt","yuv420p","-movflags","+faststart",str(movie)
    ]
    motion=[]
    proc=subprocess.Popen(ffmpeg,stdin=subprocess.PIPE)
    try:
        for index in range(total):
            time=meta["steps"]*index/max(total-1,1)
            # Four observed 4D hyperplanes, cyclically navigated, with
            # interpolation explicitly restricted to the displayed fields.
            omega_pos=(time/meta["steps"])*len(omega)*1.35
            vol,ref=observed_volume(states,steps,omega,time,omega_pos)
            frame=compose(vol,meta,time,omega_pos,width,height,ray_samples)
            if index==int(total*.72):
                frame.save(poster,optimize=True)
            if index%max(1,total//12)==0:
                motion.append(hashlib.sha256(frame.tobytes()).hexdigest())
                print(f"Volumetric frame {index}/{total}; t={time:.2f}; "
                      f"omega={ref['omega_lower']}..{ref['omega_upper']}",
                      flush=True)
            proc.stdin.write(frame.tobytes())
        proc.stdin.close()
        result=proc.wait()
        if result!=0:
            raise RuntimeError(f"FFmpeg encoder exited with {result}")
    except Exception:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        raise
    if len(set(motion))<7 or not movie.is_file() or movie.stat().st_size<4096:
        raise ValueError("Inadequate cinematic change or missing video output")
    if not poster.is_file():
        raise ValueError("Missing cinematic poster")
    provenance={
        "generation":"0028","edition":"cinematic-fidelity-2",
        "source_sha":meta["source_sha"],
        "source_archive_sha256":meta["archive"]["sha256"],
        "measured_sample_count":meta["sample_count"],
        "sample_every":meta["sample_every"],
        "omega_indices":list(map(int,omega)),
        "native_4d_grid":meta["n"],"ray_samples_per_axis":ray_samples,
        "video_frames":total,"fps":fps,"width":width,"height":height,
        "temporal_and_omega_interpolation":"for-display only; not mathematical integration",
        "frame_motion_samples":len(set(motion)),
        "numerical_precision":"float32 stepped dynamics; float16 visual archive; float32 full-4D keyframes",
        "render_contrast":"Spatial matrix p35 to p995 contrast with absolute signal gate and measured 3D matrix gradients (not a change to simulated concentrations)",
    }
    movie.with_suffix(".render.json").write_text(json.dumps(provenance,indent=2)+"\n")
    print(json.dumps({"movie":str(movie),"poster":str(poster),
                      "bytes":movie.stat().st_size,
                      "frames":total,"ray_samples":ray_samples,
                      "unique_motion_samples":len(set(motion))},indent=2))


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
    p.add_argument("--ray-samples",type=int,default=96)
    a=p.parse_args()
    render(a.input,a.metadata,a.movie,a.poster,
           seconds=a.seconds,fps=a.fps,width=a.width,
           height=a.height,ray_samples=a.ray_samples)


if __name__=="__main__":
    main()
