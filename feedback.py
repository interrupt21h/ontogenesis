"""Generation 0005: matter-driven flow feedback."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from render import lap

def advect(a, vx, vy):
    # Conservative first-order upwind flux on periodic cell faces.
    fx = np.maximum(vx, 0)*a + np.minimum(vx, 0)*np.roll(a,-1,axis=1)
    fy = np.maximum(vy, 0)*a + np.minimum(vy, 0)*np.roll(a,-1,axis=0)
    return a - fx + np.roll(fx,1,axis=1) - fy + np.roll(fy,1,axis=0)

def main():
    n=256
    rng=np.random.default_rng(42)
    y,x=np.mgrid[:n,:n]*2*np.pi/n
    habitat=(np.sin(x)+np.cos(y)+0.5*np.sin(2*x-y))/2.5
    u=np.ones((n,n))
    v=rng.uniform(0,0.005,(n,n))
    w=rng.uniform(0,0.005,(n,n))
    for i in range(12):
        a,b=rng.integers(15,n-15,2)
        u[a-6:a+6,b-6:b+6]=0.5
        (v if i%2 else w)[a-6:a+6,b-6:b+6]=0.25
    out=Path("gallery/0005")
    out.mkdir(parents=True,exist_ok=True)
    metrics=[]
    feedback=np.zeros_like(u)
    speed=0.0
    for step in range(8001):
        if step%40==0:
            assert all(np.isfinite(z).all() and z.min()>=-1e-10 for z in (u,v,w))
            rgb=np.stack((v*2.7+w*0.15,v*0.55+w*1.8,w*2.7+v*0.25),axis=-1)
            plt.imsave(out/f"{step:05d}.png",np.clip(rgb,0,1))
            metrics.append(dict(step=step,v_mean=float(v.mean()),w_mean=float(w.mean()),v_active=float((v>0.1).mean()),w_active=float((w>0.1).mean()),flow_rms=speed,feedback_rms=float(np.sqrt(np.mean(feedback**2)))))
        if step==8000:
            break
        phase=step*0.002
        psi=2.0*(np.sin(x+phase)*np.sin(y)+0.5*np.cos(2*x-y-phase))
        # Relaxing field sourced by local species imbalance.
        feedback += 0.12*lap(feedback) + 0.025*(v-w-feedback)
        psi += 0.8*feedback
        vx=psi-np.roll(psi,1,axis=0)
        vy=-(psi-np.roll(psi,1,axis=1))
        cfl=np.max(np.abs(vx)+np.abs(vy)+np.abs(np.roll(vx,1,axis=1))+np.abs(np.roll(vy,1,axis=0)))
        if cfl>0.8:
            vx*=0.8/cfl
            vy*=0.8/cfl
        speed=float(np.sqrt(np.mean(vx*vx+vy*vy)))
        u,v,w=(advect(z,vx,vy) for z in (u,v,w))
        a=u*v*v
        b=u*w*w
        u,v,w=(u+0.16*lap(u)-a-b+0.035*(1-u),
               v+0.08*lap(v)+a-(0.097+0.009*habitat)*v,
               w+0.065*lap(w)+b-(0.094-0.009*habitat)*w)
    plt.imsave(out/"habitat.png",habitat,cmap="coolwarm",vmin=-1,vmax=1)
    (out/"metrics.json").write_text(json.dumps(metrics,indent=2))
    print(json.dumps(metrics[-1],indent=2))
if __name__=="__main__":
    main()
