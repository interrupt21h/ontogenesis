"""G0033: quantify multi-seed persistence and real native 4D interfaces.

Read-only numerical measurements from verified G0032-compatible field archives.
Shuffle controls permute the four activity classes, preserving exact counts.
They do not create a new or biological simulation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

from niche_spatial_interface import metrics
from niche_spatial_render import load_fields

THRESHOLDS = (0.05, 0.10, 0.20)
PERMUTATIONS = 16


def categories(v, w, cutoff):
    return ((v > cutoff).astype(np.uint8) |
            ((w > cutoff).astype(np.uint8) << 1))


def describe(v, w, m, threshold):
    # Existing G0032 metrics defines >0.1. Scale inputs so the same
    # independently tested 4D face logic implements alternative cutoffs.
    factor = 0.1 / threshold
    return metrics(v * factor, w * factor, m)


def permutation_reference(v, w, threshold, *, seed, repetitions=PERMUTATIONS):
    if repetitions < 1:
        raise ValueError("At least one null permutation is required")
    labels = categories(v, w, threshold).ravel()
    rng = np.random.default_rng(seed)
    totals = []
    for _ in range(repetitions):
        shuffled = labels[rng.permutation(labels.size)].reshape(v.shape)
        # Construct actual binary masks for the contact statistic. This
        # preserves four classes (neither, V, W, both) exactly.
        sv = (shuffled & 1).astype(np.float32)
        sw = ((shuffled & 2) != 0).astype(np.float32)
        totals.append(metrics(sv, sw, np.zeros_like(sv))[
            "four_dimensional_face_contacts"])
    return {"permutations": repetitions,
            "mean_contact_faces": float(np.mean(totals)),
            "std_contact_faces": float(np.std(totals)),
            "min_contact_faces": int(min(totals)),
            "max_contact_faces": int(max(totals))}


def analyze(archive, metadata, *, permutations=PERMUTATIONS):
    fields, info, sha = load_fields(archive, metadata)
    if info["steps"] != 240 or info["n"] != 16 or info["seed"] < 0:
        raise ValueError("G0033 pilot requires one 16^4, 240-step seed archive")
    result = {
        "generation": "0033",
        "edition": "multi-seed-native-interface-robustness-pilot-v1",
        "seed": info["seed"], "n": info["n"], "steps": info["steps"],
        "sample_steps": info["sample_steps"],
        "thresholds": list(THRESHOLDS),
        "source_archive_sha256": sha,
        "source_numerical_revision": info["source_sha"],
        "treatments": list(info["treatments"]),
        "observations": {}, "endpoints": {},
        "definition": "Native four-axis periodic adjacency between exclusively active V/W sites",
        "null_model": "Exact joint-class-preserving random permutations; spatial correlations destroyed",
        "limitations": [
            "A finite 240-step pilot is not established long-term coexistence",
            "Predefined external niches are not evolved organism preferences",
            "Contact faces do not demonstrate communication or metabolite transport",
            "Permutation reference is descriptive, not a mechanistic control",
        ],
    }
    n = info["n"]
    for arm_index, arm in enumerate(info["treatments"]):
        records = []
        for i, step in enumerate(info["sample_steps"]):
            v = fields[f"{arm}_v"][i]
            w = fields[f"{arm}_w"][i]
            m = fields[f"{arm}_m"][i]
            by_threshold = {}
            for cutoff in THRESHOLDS:
                observed = describe(v, w, m, cutoff)
                if observed["four_dimensional_face_contacts"] > 4 * n**4:
                    raise AssertionError("More contact faces than periodic grid faces")
                by_threshold[f"{cutoff:.2f}"] = observed
            records.append({"step": step, "thresholds": by_threshold})
        result["observations"][arm] = records
        end = records[-1]
        endpoints = {}
        for ti, cutoff in enumerate(THRESHOLDS):
            key = f"{cutoff:.2f}"
            endpoint = dict(end["thresholds"][key])
            v = fields[f"{arm}_v"][-1]
            w = fields[f"{arm}_w"][-1]
            control_seed = (info["seed"] * 100003 + arm_index * 1009 + ti * 97)
            endpoint["shuffled_spatial_reference"] = permutation_reference(
                v, w, cutoff, seed=control_seed, repetitions=permutations
            )
            endpoints[key] = endpoint
        result["endpoints"][arm] = endpoints
    return result


def write_report(archive, metadata, output, *, permutations=PERMUTATIONS):
    result = analyze(archive, metadata, permutations=permutations)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(f"G0033 seed {result['seed']} evidence: " +
          ", ".join(f"{arm} contacts={rows['0.10']['four_dimensional_face_contacts']}"
                    for arm, rows in result["endpoints"].items()), flush=True)
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--metadata", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--permutations", type=int, default=PERMUTATIONS)
    a = p.parse_args()
    write_report(a.data, a.metadata, a.out, permutations=a.permutations)
