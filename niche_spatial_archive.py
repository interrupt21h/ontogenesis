"""Record actual four-dimensional G0032 fields without a reconstructed restart.

Seed 73, near-transition and complementary-niche arms. Fields are copied from
a read-only observer at recorded times. The original step-240 state SHA256 is
checked and reported, not assumed to identify a physically restarted state.
"""
from __future__ import annotations
import argparse,hashlib,json,os
from pathlib import Path
import numpy as np
import consolidation

ARMS={
    "near_transition":{"v_decay_multiplier":.97,"niche_strength":0.0},
    "separated_070":{"v_decay_multiplier":.97,"niche_strength":.70},
}
CHANNELS={"v":"species_v","w":"species_w","m":"matrix"}

def capture(archive,metadata,*,source=None,n=16,steps=480,stride=24,seed=73):
    if not 8<=n<=16 or not 48<=steps<=480 or steps%stride or not 6<=stride<=48:
        raise ValueError("Out-of-budget native field archive")
    if seed<0:raise ValueError("Seed must be nonnegative")
    original=None
    if source is not None:
        original_bytes=Path(source).read_bytes()
        original=json.loads(original_bytes)
        if (original.get("generation"),original.get("n"),
            original.get("steps"),original.get("seeds"))!=("0032",n,240,[42,73]):
            raise ValueError("Source G0032 numerical scope mismatch")
        for arm,cfg in ARMS.items():
            if original["arms"][arm]!=cfg:
                raise ValueError("Source model intervention parameters changed")
    times=list(range(0,steps+1,stride))
    arrays={"steps":np.asarray(times,dtype=np.int32)}
    info={
        "generation":"0032","edition":"native-4d-field-archive-v1",
        "n":n,"steps":steps,"stride":stride,"seed":seed,
        "sample_steps":times,"treatments":ARMS,"channels":CHANNELS,
        "source_sha":os.getenv("GITHUB_SHA","unversioned"),
        "reference_pilot_revision":original["source_sha"] if original else None,
        "reference_pilot_sha256":hashlib.sha256(original_bytes).hexdigest() if original else None,
        "same_seed_initial_state_matches":{},
        "step240_state_hash_matches":{},
        "solver_hashes":{},
        "limitations":[
            "Independent same-seed runs, not a restart from archived full state",
            "All retained state arrays are native float32 four-dimensional fields",
            "Only seed 73 and two fixed interventions are represented",
            "No genotype chooses a niche and no organism is inferred",
        ],
    }
    for arm,settings in ARMS.items():
        recorded={ch:[] for ch in CHANNELS}
        def observer(step,fields):
            for key,field in CHANNELS.items():
                arr=fields[field]
                if arr.shape!=(n,)*4 or arr.flags.writeable:
                    raise AssertionError("Observer must provide a read-only native 4D field")
                if not np.isfinite(arr).all() or arr.min() < -1e-6:
                    raise AssertionError("Invalid observed concentration")
                recorded[key].append(np.array(arr,copy=True,dtype=np.float32))
        result=consolidation.run(
            seed=seed,n=n,steps=steps,observe=False,
            crossfeed=(True,True),season_switch=None,
            ecology_observer=observer,ecology_steps=set(times),**settings)
        for ch,records in recorded.items():
            if len(records)!=len(times):
                raise AssertionError("A recorded numerical timestep was skipped")
            arrays[f"{arm}_{ch}"]=np.stack(records)
        info["solver_hashes"][arm]=result["hashes"]
        if original is not None:
            old=original["hashes"][str(seed)][arm]
            info["same_seed_initial_state_matches"][arm]=(result["hashes"]["0"]==old["0"])
            info["step240_state_hash_matches"][arm]=(result["hashes"].get("240")==old["240"])
            if not info["same_seed_initial_state_matches"][arm]:
                raise AssertionError("Seed did not reproduce the source initialization")
        print(f"G0032 {arm}: {len(times)} native 4D snapshots archived",flush=True)
    if len({info["solver_hashes"][arm]["0"] for arm in ARMS})!=1:
        raise AssertionError("Matched treatments began from different initial states")
    archive,metadata=Path(archive),Path(metadata)
    archive.parent.mkdir(parents=True,exist_ok=True)
    metadata.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(archive,**arrays)
    info["archive_sha256"]=hashlib.sha256(archive.read_bytes()).hexdigest()
    info["archive_bytes"]=archive.stat().st_size
    metadata.write_text(json.dumps(info,indent=2,allow_nan=False)+"\n")
    return info

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--metadata",required=True,type=Path)
    p.add_argument("--source",type=Path)
    p.add_argument("--n",type=int,default=16)
    p.add_argument("--steps",type=int,default=480)
    p.add_argument("--stride",type=int,default=24)
    p.add_argument("--seed",type=int,default=73)
    a=p.parse_args()
    print(json.dumps(capture(a.out,a.metadata,source=a.source,n=a.n,
                             steps=a.steps,stride=a.stride,seed=a.seed),indent=2))
