"""Capture reproducible native 4D fields for G0030/G0031 cinematic editions.

These are independent same-seed reruns, never checkpoint restarts or images
reconstructed from numerical summaries. Capture only the named matched arms.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path

import numpy as np

import consolidation

CONFIG = {
    "0030": {
        "steps": 180,
        "reference": "g0030-viability.json",
        "arms": {
            "unchanged": {"season_switch": None, "crossfeed": (True, True)},
            "invert_24": {"season_switch": 24, "crossfeed": (True, True)},
        },
    },
    "0031": {
        "steps": 240,
        "reference": "g0031-pilot.json",
        "arms": {
            "historical": {"v_decay_multiplier": 1.0},
            "v_loss_095": {"v_decay_multiplier": 0.95},
        },
    },
}
CHANNELS = {"v": "species_v", "w": "species_w", "m": "matrix"}


def capture(generation, archive, metadata, *, reference=None,
            seed=42, n=16, stride=12, steps=None):
    if generation not in CONFIG:
        raise ValueError("Only G0030 and G0031 have native cinema capture profiles")
    config = CONFIG[generation]
    steps = config["steps"] if steps is None else steps
    if not 8 <= n <= 16 or not 24 <= steps <= config["steps"] or not 1 <= stride <= 24:
        raise ValueError("Capture outside bounded CI budget")
    if steps % stride or seed < 0:
        raise ValueError("Invalid capture cadence or seed")
    if generation == "0030" and steps <= 24:
        raise ValueError("G0030 event must precede final timestep")

    reference_data = None
    reference_bytes = None
    if reference is not None:
        reference_bytes = Path(reference).read_bytes()
        reference_data = json.loads(reference_bytes)
        if (reference_data["generation"] != generation or
                reference_data["n"] != n or reference_data["steps"] != config["steps"] or
                seed not in reference_data["seeds"]):
            raise ValueError("Original pilot numerical scope mismatch")

    times = list(range(0, steps + 1, stride))
    arrays = {"steps": np.asarray(times, dtype=np.int32)}
    hashes = {}
    comparisons = {}
    for arm, settings in config["arms"].items():
        samples = {key: [] for key in CHANNELS}

        def observer(step, fields):
            for key, original in CHANNELS.items():
                view = fields[original]
                if view.flags.writeable or view.shape != (n,) * 4:
                    raise AssertionError("Expected read-only native 4D numerical field")
                if not np.isfinite(view).all() or view.min() < -1e-6:
                    raise AssertionError("Nonfinite or negative captured field")
                samples[key].append(np.array(view, dtype=np.float32, copy=True))

        result = consolidation.run(
            seed=seed, n=n, steps=steps, observe=False,
            ecology_observer=observer, ecology_steps=set(times), **settings
        )
        for channel, records in samples.items():
            if len(records) != len(times):
                raise AssertionError("Missing native samples")
            arrays[f"{arm}_{channel}"] = np.stack(records)
        hashes[arm] = result["hashes"]
        if reference_data is not None:
            source_hashes = (reference_data["state_hashes"] if generation == "0030"
                             else reference_data["hashes"])[str(seed)][arm]
            # Exact equivalence is expected even for a shorter rerun at t=0.
            common = set(source_hashes) & set(result["hashes"])
            comparisons[arm] = {step: result["hashes"][step] == source_hashes[step]
                                for step in sorted(common, key=int)}
            if not comparisons[arm].get("0"):
                raise AssertionError("Initial state diverged from reference study")
            if steps == config["steps"] and not all(comparisons[arm].values()):
                raise AssertionError("Native rerun diverged from verified numerical pilot")

    if len({hashes[arm]["0"] for arm in config["arms"]}) != 1:
        raise AssertionError("Matched controls must have identical initial conditions")
    archive, metadata = Path(archive), Path(metadata)
    archive.parent.mkdir(parents=True, exist_ok=True)
    metadata.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(archive, **arrays)
    info = {
        "generation": generation,
        "edition": "native-4d-cinematic-capture-v1",
        "seed": seed, "n": n, "steps": steps, "stride": stride,
        "sample_steps": times, "arms": list(config["arms"]),
        "arm_parameters": {k: dict(v) for k, v in config["arms"].items()},
        "channels": CHANNELS, "axis_order": "omega,z,y,x",
        "dtype": "float32", "activity_threshold": 0.1,
        "source_sha": os.getenv("GITHUB_SHA", "unversioned"),
        "reference_pilot_sha256": (hashlib.sha256(reference_bytes).hexdigest()
                                   if reference_bytes is not None else None),
        "reference_checkpoint_comparisons": comparisons,
        "solver_hashes": hashes,
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "archive_bytes": archive.stat().st_size,
        "limitations": [
            "Independent matching-seed reruns, not numerical checkpoint restarts",
            "Only the two selected arms and one seed are filmed",
            "Discrete selected native 4D snapshots; no invented intermediate numerical states",
            "Presentation camera rotation does not imply physical motion",
            "These are chemical fields, not autonomous organisms",
        ],
    }
    metadata.write_text(json.dumps(info, indent=2, allow_nan=False) + "\n")
    return info


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--generation", choices=CONFIG, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--metadata", type=Path, required=True)
    p.add_argument("--reference", type=Path)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--n", type=int, default=16)
    p.add_argument("--stride", type=int, default=12)
    a = p.parse_args()
    print(json.dumps(capture(a.generation, a.out, a.metadata,
                             reference=a.reference, seed=a.seed, n=a.n,
                             stride=a.stride), indent=2))


if __name__ == "__main__":
    main()
