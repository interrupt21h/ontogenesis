"""Aggregate only the complete G0036 matched eight-seed replication cohort."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import numpy as np

SEEDS=(42,73,101,137,211,307,401,509)
FIELDS=("v","w","m","e")


def aggregate(paths):
    if len(paths)!=len(SEEDS):
        raise ValueError("Eight seed reports are required")
    reports={}
    for path in paths:
        d=json.loads(Path(path).read_text())
        seed=d.get("seed")
        if seed not in SEEDS or seed in reports:
            raise ValueError("Unexpected/duplicate numerical seed")
        if (d.get("generation"),d.get("n"),d.get("steps"),
            d.get("feedback_gain"),d.get("sample_steps"),
            d.get("initial_hash_matches"),d.get("endpoint_hashes_differ"))!=(
            "0036",12,120,.035,[0,60,120],True,True):
            raise ValueError("Unmatched or invalid replication run")
        if len(d.get("observations",[]))!=3:
            raise ValueError("Missing numerical evidence")
        if [v["step"] for v in d["observations"]]!=[0,60,120]:
            raise ValueError("Wrong numerical observation times")
        for sample in d["observations"]:
            if set(sample["mean_absolute_differences"])!=set(FIELDS):
                raise ValueError("Incomplete observed fields")
            if any(not np.isfinite(x) or x<0
                   for x in sample["mean_absolute_differences"].values()):
                raise ValueError("Invalid feedback effect")
        if any(d["observations"][0]["mean_absolute_differences"][k]!=0
               for k in FIELDS):
            raise ValueError("Control/treatment initial states are different")
        reports[seed]=d
    if set(reports)!=set(SEEDS):
        raise ValueError("Incomplete replication cohort")
    observed={}
    for field in FIELDS:
        samples=np.asarray([
            [reports[seed]["observations"][i]["mean_absolute_differences"][field]
             for i in range(3)] for seed in SEEDS],dtype=np.float64)
        observed[field]={
            "by_seed":{str(seed):[float(x) for x in samples[j]]
                       for j,seed in enumerate(SEEDS)},
            "endpoint_mean":float(samples[:,-1].mean()),
            "endpoint_median":float(np.median(samples[:,-1])),
            "endpoint_min":float(samples[:,-1].min()),
            "endpoint_max":float(samples[:,-1].max()),
            "endpoint_nonzero_seeds":int(np.count_nonzero(samples[:,-1]>0)),
        }
    return {
        "generation":"0036",
        "edition":"validated-eight-seed-matched-feedback-replication-v1",
        "seeds":list(SEEDS),"n":12,"steps":120,
        "sample_steps":[0,60,120],
        "model_intervention":"State-derived divergence-free transport correction",
        "feedback_gain":.035,
        "results":observed,
        "observations_by_seed":{
            str(seed):reports[seed]["observations"] for seed in SEEDS},
        "limits":"Eight finite matched numerical trials, not a biological or adaptive-life claim",
    }


def plot(summary,path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(12,7),sharex=True)
    for ax,field in zip(axes.flat,FIELDS):
        x=list(SEEDS)
        y=[summary["results"][field]["by_seed"][str(seed)][-1]
           for seed in SEEDS]
        ax.bar(range(len(x)),y)
        ax.set_title(f"{field.upper()} · terminal mean absolute feedback difference")
        ax.set_xticks(range(len(x)),[str(s) for s in x],rotation=45)
        ax.set_ylabel("Concentration units")
        ax.grid(axis="y",alpha=.2)
    fig.suptitle("G0036 · Eight matched native 4D structural feedback experiments")
    fig.tight_layout()
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(path,dpi=150)
    plt.close(fig)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--inputs",nargs="+",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--plot",type=Path,required=True)
    a=p.parse_args()
    report=aggregate(a.inputs)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    plot(report,a.plot)
    print(json.dumps({k:v["endpoint_median"]
                      for k,v in report["results"].items()},indent=2))


if __name__=="__main__":
    main()
