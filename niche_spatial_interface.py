"""G0032: measure actual contact and overlap in archived 4D spatial fields.

Uses the *native* 16^4 numerical state, not image colors, presentation-space
projections, or the interpolation of sampled population summaries. A lattice
face between a V-only cell and W-only cell is counted once, with periodic
adjacency over all four dimensions. Contacts do not imply mutualism.
"""
from __future__ import annotations
import argparse,hashlib,json,math
from pathlib import Path
import numpy as np
from niche_spatial_archive import ARMS
from niche_spatial_render import load_fields

def metrics(v,w,m):
    av=v>.1;aw=w>.1
    v_only=av&~aw;w_only=aw&~av
    both=av&aw
    contacts=sum(int(np.count_nonzero(
        (v_only&np.roll(w_only,-1,axis=axis))|
        (w_only&np.roll(v_only,-1,axis=axis))
    )) for axis in range(4))
    n=v.size
    counts={
        "v_active_cells":int(av.sum()),"w_active_cells":int(aw.sum()),
        "v_only_cells":int(v_only.sum()),"w_only_cells":int(w_only.sum()),
        "both_active_cells":int(both.sum()),
        "neither_active_cells":int((~(av|aw)).sum()),
        "four_dimensional_face_contacts":contacts,
    }
    if counts["v_only_cells"]+counts["w_only_cells"]+counts["both_active_cells"]+counts["neither_active_cells"]!=n:
        raise AssertionError("Population masks fail to partition the 4D grid")
    denominator=float(np.maximum(v,w).sum(dtype=np.float64))
    continuous=float(np.minimum(v,w).sum(dtype=np.float64))/denominator if denominator else 0.
    counts.update(
        v_active_fraction=counts["v_active_cells"]/n,
        w_active_fraction=counts["w_active_cells"]/n,
        same_cell_fraction=counts["both_active_cells"]/n,
        contact_fraction_per_face=contacts/(4*n),
        continuous_shared_mass_ratio=continuous,
        matrix_over_02_fraction=float((m>.2).mean()),
    )
    if not all(math.isfinite(v) for v in counts.values()):
        raise AssertionError("Nonfinite spatial diagnostic")
    return counts

def chart(result,filename):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,axs=plt.subplots(2,2,figsize=(13,8.5),constrained_layout=True)
    fig.patch.set_facecolor("#101D2C")
    for ax in axs.flat:
        ax.set_facecolor("#1A3044")
        ax.tick_params(colors="#D7E4ED")
        ax.set_xlabel("Recorded numerical step",color="#BBD0DD")
        ax.grid(alpha=.16)
        for spine in ax.spines.values():spine.set_color("#4C7185")
    colors=("#53D7BD","#F4A969","#B48DE2","#86B4E9")
    times=result["times"]
    for i,(arm,rows) in enumerate(result["observations"].items()):
        axes=axs[0,0]
        axes.plot(times,[r["v_active_fraction"]*100 for r in rows],label=f"{arm} / V",lw=2,
                  color=colors[i*2])
        axes.plot(times,[r["w_active_fraction"]*100 for r in rows],label=f"{arm} / W",lw=2,
                  color=colors[i*2+1])
        axes=axs[0,1]
        axes.plot(times,[r["same_cell_fraction"]*100 for r in rows],
                  label=arm,lw=2,color=colors[i*2])
        axes=axs[1,0]
        axes.plot(times,[r["four_dimensional_face_contacts"] for r in rows],
                  label=arm,lw=2,color=colors[i*2])
        axes=axs[1,1]
        axes.plot(times,[r["continuous_shared_mass_ratio"] for r in rows],
                  label=arm,lw=2,color=colors[i*2])
    axs[0,0].set_title("Active V / W volume (%)",color="#EAF5FA")
    axs[0,1].set_title("Exact same-cell active overlap (%)",color="#EAF5FA")
    axs[1,0].set_title("Faces between exclusive V and W sites (4D)",color="#EAF5FA")
    axs[1,1].set_title("Continuous shared-mass ratio",color="#EAF5FA")
    axs[0,0].legend(facecolor="#253E52",labelcolor="#EAF5FA",fontsize=8)
    axs[0,1].legend(facecolor="#253E52",labelcolor="#EAF5FA",fontsize=8)
    fig.suptitle("ONTOGENESIS G0032 / NATIVE 4D SPATIAL CONTACTS\n"
                 "Directly measured numerical cells; not an organism interface",
                 color="#F0F7FB",fontsize=17)
    filename=Path(filename)
    filename.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(filename,dpi=110,facecolor=fig.get_facecolor())
    plt.close(fig)

def study(archive,metadata,out,figure):
    arrays,info,digest=load_fields(archive,metadata)
    result={
        "generation":"0032","edition":"native-4d-spatial-contact-analysis-v1",
        "seed":info["seed"],"source_archive_sha256":digest,
        "source_numerical_revision":info["source_sha"],
        "n":info["n"],"times":info["sample_steps"],
        "arms":ARMS,"observations":{},"endpoints":{},
        "definition":"One periodic 4D face incident to an exclusively V-active and an exclusively W-active cell, counted once.",
        "limitation":"Contact counts and continuous overlap are spatial statistics; neither establishes functional transfer, organism boundaries or ecological stability.",
    }
    for arm in ARMS:
        rows=[]
        for i,step in enumerate(info["sample_steps"]):
            row=metrics(arrays[f"{arm}_v"][i],
                        arrays[f"{arm}_w"][i],
                        arrays[f"{arm}_m"][i])
            rows.append({"step":step,**row})
        result["observations"][arm]=rows
        result["endpoints"][arm]=rows[-1]
        print(f"{arm}: final V cells={rows[-1]['v_active_cells']}, "
              f"W cells={rows[-1]['w_active_cells']}, "
              f"shared={rows[-1]['both_active_cells']}, "
              f"exclusive-contact faces={rows[-1]['four_dimensional_face_contacts']}",
              flush=True)
    out,figure=Path(out),Path(figure)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    chart(result,figure)
    if figure.stat().st_size<4096:raise RuntimeError("Missing measured spatial analysis plot")
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data",type=Path,required=True)
    p.add_argument("--metadata",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--plate",type=Path,required=True)
    a=p.parse_args()
    study(a.data,a.metadata,a.out,a.plate)
