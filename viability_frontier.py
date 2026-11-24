"""G0031: controlled V mortality-rate frontier for a viable two-population baseline.

The source numerical model is G0026, with only one explicit experimental
parameter: a multiplier on the existing V loss-rate constant (0.097).
The unmodified model is retained as the 1.0 baseline. This external rate
change is *not* evolution, a new genotype or an organism selecting survival.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import numpy as np

import consolidation
from ecological_succession import snapshot
from scripts.analyze_g0030 import loss_window, time_average

ARMS = {
    "historical": 1.0,
    "v_loss_095": 0.95,
    "v_loss_090": 0.90,
    "v_loss_085": 0.85,
    "v_loss_080": 0.80,
}
FIELDS=("v_active","w_active","coexistence","v_mean","w_mean",
        "matrix_mean","matrix_coverage","energy_mean","genotype_entropy_bits")


def graph(info,out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(14,8.5),constrained_layout=True)
    colors=("#B8CBDF","#51D2C4","#F5A874","#D48BDD","#67A9FC")
    fig.patch.set_facecolor("#101D2C")
    plots=(("v_active","V active coverage > 0.1 (%)",100),
           ("w_active","W active coverage > 0.1 (%)",100),
           ("coexistence","Co-occupied cells (%)",100),
           ("v_mean","Mean V concentration (log10)",None))
    for ax,(key,title,mult) in zip(axes.flat,plots):
        ax.set_facecolor("#192D40")
        for i,(label,loss_scale) in enumerate(ARMS.items()):
            for j,seed in enumerate(info["seeds"]):
                rows=info["observations"][str(seed)][label]
                yy=[float(np.log10(max(0.,r[key])+1e-14)) if mult is None
                    else r[key]*mult for r in rows]
                ax.plot([r["step"] for r in rows],yy,linewidth=1.9,
                        linestyle="-" if j==0 else "--",color=colors[i],
                        label=f"{label} / seed {seed}")
        ax.set_title(title,color="#E6F1F8",fontsize=12)
        ax.tick_params(colors="#C6D6E2")
        ax.set_xlabel("Numerical steps",color="#B3C6D3")
        for sp in ax.spines.values():sp.set_color("#4A6379")
        ax.grid(alpha=.15)
    axes[0,0].legend(fontsize=7,facecolor="#223A50",
                     labelcolor="#E6F1F8",ncol=2)
    fig.suptitle("ONTOGENESIS G0031 / POPULATION VIABILITY FRONTIER\n"
                 f"Externally specified V loss-rate multipliers / "
                 f"{info['n']}⁴ / {info['steps']} steps / both seeds",
                 color="#ECF4FB",fontsize=16)
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(out,facecolor=fig.get_facecolor(),dpi=112)
    plt.close(fig)


def run_screen(out,plate,*,n=16,steps=240,stride=6,seeds=(42,73)):
    if not 8<=n<=20 or not 60<=steps<=480 or not 1<=stride<=12:
        raise ValueError("Outside controlled G0031 numerical budget")
    if not seeds or len(set(seeds))!=len(seeds) or any(s<0 for s in seeds):
        raise ValueError("Need distinct nonnegative seeds")
    times=sorted(set(range(0,steps+1,stride))|{t for t in
                 (0,30,36,54,60,90,120,180,240,steps) if t<=steps})
    selected=set(times)
    info={
        "generation":"0031","edition":"controlled-v-viability-frontier-v1",
        "source_sha":os.environ.get("GITHUB_SHA","unversioned"),
        "n":n,"steps":steps,"stride":stride,"seeds":list(seeds),
        "arms":ARMS,
        "physical_ancestry":"G0026 base dynamics with only the explicitly varied V mortality rate",
        "controlled_change":"Existing V decay constant 0.097 is multiplied by each arm's scale. Spatial modifier 0.009*h, all W losses, all reproduction and transport unchanged.",
        "active_definition":"fraction of cells where species concentration > 0.1",
        "times":times,"observations":{},"diagnostics":{},"hashes":{},
        "limitations":[
            "The changed death rate is externally set, not evolved by simulated genotypes.",
            "Two seeds and finite duration are not evidence of durable life-like survival.",
            "Thresholded coverage is not direct proof of biological individuals.",
            "Co-occupancy does not establish mutualism, spatial enclosure or reproduction.",
            "Rates and thresholds are specific to this model; 24^4 validation is gated.",
            "The initial 0.25 V-loss-multiplier screen triggered a nonnegative-state assertion; the finer 0.80-1.0 study intentionally avoids that unstable perturbation and does not suppress assertions.",
        ],
    }
    for seed in seeds:
        index=str(seed)
        info["observations"][index]={}
        info["diagnostics"][index]={}
        info["hashes"][index]={}
        for label,scale in ARMS.items():
            rows=[]
            def record(step,fields):
                rows.append(snapshot(step,fields))
            result=consolidation.run(
                seed=seed,n=n,steps=steps,observe=False,crossfeed=(True,True),
                v_decay_multiplier=scale,
                ecology_observer=record,ecology_steps=selected)
            if [r["step"] for r in rows]!=times:
                raise AssertionError(f"G0031 samples diverged: seed={seed} arm={label}")
            info["observations"][index][label]=rows
            info["hashes"][index][label]=result["hashes"]
            final=rows[-1]
            info["diagnostics"][index][label]={
                "endpoint":{key:final[key] for key in FIELDS},
                "v_activity_window":loss_window(rows,"v_active"),
                "w_activity_window":loss_window(rows,"w_active"),
                "time_mean_v_active":time_average(rows,"v_active"),
                "time_mean_w_active":time_average(rows,"w_active"),
                "time_mean_cooccupancy":time_average(rows,"coexistence"),
                "endpoints_both_active":bool(final["v_active"]>0 and final["w_active"]>0),
                "peak_v_activity":max(r["v_active"] for r in rows),
            }
            print(f"seed {seed} {label} ({scale:.2f}): V={final['v_active']:.7f}, "
                  f"W={final['w_active']:.7f}, coexist={final['coexistence']:.7f}",
                  flush=True)
        if len({x["0"] for x in info["hashes"][index].values()})!=1:
            raise AssertionError("Arms do not share the same state at t=0")
    info["any_endpoint_both_active"]=any(
        v["endpoints_both_active"]
        for seed in info["diagnostics"].values() for v in seed.values())
    out=Path(out);plate=Path(plate)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(info,indent=2,allow_nan=False)+"\n")
    graph(info,plate)
    if plate.stat().st_size<4096:
        raise RuntimeError("Missing measured G0031 plot")
    return info


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n",type=int,default=16)
    p.add_argument("--steps",type=int,default=240)
    p.add_argument("--stride",type=int,default=6)
    p.add_argument("--seeds",default="42,73")
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--plate",type=Path,required=True)
    a=p.parse_args()
    result=run_screen(a.out,a.plate,n=a.n,steps=a.steps,stride=a.stride,
                      seeds=tuple(int(x) for x in a.seeds.split(",")))
    print("Any matched-seed arms preserve endpoint V+W activity:",
          result["any_endpoint_both_active"],flush=True)


if __name__=="__main__":
    main()
