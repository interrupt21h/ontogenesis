"""Generation 0021: periodic cubical Euler characteristic and cut-invariant complement components."""
import json
from pathlib import Path
import numpy as np
from PIL import Image

N=24
STEPS=4800
STRIDE=4

def lap(a):
    return sum(np.roll(a,s,axis=i) for i in range(a.ndim) for s in (-1,1))-2*a.ndim*a

def transport(a, velocities):
    result=a.copy()
    for axis, velocity in enumerate(velocities):
        flux=np.maximum(velocity,0)*a+np.minimum(velocity,0)*np.roll(a,-1,axis=axis)
        result+=np.roll(flux,1,axis=axis)-flux
    return result

def diffuse(a,coefficient,barrier=None):
    result=np.zeros_like(a)
    for axis in range(a.ndim):
        face=.5*(coefficient+np.roll(coefficient,-1,axis=axis))
        if barrier is not None:
            face=face*np.exp(-barrier[0]*np.abs(np.roll(barrier[1],-1,axis=axis)-barrier[1]))
        flux=face*(np.roll(a,-1,axis=axis)-a)
        result+=flux-np.roll(flux,1,axis=axis)
    return result

def render(v,w,e,m,pulse,trait,step,path=None,identities=None):
    # Orthographic emission-absorption ray integration through an orbiting volume.
    angle=4*np.pi*step/STEPS
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
    entity=map_coordinates(identities,coords,order=0,mode="constant",cval=0,prefilter=False) if identities is not None else None
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
        if entity is not None:
            for identity in np.unique(entity[k]):
                if identity:
                    mask=entity[k]==identity
                    color[mask]=.3*color[mask]+.7*np.array(entity_color(int(identity)))/255
        rgb+=trans[...,None]*opacity[...,None]*color
        trans*=1-opacity
    rgb=np.clip(rgb,0,1)**0.75
    image=Image.fromarray(np.uint8(rgb*255)).resize((480,480),Image.Resampling.BICUBIC)
    if path is not None:
        image.save(path)
    return image

def entity_color(identity):
    import colorsys
    return tuple(int(c*255) for c in colorsys.hsv_to_rgb((identity*.61803398875)%1,.65,1))

def observatory(fields,identities,tracker,step,position,path,metrics):
    from PIL import ImageDraw, ImageFont
    canvas=Image.new("RGB",(1280,720),(8,13,23))
    draw=ImageDraw.Draw(canvas)
    font=ImageFont.load_default(size=16)
    title=ImageFont.load_default(size=26)
    small=ImageFont.load_default(size=13)
    draw.text((24,16),"ONTOGENESIS / 0021     OBSERVATORY",font=title,fill=(220,232,247))
    draw.text((24,54),f"STEP {step:04d} / {STEPS}     FOUR-DIMENSIONAL PERIODIC DOMAIN",font=font,fill=(136,166,190))
    for j,offset in enumerate((0,N/2)):
        p=(position+offset)%N
        index=int(p)
        frac=p%1
        sections=[(1-frac)*a[index]+frac*a[(index+1)%N] for a in fields]
        nearest=identities[int(np.floor(p+.5))%N]
        image=render(*sections,step,identities=nearest if j else None)
        canvas.paste(image,(20+j*485,103))
        draw.text((30+j*485,83),f"{'CHEMISTRY + METABOLITES' if not j else 'ENTITY IDENTITIES'} / omega={p:.2f}",font=font,fill=(200,220,240))
    draw.text((1000,90),"LIVE ENTITY RECORD",font=font,fill=(220,232,247))
    records=sorted(tracker.history[-1]["entities"],key=lambda a:-a["size"])
    for j,a in enumerate(records[:8]):
        y=120+j*35
        draw.rectangle((1000,y,1011,y+11),fill=entity_color(a["id"]))
        draw.text((1020,y-2),f"#{a['id']}  {a['size']:,} cells",font=small,fill="white")
        draw.text((1020,y+12),f"age {a['age']} steps",font=small,fill=(145,167,190))
    draw.text((1000,385),f"Euler chi: {metrics[-1]['euler_characteristic']}",font=small,fill=(100,220,180))
    draw.text((1000,413),"RECENT EVENTS",font=font,fill=(220,232,247))
    for j,event in enumerate(tracker.events[-7:]):
        draw.text((1000,440+j*18),f"{event['step']:04d}  {event['type']}",font=small,fill=(180,190,210))
    # Fixed scales and full-run time axis; no rescaling as history grows.
    panels=[("ACTIVE COVERAGE", [("v_active",(239,165,74),1),("w_active",(60,190,235),1),("structure_active",(180,145,235),1)]),
            ("GENETIC ENTROPY / 3 bits",[("genotype_entropy",(220,170,245),3)]),
            ("SECONDARY COMPLEMENT / coverage",[("cavity_fraction",(80,220,160),1)])]
    for j,(heading,series) in enumerate(panels):
        left=24+j*320
        draw.text((left,590),heading,font=small,fill=(200,220,240))
        draw.rectangle((left,614,left+300,692),outline=(75,90,110))
        for key,color,scale in series:
            points=[(left+300*h["step"]/STEPS,692-78*np.clip(h[key]/scale,0,1)) for h in metrics]
            if len(points)>1:
                draw.line(points,fill=color,width=2)
        for k,(key,color,scale) in enumerate(series):
            draw.text((left+k*98,696),key.replace("structure_active","matrix").replace("_active",""),font=small,fill=color)
    canvas.save(path)

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

def cubical_counts(mask):
    # Occupied voxels generate a closed cubical complex on the torus.
    from itertools import combinations
    counts=[]
    for k in range(mask.ndim+1):
        total=0
        for axes in combinations(range(mask.ndim),k):
            cells=mask.copy()
            for axis in range(mask.ndim):
                if axis not in axes:
                    cells |= np.roll(cells,1,axis=axis)
            total+=int(cells.sum())
        counts.append(total)
    return counts

def winding_components(mask):
    from scipy.ndimage import label
    labels,n=label(mask)
    graph=[[] for _ in range(n+1)]
    for axis in range(mask.ndim):
        lo=np.take(labels,0,axis=axis)
        hi=np.take(labels,-1,axis=axis)
        valid=(lo>0)&(hi>0)
        shift=np.zeros(mask.ndim,dtype=int)
        shift[axis]=-1
        for a,b in np.unique(np.stack((lo[valid],hi[valid]),axis=1),axis=0):
            graph[a].append((b,shift))
            graph[b].append((a,-shift))
    sizes=np.bincount(labels.ravel(),minlength=n+1)
    offsets={}
    results=[]
    for root in range(1,n+1):
        if root in offsets: continue
        offsets[root]=np.zeros(mask.ndim,dtype=int)
        queue=[root]
        axes=np.zeros(mask.ndim,dtype=bool)
        size=0
        for a in queue:
            size+=int(sizes[a])
            for b,delta in graph[a]:
                expected=offsets[a]+delta
                if b in offsets:
                    axes |= expected!=offsets[b]
                else:
                    offsets[b]=expected
                    queue.append(b)
        results.append(dict(size=size,winding_axes=np.flatnonzero(axes).tolist()))
    return results

def multiscale_topology(m):
    result=[]
    for threshold in (.10,.15,.20,.25,.30):
        mask=m>threshold
        counts=cubical_counts(mask)
        components=winding_components(mask)
        complement=winding_components(~mask)
        result.append(dict(threshold=threshold,coverage=float(mask.mean()),
            euler=sum((-1)**k*n for k,n in enumerate(counts)),
            components=len(components),
            winding_components=sum(bool(c["winding_axes"]) for c in components),
            winding_axes=sorted({a for c in components for a in c["winding_axes"]}),
            nonwinding_complement_cells=sum(c["size"] for c in complement if not c["winding_axes"]),
            nonwinding_complement_components=sum(not c["winding_axes"] for c in complement)))
    return result

def cavity_metrics(m,v,w,e):
    # Periodic face components; distinguish largest background from smaller
    # components without claiming that smaller components are contractible.
    labels,sizes=periodic_labels((m<=.2).astype(np.float32))
    exterior=max(sizes,key=lambda i:(sizes[i],-i)) if sizes else 0
    candidates=[i for i,n in sizes.items() if i!=exterior and n>=8]
    mask=np.isin(labels,candidates)
    counts=cubical_counts(m>.2)
    return dict(cavity_candidates=len(candidates),cavity_fraction=float(mask.mean()),
                largest_cavity=max((sizes[i] for i in candidates),default=0),
                cavity_v_mean=float(v[mask].mean()) if mask.any() else None,
                cavity_w_mean=float(w[mask].mean()) if mask.any() else None,
                cavity_energy_mean=float(e[mask].mean()) if mask.any() else None,
                complement_components=len(sizes),cubical_cells=counts,
                euler_characteristic=sum((-1)**k*n for k,n in enumerate(counts)))

def topology_selftest():
    a=np.zeros((4,)*4,dtype=bool)
    assert cubical_counts(a)==[0]*5
    a[0,0,0,0]=True
    assert cubical_counts(a)==[16,32,24,8,1]
    a[:]=True
    assert cubical_counts(a)==[256,1024,1536,1024,256]
    a[:]=False
    a[:,1,1,1]=True
    c=cubical_counts(a)
    assert sum((-1)**k*n for k,n in enumerate(c))==0

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
    topology_selftest()
    a=np.zeros((4,)*4,dtype=bool)
    a[0,1,1,1]=a[-1,1,1,1]=True
    assert winding_components(a)==[dict(size=2,winding_axes=[])]
    a[:,1,1,1]=True
    assert winding_components(a)==[dict(size=4,winding_axes=[0])]
    assert winding_components(np.ones_like(a))==[dict(size=256,winding_axes=[0,1,2,3])]
    assert winding_components(np.zeros_like(a))==[]
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
    xv=np.zeros_like(u)
    xw=np.zeros_like(u)

    supply=.012+.008*(h+1)/2
    for i in range(20):
        d,a,b,c=rng.integers(3,N-3,4)
        sl=np.s_[d-2:d+2,a-2:a+2,b-2:b+2,c-2:c+2]
        u[sl]=.5
        (v if i%2 else w)[sl]=.25
    bits=np.array([[(g>>i)&1 for i in range(3)] for g in range(8)])
    gv=np.stack([v/8 for _ in bits])
    gw=np.stack([w/8 for _ in bits])
    pulse[(slice(N//2-2,N//2+2),)*4]=.95
    out=Path("gallery/0021")
    out.mkdir(parents=True,exist_ok=True)
    metrics=[]
    tracker=Tracker()
    for step in range(STEPS+1):
        if step%STRIDE==0:
            assert all(np.isfinite(a).all() and a.min()>=-1e-6 for a in (u,v,w,e,m))
            slice_position=(step/STEPS)*N*4
            index=int(slice_position)%N
            frac=slice_position%1
            def section(a):
                return (1-frac)*a[index]+frac*a[(index+1)%N]
            identities,entity_metrics=tracker.update(m,step)
            pooled=gv+gw
            allele=np.clip((xv+xw)/.3,0,1)
            totals=pooled.sum(axis=(1,2,3,4),dtype=np.float64)
            frequencies=totals/max(totals.sum(),1e-30)
            entropy=float(-sum(p*np.log2(p) for p in frequencies if p>0))
            cavities=cavity_metrics(m,v,w,e)
            mask=m>.2
            boundary_faces=sum(int(np.count_nonzero(mask!=np.roll(mask,-1,axis=i))) for i in range(m.ndim))
            occupied=int(mask.sum())
            overlap=None if previous_mask is None else float(np.count_nonzero(mask & previous_mask)/max(1,np.count_nonzero(mask | previous_mask)))
            previous_mask=mask.copy()
            metrics.append(dict(step=step,slice_position=float(slice_position%N),v_mean=float(v.mean()),w_mean=float(w.mean()),v_active=float((v>.1).mean()),w_active=float((w>.1).mean()),feedback_rms=float(np.sqrt(np.mean(q*q))),energy_mean=float(e.mean()),energy_min=float(e.min()),energy_depleted=float((e<.25).mean()),structure_mean=float(m.mean()),structure_active=float((m>.2).mean()),signal_mean=float(pulse.mean()),signal_active=float((pulse>.5).mean()),recovery_mean=float(recovery.mean()),trait_mean=float(trait.mean()),trait_std=float(trait.std()),trait_min=float(trait.min()),trait_max=float(trait.max()),structure_jaccard=overlap,boundary_faces=boundary_faces,boundary_per_cell=boundary_faces/max(occupied,1),matrix_threshold_coverage={str(t):float((m>t).mean()) for t in (.1,.15,.2,.25,.3)},metabolite_v_mean=float(xv.mean()),metabolite_w_mean=float(xw.mean()),metabolite_overlap=float(np.minimum(xv,xw).mean()),genotype_frequencies=frequencies.tolist(),genotype_entropy=entropy,trait_frequencies=(frequencies@bits).tolist(),**entity_metrics,**cavities))
            if step%120==0:
                metrics[-1]['multiscale_topology']=multiscale_topology(m)
            observatory((v,w,e,m,pulse,allele),identities,tracker,step,slice_position,out/f"{step:05d}.png",metrics)
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
        u,e,xv,xw=(transport(a,velocities) for a in (u,e,xv,xw))
        gv=np.stack([transport(a,velocities) for a in gv])
        gw=np.stack([transport(a,velocities) for a in gw])
        v,w=gv.sum(axis=0),gw.sum(axis=0)
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
        # Linked binary genes: catalytic throughput, energy economy, signal response.
        mutation=rng.uniform(.001,.009,v.shape).astype(np.float32)
        def reproduce(pop,total,base,donor):
            births=[]
            uptake=[]
            for g,(c,k,s) in enumerate(bits):
                fitness=(1+.16*(2*c-1))*(1+.18*(2*k-1)*(1-e))*(1+.20*(2*s-1)*(2*pulse-1))
                cost=(.085+.035*c-.025*k)
                bonus=.45*donor/(.12+donor)*(.35+.65*k)
                rate=base*pop[g]/np.maximum(total,1e-30)*fitness*(1+bonus)
                uptake.append(rate*bonus/(1+bonus))
                births.append(rate)
            raw=np.stack(births)
            mutated=raw*(1-3*mutation)
            for g in range(8):
                for bit in (1,2,4):
                    mutated[g]+=mutation*raw[g^bit]
            consumption=sum(raw[g]*(.085+.035*c-.025*k) for g,(c,k,s) in enumerate(bits))
            matrix=sum(raw[g]*(.045+.065*s) for g,(c,k,s) in enumerate(bits))
            return mutated,raw.sum(axis=0),consumption,matrix,sum(uptake)
        bv,a,cv,mv,uv=reproduce(gv,v,u*v*v*e*(1+.12*pulse+advantage),xw)
        bw,b,cw,mw,uw=reproduce(gw,w,u*w*w*e*(1-.12*pulse-advantage),xv)
        # Secreted metabolites diffuse, decay and are consumed by the other species.
        xv=xv+.06*lap(xv)+.18*a-.025*xv-np.minimum(.12*uw,.25*xv)
        xw=xw+.06*lap(xw)+.18*b-.025*xw-np.minimum(.12*uv,.25*xw)
        assert all(np.isfinite(z).all() and z.min()>=-1e-6 for z in (xv,xw))
        e=e+.075*lap(e)+supply*(1-e)-cv-cw
        assert np.isfinite(e).all() and e.min()>=-1e-6 and e.max()<=1.00001
        # Activity deposits a slowly relaxing structural field; structure impedes diffusion.
        deposit=mv+mw
        m=m+.025*lap(m)+deposit*(1-m)-(.005+.006*pulse)*m
        assert np.isfinite(m).all() and m.min()>=-1e-6 and m.max()<=1.00001
        mobility=1/(1+5*m)
        gv=np.stack([g+diffuse(g,.045*mobility,(4.,m))+born-(.097+.009*h)*g for g,born in zip(gv,bv)])
        gw=np.stack([g+diffuse(g,.0375*mobility,(4.,m))+born-(.094-.009*h)*g for g,born in zip(gw,bw)])
        u=u+diffuse(u,.085*mobility,(1.,m))-a-b+.035*(1-u)
        v,w=gv.sum(axis=0),gw.sum(axis=0)
        assert np.isfinite(gv).all() and np.isfinite(gw).all()
        assert gv.min()>=-1e-6 and gw.min()>=-1e-6
    (out/"metrics.json").write_text(json.dumps(metrics,indent=2))
    (out/"lineages.json").write_text(json.dumps(dict(history=tracker.history,events=tracker.events),indent=2))
    print(json.dumps(metrics[-1],indent=2))

if __name__=="__main__":
    main()
