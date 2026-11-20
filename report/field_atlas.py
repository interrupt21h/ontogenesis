"""Scientific plates from actual numerical states, never from video pixels."""
import argparse
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from field_archive import load_snapshot

plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"text.color":"#19334a","axes.labelcolor":"#19334a","axes.spines.top":False,"axes.spines.right":False,"pdf.fonttype":42})
def render(folder,out):
    paths=sorted(Path(folder).glob("state-*.npz"))
    if not paths: raise ValueError("No numerical snapshots")
    states=[load_snapshot(p) for p in paths]
    meta=states[-1][0]
    assert [m["step"] for m,f in states]==[0,1200,2400,3600,4800]
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
    fig,axs=plt.subplots(len(fields),len(states),figsize=(10,10),layout="constrained")
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
    for ax,(a,b,title) in zip(axs.flat,[("xv","xw","Metabolites"),("m","e","Matrix and energy"),("v","w","Species concentrations")]*2):
        pass
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
    fig,axs=plt.subplots(1,2,figsize=(9,4.5),layout="constrained")
    for ax,offset in zip(axs,[0,len(f["m"])//2]):
        idx=(omega+offset)%len(f["m"])
        coords=np.argwhere(f["m"][idx]>.2)
        ax.remove(); ax=fig.add_subplot(1,2,1 if offset==0 else 2,projection="3d")
        if len(coords):
            ax.scatter(coords[:,2],coords[:,1],coords[:,0],c=f["m"][idx][tuple(coords.T)],cmap="cividis",vmin=.2,vmax=1,s=7,alpha=.65)
        n=meta["shape"][1]
        ax.set(xlim=(0,n-1),ylim=(0,n-1),zlim=(0,n-1),xlabel="x",ylabel="y",zlabel="z",title=f"omega={idx} | {len(coords)} occupied cells")
        ax.set_box_aspect((1,1,1))
        ax.view_init(24,36)
    fig.suptitle("Final structural occupancy | M > 0.20 | native cell centers",fontsize=13)
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
