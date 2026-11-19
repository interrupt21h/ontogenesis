"""Generation 0007: three-axis curl transport and trilinear volume rendering."""
import json
from pathlib import Path
import numpy as np
from PIL import Image

N=80
STEPS=2400
STRIDE=12

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
    # Pad the viewing domain to contain the entire rotating cube.
    R=144
    p=np.linspace(-N*.88,N*.88,R,dtype=np.float32)
    z,y,x=np.meshgrid(p,p,p,indexing="ij")
    elevation=.35*np.sin(angle)+.22
    ce,se=np.cos(elevation),np.sin(elevation)
    yy=ce*y-se*z
    zz=se*y+ce*z
    c,s=np.cos(angle),np.sin(angle)
    coords=np.array([-s*x+c*zz,yy,c*x+s*zz],dtype=np.float32)+(N-1)/2
    from scipy.ndimage import map_coordinates
    a=map_coordinates(v,coords,order=1,mode="constant",cval=0,prefilter=False)
    b=map_coordinates(w,coords,order=1,mode="constant",cval=0,prefilter=False)
    rgb=np.zeros((R,R,3),np.float32)
    trans=np.ones((R,R),np.float32)
    for k in range(R):
        density=a[k]+b[k]
        opacity=1-np.exp(-0.20*density)
        color=(a[k,...,None]*np.array([1.0,0.28,0.045])+b[k,...,None]*np.array([0.04,0.62,1.0]))/np.maximum(density[...,None],1e-8)
        rgb+=trans[...,None]*opacity[...,None]*color
        trans*=1-opacity
    rgb=np.clip(rgb,0,1)**0.75
    Image.fromarray(np.uint8(rgb*255)).resize((640,640),Image.Resampling.BICUBIC).save(path)

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
    out=Path("gallery/0007")
    out.mkdir(parents=True,exist_ok=True)
    metrics=[]
    for step in range(STEPS+1):
        if step%STRIDE==0:
            assert all(np.isfinite(a).all() and a.min()>=-1e-6 for a in (u,v,w))
            render(v,w,step,out/f"{step:05d}.png")
            metrics.append(dict(step=step,v_mean=float(v.mean()),w_mean=float(w.mean()),v_active=float((v>.1).mean()),w_active=float((w>.1).mean()),feedback_rms=float(np.sqrt(np.mean(q*q)))))
        if step==STEPS: break
        q+=.10*lap(q)+.025*(v-w-q)
        # Backward differences commute, so the discrete face divergence of curl is zero.
        def d(a,axis):
            return a-np.roll(a,1,axis=axis)
        az=.8*q+.45*np.sin(x+step*.003)*np.sin(y)
        ay=.6*q+.45*np.sin(z-step*.002)*np.cos(x)
        ax=-.5*q+.45*np.cos(y+step*.002)*np.sin(z)
        vx=d(az,1)-d(ay,0)
        vy=d(ax,0)-d(az,2)
        vz=d(ay,2)-d(ax,1)
        velocities=(vz,vy,vx)
        outgoing=sum(np.maximum(a,0)+np.maximum(-np.roll(a,1,axis=i),0) for i,a in enumerate(velocities))
        scale=min(1.,.8/max(float(outgoing.max()),1e-8))
        velocities=tuple(a*scale for a in velocities)
        divergence=sum(d(a,i) for i,a in enumerate(velocities))
        assert float(np.abs(divergence).max())<1e-5
        u,v,w=(transport(a,velocities) for a in (u,v,w))
        a=u*v*v
        b=u*w*w
        u,v,w=(u+.12*lap(u)-a-b+.035*(1-u),v+.06*lap(v)+a-(.097+.009*h)*v,w+.05*lap(w)+b-(.094-.009*h)*w)
    (out/"metrics.json").write_text(json.dumps(metrics,indent=2))
    print(json.dumps(metrics[-1],indent=2))

if __name__=="__main__":
    main()
