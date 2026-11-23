"""G0030: matched directional cross-feeding ecology screen.

A 2x2 factorial ablation measures which secreted-metabolite direction matters.
Both seeds receive the same externally imposed spatial supply inversion.
This is a screen for succession-like dynamics, not proof of mutualism or life.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import numpy as np
import consolidation

ARMS = {"neither": (False,False), "w_to_v_only": (True,False),
        "v_to_w_only": (False,True), "both": (True,True)}
METRICS = ("v_active","w_active","coexistence","v_mean","w_mean",
           "metabolite_v_mean","metabolite_w_mean","metabolite_overlap",
           "energy_mean","matrix_mean","matrix_coverage","genotype_entropy_bits")


def snapshot(step, f):
    v,w,xv,xw=f["species_v"],f["species_w"],f["metabolite_v"],f["metabolite_w"]
    genotype=np.concatenate((
        f["genotypes_v"].sum(axis=(1,2,3,4),dtype=np.float64),
        f["genotypes_w"].sum(axis=(1,2,3,4),dtype=np.float64)))
    prob=genotype/max(float(genotype.sum()),1e-20)
    prob=prob[prob>0]
    d={"step":int(step),
       "v_active":float(np.mean(v>.1)),
       "w_active":float(np.mean(w>.1)),
       "coexistence":float(np.mean((v>.1)&(w>.1))),
       "v_mean":float(v.mean()),"w_mean":float(w.mean()),
       "metabolite_v_mean":float(xv.mean()),
       "metabolite_w_mean":float(xw.mean()),
       "metabolite_overlap":float(np.minimum(xv,xw).mean()),
       "energy_mean":float(f["energy"].mean()),
       "matrix_mean":float(f["matrix"].mean()),
       "matrix_coverage":float(np.mean(f["matrix"]>.2)),
       "genotype_entropy_bits":float(-(prob*np.log2(prob)).sum())}
    if not all(np.isfinite(value) for value in d.values()):
        raise ValueError("Nonfinite ecological measurement")
    return d


def window_summary(rows,event,steps):
    span=max(1,steps//10)
    before=[r for r in rows if event-span<=r["step"]<event]
    after=[r for r in rows if r["step"]>=steps-span]
    if not before or not after:
        raise AssertionError("Insufficient observations around seasonal change")
    return {name:{key:float(np.mean([r[key] for r in subset])) for key in METRICS}
            for name,subset in (("before",before),("late",after))}


def plot_plate(info,path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    seed=str(info["seeds"][0])
    histories=info["observations"][seed]
    plots=(("v_active","Species V coverage (%)",100),
           ("w_active","Species W coverage (%)",100),
           ("coexistence","Co-occupied cells (%)",100),
           ("matrix_coverage","Matrix coverage (%)",100),
           ("metabolite_overlap","Metabolite overlap (mean minimum)",1),
           ("genotype_entropy_bits","Genotype entropy (bits)",1))
    fig,axes=plt.subplots(2,3,figsize=(16,9),constrained_layout=True)
    fig.patch.set_facecolor("#101e2d")
    colors=("#b5c2d1","#39c9be","#eeae67","#d18ae3")
    for ax,(key,title,scale) in zip(axes.flat,plots):
        ax.set_facecolor("#17283a")
        for (arm,series),color in zip(histories.items(),colors):
            ax.plot([r["step"] for r in series],[r[key]*scale for r in series],
                    lw=1.8,color=color,label=arm.replace("_"," "))
        ax.axvline(info["season_switch"],color="#dae4ea",ls="--",alpha=.65)
        ax.set_title(title,color="#eaf1fa")
        ax.tick_params(colors="#c6d7e4")
        for spine in ax.spines.values():
            spine.set_color("#42647a")
        ax.grid(alpha=.13)
    axes[0,0].legend(fontsize=8,facecolor="#24394b",labelcolor="#eaf1fa")
    fig.suptitle("ONTOGENESIS / G0030 — ECOLOGICAL FACTORIAL SCREEN\n"
                 f"Actual observations, seed {seed}, {info['n']}^4 cells; "
                 f"supply reverses at step {info['season_switch']}",
                 color="#eaf1fa",fontsize=17)
    path.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(path,dpi=110,facecolor=fig.get_facecolor())
    plt.close(fig)


def run_screen(out,plate,*,seeds=(42,73),n=16,steps=1200,stride=30):
    if not seeds or len(set(seeds))!=len(seeds) or any(s<0 for s in seeds):
        raise ValueError("Seeds must be unique nonnegative integers")
    if not 8<=n<=24 or not 60<=steps<=6000 or not 1<=stride<=steps//10:
        raise ValueError("Outside permitted numerical budget or cadence")
    switch=steps//2
    times=sorted(set(range(0,steps+1,stride))|{0,switch-1,switch,switch+1,steps})
    selected=set(times)
    info={"generation":"0030","edition":"ecology-factorial-season-1",
          "verification":"generated; CI verification pending",
          "source_sha":os.environ.get("GITHUB_SHA","unversioned"),
          "n":n,"steps":steps,"stride":stride,"seeds":list(seeds),
          "season_switch":switch,
          "season_definition":"At step T/2 invert spatial supply about its mean; same forcing in every arm.",
          "arm_semantics":{"neither":"Neither species receives a metabolite reproductive bonus",
                           "w_to_v_only":"W-secreted Xw can benefit V; reverse disabled",
                           "v_to_w_only":"V-secreted Xv can benefit W; reverse disabled",
                           "both":"Original two-way benefit"},
          "times":times,"metrics":list(METRICS),
          "observations":{},"endpoints":{},"window_means":{},
          "within_seed_differences_vs_neither":{},"state_hashes":{}}
    for seed in seeds:
        s=str(seed)
        info["observations"][s]={}
        info["endpoints"][s]={}
        info["window_means"][s]={}
        info["state_hashes"][s]={}
        print(f"Seed {seed}: four factorial controls",flush=True)
        for label,flags in ARMS.items():
            rows=[]
            def capture(t,fields):
                rows.append(snapshot(t,fields))
            result=consolidation.run(
                seed=seed,n=n,steps=steps,observe=False,crossfeed=flags,
                season_switch=switch,ecology_observer=capture,
                ecology_steps=selected)
            if [r["step"] for r in rows]!=times:
                raise AssertionError("Unmatched sample timestamps")
            info["observations"][s][label]=rows
            info["endpoints"][s][label]=rows[-1]
            info["window_means"][s][label]=window_summary(rows,switch,steps)
            info["state_hashes"][s][label]=result["hashes"]
            print(label,": ",{k:rows[-1][k] for k in ("v_active","w_active","coexistence")},flush=True)
        if len({v["0"] for v in info["state_hashes"][s].values()})!=1:
            raise AssertionError("Different initial conditions within seed")
        baseline=info["endpoints"][s]["neither"]
        info["within_seed_differences_vs_neither"][s]={
            arm:{key:float(row[key]-baseline[key]) for key in METRICS}
            for arm,row in info["endpoints"][s].items() if arm!="neither"}
    info["limitations"]=[
        "Two seeds are a sensitivity check, not statistical significance.",
        "Temporal response to imposed season does not prove ecological succession.",
        "Cross-feeding ablation suppresses recipient benefit and uptake; secretion remains.",
        "Co-occupancy and overlap do not establish individual or ecological mutualism.",
        "Fixed 16-category genotype representation cannot invent new loci.",
        "Full 24^4 simulation is not part of the automatic pilot."]
    out=Path(out);plate=Path(plate)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(info,indent=2,allow_nan=False)+"\n")
    plot_plate(info,plate)
    if plate.stat().st_size<4096:
        raise AssertionError("Measured ecological plate missing")
    return info


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n",type=int,default=16)
    p.add_argument("--steps",type=int,default=1200)
    p.add_argument("--stride",type=int,default=30)
    p.add_argument("--seeds",default="42,73")
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--plate",type=Path,required=True)
    args=p.parse_args()
    run_screen(args.out,args.plate,n=args.n,steps=args.steps,stride=args.stride,
               seeds=tuple(int(x) for x in args.seeds.split(",")))


if __name__=="__main__":
    main()
