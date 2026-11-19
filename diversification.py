"""Generation 0002: competing autocatalysts sharing a substrate."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from render import lap

def main():
    n=256
    rng=np.random.default_rng(42)
    u=np.ones((n,n))
    v=rng.uniform(0,0.005,(n,n))
    w=rng.uniform(0,0.005,(n,n))
    for i in range(12):
        x,y=rng.integers(15,n-15,2)
        u[x-6:x+6,y-6:y+6]=0.5
        (v if i%2 else w)[x-6:x+6,y-6:y+6]=0.25
    out=Path("gallery/0002")
    out.mkdir(parents=True,exist_ok=True)
    metrics=[]
    for step in range(1,6001):
        a=u*v*v
        b=u*w*w
        u,v,w=(u+0.16*lap(u)-a-b+0.035*(1-u),
               v+0.08*lap(v)+a-0.097*v,
               w+0.065*lap(w)+b-0.094*w)
        if step%250==0:
            assert all(np.isfinite(z).all() and z.min()>=-1e-10 for z in (u,v,w))
            metrics.append(dict(step=step,v_mean=float(v.mean()),w_mean=float(w.mean()),v_active=float((v>0.1).mean()),w_active=float((w>0.1).mean())))
            rgb=np.stack((v*2.7+w*0.15,v*0.55+w*1.8,w*2.7+v*0.25),axis=-1)
            plt.imsave(out/f"{step:05d}.png",np.clip(rgb,0,1))
    (out/"metrics.json").write_text(json.dumps(metrics,indent=2))
    print(json.dumps(metrics[-1],indent=2))

if __name__=="__main__":
    main()
