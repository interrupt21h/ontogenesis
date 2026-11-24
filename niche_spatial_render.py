"""Render an authentic fixed-omega 3D slice of G0032's archived 4D fields.

Only stored 4D float32 arrays are shown. A continuously rotating display
camera does not imply new integration steps. No synthetic population shapes
or interpolated concentration fields are generated.
"""
from __future__ import annotations
import argparse,hashlib,json,math,os,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from ecological_diagnostic_render import background,font
from niche_spatial_archive import ARMS,CHANNELS

def load_fields(archive,metadata):
    raw=Path(archive).read_bytes()
    info=json.loads(Path(metadata).read_text())
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=info["archive_sha256"] or info.get("generation")!="0032":
        raise ValueError("G0032 native field archive provenance mismatch")
    if info["treatments"]!=ARMS or info["channels"]!=CHANNELS:
        raise ValueError("Unexpected G0032 numerical channels or treatments")
    with np.load(archive,allow_pickle=False) as npz:
        data={key:np.asarray(npz[key]) for key in npz.files}
    n=info["n"];times=info["sample_steps"]
    if not 8<=n<=16 or len(times)<3 or data["steps"].tolist()!=times:
        raise ValueError("Native spatial sample timeline invalid")
    for arm in ARMS:
        for ch in CHANNELS:
            arr=data.get(f"{arm}_{ch}")
            if arr is None or arr.dtype!=np.float32 or arr.shape!=(len(times),)+(n,)*4:
                raise ValueError("Native 4D field channel missing or reshaped")
            if not np.isfinite(arr).all() or arr.min()< -1e-6:
                raise ValueError("Non-finite or negative numerical field")
    return data,info,digest

def scatter(draw,fields,step_index,omega,angle,rect):
    x0,y0,x1,y1=rect
    V=fields["v"][step_index,omega]
    W=fields["w"][step_index,omega]
    M=fields["m"][step_index,omega]
    n=V.shape[-1]
    z,y,x=np.indices(V.shape)
    x=x.ravel()-(n-1)/2
    y=y.ravel()-(n-1)/2
    z=z.ravel()-(n-1)/2
    v,w,m=V.ravel(),W.ravel(),M.ravel()
    keep=(v>.1)|(w>.1)|(m>.22)
    x,y,z=x[keep],y[keep],z[keep]
    v,w,m=v[keep],w[keep],m[keep]
    c,s=math.cos(angle),math.sin(angle)
    horiz=x*c-y*s
    depth=x*s+y*c
    scale=min((x1-x0)*.032,(y1-y0)*.060)
    sx=(x0+x1)*.5+horiz*scale
    sy=(y0+y1)*.5+(depth*.43-z*.93)*scale
    for idx in np.argsort(depth):
        xx,yy=int(sx[idx]),int(sy[idx])
        if xx<x0+8 or xx>x1-8 or yy<y0+8 or yy>y1-8:continue
        if m[idx]>.22:
            draw.ellipse((xx-2,yy-2,xx+2,yy+2),fill=(117,113,204,110))
        if v[idx]>.1:
            strength=min(1.,float(v[idx]))
            r=2+int(strength*2)
            draw.ellipse((xx-r,yy-r,xx+r,yy+r),
                         fill=(69,231,197,int(95+160*strength)))
        if w[idx]>.1:
            strength=min(1.,float(w[idx]))
            r=2+int(strength*2)
            draw.ellipse((xx-r,yy-r,xx+r,yy+r),
                         fill=(255,177,108,int(95+160*strength)))
    return (int((V>.1).sum()),int((W>.1).sum()),
            int(((V>.1)&(W>.1)).sum()))

def image_at(data,info,t,seconds,base=None,*,omega_sweep=False):
    if seconds<=0:raise ValueError("Duration must be positive")
    pct=max(0,min(1,t/seconds))
    times=info["sample_steps"]
    idx=min(len(times)-1,int(pct*(len(times)-1)))
    # Sample only authentic stored hyperplanes: no interpolation between 4D slices.
    omega=(min(info["n"]-1,int(pct*info["n"])) if omega_sweep
           else info["n"]//2)
    step=times[idx]
    angle=.26+math.pi*2*.76*pct
    im=base.copy() if base is not None else background()
    d=ImageDraw.Draw(im)
    d.rectangle((0,0,1280,8),fill="#56dfce")
    d.text((40,20),"ONTOGENESIS / G0032 / NATIVE FOUR-DIMENSIONAL DATA",
           font=font(20,True),fill="#5cdec8")
    d.text((39,58),"A PLACE FOR EACH",font=font(45,True),fill="#f0f7fb")
    d.text((41,120),f"Seed {info['seed']} · Fixed 3D hyperplane omega={omega} · Recorded step {step}/{info['steps']}",
           font=font(17),fill="#bdd3e0")
    bg=Image.new("RGBA",im.size,(0,0,0,0))
    pen=ImageDraw.Draw(bg)
    labels=("NO NICHE / V LOSS ×0.97","COMPLEMENTARY NICHE / STRENGTH 0.70")
    for arm,rect,label in zip(ARMS,((40,174,622,574),(655,174,1239,574)),labels):
        d.text((rect[0]+8,144),label,font=font(16,True),fill="#e5f0f7")
        d.rounded_rectangle(rect,radius=14,fill="#192d41",outline="#45647a",width=2)
        local={ch:data[f"{arm}_{ch}"] for ch in CHANNELS}
        v_cells,w_cells,overlap=scatter(pen,local,idx,omega,angle,rect)
        d.text((rect[0]+8,588),
               f"Observed slice cells: V {v_cells:,}  ·  W {w_cells:,}  ·  Both {overlap:,}",
               font=font(14),fill="#d2e4ed")
    im=Image.alpha_composite(im.convert("RGBA"),bg).convert("RGB")
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((41,622,1238,667),radius=8,fill="#274559")
    for x,color,label in ((57,"#46e7c5","V > 0.1"),(245,"#ffb16d","W > 0.1"),
                          (433,"#7571cc","Matrix > 0.22")):
        d.ellipse((x,641,x+16,657),fill=color)
        d.text((x+24,637),label,font=font(15),fill="#e1f0f8")
    d.text((42,684),"TRUE RECORDED 3D SLICE FROM 4D STATE · ROTATING CAMERA · NO INTERPOLATED PHYSICAL TIMESTEPS",
           font=font(12),fill="#b9ceda")
    d.rectangle((0,711,round(1280*pct),720),fill="#53deca")
    return im

def render(archive,source_meta,movie,poster,*,seconds=24,fps=24,omega_sweep=False):
    if not 2<=seconds<=60 or fps not in (8,12,24,30):
        raise ValueError("Outside bounded rendering duration")
    data,info,digest=load_fields(archive,source_meta)
    import imageio_ffmpeg
    movie,poster=Path(movie),Path(poster)
    movie.parent.mkdir(parents=True,exist_ok=True)
    poster.parent.mkdir(parents=True,exist_ok=True)
    args=[imageio_ffmpeg.get_ffmpeg_exe(),"-hide_banner","-loglevel","error","-y",
          "-f","rawvideo","-pix_fmt","rgb24","-s","1280x720","-r",str(fps),
          "-i","-","-an","-c:v","libx264","-preset","fast","-crf","21",
          "-pix_fmt","yuv420p","-movflags","+faststart",str(movie)]
    proc=subprocess.Popen(args,stdin=subprocess.PIPE)
    count=seconds*fps;base=background();keyframes=[]
    try:
        for i in range(count):
            frame=image_at(data,info,i/fps,seconds,base,omega_sweep=omega_sweep)
            if i in (0,count//3,count*2//3,count-1):
                keyframes.append(hashlib.sha256(frame.tobytes()).hexdigest())
            if i==count*3//4:frame.save(poster)
            proc.stdin.write(frame.tobytes())
    finally:
        if proc.stdin:proc.stdin.close()
    if proc.wait()!=0 or not movie.exists() or movie.stat().st_size<8192:
        raise RuntimeError("FFmpeg spatial rendering failed")
    if not poster.exists() or poster.stat().st_size<4096 or len(set(keyframes))!=4:
        raise RuntimeError("Spatial poster or temporal frames failed")
    provenance={
        "generation":"0032","edition":("native-4d-hyperplane-journey-v1" if omega_sweep
                                         else "native-4d-omega-slice-cinematic-v1"),
        "source_archive_sha256":digest,
        "source_numeric_revision":info["source_sha"],
        "render_commit":os.getenv("GITHUB_SHA","unversioned"),
        "source_dimensions":[info["n"]]*4,
        "fixed_omega_slice":None if omega_sweep else info["n"]//2,
        "omega_sampling":("discrete-recorded-hyperplanes" if omega_sweep else "fixed"),
        "omega_indices":(list(range(info["n"])) if omega_sweep else [info["n"]//2]),
        "numerical_sample_steps":info["sample_steps"],
        "interpolated_numerical_states":False,"camera_rotation_for_visualization":True,
        "seed":info["seed"],"treatments":list(ARMS),
        "frames":count,"seconds":seconds,"fps":fps,"width":1280,"height":720,
        "featured_G0028_preserved":True,
        "interpretation":"Recorded concentrations on a fixed hyperplane, not individual organisms",
    }
    movie.with_suffix(".render.json").write_text(json.dumps(provenance,indent=2)+"\n")
    return provenance

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data",required=True,type=Path)
    p.add_argument("--metadata",required=True,type=Path)
    p.add_argument("--movie",required=True,type=Path)
    p.add_argument("--poster",required=True,type=Path)
    p.add_argument("--seconds",type=int,default=24)
    p.add_argument("--fps",type=int,default=24)
    p.add_argument("--omega-sweep",action="store_true",
                   help="Visit stored 4D hyperplanes discretely; never synthesize slices")
    a=p.parse_args()
    print(json.dumps(render(a.data,a.metadata,a.movie,a.poster,
                            seconds=a.seconds,fps=a.fps,
                            omega_sweep=a.omega_sweep),indent=2))
