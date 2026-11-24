"""G0036: causal structural feedback into the existing 4D transport solver.

A state-dependent, antisymmetric face potential generates a bounded
divergence-free correction from measured structure and V/W contrast. The
control uses precisely the original solver with feedback=None. Identical
initial seed, intervention, and observation schedule are held fixed.

The correction is recomputed from the *current solver fields* each time;
unlike G0034/G0035, this is a genuinely new numerical update.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import numpy as np
import consolidation

ARMS=("control","feedback")
CHANNELS={"v":"species_v","w":"species_w","m":"matrix","e":"energy"}
GAIN=.035
SAMPLES=tuple(range(0,121,12))
SEEDS=(42,73)
N=12


def feedback(step,state,gain=GAIN):
    """Antisymmetric discrete potential: D_i D_j A_ij cancels identically.

    Uses backward differences identical to consolidation.run. Returns face
    velocities in all four axes. No nonconservative source or sink is added.
    """
    if not 0<=gain<=.08:
        raise ValueError("Feedback gain must be bounded")
    m,v,w=(state[k] for k in ("matrix","species_v","species_w"))
    if m.ndim!=4 or m.shape!=v.shape or m.shape!=w.shape:
        raise ValueError("Four matching native 4D solver fields required")
    if not all(np.isfinite(a).all() for a in (m,v,w)):
        raise ValueError("Nonfinite numerical feedback field")
    p=np.tanh(3.0*(m-.12)+1.7*(v-w)).astype(np.float32)
    # The potential is zero if feedback is disabled and periodic in all axes.
    phi=gain*p
    def d(a,axis):
        return a-np.roll(a,1,axis=axis)
    # Independent antisymmetric planes (omega,z) and (y,x):
    # δu_0=D_1 φ, δu_1=-D_0 φ, δu_2=D_3 φ, δu_3=-D_2 φ.
    correction=(d(phi,1),-d(phi,0),d(phi,3),-d(phi,2))
    divergence=sum(d(u,i) for i,u in enumerate(correction))
    if float(np.max(np.abs(divergence)))>3e-7:
        raise AssertionError("Structural feedback violates 4D divergence-free condition")
    return tuple(np.asarray(a,dtype=np.float32) for a in correction)


def measured(v,w,m,e):
    va,wa=v>.1,w>.1
    vo,wo=va&~wa,wa&~va
    contacts=0
    for axis in range(4):
        contacts+=int(np.count_nonzero(
            (vo&np.roll(wo,-1,axis=axis)) |
            (wo&np.roll(vo,-1,axis=axis))))
    return {
        "v_active":int(va.sum()),"w_active":int(wa.sum()),
        "joint_active":int((va&wa).sum()),
        "exclusive_contacts":contacts,
        "matrix_mean":float(m.mean(dtype=np.float64)),
        "energy_mean":float(e.mean(dtype=np.float64)),
    }


def capture(seed,archive,metadata,*,n=N,steps=120,stride=12,gain=GAIN):
    if seed not in SEEDS or n not in (8,12) or not 24<=steps<=120:
        raise ValueError("Out of bounded pilot scope")
    if stride not in (12,24) or steps%stride:
        raise ValueError("Expected complete discrete observation clock")
    if not 0<gain<=.08:
        raise ValueError("Feedback must be enabled in the treatment")
    sample_steps=list(range(0,steps+1,stride))
    data={"steps":np.array(sample_steps,dtype=np.int32)}
    numerical={}
    for arm in ARMS:
        stored={k:[] for k in CHANNELS}
        summaries=[]
        def record(step,fields):
            values={k:fields[ch] for k,ch in CHANNELS.items()}
            if any(a.flags.writeable or a.shape!=(n,)*4 for a in values.values()):
                raise AssertionError("Invalid or mutable native observer view")
            for k,a in values.items():
                if not np.isfinite(a).all() or a.min() < -1e-6:
                    raise AssertionError("Invalid native recorded fields")
                stored[k].append(np.array(a,copy=True,dtype=np.float32))
            summaries.append({"step":step,**measured(
                values["v"],values["w"],values["m"],values["e"])})
        settings=dict(seed=seed,n=n,steps=steps,observe=False,
                      crossfeed=(True,True),v_decay_multiplier=.97,
                      niche_strength=.70,
                      ecology_observer=record,
                      ecology_steps=set(sample_steps))
        if arm=="feedback":
            settings["velocity_feedback"]=lambda step,state:feedback(step,state,gain)
        result=consolidation.run(**settings)
        for k,rows in stored.items():
            if len(rows)!=len(sample_steps):
                raise AssertionError("Incomplete numerical archive")
            data[f"{arm}_{k}"]=np.stack(rows)
        numerical[arm]={"hashes":result["hashes"],"observations":summaries,
                        "final":summaries[-1]}
    assert numerical["control"]["hashes"]["0"]==numerical["feedback"]["hashes"]["0"],(
        "Matched arms have different initial states")
    if not any(numerical["control"]["hashes"][key]!=numerical["feedback"]["hashes"][key]
               for key in numerical["control"]["hashes"] if key!="0"):
        raise AssertionError("Intervention had no numerical effect")
    differences={
        k:float(np.mean(np.abs(data["control_"+k][-1]-
                                data["feedback_"+k][-1]),dtype=np.float64))
        for k in CHANNELS
    }
    if not all(np.isfinite(v) and v>=0 for v in differences.values()):
        raise AssertionError("Invalid treatment separation")
    archive,metadata=Path(archive),Path(metadata)
    archive.parent.mkdir(parents=True,exist_ok=True)
    metadata.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(archive,**data)
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    output={
        "generation":"0036","edition":"matched-native-4d-structural-feedback-pilot-v1",
        "seed":seed,"n":n,"steps":steps,"sample_steps":sample_steps,
        "feedback_gain":gain,"source_solver":"consolidation.run",
        "intervention":"bounded curl-like divergence-free face velocities derived from current native matrix and V/W fields",
        "numerical_controls":"identical seed, static niche strength 0.70, V decay multiplier 0.97, original transport model",
        "arms":list(ARMS),"channels":list(CHANNELS),
        "archive_sha256":digest,"archive_bytes":archive.stat().st_size,
        "matched_initial_hash":numerical["control"]["hashes"]["0"],
        "numerical":numerical,"endpoint_mean_absolute_differences":differences,
        "source_revision":os.getenv("GITHUB_SHA","unversioned"),
        "limitations":[
            "This is an imposed algorithmic transport feedback, not learned behavior",
            "Mean differences establish intervention sensitivity, not biological adaptation",
            "Small matched seeds and 120 steps do not prove long-term persistence",
            "The correction is divergence-free, but underlying reactions still exchange matter and energy",
        ]
    }
    metadata.write_text(json.dumps(output,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"seed":seed,"difference":differences,
                      "archive_sha256":digest},indent=2),flush=True)
    return output


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed",type=int,required=True)
    p.add_argument("--n",type=int,default=N)
    p.add_argument("--steps",type=int,default=120)
    p.add_argument("--stride",type=int,default=12)
    p.add_argument("--gain",type=float,default=GAIN)
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--metadata",type=Path,required=True)
    a=p.parse_args()
    capture(a.seed,a.archive,a.metadata,n=a.n,steps=a.steps,
            stride=a.stride,gain=a.gain)


if __name__=="__main__":
    main()
