"""Generation 0006: volumetric competing autocatalysts and endogenous curl transport."""
import json
from pathlib import Path
import numpy as np
from PIL import Image

N=80
STEPS=1800
STRIDE=15

def lap(a):
    return sum(np.roll(a,s,axis=i) for i in range(3) for s in (-1,1))-6*a

def transport(a, velocities):
    result=a.copy()
    for axis, velocity in enumerate(velocities):
        flux=np.maximum(velocity,0)*a+np.minimum(velocity,0)*np.roll(a,-1,axis=axis)
        result+=np.roll(flux,1,axis=axis)-flux
    return result

def render(v,w,step,path):
    # Orthographic emission-absorption ray integration through an orbiting volume.
    angle=2*np.pi*step/STEPS
    p=np.arange(N,dtype=np.float32)-(N-1)/2
    z,y,x=np.meshgrid(p,p,p,indexing="ij")
    c,s=np.cos(angle),np.sin(angle)
    ix=np.rint(c*x+s*z+(N-1)/2).astype(int)
    iz=np.rint(-s*x+c*z+(N-1)/2).astype(int)
    iy=np.rint(y+(N-1)/2).astype(int)
    mask=(ix>=0)&(ix<N)&(iz>=0)&(iz<N)
    idx=(np.clip(iz,0,N-1),iy,np.clip(ix,0,N-1))
    a=v[idx]*mask
    b=w[idx]*mask
    rgb=np.zeros((N,N,3),np.float32)
    trans=np.ones((N,N),np.float32)
    for k in range(N):
        density=a[k]+b[k]
        opacity=1-np.exp(-0.55*density)
        color=(a[k,...,None]*np.array([1.0,0.28,0.045])+b[k,...,None]*np.array([0.04,0.62,1.0]))/np.maximum(density[...,None],1e-8)
        rgb+=trans[...,None]*opacity[...,None]*color
        trans*=1-opacity
    rgb=np.clip(rgb,0,1)**0.75
    Image.fromarray(np.uint8(rgb*255)).resize((512,512),Image.Resampling.BICUBIC).save(path)

def main():
    rng=np.random.default_rng(42)
    z,y,x=np.mgrid[:N,:N,:N].astype(np.float32)*(2*np.pi/N)
    h=(np.sin(x)+np.cos(y)+np.sin(z))/3
    u=np.ones_like(h)
    v=rng.uniform(0,.003,h.shape).astype(np.float32)
    w=rng.uniform(0,.003,h.shape).astype(np.float32)
    q=np.zeros_like(u)
    for i in range(20):
        a,b,c=rng.integers(5,N-5,3)
        sl=np.s_[a-3:a+3,b-3:b+3,c-3:c+3]
        u[sl]=.5
        (v if i%2 else w)[sl]=.25
    out=Path("gallery/0006")
    out.mkdir(parents=True,exist_ok=True)
    metrics=[]
    for step in range(STEPS+1):
        if step%STRIDE==0:
            assert all(np.isfinite(a).all() and a.min()>=-1e-6 for a in (u,v,w))
            render(v,w,step,out/f"{step:05d}.png")
            metrics.append(dict(step=step,v_mean=float(v.mean()),w_mean=float(w.mean()),v_active=float((v>.1).mean()),w_active=float((w>.1).mean()),feedback_rms=float(np.sqrt(np.mean(q*q)))))
        if step==STEPS: break
        q+=.10*lap(q)+.025*(v-w-q)
        # Curl of a z-directed vector potential: divergence-free in each xy plane.
        psi=.8*q+.6*np.sin(x+step*.003)*np.sin(y)*np.cos(z)
        vy=-(psi-np.roll(psi,1,axis=2))
        vx=psi-np.roll(psi,1,axis=1)
        velocities=(np.zeros_like(vx),vy,vx)
        scale=min(1.,.8/max(float(np.max(2*(np.abs(vx)+np.abs(vy)))),1e-8))
        velocities=tuple(a*scale for a in velocities)
        u,v,w=(transport(a,velocities) for a in (u,v,w))
        a=u*v*v
        b=u*w*w
        u,v,w=(u+.12*lap(u)-a-b+.035*(1-u),v+.06*lap(v)+a-(.097+.009*h)*v,w+.05*lap(w)+b-(.094-.009*h)*w)
    (out/"metrics.json").write_text(json.dumps(metrics,indent=2))
    print(json.dumps(metrics[-1],indent=2))

if __name__=="__main__":
    main()
