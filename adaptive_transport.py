"""G0029: matched adaptive-curl transport experiment with true 4D observations."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
import numpy as np
import consolidation

CHANNELS = ("matrix", "species_v", "species_w", "energy", "network")
METRICS = ("energy_mean", "matrix_mean", "matrix_coverage", "activity_energy",
           "v_active", "w_active")

def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for part in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()

class AdaptiveCurl:
    """Slow field memory modulates divergence-free 4D transport."""
    def __init__(self, n, gain=.32, memory=.035):
        if not 0 <= gain <= 1 or not 0 < memory <= 1:
            raise ValueError("Invalid feedback coefficients")
        self.field = np.zeros((n,)*4, dtype=np.float32)
        self.gain, self.memory = float(gain), float(memory)
        self.rms = 0.
        self.divergence = 0.

    def __call__(self, step, state):
        e, m, v, w = [state[k] for k in ("energy","matrix","species_v","species_w")]
        target = np.clip(1.6*m + .45*(v+w) + .15*(1-e), 0, 1)
        self.field += self.memory*(target-self.field)
        potential = self.gain*self.field
        correction = [np.zeros_like(potential) for _ in range(4)]
        for i in range(4):
            for j in range(i+1,4):
                correction[i] += potential - np.roll(potential,1,axis=j)
                correction[j] -= potential - np.roll(potential,1,axis=i)
        div = sum(a-np.roll(a,1,axis=i) for i,a in enumerate(correction))
        self.divergence = float(np.abs(div).max())
        if self.divergence >= 1e-5:
            raise AssertionError("Adaptive correction lost solenoidal property")
        self.rms = float(np.sqrt(sum(float(np.mean(a*a)) for a in correction)))
        return tuple(correction)

def measured(step, e, m, v, w, feedback=None):
    p = v+w
    d = {
        "step": int(step),
        "energy_mean": float(e.mean()),
        "matrix_mean": float(m.mean()),
        "matrix_coverage": float(np.mean(m>.2)),
        "activity_energy": float(np.mean(p*e)),
        "v_active": float(np.mean(v>.1)),
        "w_active": float(np.mean(w>.1)),
        "network_mean": 0. if feedback is None else float(feedback.field.mean()),
        "network_std": 0. if feedback is None else float(feedback.field.std()),
        "feedback_rms": 0. if feedback is None else feedback.rms,
    }
    if any(not np.isfinite(x) for x in d.values()):
        raise ValueError("Nonfinite numerical metric")
    return d

def run_pair(out, metadata, *, n=12, steps=180, stride=6, omega_planes=4,
             seed=42, gain=.32, memory=.035, max_raw_mib=1000):
    if not 8 <= n <= 32 or not 12 <= steps <= 12000 or stride < 1:
        raise ValueError("Numerical bounds violated")
    if not 1 <= omega_planes <= n:
        raise ValueError("Invalid fourth-coordinate sample count")
    times = sorted(set(range(0,steps+1,stride))|{0,steps//2,steps})
    if len(times) > 1300:
        raise ValueError("Increase observation cadence")
    selected = set(times)
    omega = np.arange(omega_planes,dtype=np.int32)*n//omega_planes
    if len(set(map(int,omega))) != omega_planes:
        raise ValueError("Nonunique fourth-axis slices")
    shape = (len(times), omega_planes, len(CHANNELS), n,n,n)
    dense_steps = sorted({0,steps//2,steps})
    visual_bytes = int(np.prod(shape))*2
    dense_bytes = len(dense_steps)*len(CHANNELS)*n**4*4
    if visual_bytes+dense_bytes > max_raw_mib*1024**2:
        raise ValueError("Numerical observation exceeds archive budget")
    control, adaptive, seen, keyframes = [],[],[],[]
    def observe_control(t,e,m,v,w):
        if t in selected:
            control.append(measured(t,e,m,v,w))
    print("Running matched, unchanged G0026 control",flush=True)
    base = consolidation.run(seed=seed,n=n,steps=steps,observe=False,
                             observer=observe_control)
    feedback = AdaptiveCurl(n,gain=gain,memory=memory)
    out,metadata = Path(out),Path(metadata)
    out.parent.mkdir(parents=True,exist_ok=True)
    metadata.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="g0029-") as tmp:
        samples = np.lib.format.open_memmap(
            Path(tmp)/"sample.npy",mode="w+",dtype=np.float16,shape=shape)
        def observe_adaptive(t,e,m,v,w):
            if t in selected:
                adaptive.append(measured(t,e,m,v,w,feedback))
        def record(t,fields):
            if t not in selected:
                return
            index = len(seen)
            if index >= len(times) or times[index] != t:
                raise AssertionError("Nonmonotonic observation timestamps")
            fields = dict(fields,network=feedback.field)
            for k,fourth in enumerate(omega):
                for j,name in enumerate(CHANNELS):
                    field = fields[name][int(fourth)]
                    if not np.isfinite(field).all():
                        raise ValueError("Nonfinite native source")
                    samples[index,k,j] = field
            if t in dense_steps:
                keyframes.append(np.stack([fields[name].copy() for name in CHANNELS]))
            seen.append(t)
            if index % 30 == 0:
                print(f"Measured sample {index+1}/{len(times)} at {t}",flush=True)
        print("Running adaptive-curl arm",flush=True)
        treated = consolidation.run(
            seed=seed,n=n,steps=steps,observe=False,
            observer=observe_adaptive,velocity_feedback=feedback,
            cinematic_observer=record,cinematic_steps=selected)
        if seen != times or [x["step"] for x in control] != times:
            raise AssertionError("Unmatched observation schedule")
        if len(keyframes) != len(dense_steps):
            raise AssertionError("Dense native samples missing")
        exposures={}
        for j,name in enumerate(CHANNELS):
            subset=np.asarray(samples[::max(1,len(times)//40),:,j],np.float32)
            exposures[name]=float(np.percentile(subset,99.5))
        np.savez_compressed(out,states=samples,
            steps=np.asarray(times,dtype=np.int32),omega_indices=omega,
            dense_steps=np.asarray(dense_steps,dtype=np.int32),
            dense_states=np.stack(keyframes).astype(np.float32))
        del samples
    differences=[{"step":a["step"],**{
        k+"_adaptive_minus_control":a[k]-c[k] for k in METRICS
    }} for c,a in zip(control,adaptive)]
    info={
        "generation":"0029","edition":"paired-adaptive-curl-1",
        "source_sha":os.environ.get("GITHUB_SHA","unversioned"),
        "status":"generated; CI verification pending",
        "parent":"G0026 unchanged numerical rules with optional solenoidal correction",
        "seed":seed,"n":n,"steps":steps,"stride":stride,
        "sample_count":len(times),
        "feedback":{"gain":gain,"memory":memory,
            "target":"clip(1.6*M+.45*(V+W)+.15*(1-E),0,1)",
            "last_rms":feedback.rms,"last_divergence":feedback.divergence,
            "externally_specified":True},
        "recording":{"axis_order":["omega","z","y","x"],
            "channel_order":list(CHANNELS),"shape":list(shape),
            "dtype":"float16","omega_indices":list(map(int,omega)),
            "dense_steps":dense_steps,
            "dense_shape":[len(dense_steps),len(CHANNELS),n,n,n,n],
            "dense_dtype":"float32","restart_checkpoint":False,
            "fixed_exposure_p995":exposures,
            "uncompressed_visual_bytes":visual_bytes,
            "uncompressed_dense_bytes":dense_bytes},
        "control":control,"adaptive":adaptive,"paired":differences,
        "hashes":{"control":base["hashes"],"adaptive":treated["hashes"]},
        "final":{"control":control[-1],"adaptive":adaptive[-1],
                 "difference":differences[-1]},
        "archive":{"sha256":digest(out),"bytes":out.stat().st_size},
    }
    metadata.write_text(json.dumps(info,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"sample_count":len(times),"final":info["final"],
                      "archive_bytes":out.stat().st_size},indent=2),flush=True)
    return info

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for name,default in (("n",12),("steps",180),("stride",6),("omega-planes",4),
                         ("seed",42),("max-raw-mib",1000)):
        p.add_argument("--"+name,type=int,default=default)
    p.add_argument("--gain",type=float,default=.32)
    p.add_argument("--memory",type=float,default=.035)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--metadata",type=Path,required=True)
    a=p.parse_args()
    run_pair(a.out,a.metadata,n=a.n,steps=a.steps,stride=a.stride,
             omega_planes=a.omega_planes,seed=a.seed,gain=a.gain,
             memory=a.memory,max_raw_mib=a.max_raw_mib)
