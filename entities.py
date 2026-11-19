"""Generation 0013: four-dimensional component lineage tracking and periodic centroids."""
import json
from pathlib import Path
import numpy as np
from PIL import Image

N=24
STEPS=1200
STRIDE=8

def lap(a):
    return sum(np.roll(a,s,axis=i) for i in range(a.ndim) for s in (-1,1))-2*a.ndim*a

def transport(a, velocities):
    result=a.copy()
    for axis, velocity in enumerate(velocities):
        flux=np.maximum(velocity,0)*a+np.minimum(velocity,0)*np.roll(a,-1,axis=axis)
        result+=np.roll(flux,1,axis=axis)-flux
    return result

def diffuse(a,coefficient):
    result=np.zeros_like(a)
    for axis in range(a.ndim):
        face=.5*(coefficient+np.roll(coefficient,-1,axis=axis))
        flux=face*(np.roll(a,-1,axis=axis)-a)
        result+=flux-np.roll(flux,1,axis=axis)
    return result

def render(v,w,e,m,pulse,trait,step,path):
    # Orthographic emission-absorption ray integration through an orbiting volume.
    angle=2*np.pi*step/STEPS
    # Pad the viewing domain to contain the entire rotating cube.
    R=96
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
    signal=map_coordinates(pulse,coords,order=1,mode="constant",cval=0,prefilter=False)
    adaptation=map_coordinates(trait,coords,order=1,mode="constant",cval=0,prefilter=False)
    rgb=np.zeros((R,R,3),np.float32)
    trans=np.ones((R,R),np.float32)
    for k in range(R):
        density=a[k]+b[k]+.45*structure[k]
        opacity=1-np.exp(-0.20*density)
        color=(a[k,...,None]*np.array([1.0,0.28,0.045])+b[k,...,None]*np.array([0.04,0.62,1.0]))/np.maximum(density[...,None],1e-8)
        color+=.45*structure[k,...,None]*np.array([.8,.65,.95])/np.maximum(density[...,None],1e-8)
        color*= (0.25+0.75*energy[k,...,None])
        color+=signal[k,...,None]*np.array([.3,1.,.45])
        color+=.25*adaptation[k,...,None]*np.array([1.,.25,.65])
        rgb+=trans[...,None]*opacity[...,None]*color
        trans*=1-opacity
    rgb=np.clip(rgb,0,1)**0.75
    Image.fromarray(np.uint8(rgb*255)).resize((640,640),Image.Resampling.BICUBIC).save(path)

def periodic_labels(m):
    # Merge labels across periodic faces using union-find.
    from scipy.ndimage import label
    labels,count=label(m>.2)
    parent=list(range(count+1))
    def root(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]]
            i=parent[i]
        return i
    for axis in range(m.ndim):
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
    lookup=np.array([0]+[root(i) for i in range(1,count+1)],dtype=np.int32)
    return lookup[labels],merged

class Tracker:
    def __init__(self):
        self.previous=None
        self.next_id=1
        self.birth={}
        self.history=[]
        self.events=[]

    def update(self,m,step):
        labels,sizes=periodic_labels(m)
        ids=np.zeros_like(labels)
        links={}
        parents={}
        children={}
        if self.previous is not None:
            valid=(self.previous>0)&(labels>0)
            pairs,counts=np.unique(np.stack((self.previous[valid],labels[valid]),axis=1),axis=0,return_counts=True)
            old_sizes=dict(zip(*np.unique(self.previous[self.previous>0],return_counts=True)))
            for (old,new),n in zip(pairs,counts):
                old,new,n=int(old),int(new),int(n)
                if n/min(old_sizes[old],sizes[new])>=.1:
                    score=n/(old_sizes[old]+sizes[new]-n)
                    links[old,new]=score
                    parents.setdefault(new,[]).append(old)
                    children.setdefault(old,[]).append(new)
        matched={}
        used=set()
        for (old,new),score in sorted(links.items(),key=lambda item:(-item[1],item[0])):
            if old not in used and new not in matched:
                matched[new]=old
                used.add(old)
        records=[]
        mapping=np.zeros(int(labels.max())+1,dtype=np.int32)
        for new,size in sorted(sizes.items()):
            if new in matched:
                identity=matched[new]
            else:
                identity=self.next_id
                self.next_id+=1
                self.birth[identity]=step
                self.events.append(dict(step=step,type="birth",id=identity,parents=parents.get(new,[])))
            mapping[new]=identity
            cells=np.nonzero(labels==new)
            centroid=[]
            for axis,x in enumerate(cells):
                moment=np.exp(2j*np.pi*x/m.shape[axis]).mean()
                centroid.append(None if abs(moment)<.05 else float((np.angle(moment)%(2*np.pi))*m.shape[axis]/(2*np.pi)))
            records.append(dict(id=identity,size=size,age=step-self.birth[identity],centroid=centroid))
        ids=mapping[labels]
        for old,new_labels in children.items():
            if len(new_labels)>1:
                self.events.append(dict(step=step,type="split",parent=old,children=[int(mapping[n]) for n in new_labels]))
        for new,old_ids in parents.items():
            if len(old_ids)>1:
                self.events.append(dict(step=step,type="merge",parents=old_ids,child=int(mapping[new])))
        if self.previous is not None:
            for old in np.unique(self.previous):
                if old and int(old) not in used:
                    self.events.append(dict(step=step,type="disappearance",id=int(old)))
        self.previous=ids
        self.history.append(dict(step=step,entities=records))
        return ids,dict(structure_components=len(sizes),largest_structure=max(sizes.values(),default=0),oldest_entity=max((a["age"] for a in records),default=0),lineage_events=len(self.events))


def main():
    rng=np.random.default_rng(42)
    omega,z,y,x=np.mgrid[:N,:N,:N,:N].astype(np.float32)*(2*np.pi/N)
    h=(np.sin(x)+np.cos(y)+np.sin(z)+np.cos(omega))/4
    u=np.ones_like(h)
    v=rng.uniform(0,.003,h.shape).astype(np.float32)
    w=rng.uniform(0,.003,h.shape).astype(np.float32)
    q=np.zeros_like(u)
    e=np.ones_like(u)
    m=np.zeros_like(u)
    pulse=np.zeros_like(u)
    recovery=np.zeros_like(u)
    trait=np.full_like(u,.5)
    previous_mask=None
    supply=.012+.008*(h+1)/2
    for i in range(20):
        d,a,b,c=rng.integers(3,N-3,4)
        sl=np.s_[d-2:d+2,a-2:a+2,b-2:b+2,c-2:c+2]
        u[sl]=.5
        (v if i%2 else w)[sl]=.25
    pulse[(slice(N//2-2,N//2+2),)*4]=.95
    out=Path("gallery/0013")
    out.mkdir(parents=True,exist_ok=True)
    metrics=[]
    tracker=Tracker()
    for step in range(STEPS+1):
        if step%STRIDE==0:
            assert all(np.isfinite(a).all() and a.min()>=-1e-6 for a in (u,v,w,e,m))
            slice_position=(step/STEPS)*N*2
            index=int(slice_position)%N
            frac=slice_position%1
            def section(a):
                return (1-frac)*a[index]+frac*a[(index+1)%N]
            identities,entity_metrics=tracker.update(m,step)
            render(*(section(a) for a in (v,w,e,m,pulse,trait)),step,out/f"{step:05d}.png")
            mask=m>.2
            overlap=None if previous_mask is None else float(np.count_nonzero(mask & previous_mask)/max(1,np.count_nonzero(mask | previous_mask)))
            previous_mask=mask.copy()
            metrics.append(dict(step=step,slice_position=float(slice_position%N),v_mean=float(v.mean()),w_mean=float(w.mean()),v_active=float((v>.1).mean()),w_active=float((w>.1).mean()),feedback_rms=float(np.sqrt(np.mean(q*q))),energy_mean=float(e.mean()),energy_min=float(e.min()),energy_depleted=float((e<.25).mean()),structure_mean=float(m.mean()),structure_active=float((m>.2).mean()),signal_mean=float(pulse.mean()),signal_active=float((pulse>.5).mean()),recovery_mean=float(recovery.mean()),trait_mean=float(trait.mean()),trait_std=float(trait.std()),trait_min=float(trait.min()),trait_max=float(trait.max()),structure_jaccard=overlap,**entity_metrics))
        if step==STEPS: break
        q+=.075*lap(q)+.025*(v-w-q)
        # Backward differences commute, so the discrete face divergence of curl is zero.
        def d(a,axis):
            return a-np.roll(a,1,axis=axis)
        # Antisymmetric face potential on all six coordinate planes.
        coordinates=(omega,z,y,x)
        velocities=[np.zeros_like(q) for _ in range(4)]
        for i in range(4):
            for j in range(i+1,4):
                potential=.35*q+.25*np.sin(coordinates[i]+step*.003)*np.cos(coordinates[j]-step*.002)
                velocities[i]+=d(potential,j)
                velocities[j]-=d(potential,i)
        outgoing=sum(np.maximum(a,0)+np.maximum(-np.roll(a,1,axis=i),0) for i,a in enumerate(velocities))
        scale=min(1.,.8/max(float(outgoing.max()),1e-8))
        velocities=tuple(a*scale for a in velocities)
        divergence=sum(d(a,i) for i,a in enumerate(velocities))
        assert float(np.abs(divergence).max())<1e-5
        u,v,w,e=(transport(a,velocities) for a in (u,v,w,e))
        # Energy gates autocatalysis; consumption is proportional to reaction flux.
        # Bounded excitable activator and slow refractory recovery.
        stimulus=.08*np.clip((v+w-.18)*4,0,1)
        excitation=pulse*(1-pulse)*np.maximum(pulse-.18-.65*recovery,0)
        inhibition=pulse*np.maximum(.18+.65*recovery-pulse,0)
        pulse=pulse+diffuse(pulse,.08*(.25+.75*m))+.35*(excitation-inhibition)+stimulus*(1-pulse)-.015*pulse
        recovery+=.025*(pulse-recovery)
        assert np.isfinite(pulse).all() and pulse.min()>=-1e-6 and pulse.max()<=1.00001
        assert np.isfinite(recovery).all() and recovery.min()>=-1e-6 and recovery.max()<=1.00001
        # Signals modulate chemistry without creating substrate.
        # Slow environmental memory trades off catalytic advantage between species.
        target=np.clip(.5+.45*(pulse-recovery)+.5*(e-.9)+.6*(v-w),0,1)
        trait=trait+.015*lap(trait)+.008*(target-trait)
        assert np.isfinite(trait).all() and trait.min()>=-1e-6 and trait.max()<=1.00001
        advantage=.24*(2*trait-1)
        a=u*v*v*e*(1+.12*pulse+advantage)
        b=u*w*w*e*(1-.12*pulse-advantage)
        e=e+.075*lap(e)+supply*(1-e)-.10*(a+b)
        assert np.isfinite(e).all() and e.min()>=-1e-6 and e.max()<=1.00001
        # Activity deposits a slowly relaxing structural field; structure impedes diffusion.
        deposit=.12*(a+b)
        m=m+.025*lap(m)+deposit*(1-m)-.003*m
        assert np.isfinite(m).all() and m.min()>=-1e-6 and m.max()<=1.00001
        mobility=1/(1+5*m)
        u,v,w=(u+diffuse(u,.085*mobility)-a-b+.035*(1-u),v+diffuse(v,.045*mobility)+a-(.097+.009*h)*v,w+diffuse(w,.0375*mobility)+b-(.094-.009*h)*w)
    (out/"metrics.json").write_text(json.dumps(metrics,indent=2))
    (out/"lineages.json").write_text(json.dumps(dict(history=tracker.history,events=tracker.events),indent=2))
    print(json.dumps(metrics[-1],indent=2))

if __name__=="__main__":
    main()
