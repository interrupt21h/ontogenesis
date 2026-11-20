"""G0028 cinematic archive: observed 3D sections of an evolving 4D universe.

This is a non-restartable visual archive, not a checkpoint. The renderer never
has to rerun the integrator. Numerical dynamics are inherited from G0026.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import numpy as np

import consolidation

CHANNELS = ("matrix", "species_v", "species_w", "pulse", "energy")
AXES = ("omega", "z", "y", "x")


def periodic_gaussian(n):
    center = n // 2
    coords = np.ogrid[tuple(slice(0, n) for _ in range(4))]
    radius2 = sum(np.minimum(np.abs(a - center), n - np.abs(a - center))**2
                  for a in coords)
    sigma = n / 5.5
    gaussian = np.exp(-radius2 / (2 * sigma**2)).astype(np.float32)
    return gaussian, gaussian >= np.exp(-0.5)


def samples_for(steps, event, stride):
    return set(range(0, steps + 1, stride)) | {
        0, steps, event - 1, event, min(steps, event + 1)
    }


def create_archive(out, metadata, *, seed=42, n=16, steps=720,
                   shock_step=None, sample_every=12, energy_fraction=.70,
                   matrix_fraction=.80, omega_index=None):
    if not 8 <= n <= 32 or not 12 <= steps <= 12000 or sample_every < 1:
        raise ValueError("Require 8<=n<=32, 12<=steps<=12000, sample_every>=1")
    event = steps * 2 // 3 if shock_step is None else shock_step
    if not 2 <= event <= steps - 2:
        raise ValueError("shock_step must lie between 2 and steps-2")
    if not (0 <= energy_fraction <= 1 and 0 <= matrix_fraction <= 1):
        raise ValueError("Shock fractions must lie in [0,1]")
    omega = n // 2 if omega_index is None else omega_index
    if not 0 <= omega < n:
        raise ValueError("omega_index out of range")
    schedule = samples_for(steps, event, sample_every)
    if len(schedule) > 500:
        raise ValueError("Archive exceeds 500 recorded states; increase sample_every")

    mask, core = periodic_gaussian(n)
    snapshots = []
    frame_steps = []
    metrics = []

    def intervention(step, e, m):
        if step == event:
            # The experimental event changes *only* the energy and matrix
            # fields; existing kinetic rules remain untouched.
            e *= 1.0 - energy_fraction * mask
            m *= 1.0 - matrix_fraction * mask

    def record(step, fields):
        if step not in schedule:
            return
        section = np.stack([fields[channel][omega, :, :, :]
                            for channel in CHANNELS], axis=0)
        if not np.isfinite(section).all():
            raise ValueError("Non-finite cinematic observation")
        # Store real observed values, then quantize only the archived
        # representation to float16 to fit GitHub-hosted execution budgets.
        snapshots.append(section.astype(np.float16))
        frame_steps.append(step)
        metrics.append({
            "step": step,
            "core_energy": float(fields["energy"][core].mean()),
            "core_matrix": float(fields["matrix"][core].mean()),
            "global_energy": float(fields["energy"].mean()),
            "global_matrix": float(fields["matrix"].mean()),
        })

    result = consolidation.run(
        seed=seed, n=n, steps=steps, stride=sample_every, arm="baseline",
        observe=False, intervention=intervention, cinematic_observer=record,
        cinematic_steps=schedule,
    )
    states = np.stack(snapshots, axis=0)
    frame_steps = np.asarray(frame_steps, dtype=np.int32)
    assert frame_steps.tolist() == sorted(schedule)
    assert states.shape == (len(schedule), len(CHANNELS), n, n, n)
    assert np.isfinite(states).all()
    assert frame_steps[0] == 0 and frame_steps[-1] == steps
    assert event in frame_steps and event - 1 in frame_steps
    assert set(map(int, frame_steps)) <= schedule

    out = Path(out)
    metadata = Path(metadata)
    out.parent.mkdir(parents=True, exist_ok=True)
    metadata.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, states=states, steps=frame_steps)
    digest = hashlib.sha256(out.read_bytes()).hexdigest()

    field_ranges = {}
    for index, field in enumerate(CHANNELS):
        # Fixed-in-time exposure calibration; sampled uniformly from the
        # archived series. Not a scientific statistic.
        sample = states[::max(1, len(states)//30), index].astype(np.float32)
        low, high = np.percentile(sample, (2, 99.5))
        field_ranges[field] = {"p02": float(low), "p995": float(high)}

    info = {
        "generation": "0028",
        "edition": "cinematic-1",
        "status": "CI verification pending",
        "source_sha": os.environ.get("GITHUB_SHA", "local-unversioned"),
        "seed": seed,
        "n": n,
        "steps": steps,
        "event_step": event,
        "sample_every": sample_every,
        "sample_count": int(len(frame_steps)),
        "event": {
            "geometry": "periodic four-dimensional Gaussian",
            "sigma_cells": n / 5.5,
            "energy_removal_fraction": energy_fraction,
            "matrix_removal_fraction": matrix_fraction,
            "core_cells": int(core.sum()),
            "application": "immediately before the recorded event-step state",
        },
        "recording": {
            "axis_order": list(AXES),
            "omega_index": omega,
            "volume_axes": ["z", "y", "x"],
            "channel_order": list(CHANNELS),
            "shape": list(states.shape),
            "dtype": "float16",
            "scientific_dtype": "float32",
            "quantization": "float32 to float16 after observation",
            "data_semantics": "3D hyperplane at fixed omega, not a 4D projection",
            "restart_checkpoint": False,
            "fixed_exposure_percentiles": field_ranges,
        },
        "archive": {"filename": out.name, "sha256": digest, "bytes": out.stat().st_size},
        "frame_metrics": metrics,
        "numerical_hashes": result["hashes"],
        "final": {"matrix_mean": result["final"]["matrix_mean"],
                  "energy": metrics[-1]["global_energy"],
                  "v_active": result["final"]["v_active"],
                  "w_active": result["final"]["w_active"]},
    }
    metadata.write_text(json.dumps(info, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"samples": len(frame_steps),
                      "volume_shape": list(states.shape),
                      "archive_bytes": out.stat().st_size,
                      "event_step": event,
                      "sha256": digest}, indent=2), flush=True)
    return info


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n", type=int, default=16)
    p.add_argument("--steps", type=int, default=720)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--shock-step", type=int)
    p.add_argument("--sample-every", type=int, default=12)
    p.add_argument("--omega-index", type=int)
    p.add_argument("--energy-fraction", type=float, default=.70)
    p.add_argument("--matrix-fraction", type=float, default=.80)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--metadata", type=Path, required=True)
    a = p.parse_args()
    create_archive(a.out, a.metadata, seed=a.seed, n=a.n,
                   steps=a.steps, shock_step=a.shock_step,
                   sample_every=a.sample_every,
                   energy_fraction=a.energy_fraction,
                   matrix_fraction=a.matrix_fraction,
                   omega_index=a.omega_index)


if __name__ == "__main__":
    main()
