"""Generation 0009: persistent structural memory and conservative heterogeneous diffusion."""
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

def diffuse(a,coefficient):
    result=np.zeros_like(a)
    for axis in range(3):
        face=.5*(coefficient+np.roll(coefficient,-1,axis=axis))
        flux=face*(np.roll(a,-1,axis=axis)-a)
        result+=flux-np.roll(flux,1,axis=axis)
    return result

def render(v,w,e,m,step,path):
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
    energy=map_coordinates(e,coords,order=1,mode="constant",cval=0,prefilter=False)
    structure=map_coordinates(m,coords,order=1,mode="constant",cval=0,prefilter=False)
    rgb=np.zeros((R,R,3),np.float32)
    trans=np.ones((R,R),np.float32)
    for k in range(R):
        density=a[k]+b[k]+.45*structure[k]
        opacity=1-np.exp(-0.20*density)
        color=(a[k,...,None]*np.array([1.0,0.28,0.045])+b[k,...,None]*np.array([0.04,0.62,1.0]))/np.maximum(density[...,None],1e-8)
        color+=.45*structure[k,...,None]*np.array([.8,.65,.95])/np.maximum(density[...,None],1e-8)
        color*= (0.25+0.75*energy[k,...,None])
        rgb+=trans[...,None]*opacity[...,None]*color
        trans*=1-opacity
    rgb=np.clip(rgb,0,1)**0.75
    Image.fromarray(np.uint8(rgb*255)).resize((640,640),Image.Resampling.BICUBIC).save(path)

def component_metrics(m):
    # Merge labels across periodic faces using union-find.
    from scipy.ndimage import label
    labels,count=label(m>.2)
    parent=list(range(count+1))
    def root(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]]
            i=parent[i]
        return i
    for axis in range(3):
        lo=np.take(labels,0,axis=axis).ravel()
        hi=np.take(labels,-1,axis=axis).ravel()
        mask=(lo>0)&(hi>0)
        for a,b in zip(lo[mask],hi[mask]):
            parent[root(int(a))]=root(int(b))
    sizes=np.bincount(labels.ravel(),minlength=count+1)
    merged={}
    for i in range(1,count+1):
        k=root(i)
        merged[k]=merged.get(k,0)+int(sizes[i])
    return dict(structure_components=len(merged),largest_structure=max(merged.values(),default=0))

def main():
    rng=np.random.default_rng(42)
    z,y,x=np.mgrid[:N,:N,:N].astype(np.float32)*(2*np.pi/N)
    h=(np.sin(x)+np.cos(y)+np.sin(z))/3
    u=np.ones_like(h)
    v=rng.uniform(0,.003,h.shape).astype(np.float32)
    w=rng.uniform(0,.003,h.shape).astype(np.float32)
    q=np.zeros_like(u)
    e=np.ones_like(u)
    m=np.zeros_like(u)
    supply=.012+.008*(h+1)/2
    for i in range(20):
        a,b,c=rng.integers(5,N-5,3)
        sl=np.s_[a-3:a+3,b-3:b+3,c-3:c+3]
        u[sl]=.5
        (v if i%2 else w)[sl]=.25
    out=Path("gallery/0009")
    out.mkdir(parents=True,exist_ok=True)
    metrics=[]
    for step in range(STEPS+1):
        if step%STRIDE==0:
            assert all(np.isfinite(a).all() and a.min()>=-1e-6 for a in (u,v,w,e,m))
            render(v,w,e,m,step,out/f"{step:05d}.png")
            metrics.append(dict(step=step,v_mean=float(v.mean()),w_mean=float(w.mean()),v_active=float((v>.1).mean()),w_active=float((w>.1).mean()),feedback_rms=float(np.sqrt(np.mean(q*q))),energy_mean=float(e.mean()),energy_min=float(e.min()),energy_depleted=float((e<.25).mean()),structure_mean=float(m.mean()),structure_active=float((m>.2).mean()),**component_metrics(m)))
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
        u,v,w,e=(transport(a,velocities) for a in (u,v,w,e))
        # Energy gates autocatalysis; consumption is proportional to reaction flux.
        a=u*v*v*e
        b=u*w*w*e
        e=e+.10*lap(e)+supply*(1-e)-.10*(a+b)
        assert np.isfinite(e).all() and e.min()>=-1e-6 and e.max()<=1.00001
        # Activity deposits a slowly relaxing structural field; structure impedes diffusion.
        deposit=.12*(a+b)
        m=m+.025*lap(m)+deposit*(1-m)-.003*m
        assert np.isfinite(m).all() and m.min()>=-1e-6 and m.max()<=1.00001
        mobility=1/(1+5*m)
        u,v,w=(u+diffuse(u,.12*mobility)-a-b+.035*(1-u),v+diffuse(v,.06*mobility)+a-(.097+.009*h)*v,w+diffuse(w,.05*mobility)+b-(.094-.009*h)*w)
    (out/"metrics.json").write_text(json.dumps(metrics,indent=2))
    print(json.dumps(metrics[-1],indent=2))

if __name__=="__main__":
    main()
