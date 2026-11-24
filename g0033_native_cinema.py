"""G0033 paired-seed native spatial cinematic from recorded numerical fields."""
from __future__ import annotations
import argparse,hashlib,json,math,os,subprocess
from pathlib import Path
from PIL import Image,ImageDraw
from ecological_diagnostic_render import background,font
from niche_spatial_render import load_fields,scatter

def sources(a,am,b,bm):
    pairs=(load_fields(a,am),load_fields(b,bm))
    if {v[1]["seed"] for v in pairs}!={42,73}:
        raise ValueError("Expected archived seed 42 and 73 native fields")
    if any(v[1]["n"]!=16 or v[1]["steps"]!=240 for v in pairs):
        raise ValueError("Unexpected numerical scope")
    if pairs[0][1]["sample_steps"]!=pairs[1][1]["sample_steps"]:
        raise ValueError("Unmatched archived sample times")
    return sorted(pairs,key=lambda x:x[1]["seed"])

def frame(pair,index,count):
    progress=index/max(1,count-1)
    n=pair[0][1]["n"];sample_steps=pair[0][1]["sample_steps"]
    t=min(len(sample_steps)-1,int(progress*len(sample_steps)))
    omega=min(n-1,int(progress*n))
    angle=.2+math.tau*.78*progress
    im=background();d=ImageDraw.Draw(im)
    d.rectangle((0,0,1280,8),fill="#52DAC7")
    d.text((42,24),"ONTOGENESIS / G0033 / NATIVE FOUR-DIMENSIONAL FIELDS",
           font=font(19,True),fill="#53DAC7")
    d.text((42,63),"ONE WORLD. DIFFERENT BEGINNINGS.",
           font=font(37,True),fill="#F1F7FA")
    d.text((42,121),f"Spatial preference 0.70 | step {sample_steps[t]}/240 | omega plane {omega}",
           font=font(17),fill="#BDD7E5")
    layer=Image.new("RGBA",im.size,(0,0,0,0));pen=ImageDraw.Draw(layer)
    for (data,info,_),rect in zip(pair,((40,175,623,574),(657,175,1240,574))):
        d.text((rect[0]+9,147),f"INITIALIZATION SEED {info['seed']}",
               font=font(17,True),fill="#F5F8FC")
        d.rounded_rectangle(rect,radius=14,fill="#192D41",outline="#45647A",width=2)
        channels={ch:data[f"separated_070_{ch}"] for ch in ("v","w","m")}
        v,w,both=scatter(pen,channels,t,omega,angle,rect)
        d.text((rect[0]+9,586),f"V {v:,} | W {w:,} | shared sites {both:,}",
               font=font(15),fill="#C8DFED")
    im=Image.alpha_composite(im.convert("RGBA"),layer).convert("RGB")
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((40,622,1240,667),radius=10,fill="#254357")
    d.text((56,634),"Teal = active V | Amber = active W | Violet = matrix",
           font=font(16),fill="#EDF7FB")
    d.text((42,681),"ACTUAL STORED SLICES · NO SYNTHETIC ORGANISMS · CAMERA ROTATION IS PRESENTATION",
           font=font(12),fill="#BED2DF")
    d.rectangle((0,711,round(1280*progress),720),fill="#52DAC7")
    return im

def render(a,am,b,bm,movie,poster,seconds=24,fps=24):
    if seconds not in (2,24,36) or fps not in (8,24):
        raise ValueError("Outside cinematic budget")
    pair=sources(a,am,b,bm)
    import imageio_ffmpeg
    movie,poster=Path(movie),Path(poster)
    movie.parent.mkdir(parents=True,exist_ok=True)
    poster.parent.mkdir(parents=True,exist_ok=True)
    command=[imageio_ffmpeg.get_ffmpeg_exe(),"-hide_banner","-loglevel","error",
             "-y","-f","rawvideo","-pix_fmt","rgb24","-s","1280x720",
             "-r",str(fps),"-i","-","-an","-c:v","libx264","-preset","fast",
             "-crf","21","-pix_fmt","yuv420p","-movflags","+faststart",str(movie)]
    p=subprocess.Popen(command,stdin=subprocess.PIPE)
    hashes=[];count=seconds*fps
    try:
        for i in range(count):
            im=frame(pair,i,count)
            if i in (0,count//3,2*count//3,count-1):
                hashes.append(hashlib.sha256(im.tobytes()).hexdigest())
            if i==count*3//4:im.save(poster)
            p.stdin.write(im.tobytes())
    finally:
        if p.stdin:p.stdin.close()
    if p.wait()!=0 or not movie.exists() or movie.stat().st_size<8192:
        raise RuntimeError("Video encoder failed")
    if len(set(hashes))!=4 or not poster.exists() or poster.stat().st_size<4096:
        raise RuntimeError("No temporal change or missing poster")
    info={"generation":"0033","edition":"native-4d-seed-comparison-v1",
          "seeds":[x[1]["seed"] for x in pair],
          "source_archive_sha256_by_seed":{str(x[1]["seed"]):x[2] for x in pair},
          "steps":240,"n":16,"sample_steps":pair[0][1]["sample_steps"],
          "arm":"separated_070","discrete_omega_slices":True,
          "interpolated_numerical_states":False,
          "camera_motion_is_presentation":True,"frames":count,"seconds":seconds,
          "fps":fps,"width":1280,"height":720,
          "render_revision":os.getenv("GITHUB_SHA","unversioned")}
    movie.with_suffix(".render.json").write_text(json.dumps(info,indent=2)+"\n")
    return info

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("a","am","b","bm","movie","poster"):
        p.add_argument("--"+name,required=True,type=Path)
    p.add_argument("--seconds",type=int,default=24)
    p.add_argument("--fps",type=int,default=24)
    args=p.parse_args()
    print(json.dumps(render(args.a,args.am,args.b,args.bm,args.movie,args.poster,
                            seconds=args.seconds,fps=args.fps),indent=2))
