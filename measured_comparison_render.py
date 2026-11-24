"""G0031/G0032 measured animated dashboards; no invented spatial footage."""
import argparse,hashlib,json,os,subprocess,math
from pathlib import Path
from PIL import ImageDraw
from ecological_diagnostic_render import background,font

SPECS={
 "0031":(("historical","v_loss_095","v_loss_090","v_loss_085","v_loss_080"),
          "WHO DOMINATES?","Measured V-loss frontier",
          "d8991d1393dde4bf9d420501f4badcb99780dcab"),
 "0032":(("historical","near_transition","separated_035","separated_070"),
          "A PLACE FOR EACH","Complementary habitat controls",
          "6f64f3e7eb66c245385d2801306f7f039eef0d66")
}
COLORS=("#b8cbdf","#51d6c4","#f3a36d","#d28ade","#70a7fa")

def validate(d,gen):
    arms,title,subtitle,sha=SPECS[gen]
    if (d.get("generation"),d.get("n"),d.get("steps"),d.get("seeds"))!=(gen,16,240,[42,73]):
        raise ValueError("Archive generation or numerical scope mismatch")
    # Mutable canonical release names are re-published by successful regression
    # runs. The workflow checks this SHA against a successful Actions run.
    # Keep the true source revision in film metadata instead of pinning an
    # older numerical commit here.
    revision=d.get("source_sha")
    if not isinstance(revision,str) or len(revision)!=40 or any(c not in "0123456789abcdef" for c in revision):
        raise ValueError("Missing full numerical source revision")
    times=d["times"]
    if len(times)<35 or times[0]!=0 or times[-1]!=240 or times!=sorted(set(times)):
        raise ValueError("Invalid measured sampling timeline")
    for seed in ("42","73"):
        if set(d["observations"][seed])!=set(arms):raise ValueError("Missing treatment")
        for name in arms:
            records=d["observations"][seed][name]
            if [r["step"] for r in records]!=times:raise ValueError("Sample time mismatch")
            for r in records:
                for k in ("v_active","w_active","coexistence"):
                    v=r[k]
                    if isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) or not 0<=v<=1:
                        raise ValueError("Invalid measured fraction")
                if r["coexistence"]>min(r["v_active"],r["w_active"])+1e-8:
                    raise ValueError("Co-occupation exceeds available populations")

def chart(d,rect,records,metric,step):
    x0,y0,x1,y1=rect
    d.rounded_rectangle(rect,radius=12,fill="#192e41",outline="#3b5c72")
    left,right=x0+50,x1-22;top,bottom=y0+17,y1-34
    for tick in (0,25,50,75,100):
        y=round(bottom-(bottom-top)*tick/100)
        d.line((left,y,right,y),fill="#304a60",width=1)
        d.text((x0+10,y-7),str(tick),font=font(12),fill="#a9c4d3")
    for tick in (0,60,120,180,240):
        x=round(left+(right-left)*tick/240)
        d.text((x-12,bottom+8),str(tick),font=font(11),fill="#a9c4d3")
    x=round(left+(right-left)*step/240)
    d.line((x,top,x,bottom),fill="#627e93",width=1)
    for i,history in enumerate(records.values()):
        points=[(round(left+(right-left)*r["step"]/240),
                 round(bottom-(bottom-top)*r[metric]))
                for r in history if r["step"]<=step]
        if len(points)>1:d.line(points,fill=COLORS[i],width=3)
        if points:
            xx,yy=points[-1];d.ellipse((xx-4,yy-4,xx+4,yy+4),fill=COLORS[i])

def frame(data,gen,time,duration,base=None):
    if duration<=0:raise ValueError("Invalid duration")
    arms,title,subtitle,sha=SPECS[gen]
    image=base.copy() if base else background()
    d=ImageDraw.Draw(image)
    progress=max(0,min(1,time/duration))
    step=int((progress/.5*80) if progress<.5 else (80+(progress-.5)*320))
    d.rectangle((0,0,1280,7),fill="#53d6c4")
    d.text((40,25),"ONTOGENESIS / G"+gen,font=font(22,True),fill="#53d6c4")
    d.text((40,63),title,font=font(43,True),fill="#e9f4fa")
    d.text((43,121),subtitle+"  /  source: recorded numerical data",font=font(17),fill="#c2d2df")
    d.rounded_rectangle((1012,38,1235,105),radius=9,fill="#284258")
    d.text((1027,46),"NUMERICAL STEP",font=font(12,True),fill="#a7bed0")
    d.text((1027,66),f"{step:03d} / 240",font=font(24,True),fill="#f0f5fa")
    width=239 if gen=="0031" else 300
    for i,label in enumerate(arms):
        x=43+i*width
        d.rounded_rectangle((x,167,x+17,182),radius=3,fill=COLORS[i])
        d.text((x+24,163),label.replace("_"," "),font=font(14),fill="#e6eef3")
    for i,seed in enumerate(("42","73")):
        top=213+i*189
        for j,metric in enumerate(("v_active","w_active")):
            x0=40 if j==0 else 655;x1=624 if j==0 else 1240
            d.text((x0+7,top-27),f"SEED {seed} / SPECIES {'V' if j==0 else 'W'} ACTIVE (%)",
                   font=font(16,True),fill="#e4f1f9")
            chart(d,(x0,top,x1,top+156),
                  {n:data["observations"][seed][n] for n in arms},metric,step)
    d.rounded_rectangle((40,597,1240,652),radius=9,fill="#254157")
    conclusion=("No tested endpoint retained both populations above threshold"
                if gen=="0031" else
                "Seed 73: both active globally; zero active same-cell overlap")
    d.text((58,612),conclusion,font=font(18,True),fill="#e7f3f8")
    d.text((43,681),"MEASURED CURVES JOIN ARCHIVED SAMPLES — NOT SPATIAL FOOTAGE",
           font=font(13),fill="#b4cbdc")
    d.rectangle((0,711,round(1280*progress),720),fill="#51d6c4")
    return image

def render(source,gen,movie,poster,seconds=24,fps=24):
    if not 2<=seconds<=60 or fps not in (8,12,24,30):raise ValueError("Invalid render budget")
    source=Path(source).read_bytes();data=json.loads(source);validate(data,gen)
    movie=Path(movie);poster=Path(poster)
    movie.parent.mkdir(parents=True,exist_ok=True);poster.parent.mkdir(parents=True,exist_ok=True)
    import imageio_ffmpeg
    cmd=[imageio_ffmpeg.get_ffmpeg_exe(),"-hide_banner","-loglevel","error","-y",
         "-f","rawvideo","-pix_fmt","rgb24","-s","1280x720","-r",str(fps),
         "-i","-","-an","-c:v","libx264","-preset","fast","-crf","21",
         "-pix_fmt","yuv420p","-movflags","+faststart",str(movie)]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE);count=seconds*fps;base=background();hashes=[]
    try:
        for i in range(count):
            im=frame(data,gen,i/fps,seconds,base)
            if i in (0,count//3,2*count//3,count-1):
                hashes.append(hashlib.sha256(im.tobytes()).hexdigest())
            if i==count*3//4:im.save(poster)
            p.stdin.write(im.tobytes())
    finally:
        if p.stdin:p.stdin.close()
    if p.wait()!=0 or not movie.exists() or movie.stat().st_size<8192:
        raise RuntimeError("FFmpeg failed")
    if not poster.exists() or poster.stat().st_size<4096 or len(set(hashes))!=4:
        raise RuntimeError("Poster or temporal animation invalid")
    meta={"generation":gen,"edition":"measured-evidence-animation","source_sha256":hashlib.sha256(source).hexdigest(),
          "numerical_revision":data["source_sha"],"render_revision":os.getenv("GITHUB_SHA","unversioned"),
          "frames":count,"seconds":seconds,"fps":fps,"width":1280,"height":720,
          "not_spatial_footage":True,"featured_G0028_preserved":True}
    movie.with_suffix(".render.json").write_text(json.dumps(meta,indent=2)+"\n")
    return meta

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--generation",choices=SPECS,required=True);a.add_argument("--data",required=True)
    a.add_argument("--movie",required=True);a.add_argument("--poster",required=True)
    a.add_argument("--seconds",type=int,default=24);a.add_argument("--fps",type=int,default=24)
    x=a.parse_args()
    print(json.dumps(render(x.data,x.generation,x.movie,x.poster,x.seconds,x.fps),indent=2))
