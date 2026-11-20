"""G0028 fidelity archive: four-dimensional integration, multi-omega 3D fields.

The stepped G0026 model is unchanged. This module is an observer and a
deterministic environmental perturbation. It records raw float32 keyframes
as well as a dense, float16 visualization archive, neither of which is a
reproducible restart checkpoint.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

import numpy as np

import consolidation
from disturbance_cinematic import periodic_gaussian, samples_for

CHANNELS = ("matrix","species_v","species_w","pulse","energy","trait","recovery")
AXES = ("omega","z","y","x")
DENSE_COUNTS = 7


def digest_file(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4*1024*1024), b""):
            sha.update(block)
    return sha.hexdigest()


def create_fidelity_archive(out, metadata, *, seed=42, n=12, steps=320,
                            shock_step=None, sample_every=4,
                            omega_planes=4, energy_fraction=.70,
                            matrix_fraction=.80, max_raw_mib=1536):
    if not 8 <= n <= 32 or not 12 <= steps <= 12000:
        raise ValueError("8<=n<=32 and 12<=steps<=12000 required")
    if sample_every < 1 or not 1 <= omega_planes <= n:
        raise ValueError("Invalid observation cadence or omega plane count")
    if not (0 <= energy_fraction <= 1 and 0 <= matrix_fraction <= 1):
        raise ValueError("Shock removal fractions must lie within [0,1]")
    event=steps*2//3 if shock_step is None else shock_step
    if not 2 <= event <= steps-2:
        raise ValueError("Shock step outside valid numerical range")
    dense_steps=sorted(set([0,steps,event-1,event,event+1,steps//4,
                            steps//2,3*steps//4]))
    schedule=sorted(samples_for(steps,event,sample_every) | set(dense_steps))
    if len(schedule)>1700:
        raise ValueError("More than 1700 samples; increase cadence")
    omega_indices=np.arange(omega_planes,dtype=np.int32)*n//omega_planes
    if len(set(omega_indices))!=len(omega_indices):
        raise ValueError("Omega planes not distinct")
    sample_shape=(len(schedule),omega_planes,len(CHANNELS),n,n,n)
    # Keep an explicit budget because high temporal and omega coverage is
    # multiplicative in N^3 and could overwhelm a GitHub-hosted runner.
    raw_bytes=int(np.prod(sample_shape))*np.dtype(np.float16).itemsize
    full_key_bytes=len(dense_steps)*len(CHANNELS)*n**4*4
    if (raw_bytes+full_key_bytes)>max_raw_mib*(1024**2):
        raise ValueError("Raw capture exceeds selected CPU-runner archive budget")

    mask,core=periodic_gaussian(n)
    metric_rows=[]
    recording_steps=[]
    raw_keyframes=[]
    recorded_dense=[]
    exposures={}
    out=Path(out)
    metadata=Path(metadata)
    out.parent.mkdir(parents=True,exist_ok=True)
    metadata.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="g28-fidelity-") as scratch:
        mmap=np.lib.format.open_memmap(
            Path(scratch)/"sampled.npy", mode="w+", dtype=np.float16,
            shape=sample_shape)
        current=0
        lookup=set(schedule)
        dense_lookup=set(dense_steps)

        def intervention(step,e,m):
            if step==event:
                e*=1-energy_fraction*mask
                m*=1-matrix_fraction*mask

        def record(step,fields):
            nonlocal current
            if step not in lookup:
                return
            if current>=len(schedule) or step!=schedule[current]:
                raise AssertionError("Nonmonotonic observer sequence")
            for p,omega in enumerate(omega_indices):
                for ch,name in enumerate(CHANNELS):
                    # Float32 measured fields are never mutated by observers;
                    # only the archived visual representation is quantized.
                    slice_=fields[name][int(omega)]
                    if not np.isfinite(slice_).all():
                        raise AssertionError("Nonfinite source concentration")
                    mmap[current,p,ch]=slice_
            recording_steps.append(step)
            s=mmap[current].astype(np.float32)
            metric_rows.append({
                "step":step,
                "measured_matrix_max":float(s[:,0].max()),
                "measured_matrix_std":float(s[:,0].std()),
                "measured_v_max":float(s[:,1].max()),
                "measured_w_max":float(s[:,2].max()),
                "measured_pulse_max":float(s[:,3].max()),
                "measured_energy_min":float(s[:,4].min()),
                "measured_trait_std":float(s[:,5].std()),
                "measured_recovery_max":float(s[:,6].max()),
                "energy_core_mean_4d":float(fields["energy"][core].mean())
                if step in dense_lookup else None,
                "matrix_core_mean_4d":float(fields["matrix"][core].mean())
                if step in dense_lookup else None,
            })
            if step in dense_lookup:
                raw_keyframes.append(np.stack(
                    [fields[name].astype(np.float32,copy=True) for name in CHANNELS]))
                recorded_dense.append(step)
            current+=1
            if current%120==0 or current==len(schedule):
                print(f"Captured {current}/{len(schedule)} native 3D samples "
                      f"(step={step})",flush=True)

        numerical=consolidation.run(
            seed=seed,n=n,steps=steps,stride=sample_every,
            arm="baseline",observe=False,
            intervention=intervention,cinematic_observer=record,
            cinematic_steps=lookup)
        if current!=len(schedule):
            raise AssertionError("Missing native samples")
        if dense_steps!=recorded_dense:
            raise AssertionError("Missing full-precision checkpoint snapshot")
        # Fixed-in-time exposure references; sampling across ALL omega
        # hyperplanes prevents accidental per-frame artificial blooming.
        for ch,name in enumerate(CHANNELS):
            sub=mmap[::max(1,len(schedule)//48),:,ch].astype(np.float32)
            low,high=np.percentile(sub,(2,99.5))
            exposures[name]={"p02":float(low),"p995":float(high)}
        np.savez_compressed(
            out,states=mmap,steps=np.array(recording_steps,dtype=np.int32),
            omega_indices=omega_indices,
            dense_steps=np.array(recorded_dense,dtype=np.int32),
            dense_states=np.stack(raw_keyframes))
        del mmap
    sha=digest_file(out)
    info={
        "generation":"0028",
        "edition":"cinematic-fidelity-2",
        "status":"generated; verification requires passing CI",
        "source_sha":os.environ.get("GITHUB_SHA","local-unversioned"),
        "parent_numerical_model":"G0026 base dynamics",
        "seed":seed,"n":n,"steps":steps,"event_step":event,
        "sample_every":sample_every,"sample_count":len(recording_steps),
        "event":{"geometry":"periodic 4D Gaussian","sigma_cells":n/5.5,
                 "energy_fraction":energy_fraction,
                 "matrix_fraction":matrix_fraction,
                 "applied_immediately_before_observation":True,
                 "core_cells":int(core.sum())},
        "recording":{
            "axis_order":list(AXES),
            "volume_axes":["z","y","x"],
            "omega_indices":list(map(int,omega_indices)),
            "channel_order":list(CHANNELS),
            "shape":list(sample_shape),
            "dtype":"float16",
            "quantization":"float32 numerical state to float16 for frequent visual archive",
            "dense_steps":dense_steps,
            "dense_dtype":"float32",
            "dense_shape":[len(dense_steps),len(CHANNELS),n,n,n,n],
            "density_planes_per_sample":int(omega_planes),
            "fixed_exposure_percentiles":exposures,
            "unrecorded_4d_cells":"Full 4D fields retained only at dense_steps",
            "restart_checkpoint":False,
        },
        "archive":{"filename":out.name,"sha256":sha,
                   "bytes":out.stat().st_size,
                   "uncompressed_sample_bytes":raw_bytes,
                   "uncompressed_full_keyframe_bytes":full_key_bytes},
        "metrics":metric_rows,"numerical_hashes":numerical["hashes"],
        "final":{
            "matrix_mean":numerical["final"]["matrix_mean"],
            "v_active":numerical["final"]["v_active"],
            "w_active":numerical["final"]["w_active"]},
    }
    metadata.write_text(json.dumps(info,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"shape":sample_shape,"dense_steps":dense_steps,
                      "archive_bytes":out.stat().st_size,
                      "sha256":sha,"numerical_hashes":len(numerical["hashes"])},
                     indent=2),flush=True)
    return info


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n",type=int,default=12)
    p.add_argument("--steps",type=int,default=320)
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--shock-step",type=int)
    p.add_argument("--sample-every",type=int,default=4)
    p.add_argument("--omega-planes",type=int,default=4)
    p.add_argument("--max-raw-mib",type=int,default=1536)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--metadata",type=Path,required=True)
    a=p.parse_args()
    create_fidelity_archive(
        a.out,a.metadata,seed=a.seed,n=a.n,steps=a.steps,
        shock_step=a.shock_step,sample_every=a.sample_every,
        omega_planes=a.omega_planes,max_raw_mib=a.max_raw_mib)


if __name__=="__main__":
    main()
