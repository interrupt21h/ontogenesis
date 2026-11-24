"""G0032: test complementary *static* spatial growth niches in the G0026 ecology.

This experiment is an externally imposed counterfactual, NOT new evolution.
Each seed runs an unchanged G0026 reference, near-transition mortality without
spatial niches, and two mirrored habitat-affinity strengths. Native 4D state
snapshots are not saved, so results are plotted as measured time series only.
"""
from __future__ import annotations
import argparse
import json
import math
import os
from pathlib import Path

import numpy as np

import consolidation
from ecological_succession import snapshot

ARMS={
    "historical": {"v_decay_multiplier":1.0,"niche_strength":0.0},
    "near_transition": {"v_decay_multiplier":0.97,"niche_strength":0.0},
    "separated_035": {"v_decay_multiplier":0.97,"niche_strength":0.35},
    "separated_070": {"v_decay_multiplier":0.97,"niche_strength":0.70},
}
FIELDS=("v_active","w_active","coexistence","v_mean","w_mean",
        "matrix_mean","energy_mean","genotype_entropy_bits",
        "habitat_v_mean","habitat_w_mean","habitat_separation")

def measure(step,fields):
    result=snapshot(step,fields)
    habitat=fields["habitat_bias"]
    v=fields["species_v"]
    w=fields["species_w"]
    total_v=float(np.sum(v,dtype=np.float64))
    total_w=float(np.sum(w,dtype=np.float64))
    # A weighted centroid measures spatial preference of *concentration*;
    # it can be influenced by tiny residual populations. Interpret alongside
    # the thresholded coverage and explicit active-mask habitat centroids.
    hv=float(np.sum(habitat*v,dtype=np.float64)/max(total_v,1e-30))
    hw=float(np.sum(habitat*w,dtype=np.float64)/max(total_w,1e-30))
    result.update(habitat_v_mean=hv,habitat_w_mean=hw,
                  habitat_separation=hv-hw)
    for species,array in (("v",v),("w",w)):
        mask=array>.1
        result[f"active_{species}_habitat_mean"]=(float(np.mean(habitat[mask]))
                                                  if np.any(mask) else None)
    if not all(math.isfinite(result[key]) for key in FIELDS):
        raise ValueError("Nonfinite habitat measurement")
    return result

def plot(info,out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,3,figsize=(16,9),constrained_layout=True)
    colors=("#B8CBDF","#52D5C1","#F3AC73","#DA8DDF")
    titles=(("v_active","V thresholded activity (%)",100),
            ("w_active","W thresholded activity (%)",100),
            ("coexistence","Active co-occupied cells (%)",100))
    fig.patch.set_facecolor("#101D2C")
    for row,seed in enumerate(info["seeds"]):
        for col,(key,title,scale) in enumerate(titles):
            ax=axes[row,col]
            ax.set_facecolor("#1A2D41")
            for i,arm in enumerate(ARMS):
                records=info["observations"][str(seed)][arm]
                ax.plot([r["step"] for r in records],
                        [r[key]*scale for r in records],color=colors[i],
                        lw=1.8,label=arm.replace("_"," "))
            ax.set_title(f"Seed {seed} — {title}",color="#EDF5F8")
            ax.tick_params(colors="#C1D4DF")
            ax.set_xlabel("Simulated step",color="#AEC5D2")
            ax.grid(alpha=.14)
            for spine in ax.spines.values():spine.set_color("#486B83")
    axes[0,0].legend(fontsize=8,facecolor="#233A50",labelcolor="#F0F6F9")
    fig.suptitle("ONTOGENESIS / G0032 — COMPLEMENTARY HABITAT SCREEN\n"
                 "Direct numerical observations; no simulated organisms or footage",
                 fontsize=16,color="#F1F7FA")
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(out,dpi=105,facecolor=fig.get_facecolor())
    plt.close(fig)

def run_screen(out,figure,*,n=16,steps=240,stride=6,seeds=(42,73)):
    if not 8<=n<=20 or not 90<=steps<=600 or not 1<=stride<=12:
        raise ValueError("Outside bounded G0032 numerical budget")
    if not seeds or len(seeds)!=len(set(seeds)) or any(s<0 for s in seeds):
        raise ValueError("Need distinct nonnegative seeds")
    times=sorted(set(range(0,steps+1,stride))|{t for t in
                 (0,30,36,54,60,90,120,180,240,steps) if t<=steps})
    info={
        "generation":"0032","edition":"complementary-habitat-screen-v1",
        "source_sha":os.environ.get("GITHUB_SHA","unversioned"),
        "n":n,"steps":steps,"seeds":list(seeds),"times":times,
        "arms":ARMS,
        "model_description":(
          "At niche_strength>0, V birth flux is multiplied by (1+s*h) "
          "and W birth flux by (1-s*h) using the preexisting static "
          "four-dimensional habitat field h; the numerical default at s=0 "
          "is untouched. Only near-transition arms change V loss to 0.97."
        ),
        "observations":{},"hashes":{},"endpoints":{},"contrasts":{},
        "limitations":[
           "Niche bias is imposed externally and static, not genotype-controlled adaptation.",
           "Weighted habitat centroids are not segmentation or proof of separate organisms.",
           "A zero thresholded activity fraction can coexist with nonzero residual concentration.",
           "Two seeds and 240 steps are not enough to establish stability or ecological speciation.",
           "No native 4D field snapshots were archived or fabricated.",
        ],
    }
    for seed in seeds:
        cohort=str(seed)
        info["observations"][cohort]={}
        info["hashes"][cohort]={}
        info["endpoints"][cohort]={}
        for name,args in ARMS.items():
            rows=[]
            def observe(t,fields):
                rows.append(measure(t,fields))
            result=consolidation.run(
                seed=seed,n=n,steps=steps,observe=False,
                crossfeed=(True,True),season_switch=None,
                ecology_observer=observe,ecology_steps=set(times),**args
            )
            if [r["step"] for r in rows]!=times:
                raise AssertionError("Mismatched G0032 sample times")
            info["observations"][cohort][name]=rows
            info["hashes"][cohort][name]=result["hashes"]
            info["endpoints"][cohort][name]={f:rows[-1][f] for f in FIELDS}
            print(f"seed {seed} {name}: V={rows[-1]['v_active']:.6f}, "
                  f"W={rows[-1]['w_active']:.6f}, "
                  f"cooccupancy={rows[-1]['coexistence']:.6f}, "
                  f"habitat-separation={rows[-1]['habitat_separation']:.6f}",
                  flush=True)
        if len({record["0"] for record in info["hashes"][cohort].values()})!=1:
            raise AssertionError("Same-seed arms had different starting states")
        original=info["endpoints"][cohort]["near_transition"]
        info["contrasts"][cohort]={
            name:{
                key:float(values[key]-original[key])
                for key in ("v_active","w_active","coexistence","habitat_separation")
            }
            for name,values in info["endpoints"][cohort].items()
            if name.startswith("separated_")
        }
    info["any_endpoint_cooccupancy"]=any(
        row["coexistence"]>0 for seed in info["endpoints"].values()
        for row in seed.values()
    )
    out=Path(out);figure=Path(figure)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(info,indent=2,allow_nan=False)+"\n")
    plot(info,figure)
    if figure.stat().st_size<4096:
        raise AssertionError("G0032 measured plot missing")
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
    print("Any measured endpoint has active co-occupied cells:",
          result["any_endpoint_cooccupancy"],flush=True)

if __name__=="__main__":
    main()
