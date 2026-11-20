"""Versioned, lossless observation snapshots (not integrator restart checkpoints)."""
import json
import os
from pathlib import Path
import numpy as np

AXES=("omega","z","y","x")
def save_snapshot(folder,step,steps,fields,generation="0024",seed=42):
    folder=Path(folder)
    folder.mkdir(parents=True,exist_ok=True)
    shape=fields["u"].shape
    arrays={}
    for name,value in fields.items():
        a=np.asarray(value)
        expected=(16,*shape) if name in ("gv","gw") else shape
        if a.shape!=expected or a.dtype.kind not in "fiu" or not np.isfinite(a).all():
            raise ValueError(f"Invalid field {name}: {a.shape} {a.dtype}")
        arrays[name]=a
    metadata=dict(schema=1,generation=generation,step=step,total_steps=steps,seed=seed,
                  axes=AXES,shape=shape,periodic=[True]*4,revision=os.environ.get("GITHUB_SHA","local"),
                  loci=["C","K","S","B"],units="dimensionless",
                  fields={k:str(v.dtype) for k,v in arrays.items()})
    path=folder/f"state-{step:05d}.npz"
    temp=path.with_suffix(".tmp")
    with temp.open("wb") as stream:
        np.savez_compressed(stream,metadata=np.array(json.dumps(metadata)),**arrays)
    temp.replace(path)
    return path

def load_snapshot(path):
    with np.load(path,allow_pickle=False) as data:
        meta=json.loads(data["metadata"].item())
        if meta["schema"]!=1 or tuple(meta["axes"])!=AXES:
            raise ValueError("Unsupported snapshot schema")
        fields={k:data[k] for k in meta["fields"]}
    shape=tuple(meta["shape"])
    for k,a in fields.items():
        if a.shape!=((16,*shape) if k in ("gv","gw") else shape) or str(a.dtype)!=meta["fields"][k] or not np.isfinite(a).all():
            raise ValueError(f"Invalid archived field {k}")
    return meta,fields
