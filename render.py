import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def lap(a):
    return sum(np.roll(a, s, axis=ax) for ax in (0,1) for s in (-1,1))-4*a

def main():
    p=json.loads(Path("experiments/0001.json").read_text())
    n=p["size"]
    rng=np.random.default_rng(p["seed"])
    u=np.ones((n,n))
    v=np.zeros_like(u)
    c=n//2
    u[c-12:c+12,c-12:c+12]=0.5
    v[c-12:c+12,c-12:c+12]=0.25
    v+=rng.uniform(0,0.01,v.shape)
    out=Path("gallery")
    out.mkdir(exist_ok=True)
    for step in range(1,p["steps"]+1):
        reaction=u*v*v
        u,v=u+p["du"]*lap(u)-reaction+p["feed"]*(1-u),v+p["dv"]*lap(v)+reaction-(p["feed"]+p["kill"])*v
        if step in (100,500,1000,2000,p["steps"]):
            assert np.isfinite(u).all() and np.isfinite(v).all()
            plt.imsave(out/f"0001-{step:05d}.png",v,cmap="magma",vmin=0,vmax=0.4)
    metrics={"parameters":p,"mean":float(v.mean()),"std":float(v.std()),"active_fraction":float((v>0.1).mean())}
    (out/"metrics.json").write_text(json.dumps(metrics,indent=2))
    print(json.dumps(metrics,indent=2))

if __name__=="__main__":
    main()
