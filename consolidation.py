"""G0026 consolidation: unchanged G0023 integrator, independent observers."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
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


def measure(m):
    x=m.astype(np.float64); mean=float(x.mean()); std=float(x.std())
    hist,edges=np.histogram(x,bins=100,range=(0,1))
    centered=x-mean
    power=np.abs(np.fft.rfftn(centered))**2
    power.flat[0]=0
    peak=np.unravel_index(power.argmax(),power.shape)
    freq=[np.fft.fftfreq(n)[i] if j<3 else np.fft.rfftfreq(n)[i] for j,(n,i) in enumerate(zip(x.shape,peak))]
    radial=float(np.linalg.norm(freq))
    return dict(matrix_mean=mean,matrix_std=std,matrix_cv=std/max(mean,1e-12),gradient_energy=sum(float(np.mean((np.roll(x,1,axis=j)-x)**2)) for j in range(4)),histogram=hist.tolist(),histogram_edges=edges.tolist(),dominant_mode_wavelength_cells=1/radial if radial and std>0 else None,quantiles=np.quantile(x,[.05,.25,.5,.75,.95]).tolist(),coverage={str(t):float((x>t).mean()) for t in (.1,.15,.2,.25,.3)})
def run(seed=42,n=24,steps=4800,stride=4,arm="baseline",observe=True,intervention=None,observer=None,cinematic_observer=None,cinematic_steps=None,velocity_feedback=None,crossfeed=(True,True),season_switch=None,ecology_observer=None,ecology_steps=None,v_decay_multiplier=1.0,niche_strength=0.0):
    if len(crossfeed)!=2 or any(type(flag) is not bool for flag in crossfeed):
        raise ValueError("crossfeed must be (W-to-V, V-to-W) booleans")
    if season_switch is not None and not 1<=season_switch<steps:
        raise ValueError("season_switch must be strictly within simulation")
    # Explicit G0031 controlled mortality-rate perturbation; default is
    # exactly the historical G0026/G0028/G0030 numerical update.
    if not 0.05 <= float(v_decay_multiplier) <= 1.5:
        raise ValueError("v_decay_multiplier must be in [0.05, 1.5]")
    # G0032 opt-in spatial preference; zero is exactly the historical update.
    if not 0.0 <= float(niche_strength) <= 0.75:
        raise ValueError("niche_strength must be finite and in [0.0, 0.75]")
    N=n;STEPS=steps
    COST=float(arm in ("cost","combined")); MAINT=float(arm in ("maintenance","combined"))
    rng=np.random.default_rng(seed)
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
    # Matched environmental inversion with unchanged domain-mean replenishment.
    winter_supply=(2*float(supply.mean())-supply).astype(np.float32)
    for i in range(20):
        d,a,b,c=rng.integers(3,N-3,4)
        sl=np.s_[d-2:d+2,a-2:a+2,b-2:b+2,c-2:c+2]
        u[sl]=.5
        (v if i%2 else w)[sl]=.25
    bits=np.array([[(g>>i)&1 for i in range(3)] for g in range(8)])
    gv=np.stack([v/8 for _ in bits])
    gw=np.stack([w/8 for _ in bits])
    pulse[(slice(N//2-2,N//2+2),)*4]=.95

    hashes={}; rows=[]
    for step in range(STEPS+1):
        # Inert for historical runs; G0028 applies a deterministic experiment.
        if intervention is not None:
            intervention(step,e,m)
        if observer is not None:
            frozen=tuple(field.view() for field in (e,m,v,w))
            for field in frozen:
                field.flags.writeable=False
            observer(step,*frozen)
        if cinematic_observer is not None and (cinematic_steps is None or step in cinematic_steps):
            # Selected full-resolution 3D numerical volumes. Read-only views are
            # temporary; the consumer must snapshot the requested sections.
            fields = {"energy": e.view(), "matrix": m.view(),
                      "species_v": v.view(), "species_w": w.view(),
                      "pulse": pulse.view(), "trait": trait.view(),
                      "recovery": recovery.view()}
            for field in fields.values():
                field.flags.writeable = False
            cinematic_observer(step, fields)
        if ecology_observer is not None and (ecology_steps is None or step in ecology_steps):
            ecological_fields={"energy":e.view(),"matrix":m.view(),
                               "species_v":v.view(),"species_w":w.view(),
                               "metabolite_v":xv.view(),"metabolite_w":xw.view(),
                               "genotypes_v":gv.view(),"genotypes_w":gw.view(),
                               "habitat_bias":h.view()}
            for field in ecological_fields.values():
                field.flags.writeable=False
            ecology_observer(step,ecological_fields)
        if step%120==0 or step==STEPS:
            hashes[str(step)]=hashlib.sha256(b"".join(np.ascontiguousarray(a).tobytes() for a in (u,v,w,q,e,m,pulse,recovery,trait,xv,xw,gv,gw))).hexdigest()
        if observe and (step%stride==0 or step==STEPS):
            # Observer receives a read-only copy, never the integrator's arrays.
            snapshot=m.copy();snapshot.flags.writeable=False
            row=measure(snapshot) if step%120==0 or step==STEPS else {"matrix_mean":float(snapshot.mean())}
            rows.append(dict(step=step,**row))
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
        if velocity_feedback is not None:
            state = {"energy": e.view(), "matrix": m.view(),
                     "species_v": v.view(), "species_w": w.view()}
            for field in state.values():
                field.flags.writeable = False
            correction = velocity_feedback(step, state)
            if len(correction) != 4 or any(a.shape != q.shape for a in correction):
                raise ValueError("Feedback requires four full-dimensional face fields")
            for axis in range(4):
                velocities[axis] += correction[axis]
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
                bonus=(.45*donor/(.12+donor)*(.35+.65*k) if donor is not None else 0.)
                rate=base*pop[g]/np.maximum(total,1e-30)*fitness*(1+bonus)*(1-.08*s*COST)
                uptake.append(rate*bonus/(1+bonus))
                births.append(rate)
            raw=np.stack(births)
            mutated=raw*(1-3*mutation)
            for g in range(8):
                for bit in (1,2,4):
                    mutated[g]+=mutation*raw[g^bit]
            consumption=sum(raw[g]*(.085+.035*c-.025*k+.02*s*COST) for g,(c,k,s) in enumerate(bits))
            matrix=sum(raw[g]*(.045+.065*s) for g,(c,k,s) in enumerate(bits))
            return mutated,raw.sum(axis=0),consumption,matrix,sum(uptake)
        base_v=u*v*v*e*(1+.12*pulse+advantage)
        base_w=u*w*w*e*(1-.12*pulse-advantage)
        # Matched static environmental niches.  At zero strength no extra
        # multiplication is performed, preserving historic floating-point
        # ordering and baseline state hashes exactly.
        if niche_strength:
            base_v=base_v*(1+niche_strength*h)
            base_w=base_w*(1-niche_strength*h)
        bv,a,cv,mv,uv=reproduce(gv,v,base_v,
                                 xw if crossfeed[0] else None)
        bw,b,cw,mw,uw=reproduce(gw,w,base_w,
                                 xv if crossfeed[1] else None)
        # Secreted metabolites diffuse, decay and are consumed by the other species.
        xv=xv+.06*lap(xv)+.18*a-.025*xv-np.minimum(.12*uw,.25*xv)
        xw=xw+.06*lap(xw)+.18*b-.025*xw-np.minimum(.12*uv,.25*xw)
        assert all(np.isfinite(z).all() and z.min()>=-1e-6 for z in (xv,xw))
        e=e+.075*lap(e)+(winter_supply if season_switch is not None and step>=season_switch else supply)*(1-e)-cv-cw
        assert np.isfinite(e).all() and e.min()>=-1e-6 and e.max()<=1.00001
        # Activity deposits a slowly relaxing structural field; structure impedes diffusion.
        deposit=mv+mw
        builders=(gv[4:].sum(axis=0)+gw[4:].sum(axis=0))
        maintenance=builders/(.08+builders)*e
        m=m+.025*lap(m)+deposit*(1-m)-(.005+.006*pulse)*(1-.65*maintenance*MAINT)*m
        assert np.isfinite(m).all() and m.min()>=-1e-6 and m.max()<=1.00001
        mobility=1/(1+5*m)
        gv=np.stack([g+diffuse(g,.045*mobility,(4.,m))+born-(.097*v_decay_multiplier+.009*h)*g for g,born in zip(gv,bv)])
        gw=np.stack([g+diffuse(g,.0375*mobility,(4.,m))+born-(.094-.009*h)*g for g,born in zip(gw,bw)])
        u=u+diffuse(u,.085*mobility,(1.,m))-a-b+.035*(1-u)
        v,w=gv.sum(axis=0),gw.sum(axis=0)
        assert np.isfinite(gv).all() and np.isfinite(gw).all()
        assert gv.min()>=-1e-6 and gw.min()>=-1e-6

    return dict(seed=seed,n=n,steps=steps,arm=arm,hashes=hashes,observations=rows,final=dict(**measure(m),v_active=float((v>.1).mean()),w_active=float((w>.1).mean())))
def main():
    p=argparse.ArgumentParser();p.add_argument("--seed",type=int,default=42);p.add_argument("--n",type=int,default=24);p.add_argument("--steps",type=int,default=4800);p.add_argument("--arm",choices=["baseline","cost","maintenance","combined"],default="baseline");p.add_argument("--verify",action="store_true");p.add_argument("--out",type=Path,required=True);a=p.parse_args()
    ref=run(a.seed,a.n,a.steps,4,a.arm,False)
    if a.verify:
        for stride in (4,6):
            candidate=run(a.seed,a.n,a.steps,stride,a.arm,True)
            assert candidate["hashes"]==ref["hashes"],f"Observer divergence stride {stride}"
        ref["observer_verification"]="passed at recorded checkpoints (strides 4 and 6)"
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(ref,indent=2))
if __name__=="__main__":main()
