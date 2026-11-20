"""Render recorded diagnostics; never synthesize missing spatial data."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

root=Path(__file__).resolve().parent/"build"
out=root/"atlas"
out.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({"font.size":11,"axes.spines.top":False,"axes.spines.right":False,"axes.titleweight":"bold","axes.labelcolor":"#19334a"})
for gen,artifact in (("0026",14651386328),("0027",14662151055)):
    data=json.loads((root/"evidence"/gen/"result.json").read_text())
    assert data["n"]==24 and data["steps"]==4800 and data["seed"]==42
    m=data["final"]
    fig,ax=plt.subplots(2,2,figsize=(10,8),layout="constrained")
    fig.suptitle(f"ONTOGENESIS / {gen}  |  Recorded numerical evidence",fontweight="bold",color="#19334a")
    edges=np.asarray(m["histogram_edges"])
    hist=np.asarray(m["histogram"])
    ax[0,0].stairs(hist/hist.sum()*100,edges,color="#245a78",fill=True,alpha=.65)
    ax[0,0].axvline(.2,color="#a46b20",linestyle="--",label="Fixed threshold")
    if gen=="0027":
        ax[0,0].axvline(m["otsu_threshold"],color="#087b65",label="Adaptive threshold")
    ax[0,0].set(xlabel="Matrix concentration",ylabel="Cells (%)",title="Endpoint distribution",xlim=(0,.35))
    ax[0,0].legend(fontsize=8)
    coverage=m.get("matrix_threshold_coverage",m.get("threshold_coverage",m.get("coverage")))
    if not isinstance(coverage,dict):
        raise ValueError(f"Missing threshold mapping; keys: {list(m)}")
    pairs=sorted((float(k),100*v) for k,v in coverage.items())
    ax[0,1].plot(*zip(*pairs),marker="o",color="#087b65")
    ax[0,1].set(xlabel="Threshold",ylabel="Coverage (%)",title="Threshold sensitivity",ylim=(0,100))
    if gen=="0026":
        assert "passed" in data["observer_verification"]
        steps=sorted(map(int,data["hashes"]))
        for y,label in enumerate(("Headless reference","Stride 4","Stride 6")):
            ax[1,0].scatter(steps,[y]*len(steps),s=9,color="#087b65")
        ax[1,0].set(yticks=range(3),yticklabels=["Headless","Stride 4","Stride 6"],xlabel="Integration step",title="Verified checkpoint agreement")
        ax[1,1].bar(["V","W"],[100*m["v_active"],100*m["w_active"]],color=["#a34d46","#245a78"])
        ax[1,1].set(ylabel="Active coverage (%)",title="Endpoint chemical activity",ylim=(0,100))
    else:
        rows=data["observations"]
        assert len(rows)==41
        ax[1,0].plot([x["step"] for x in rows],[100*x["otsu_coverage"] if x["otsu_coverage"] is not None else np.nan for x in rows],color="#087b65")
        ax[1,0].set(xlabel="Integration step",ylabel="Coverage (%)",title="Adaptive segmentation over time",ylim=(0,100))
        ax[1,1].stairs(np.array(m["spectral_fraction"])*100,m["spectral_edges"],fill=True,color="#526c91")
        ax[1,1].set(xlabel="Radial frequency (cycles/cell)",ylabel="Spectral energy (%)",title="Endpoint radial spectrum")
    fig.supxlabel(f"Source: Actions artifact {artifact} | 24^4 periodic lattice | step 4800",fontsize=9)
    fig.savefig(out/f"{gen}-evidence.pdf")
    plt.close(fig)
