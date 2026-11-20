"""Postprocess a uniform observatory film without changing the simulation."""
import argparse,json,subprocess,tempfile
from pathlib import Path
import numpy as np

KEYS=("v_active","w_active","structure_active","structure_mean","signal_active","genotype_entropy","energy_mean")
def schedule(rows, seconds=60, fps=24, emphasis=3):
    t=np.array([r["step"] for r in rows],float)
    assert len(t)>1 and np.all(np.diff(t)>0)
    x=np.array([[r[k] for k in KEYS] for r in rows],float)
    assert np.isfinite(x).all()
    scale=np.maximum(np.ptp(x,axis=0),1e-9)
    change=np.mean(np.abs(np.diff(x,axis=0))/scale,axis=1)
    change=np.convolve(np.pad(change,(4,4),mode="edge"),np.ones(9)/9,mode="valid")
    base=np.diff(t)/(t[-1]-t[0])
    mass=base+emphasis*change/max(change.sum(),1e-12)
    c=np.r_[0,np.cumsum(mass)]
    c/=c[-1]
    indices=np.rint(np.interp(np.linspace(0,1,seconds*fps),c,np.arange(len(t)))).astype(int)
    return indices.tolist()

def events(rows):
    out={"initial":rows[0]["step"],"final":rows[-1]["step"]}
    for k in KEYS+("euler_characteristic","builder_mass"):
        if k in rows[0]:
            for label,fn in (("max",max),("min",min)):
                out[k+"_"+label]=fn(rows,key=lambda r:r[k])["step"]
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("metrics",type=Path);p.add_argument("video",type=Path);p.add_argument("out",type=Path)
    args=p.parse_args()
    rows=json.loads(args.metrics.read_text())
    args.out.mkdir(parents=True,exist_ok=True)
    indices=schedule(rows)
    (args.out/"temporal.json").write_text(json.dumps(dict(events=events(rows),source_steps=[r["step"] for r in rows],adaptive_source_indices=indices,fps=24),indent=2))
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp)
        subprocess.run(["ffmpeg","-v","error","-i",str(args.video),"-vsync","0",str(tmp/"%06d.png")],check=True)
        frames=sorted(tmp.glob("*.png"))
        if len(frames)!=len(rows): raise ValueError("Video and metrics are not aligned")
        seq=tmp/"sequence";seq.mkdir()
        for i,j in enumerate(indices):
            (seq/f"{i:06d}.png").symlink_to(frames[j])
        subprocess.run(["ffmpeg","-v","error","-y","-framerate","24","-i",str(seq/"%06d.png"),"-c:v","libx264","-pix_fmt","yuv420p","-crf","23","-movflags","+faststart",str(args.out/"adaptive.mp4")],check=True)
        for label,step in events(rows).items():
            import shutil
            shutil.copyfile(frames[next(i for i,r in enumerate(rows) if r["step"]==step)],args.out/f"{label}.png")
if __name__=="__main__": main()
