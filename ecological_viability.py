"""G0030 early-viability screen: controls before the V-activity collapse.

No new artificial-life mechanism is introduced. Four independently initialized
trajectories per seed compare *no forced supply change* against early inversions
of the existing supply gradient. Reuse G0026's dynamics, both metabolite
benefits enabled, with matching seeds and observation times. This does NOT
establish stable coexistence or evolutionary rescue.
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

CASES={"unchanged":None,"invert_12":12,"invert_24":24,"invert_48":48}
METRICS=("v_active","w_active","coexistence","v_mean","w_mean",
         "energy_mean","matrix_mean","matrix_coverage")

def run_screen(out,plate,*,n=16,steps=180,stride=6,seeds=(42,73)):
    if not 8<=n<=20 or not 60<=steps<=600 or not 1<=stride<=10:
        raise ValueError("Outside bounded early-viability experiment")
    if not seeds or len(set(seeds))!=len(seeds) or any(s<0 for s in seeds):
        raise ValueError("Unique nonnegative seeds required")
    if any(event is not None and not 0<event<steps for event in CASES.values()):
        raise ValueError("Event steps must occur within the integration window")
    times=sorted(set(range(0,steps+1,stride))|{0,steps,30,60,90}|
                 {x+o for x in CASES.values() if x is not None
                  for o in (-1,0,1) if 0<=x+o<=steps})
    selected=set(times)
    info={"generation":"0030","edition":"preseason-viability-screen-v1",
          "source_sha":os.getenv("GITHUB_SHA","unversioned"),
          "n":n,"steps":steps,"seeds":list(seeds),"times":times,
          "controlled_intervention":"Spatial energy-supply inversion with unchanged domain mean",
          "crossfeed":"Both directions enabled, same as G0026 default",
          "cases":CASES,"observations":{},"state_hashes":{},
          "diagnostics":{},"comparisons_vs_unchanged":{},
          "limitations":[
              "Short-window viability screen only, not a 1200-step ecological experiment.",
              "Inversion timing is exogenous; no biological adaptation is implied.",
              "Active coverage uses concentration >0.1; loss of coverage is not mathematical extinction.",
              "Two seeds and one resolution do not establish generality.",
              "Recorded time-integrals interpolate linearly between sampled observations.",
          ]}
    for seed in seeds:
        key=str(seed)
        info["observations"][key]={}
        info["state_hashes"][key]={}
        info["diagnostics"][key]={}
        print(f"G0030 early-viability seed {seed}",flush=True)
        for name,event in CASES.items():
            rows=[]
            def record(step,fields):
                rows.append(snapshot(step,fields))
            result=consolidation.run(
                seed=seed,n=n,steps=steps,stride=steps,
                observe=False,season_switch=event,crossfeed=(True,True),
                ecology_observer=record,ecology_steps=selected)
            if [r["step"] for r in rows]!=times:
                raise AssertionError("Unmatched sample times")
            info["observations"][key][name]=rows
            info["state_hashes"][key][name]=result["hashes"]
            at60=next(r for r in rows if r["step"]==60)
            info["diagnostics"][key][name]={
                "v_loss_window":loss_window(rows,"v_active"),
                "v_active_at_30":next(r["v_active"] for r in rows if r["step"]==30),
                "v_active_at_60":at60["v_active"],
                "v_mean_at_60":at60["v_mean"],
                "w_active_at_60":at60["w_active"],
                "cooccupancy_at_60":at60["coexistence"],
                "mean_v_active_0_to_60":time_average([r for r in rows if r["step"]<=60],"v_active"),
                "endpoint":{k:rows[-1][k] for k in METRICS},
            }
            print(name,info["diagnostics"][key][name],flush=True)
        if len({v["0"] for v in info["state_hashes"][key].values()})!=1:
            raise AssertionError("Initial state not identical within seed")
        reference=info["diagnostics"][key]["unchanged"]
        info["comparisons_vs_unchanged"][key]={
            name:{
                "v_coverage_60_difference_percentage_points":100*(item["v_active_at_60"]-reference["v_active_at_60"]),
                "v_mean_60_difference":item["v_mean_at_60"]-reference["v_mean_at_60"],
                "w_coverage_60_difference_percentage_points":100*(item["w_active_at_60"]-reference["w_active_at_60"]),
            }
            for name,item in info["diagnostics"][key].items() if name!="unchanged"
        }
    out=Path(out);plate=Path(plate)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(info,indent=2,allow_nan=False)+"\n")
    plot(info,plate)
    if plate.stat().st_size<4096:
        raise AssertionError("Missing measured pre-season plot")
    return info

def plot(info,plate):
    """Time series from numerical fields, not a cinematic organism portrait."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,axs=plt.subplots(2,2,figsize=(13,8),constrained_layout=True)
    fig.patch.set_facecolor("#101e2d")
    items=(("v_active","V coverage >0.1 (%)",100),
           ("w_active","W coverage >0.1 (%)",100),
           ("v_mean","log10(mean V + 1e-12)",1),
           ("coexistence","Co-occupied volume (%)",100))
    colors=("#b6c7d5","#52c7bd","#eba768","#ca8bdc")
    for ax,(metric,title,factor) in zip(axs.flat,items):
        ax.set_facecolor("#18293c")
        for seed in info["seeds"]:
            rows=info["observations"][str(seed)]
            for (name,series),color in zip(rows.items(),colors):
                y=([np.log10(max(r[metric],0)+1e-12) for r in series]
                   if metric=="v_mean" else [r[metric]*factor for r in series])
                ax.plot([r["step"] for r in series],y,
                        label=f"{name} / seed {seed}",lw=1.7,
                        color=color,ls="-" if seed==info["seeds"][0] else "--")
        ax.set_title(title,color="#e8eff6")
        ax.set_xlabel("Simulated step",color="#bac9d6")
        ax.tick_params(colors="#bac9d6")
        ax.axvline(60,color="#e9e9f0",ls=":",alpha=.6)
        for spine in ax.spines.values():
            spine.set_color("#486479")
        ax.grid(alpha=.13)
    axs[0,0].legend(fontsize=7,facecolor="#1e3246",labelcolor="#e8eff6",ncol=2)
    fig.suptitle("ONTOGENESIS / G0030 — EARLY VIABILITY SCREEN\n"
                 "Two seeds / no inversion vs early supply inversion / measured simulation",
                 fontsize=16,color="#e8eff6")
    plate.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(plate,dpi=120,facecolor=fig.get_facecolor())
    plt.close(fig)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n",type=int,default=16)
    p.add_argument("--steps",type=int,default=180)
    p.add_argument("--stride",type=int,default=6)
    p.add_argument("--seeds",default="42,73")
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--plate",type=Path,required=True)
    a=p.parse_args()
    run_screen(a.out,a.plate,n=a.n,steps=a.steps,stride=a.stride,
               seeds=tuple(int(x) for x in a.seeds.split(",")))

if __name__=="__main__":
    main()
