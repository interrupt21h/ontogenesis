"""G0027: threshold-independent measurements using the G0026 integrator."""
import argparse,json
from pathlib import Path
import numpy as np
import consolidation

def structural(m):
    result=original(m)
    x=m.astype(np.float64); x-=x.mean()
    p=np.abs(np.fft.rfftn(x))**2
    weights=np.full(p.shape[-1],2.);weights[0]=1
    if x.shape[-1]%2==0: weights[-1]=1
    p*=weights
    p.flat[0]=0
    axes=[np.fft.fftfreq(n) for n in x.shape[:-1]]+[np.fft.rfftfreq(x.shape[-1])]
    radius=np.sqrt(sum(a*a for a in np.ix_(*axes)))
    edges=np.linspace(0,1,33)
    shell,_=np.histogram(radius,bins=edges,weights=p)
    total=float(p.sum())
    assert np.isclose(total/x.size**2,x.var(),rtol=1e-8,atol=1e-14)
    hist=np.array(result["histogram"],dtype=float)
    centers=(np.array(result["histogram_edges"])[1:]+np.array(result["histogram_edges"])[:-1])/2
    prob=hist/max(hist.sum(),1)
    mass=np.cumsum(prob); moment=np.cumsum(prob*centers)
    score=np.divide((moment[-1]*mass-moment)**2,mass*(1-mass),out=np.zeros_like(mass),where=(mass>0)&(mass<1))
    threshold=float(result["histogram_edges"][int(score.argmax())+1]) if score.max()>0 else None
    result.update(spectral_edges=edges.tolist(),spectral_fraction=(shell/total if total else shell).tolist(),otsu_threshold=threshold,otsu_coverage=float((m>threshold).mean()) if threshold is not None else None,otsu_separability=float(score.max()/np.sum(prob*(centers-moment[-1])**2)) if score.max()>0 else None)
    return result

original=consolidation.measure

def main():
    p=argparse.ArgumentParser();p.add_argument("--n",type=int,default=24);p.add_argument("--steps",type=int,default=4800);p.add_argument("--seed",type=int,default=42);p.add_argument("--verify",action="store_true");p.add_argument("--out",type=Path,required=True);a=p.parse_args()
    consolidation.measure=structural
    result=consolidation.run(a.seed,a.n,a.steps,120,"baseline",True)
    if a.verify:
        consolidation.measure=original
        reference=consolidation.run(a.seed,a.n,a.steps,120,"baseline",False)
        result["observer_verification"]={"same_process":True,"matching_checkpoints":sum(reference["hashes"].get(k)==v for k,v in result["hashes"].items()),"total":len(result["hashes"])}
        assert reference["hashes"]==result["hashes"],"Structural observer changed state"
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2,allow_nan=False))
if __name__=="__main__":main()
