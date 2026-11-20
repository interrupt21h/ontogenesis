"""Frozen-state spatial exploration and matched native-state comparison."""
import argparse,sys,subprocess,tempfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from field_archive import load_snapshot

def panel(meta,f,omega,z):
    # Fixed absolute concentration mapping; no per-frame normalization.
    v,w,m=(f[k][omega,z] for k in ("v","w","m"))
    rgb=np.stack([v+.45*m,.35*v+.65*w+.35*m,w+.6*m],axis=-1)
    im=Image.fromarray(np.uint8(np.clip(rgb,0,1)**.75*255)).resize((480,480),Image.Resampling.NEAREST)
    canvas=Image.new("RGB",(520,550),(8,13,23));canvas.paste(im,(20,55))
    ImageDraw.Draw(canvas).text((20,14),f"G{meta['generation']} | step {meta['step']} | omega {omega} | z {z}",fill="white")
    return canvas

def film(frames,path,fps):
    with tempfile.TemporaryDirectory() as d:
        for i,im in enumerate(frames): im.save(Path(d)/f"{i:05d}.png")
        subprocess.run(["ffmpeg","-v","error","-y","-framerate",str(fps),"-i",d+"/%05d.png","-c:v","libx264","-pix_fmt","yuv420p",str(path)],check=True)

def main():
    p=argparse.ArgumentParser();p.add_argument("folder",type=Path);p.add_argument("out",type=Path);p.add_argument("--parent",type=Path);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    paths=sorted(a.folder.glob("state-*.npz"))
    if not paths: raise ValueError("No states")
    m,f=load_snapshot(paths[-1])
    film((panel(m,f,i,m["shape"][1]//2) for i in range(m["shape"][0])),a.out/"frozen-omega.mp4",4)
    if a.parent:
        pairs=[(p,a.parent/p.name) for p in paths if (a.parent/p.name).exists()]
        if not pairs: raise ValueError("No matched observations")
        def comparison():
            for p,q in pairs:
                m,f=load_snapshot(p);n,g=load_snapshot(q)
                assert m["step"]==n["step"] and m["shape"]==n["shape"] and m["seed"]==n["seed"]
                im=Image.new("RGB",(1040,550));im.paste(panel(n,g,0,n["shape"][1]//2),(0,0));im.paste(panel(m,f,0,m["shape"][1]//2),(520,0));yield im
        film(comparison(),a.out/"matched-states.mp4",1)
if __name__=="__main__":main()
