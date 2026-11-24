"""G0036 eight-seed matched structural feedback replication.

Read-only endpoint/sparse-step evidence.  Uses the *same* control and
divergence-free intervention as the verified two-seed native archive; stores
numerical effects rather than duplicating large field archives.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import numpy as np

import consolidation
from g0036_structural_feedback import feedback, measured, GAIN

SEEDS=(42,73,101,137,211,307,401,509)
CLOCK=(0,60,120)
CHANNELS=("v","w","m","e")


def replicate(seed, *, n=12, steps=120):
    if seed not in SEEDS or n!=12 or steps!=120:
        raise ValueError("Unapproved pilot scope")
    arms={}
    for arm in ("control","feedback"):
        snapshots={}
        def observer(step,fields):
            records={
                "v":fields["species_v"],
                "w":fields["species_w"],
                "m":fields["matrix"],
                "e":fields["energy"],
            }
            snapshots[step]={k:np.array(v,copy=True,dtype=np.float32)
                             for k,v in records.items()}
        kwargs={
            "seed":seed,"n":n,"steps":steps,"observe":False,
            "v_decay_multiplier":.97,"niche_strength":.70,
            "crossfeed":(True,True),
            "ecology_observer":observer,"ecology_steps":set(CLOCK)
        }
        if arm=="feedback":
            kwargs["velocity_feedback"]=feedback
        result=consolidation.run(**kwargs)
        if set(snapshots)!=set(CLOCK):
            raise AssertionError("Missing native numerical replication samples")
        arms[arm]={"fields":snapshots,"hashes":result["hashes"]}
    if arms["control"]["hashes"]["0"]!=arms["feedback"]["hashes"]["0"]:
        raise AssertionError("Replication initial states are not matched")
    if arms["control"]["hashes"]["120"]==arms["feedback"]["hashes"]["120"]:
        raise AssertionError("Intervention has no state effect")
    records=[]
    for step in CLOCK:
        a,b=(arms[k]["fields"][step] for k in ("control","feedback"))
        means={k:float(np.mean(np.abs(b[k]-a[k]),dtype=np.float64))
               for k in CHANNELS}
        for k in CHANNELS:
            if means[k]<0 or not np.isfinite(means[k]):
                raise AssertionError("Nonfinite treatment effect")
        records.append({
            "step":step,
            "mean_absolute_differences":means,
            "control":measured(a["v"],a["w"],a["m"],a["e"]),
            "feedback":measured(b["v"],b["w"],b["m"],b["e"]),
        })
    return {
        "generation":"0036",
        "edition":"independent-eight-seed-structural-feedback-replication-v1",
        "seed":seed,"n":n,"steps":steps,
        "feedback_gain":GAIN,"sample_steps":list(CLOCK),
        "matched_initial_hash":arms["control"]["hashes"]["0"],
        "initial_hash_matches":True,
        "endpoint_hashes_differ":True,
        "observations":records,
        "source_revision":os.getenv("GITHUB_SHA","unversioned"),
        "limitations":"Prescribed conservative feedback and finite numerical trajectories, not autonomous learning",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed",required=True,type=int)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    d=replicate(args.seed)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(d,indent=2,allow_nan=False)+"\n")
    print(f"G0036 replicate seed={args.seed} V endpoint MAE="
          f"{d['observations'][-1]['mean_absolute_differences']['v']:.8f}",flush=True)


if __name__=="__main__":
    main()
