"""G0029 camera orbit and volumetric ray art from measured numerical fields."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageFont
from scipy.ndimage import map_coordinates
from adaptive_transport import CHANNELS,digest

PALETTE=np.array(((.80,.39,1.),(1.,.38,.12),(.12,.55,1.),
                  (.94,.79,.37),(.13,1.,.82)),np.float32)

def load(path,manifest):
    m=json.loads(Path(manifest).read_text())
    if (m["generation"],m["edition"])!=("0029","paired-adaptive-curl-1"):
        raise ValueError("Not G0029")
    if m["recording"]["channel_order"]!=list(CHANNELS):
        raise ValueError("Unknown channels")
    if digest(path)!=m["archive"]["sha256"]:
        raise ValueError("Native archive checksum differs")
    with np.load(path,allow_pickle=False) as data:
        volumes=data["states"]; times=data["steps"]; omega=data["omega_indices"]
        keys=data["dense_states"]; key_times=data["dense_steps"]
    if (list(volumes.shape)!=m["recording"]["shape"] or
        list(keys.shape)!=m["recording"]["dense_shape"] or
        volumes.dtype!=np.float16 or keys.dtype!=np.float32 or
        list(map(int,key_times))!=m["recording"]["dense_steps"] or
        list(map(int,omega))!=m["recording"]["omega_indices"] or
        times[0]!=0 or times[-1]!=m["steps"] or
        not np.all(np.diff(times)>0)):
        raise ValueError("Malformed or incomplete archive")
    if not np.isfinite(volumes).all() or not np.isfinite(keys).all():
        raise ValueError("Nonfinite native fields")
    return volumes,times,omega,m

def at(volumes,times,omega,t,fourth):
    upper=max(1,min(len(times)-1,int(np.searchsorted(times,t,side="right"))))
    lower=upper-1
    a=float(np.clip((t-times[lower])/(times[upper]-times[lower]),0,1))
    p=int(math.floor(fourth))%len(omega)
    q=(p+1)%len(omega)
    b=fourth-math.floor(fourth)
    v=(1-a)*volumes[lower,p].astype(np.float32)+a*volumes[upper,p].astype(np.float32)
    if b>1e-8 and p!=q:
        v=(1-b)*v+b*((1-a)*volumes[lower,q].astype(np.float32)+a*volumes[upper,q].astype(np.float32))
    return v

def ray(volume,meta,progress,count):
    if not 24<=count<=128:
        raise ValueError("Ray count 24..128")
    n=volume.shape[-1]
    axis=np.linspace(-.84*n,.84*n,count,dtype=np.float32)
    z,y,x=np.meshgrid(axis,axis,axis,indexing="ij")
    angle=.2+progress*math.pi*2.8
    elevation=.29+.13*math.sin(progress*2*math.pi)
    yy=np.cos(elevation)*y-np.sin(elevation)*z
    zz=np.sin(elevation)*y+np.cos(elevation)*z
    coords=np.array((-np.sin(angle)*x+np.cos(angle)*zz,yy,
                     np.cos(angle)*x+np.sin(angle)*zz),dtype=np.float32)+(n-1)/2
    inside=np.all((coords>=0)&(coords<n-1),axis=0)
    src=np.stack([map_coordinates(volume[i],coords,order=1,
                mode="constant",cval=0,prefilter=False)
                for i in range(len(CHANNELS))])
    reference=meta["recording"]["fixed_exposure_p995"]
    limits=np.array([max(reference[name],floor) for name,floor in zip(
        CHANNELS,(.04,.012,.012,.75,.015))],np.float32)
    fields=np.clip(src/limits[:,None,None,None],0,1)
    fields[0]=np.clip(fields[0]-.20,0,1)*.60
    fields[3]*=.10
    fields[4]=np.clip((src[4]-float(volume[4].mean()))/
                      max(limits[4]*.35,.015),0,1)*min(1.,float(volume[4].max())/.02)*1.4
    rgb=np.zeros((count,count,3),np.float32)
    trans=np.ones((count,count),np.float32)
    for k in range(count):
        layers=fields[:,k]
        total=layers.sum(axis=0)
        opacity=(1-np.exp(-.17*total))*inside[k]
        color=np.tensordot(layers.transpose(1,2,0),PALETTE,axes=([2],[0]))
        color/=np.maximum(total[:,:,None],1e-6)
        rgb+=trans[:,:,None]*opacity[:,:,None]*color
        trans*=1-opacity
    return Image.fromarray(np.uint8(np.clip((rgb*1.8)**.78*255,0,255)),"RGB")

def font(size,bold=False):
    path=Path("/usr/share/fonts/truetype/dejavu")/(
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")
    return ImageFont.truetype(str(path),size) if path.exists() else ImageFont.load_default()

def compose(volume,meta,t,width,height,rays):
    progress=t/meta["steps"]
    view=ray(volume,meta,progress,rays)
    back=view.resize((width,height),Image.Resampling.BICUBIC).filter(
        ImageFilter.GaussianBlur(max(12,width//46)))
    canvas=Image.blend(Image.new("RGB",(width,height),(5,12,23)),back,.25)
    side=int(height*.92)
    canvas.paste(view.resize((side,side),Image.Resampling.BICUBIC),
                 ((width-side)//2,(height-side)//2))
    layer=Image.new("RGBA",(width,height))
    pen=ImageDraw.Draw(layer)
    pen.rectangle((0,0,width,int(height*.16)),fill=(3,9,20,182))
    pen.rectangle((0,int(height*.82),width,height),fill=(3,9,20,196))
    img=Image.alpha_composite(canvas.convert("RGBA"),layer).convert("RGB")
    pen=ImageDraw.Draw(img)
    inset=int(width*.035)
    pen.text((inset,int(height*.034)),"ONTOGENESIS  /  G0029",
             font=font(max(20,height//28),True),fill=(224,240,250))
    pen.text((inset,int(height*.108)),"ADAPTIVE TRANSPORT  /  PERSISTENT FIELD MEMORY",
             font=font(max(12,height//50),True),fill=(67,234,208))
    pen.text((inset,int(height*.854)),f"NUMERICAL STEP  {t:.1f} / {meta['steps']}",
             font=font(max(12,height//40),True),fill=(223,240,246))
    pen.text((inset,int(height*.943)),
             "MEASURED 3D SECTIONS  /  ORBIT + INTERPOLATION ARE DISPLAY ONLY",
             font=font(max(10,height//74)),fill=(141,179,195))
    x0=int(width*.49);x1=int(width*.94);y=int(height*.90)
    pen.line((x0,y,x1,y),fill=(56,89,107),width=4)
    pen.line((x0,y,x0+int((x1-x0)*progress),y),fill=(72,226,207),width=4)
    return img

def render(archive,manifest,movie,poster,seconds=12,fps=24,
           width=960,height=540,rays=56):
    if width%2 or height%2 or width<640 or height<360 or not 6<=seconds<=120:
        raise ValueError("Invalid video settings")
    states,times,omega,meta=load(archive,manifest)
    movie,poster=Path(movie),Path(poster)
    movie.parent.mkdir(parents=True,exist_ok=True)
    poster.parent.mkdir(parents=True,exist_ok=True)
    args=["ffmpeg","-hide_banner","-loglevel","error","-y",
          "-f","rawvideo","-pix_fmt","rgb24","-s",f"{width}x{height}",
          "-r",str(fps),"-i","pipe:0","-an","-c:v","libx264",
          "-preset","veryfast","-crf","19","-pix_fmt","yuv420p",
          "-movflags","+faststart",str(movie)]
    proc=subprocess.Popen(args,stdin=subprocess.PIPE)
    samples=set()
    total=seconds*fps
    try:
        for index in range(total):
            position=index/max(1,total-1)
            t=position*meta["steps"]
            volume=at(states,times,omega,t,position*len(omega)*1.45)
            image=compose(volume,meta,t,width,height,rays)
            if index==int(total*.67):
                image.save(poster)
            if index%max(1,total//12)==0:
                samples.add(hashlib.sha256(image.tobytes()).hexdigest())
                print(f"Volumetric frame {index}/{total}",flush=True)
            proc.stdin.write(image.tobytes())
        proc.stdin.close()
        if proc.wait()!=0:
            raise RuntimeError("FFmpeg video encoding failed")
    except Exception:
        if proc.poll() is None:
            proc.kill();proc.wait()
        raise
    if len(samples)<6 or not poster.exists() or movie.stat().st_size<4096:
        raise ValueError("Missing or insufficient cinematic motion")
    info={"generation":"0029","frames":total,"fps":fps,"width":width,
          "height":height,"ray_samples_per_axis":rays,
          "unique_motion_hashes":len(samples),
          "archive_sha256":meta["archive"]["sha256"],
          "source_sha":meta["source_sha"],
          "presentation_only":"camera orbit, exposure, ray integration and interpolation"}
    movie.with_suffix(".render.json").write_text(json.dumps(info,indent=2)+"\n")
    return info

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for option in ("input","metadata","movie","poster"):
        p.add_argument("--"+option,type=Path,required=True)
    for name,default in (("seconds",12),("fps",24),("width",960),
                         ("height",540),("rays",56)):
        p.add_argument("--"+name,type=int,default=default)
    a=p.parse_args()
    print(json.dumps(render(a.input,a.metadata,a.movie,a.poster,
          a.seconds,a.fps,a.width,a.height,a.rays),indent=2),flush=True)
