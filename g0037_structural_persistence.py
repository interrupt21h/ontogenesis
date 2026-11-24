"""G0037: controlled feedback-strength and structural-memory pilot.

Three genuinely integrated arms: 0, 0.0175 and 0.0700 feedback gain.
Each is initialized by the same solver seed, static habitat and parameters.
Structural persistence is the Jaccard overlap between periodic 4D matrix
threshold masks at consecutive *recorded* times. It is not tracked life,
fitness, or evidence of an agent remembering anything.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import consolidation
from g0036_structural_feedback import feedback, measured

SEEDS=(42,73,101,137)
GAINS={"control":0.0,"low":0.0175,"high":0.07}
TIMES=tuple(range(0,121,24))
CHANNELS={"v":"species_v","w":"species_w","m":"matrix"}
THRESHOLD=0.15
N=12


def persistence(before,after,threshold=THRESHOLD):
    """Exact coordinate overlap on a four-dimensional native lattice."""
    if before.shape!=after.shape or before.ndim!=4:
        raise ValueError("Persistence needs equal native 4D states")
    if not np.isfinite(before).all() or not np.isfinite(after).all():
        raise ValueError("Invalid source field")
    a,b=before>threshold,after>threshold
    union=int(np.count_nonzero(a|b))
    intersection=int(np.count_nonzero(a&b))
    return {"intersection":intersection,"union":union,
            "jaccard":float(intersection/union) if union else None,
            "both_empty":union==0}


def analyze(seed,*,n=N,steps=120):
    if seed not in SEEDS or n!=N or steps!=120:
        raise ValueError("Out of G0037 bounded study scope")
    arrays={"steps":np.asarray(TIMES,dtype=np.int32)}
    results={}
    for arm,gain in GAINS.items():
        captured={}
        def observe(step,fields):
            if step not in TIMES:
                raise AssertionError("Unexpected captured solver step")
            record={}
            for alias,key in CHANNELS.items():
                a=fields[key]
                if a.flags.writeable or a.shape!=(n,)*4 or not np.isfinite(a).all():
                    raise AssertionError("Observer must expose immutable native 4D data")
                record[alias]=np.array(a,copy=True,dtype=np.float32)
            record["e"]=np.array(fields["energy"],copy=True,dtype=np.float32)
            captured[step]=record
        kwargs=dict(seed=seed,n=n,steps=steps,observe=False,
                    crossfeed=(True,True),v_decay_multiplier=.97,niche_strength=.70,
                    ecology_observer=observe,ecology_steps=set(TIMES))
        if gain:
            kwargs["velocity_feedback"]=(lambda step,state,g=gain:feedback(step,state,g))
        solver=consolidation.run(**kwargs)
        if set(captured)!=set(TIMES):
            raise AssertionError("Native snapshot clock is incomplete")
        observations=[]
        previous=None
        for step in TIMES:
            record=captured[step]
            metric=measured(record["v"],record["w"],record["m"],record["e"])
            memory=persistence(previous["m"],record["m"]) if previous is not None else None
            observations.append({"step":step,**metric,"matrix_persistence":memory})
            previous=record
        for alias in CHANNELS:
            arrays[f"{arm}_{alias}"]=np.stack([captured[t][alias] for t in TIMES])
        results[arm]={"gain":gain,"solver_hashes":solver["hashes"],
                      "observations":observations}
    hashes={v["solver_hashes"]["0"] for v in results.values()}
    if len(hashes)!=1:
        raise AssertionError("Matched source initial states differ")
    for ch in CHANNELS:
        if not all(np.array_equal(arrays[f"control_{ch}"][0],arrays[f"{arm}_{ch}"][0])
                   for arm in GAINS):
            raise AssertionError("Different initial source fields")
    if not any(results["control"]["solver_hashes"]["120"]!=
               results[arm]["solver_hashes"]["120"] for arm in ("low","high")):
        raise AssertionError("Feedback-strength intervention produced no difference")
    effect={}
    for arm in ("low","high"):
        effect[arm]={channel:float(np.abs(arrays[f"{arm}_{channel}"][-1]-
                                             arrays[f"control_{channel}"][-1]).mean(dtype=np.float64))
                     for channel in CHANNELS}
    return arrays,{
        "generation":"0037","edition":"matched-4d-feedback-strength-and-persistence-v1",
        "seed":seed,"n":n,"steps":steps,"sample_steps":list(TIMES),
        "arms":list(GAINS),"feedback_gains":GAINS,"matrix_threshold":THRESHOLD,
        "matched_initial_hash":next(iter(hashes)),
        "results":results,"endpoint_mean_absolute_difference_from_control":effect,
        "numerical_definition":"4D matrix-mask Jaccard at same voxel positions between consecutive archived 24-step snapshots",
        "limitations":[
            "Structural overlap is a thresholded coordinate statistic, not memory or cognition",
            "The gain is prescribed, not selected by organisms",
            "Finite pilot does not establish persistence beyond step 120",
            "Jaccard is undefined for two empty masks and recorded as null",
        ],"source_revision":os.getenv("GITHUB_SHA","unversioned")}


def capture(seed,archive,metadata):
    fields,info=analyze(seed)
    archive,metadata=Path(archive),Path(metadata)
    archive.parent.mkdir(parents=True,exist_ok=True)
    metadata.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(archive,**fields)
    info["archive_sha256"]=hashlib.sha256(archive.read_bytes()).hexdigest()
    info["archive_bytes"]=archive.stat().st_size
    metadata.write_text(json.dumps(info,indent=2,allow_nan=False)+"\n")
    return info


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed",type=int,required=True)
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--metadata",type=Path,required=True)
    a=p.parse_args()
    d=capture(a.seed,a.archive,a.metadata)
    print(json.dumps({"seed":d["seed"],"endpoint_difference":
                      d["endpoint_mean_absolute_difference_from_control"]},indent=2))
