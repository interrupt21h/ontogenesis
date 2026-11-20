"""Scientific plates from actual numerical states, never from video pixels."""
import argparse
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from field_archive import load_snapshot

plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"text.color":"#19334a","axes.labelcolor":"#19334a","axes.spines.top":False,"axes.spines.right":False,"pdf.fonttype":42})
def render(folder,out):
    paths=sorted(Path(folder).glob("state-*.npz"))
    if not paths: raise ValueError("No numerical snapshots")
    states=[load_snapshot(p) for p in paths]
    meta=states[-1][0]
    assert states[0][0]["step"]==0 and meta["step"]==meta["total_steps"]
    assert all(a[0]["step"]<b[0]["step"] for a,b in zip(states,states[1:]))
    assert all(m["generation"]==meta["generation"] and m["revision"]==meta["revision"] and m["shape"]==meta["shape"] for m,f in states)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    gen=meta["generation"]
    def save(fig,name):
        for ext in ("pdf","png"):
            fig.savefig(out/f"{gen}-{name}.{ext}",dpi=220,bbox_inches="tight",pad_inches=.15)
        plt.close(fig)
    fields=[("v","Species V","magma"),("w","Species W","viridis"),("m","Matrix","cividis"),("e","Energy","viridis"),("pulse","Signal","plasma")]
    # Fixed native lattice section across time: no moving camera or changing cut.
    omega,z,y,x=[n//2 for n in meta["shape"]]
    fig,axs=plt.subplots(len(fields),len(states),figsize=(max(10,1.7*len(states)),10),layout="constrained")
    for i,(key,title,cmap) in enumerate(fields):
        maximum=1 if key in ("e","pulse","m") else max(float(f[key].max()) for _,f in states)
        for j,(m,f) in enumerate(states):
            ax=axs[i,j]; im=ax.imshow(f[key][omega,z],origin="lower",interpolation="nearest",cmap=cmap,norm=Normalize(0,max(maximum,1e-12)))
            ax.set_xticks([]);ax.set_yticks([])
            if i==0:ax.set_title(f'Step {m["step"]}')
            if j==0:ax.set_ylabel(title)
        fig.colorbar(im,ax=axs[i,:],shrink=.72,label="Concentration")
    fig.suptitle(f"Fixed spatial section | omega={omega}, z={z} | horizontal x, vertical y",fontsize=14)
    save(fig,"field-evolution")
    m,f=states[-1]
    fig,axs=plt.subplots(2,3,figsize=(9,6),layout="constrained")
    for ax,key,cmap in zip(axs.flat,["u","xv","xw","m","pulse","e"],["viridis","magma","magma","cividis","plasma","viridis"]):
        # Average over fourth axis then z: explicitly a projection, not a slice.
        im=ax.imshow(f[key].mean(axis=(0,1),dtype=np.float64),origin="lower",interpolation="nearest",cmap=cmap)
        ax.set(title=key,xlabel="x",ylabel="y")
        fig.colorbar(im,ax=ax,shrink=.75)
    fig.suptitle("Final state | mean projection over omega and z",fontsize=14)
    save(fig,"field-projections")
    pooled=f["gv"]+f["gw"]; total=pooled.sum(axis=0,dtype=np.float64)
    bits=np.array([[(g>>i)&1 for i in range(4)] for g in range(16)])
    fig,axs=plt.subplots(2,2,figsize=(8,7),layout="constrained")
    for i,(ax,title) in enumerate(zip(axs.flat,["Catalysis C","Energy economy K","Signal response S","Construction B"])):
        numerator=pooled[bits[:,i]==1].sum(axis=0,dtype=np.float64)
        frequency=np.divide(numerator,total,out=np.full_like(total,np.nan),where=total>1e-12)
        im=ax.imshow(frequency[omega,z],vmin=0,vmax=1,cmap="viridis",origin="lower",interpolation="nearest")
        ax.set(title=title,xlabel="x",ylabel="y")
    fig.colorbar(im,ax=axs.ravel(),label="Population-weighted local allele fraction",shrink=.8)
    fig.suptitle(f"Final hereditary landscape | omega={omega}, z={z}",fontsize=14)
    save(fig,"trait-landscape")
    # Show absolute concentration, relative spatial contrast, and occupancy together.
    matrix=f["m"]; counts=(matrix>.2).sum(axis=(1,2,3))
    peak_counts=np.argmax(counts) if counts.max()>0 else np.argmax(matrix.max(axis=(1,2,3)))
    idx=int(peak_counts); n=matrix.shape[1]
    section=matrix[idx]; zidx=int(np.argmax(section.max(axis=(1,2))))
    mean=float(matrix.mean(dtype=np.float64)); std=float(matrix.std(dtype=np.float64))
    lo=float(matrix.min()); hi=float(matrix.max())
    fig=plt.figure(figsize=(10,8),layout="constrained")
    ax=fig.add_subplot(2,2,1)
    im=ax.imshow(section[zidx],origin="lower",cmap="cividis",vmin=0,vmax=max(.25,hi),interpolation="nearest")
    ax.set(title=f"Absolute concentration | omega={idx}, z={zidx}",xlabel="x",ylabel="y")
    fig.colorbar(im,ax=ax,shrink=.8,label="M")
    ax=fig.add_subplot(2,2,2)
    span=max(abs(lo-mean),abs(hi-mean),1e-12)
    im=ax.imshow(section[zidx]-mean,origin="lower",cmap="RdBu_r",vmin=-span,vmax=span,interpolation="nearest")
    ax.set(title="Deviation from global mean | same section",xlabel="x",ylabel="y")
    fig.colorbar(im,ax=ax,shrink=.8,label="M minus global mean")
    ax=fig.add_subplot(2,2,3)
    ax.hist(matrix.ravel(),bins=np.linspace(min(0.,lo),max(.25,hi)+1e-9,101),weights=np.full(matrix.size,100/matrix.size),color="#397f91")
    ax.axvline(.2,color="#a64d36",linestyle="--",label="M = 0.20")
    ax.axvline(mean,color="#19334a",label="Global mean")
    ax.set(title=f"Global distribution | mean={mean:.4f}, SD={std:.4f}",xlabel="Matrix concentration",ylabel="Cells per bin (%)")
    ax.legend(frameon=False,fontsize=8)
    ax=fig.add_subplot(2,2,4)
    if counts.sum():
        ax.bar(np.arange(len(counts)),counts,color="#397f91")
        ax.set(title=f"Global occupancy: {int(counts.sum()):,} cells above 0.20",xlabel="Fourth coordinate (omega)",ylabel="Occupied cells in section")
        ax.set_ylim(bottom=0)
    else:
        levels=np.linspace(0,max(.25,hi),101)
        ordered=np.sort(matrix.ravel())
        coverage=100*(matrix.size-np.searchsorted(ordered,levels,side="right"))/matrix.size
        ax.plot(levels,coverage,color="#397f91")
        ax.axvline(.2,color="#a64d36",linestyle="--")
        ax.set(title="No cells above 0.20 | threshold sensitivity",xlabel="Threshold",ylabel="Global coverage (%)",ylim=(-2,102))
    fig.suptitle(f"G{gen} | step {meta['step']} | matrix range {lo:.4f}–{hi:.4f}",fontsize=14)
    save(fig,"structural-volume")
    # Same global diagnostics computed independently from archived arrays.
    fig,axs=plt.subplots(2,1,figsize=(8,6),layout="constrained")
    steps=[m["step"] for m,f in states]
    for key,cut,title in [("v",.1,"V"),("w",.1,"W"),("m",.2,"Matrix")]:
        axs[0].plot(steps,[100*np.mean(f[key]>cut) for _,f in states],"o-",label=title)
    axs[0].set(ylabel="Active coverage (%)",ylim=(0,100));axs[0].legend(frameon=False)
    for i,name in enumerate("CKSB"):
        values=[]
        for _,f in states:
            masses=(f["gv"]+f["gw"]).sum(axis=(1,2,3,4),dtype=np.float64)
            values.append(float(masses@bits[:,i]/masses.sum()) if masses.sum()>0 else np.nan)
        axs[1].plot(steps,values,"o-",label=name)
    axs[1].set(xlabel="Integration step",ylabel="Global allele fraction",ylim=(0,1));axs[1].legend(frameon=False,ncol=4)
    fig.suptitle("Independent measurements from archived numerical states",fontsize=14)
    save(fig,"field-metrics")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("folder");p.add_argument("out")
    a=p.parse_args();render(a.folder,a.out)
