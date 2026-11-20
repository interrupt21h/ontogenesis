"""G0028: localized perturbation versus matched G0026 control."""
import argparse
import json
from pathlib import Path
import numpy as np
import consolidation

def experiment(seed=42,n=12,steps=240,stride=12,energy_fraction=.70,matrix_fraction=.80):
    if n<8 or steps<4 or stride<1: raise ValueError("Invalid size, steps or stride")
    if not (0<=energy_fraction<=1 and 0<=matrix_fraction<=1):
        raise ValueError("Shock fractions must lie in [0,1]")
    event=steps//2
    center=n//2
    axes=np.ogrid[tuple(slice(0,n) for _ in range(4))]
    radius2=sum(np.minimum(np.abs(a-center),n-np.abs(a-center))**2 for a in axes)
    sigma=n/5.5
    mask=np.exp(-radius2/(2*sigma*sigma)).astype(np.float32)
    region=mask>=np.exp(-.5)
    assert region.any()
    def observe(frames):
        def sample(step,e,m,v,w):
            if step%stride and step not in (event-1,event,event+1,steps): return
            assert not e.flags.writeable and not m.flags.writeable
            frames.append(dict(step=step,energy_mean=float(e.mean()),matrix_mean=float(m.mean()),
                               local_energy=float(e[region].mean()),local_matrix=float(m[region].mean()),
                               local_v=float(v[region].mean()),local_w=float(w[region].mean()),
                               matrix_section=np.round(m[center,center,:,:],6).tolist(),
                               energy_section=np.round(e[center,center,:,:],6).tolist()))
        return sample
    def shock(step,e,m):
        if step==event:
            e *= 1-energy_fraction*mask
            m *= 1-matrix_fraction*mask
    arms={}
    for arm in ("control","shock"):
        frames=[]
        result=consolidation.run(seed=seed,n=n,steps=steps,stride=stride,arm="baseline",
                                 observe=False,intervention=shock if arm=="shock" else None,
                                 observer=observe(frames))
        assert all(np.isfinite(r["energy_mean"]) and np.isfinite(r["matrix_mean"]) for r in frames)
        arms[arm]=dict(frames=frames,final=result["final"],hashes=result["hashes"])
    a,b=arms["control"],arms["shock"]
    times=[r["step"] for r in a["frames"]]
    assert times==[r["step"] for r in b["frames"]]
    assert all(a["hashes"][str(t)]==b["hashes"][str(t)] for t in range(0,event,120))
    assert a["hashes"][str(steps)]!=b["hashes"][str(steps)]
    if event%120==0:
        assert a["hashes"][str(event)]!=b["hashes"][str(event)]
    index=times.index(event)
    def compare(field):
        initial=b["frames"][index][field]-a["frames"][index][field]
        end=b["frames"][-1][field]-a["frames"][-1][field]
        return dict(event_difference=initial,end_difference=end,
                    deviation_attenuation=1-abs(end)/abs(initial) if abs(initial)>1e-12 else None)
    return dict(generation="0028",verification="pending CI",seed=seed,n=n,steps=steps,stride=stride,
                event_step=event,axis_order=["omega","z","y","x"],
                section=dict(omega=center,z=center,varying=["y","x"]),
                shock=dict(geometry="periodic 4D Gaussian",sigma_cells=sigma,
                           core_cells=int(region.sum()),energy_fraction=energy_fraction,
                           matrix_fraction=matrix_fraction),
                comparisons=dict(local_energy=compare("local_energy"),
                                 local_matrix=compare("local_matrix")),arms=arms)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--n",type=int,default=12)
    p.add_argument("--steps",type=int,default=240)
    p.add_argument("--stride",type=int,default=12)
    p.add_argument("--energy-fraction",type=float,default=.70)
    p.add_argument("--matrix-fraction",type=float,default=.80)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=experiment(a.seed,a.n,a.steps,a.stride,a.energy_fraction,a.matrix_fraction)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps(result["comparisons"],indent=2))

if __name__=="__main__":
    main()
