"""G0032 extended persistence check, reusing exact G0032 state at step 240.

Run only the no-niche near-transition comparator and the stronger spatial niche.
For each seed, compare a committed numerical state hash at the original pilot
endpoint to the published archive BEFORE accepting extension measurements.
No native 4D spatial movie is inferred from scalar measurements.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path

import consolidation
from niche_screen import ARMS,measure

CASES=("near_transition","separated_070")


def verify_source(source,n,checkpoint,seeds):
    if (source.get("generation"),source.get("n"),source.get("steps"))!=("0032",n,checkpoint):
        raise ValueError("Original pilot scope does not match extension")
    if source.get("seeds")!=list(seeds):
        raise ValueError("Seed order or population does not match original pilot")
    if not set(CASES).issubset(source.get("arms",{})):
        raise ValueError("Required matched controls absent from original pilot")
    for arm in CASES:
        if source["arms"][arm]!=ARMS[arm]:
            raise ValueError(f"Arm parameters changed: {arm}")
    for seed in seeds:
        for arm in CASES:
            if str(checkpoint) not in source["hashes"][str(seed)][arm]:
                raise ValueError(f"Original source checkpoint absent: {seed} {arm}")


def measured_figure(payload,filename):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(13.5,8),constrained_layout=True)
    fig.patch.set_facecolor("#101D2C")
    colors=("#B8CBDF","#56D5C3")
    for i,seed in enumerate(payload["seeds"]):
        for j,field in enumerate(("v_active","w_active")):
            ax=axes[i,j]
            ax.set_facecolor("#172D40")
            for k,arm in enumerate(CASES):
                rows=payload["observations"][str(seed)][arm]
                ax.plot([r["step"] for r in rows],
                        [r[field]*100 for r in rows],
                        label="No niche (V decay ×0.97)" if k==0 else "Complementary niche 0.70",
                        color=colors[k],lw=2)
            ax.axvline(payload["source_checkpoint_step"],color="#E1B78D",
                       lw=1.6,linestyle="--",alpha=.8)
            ax.set_title(f"Seed {seed} — {'V' if j==0 else 'W'} active coverage (%)",
                         color="#EDF4F7")
            ax.tick_params(colors="#BACDD8")
            ax.set_xlabel("Numerical step",color="#B6CBD9")
            ax.set_ylim(-4,104)
            ax.grid(alpha=.15)
            for spine in ax.spines.values():spine.set_color("#49677E")
    axes[0,0].legend(facecolor="#24425A",labelcolor="#F4F6F8",fontsize=9)
    fig.suptitle("ONTOGENESIS G0032 / SPATIAL PARTITION PERSISTENCE\n"
                 "Original step-240 states verified against archived SHA-256",
                 color="#EEF5FA",fontsize=17)
    filename=Path(filename)
    filename.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(filename,dpi=110,facecolor=fig.get_facecolor())
    plt.close(fig)


def run_extension(original,out,plot,*,steps=480,stride=12):
    source=json.loads(Path(original).read_text())
    n=source["n"]
    checkpoint=source["steps"]
    seeds=tuple(source["seeds"])
    if not 8<=n<=20 or not checkpoint<steps<=600 or not 1<=stride<=20:
        raise ValueError("Outside bounded extension duration/domain")
    verify_source(source,n,checkpoint,seeds)
    times=sorted(set(range(0,steps+1,stride))|{0,checkpoint,steps,
                                            min(steps,checkpoint+1)})
    payload={
       "generation":"0032","edition":"longer-niche-persistence-v1",
       "source_sha":os.environ.get("GITHUB_SHA","unversioned"),
       "previous_source_sha":source.get("source_sha"),
       "source_checkpoint_step":checkpoint,
       "source_checkpoint_verified":False,
       "n":n,"steps":steps,"seeds":list(seeds),
       "cases":{arm:ARMS[arm] for arm in CASES},
       "times":times,"observations":{},"hashes":{},"endpoints":{},
       "limitations":[
          "Matched state hash at step 240 establishes numerical continuity, not biological fitness.",
          "A longer 480-step run still does not demonstrate indefinitely stable coexistence.",
          "The niche gradient is externally imposed; no genotype chooses a habitat.",
          "Same-cell co-occupation differs from globally simultaneous population activity.",
          "This edition records time series, not four-dimensional field frames.",
       ],
    }
    for seed in seeds:
        key=str(seed)
        payload["observations"][key]={}
        payload["hashes"][key]={}
        payload["endpoints"][key]={}
        for arm in CASES:
            records=[]
            def record(step,fields):
                records.append(measure(step,fields))
            new=consolidation.run(
                seed=seed,n=n,steps=steps,observe=False,
                crossfeed=(True,True),season_switch=None,
                ecology_observer=record,ecology_steps=set(times),**ARMS[arm]
            )
            old_hashes=source["hashes"][key][arm]
            for point in ("0",str(checkpoint)):
                if new["hashes"][point]!=old_hashes[point]:
                    raise AssertionError(f"Reproduction changed at step {point} in seed={seed} arm={arm}")
            if [r["step"] for r in records]!=times:
                raise AssertionError("Different observation cadence")
            payload["observations"][key][arm]=records
            payload["hashes"][key][arm]=new["hashes"]
            row=records[-1]
            payload["endpoints"][key][arm]={
                x:row[x] for x in ("v_active","w_active","coexistence",
                                  "habitat_v_mean","habitat_w_mean",
                                  "habitat_separation","v_mean","w_mean")}
            print(f"Seed {seed} / {arm}: at {steps} "
                  f"V={row['v_active']:.6f} W={row['w_active']:.6f} "
                  f"same-cell={row['coexistence']:.6f}",flush=True)
    payload["source_checkpoint_verified"]=True
    payload["both_species_active_at_extended_endpoint"]={
        key:bool(arms["separated_070"]["v_active"]>0 and
                 arms["separated_070"]["w_active"]>0)
        for key,arms in payload["endpoints"].items()
    }
    out=Path(out);plot=Path(plot)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload,indent=2,allow_nan=False)+"\n")
    measured_figure(payload,plot)
    if plot.stat().st_size<4096:
        raise RuntimeError("Missing real continuation graph")
    return payload


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--plate",required=True,type=Path)
    p.add_argument("--steps",default=480,type=int)
    p.add_argument("--stride",default=12,type=int)
    a=p.parse_args()
    result=run_extension(a.source,a.out,a.plate,steps=a.steps,stride=a.stride)
    print("Two populations active at extended endpoint:",
          result["both_species_active_at_extended_endpoint"],flush=True)


if __name__=="__main__":
    main()
