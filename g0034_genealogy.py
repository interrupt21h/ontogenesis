"""G0034 — measured four-dimensional component genealogy.

Threshold the native G0033 V-only and W-only fields, identify face-connected
components with periodic boundaries in *all four* axes, and link consecutive
recorded snapshots by exact voxel overlap. No intermediate simulation states,
inferred velocities, or biological identities are fabricated.

An overlap graph is an observational description: births/deaths mean entry/exit
from the chosen threshold, and split/merge mean branching in this sampled graph.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import numpy as np
from scipy import ndimage

from niche_spatial_render import load_fields

ARMS = ("near_transition", "separated_070")
SPECIES = ("v_only", "w_only")
SEEDS = (42, 73)
MIN_DISPLAY_SITES = 16
STRUCTURE = ndimage.generate_binary_structure(4, 1)


class DisjointSet:
    def __init__(self, size):
        self.parent = np.arange(size + 1, dtype=np.int32)

    def find(self, x):
        x = int(x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = int(self.parent[x])
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[max(ra, rb)] = min(ra, rb)


def periodic_components(mask):
    """4D nearest-neighbor connected component labels, wrapping all axes.

    ndimage.label handles internal nearest-neighbor faces. Union the exact
    matching mask sites on each periodic first/last hyperplane, then compact
    labels deterministically to ascending original IDs.
    """
    mask = np.asarray(mask, dtype=bool)
    if mask.ndim != 4 or any(n < 2 for n in mask.shape):
        raise ValueError("Expected a true four-dimensional periodic mask")
    labels, count = ndimage.label(mask, structure=STRUCTURE)
    if not count:
        return np.zeros(mask.shape, np.int32), np.zeros(1, np.int64)
    dsu = DisjointSet(int(count))
    for axis in range(4):
        front = np.take(labels, 0, axis=axis).ravel()
        back = np.take(labels, -1, axis=axis).ravel()
        matches = (front > 0) & (back > 0)
        if not matches.any():
            continue
        # Unique matched component pairs avoid repeated Python union work.
        pairs = np.unique(np.column_stack((front[matches], back[matches])),
                          axis=0)
        for a, b in pairs:
            dsu.union(a, b)
    roots = np.fromiter((dsu.find(i) for i in range(1, count + 1)),
                        dtype=np.int32, count=count)
    _, mapped = np.unique(roots, return_inverse=True)
    lut = np.zeros(count + 1, np.int32)
    lut[1:] = mapped + 1
    result = lut[labels]
    sizes = np.bincount(result.ravel(), minlength=int(mapped.max()) + 2)
    if int(sizes[1:].sum()) != int(mask.sum()):
        raise AssertionError("Component labeling lost active sites")
    return result, sizes


def overlap_edges(before, after):
    """Count nonempty sampled-state intersections, not trajectories."""
    if before.shape != after.shape:
        raise ValueError("Mismatched component volumes")
    valid = (before > 0) & (after > 0)
    if not valid.any():
        return []
    pairs, counts = np.unique(
        np.column_stack((before[valid], after[valid])),
        axis=0, return_counts=True)
    return [{"from": int(a), "to": int(b), "sites": int(n)}
            for (a, b), n in zip(pairs, counts)]


def summarize(fields, *, min_display_sites=MIN_DISPLAY_SITES):
    if not 1 <= min_display_sites <= 65536:
        raise ValueError("Invalid visual filter")
    series = {}
    for name in SPECIES:
        series[name] = []
        previous = None
        for t, (v, w) in enumerate(fields):
            va, wa = v > .1, w > .1
            mask = (va & ~wa) if name == "v_only" else (wa & ~va)
            labels, sizes = periodic_components(mask)
            n = len(sizes) - 1
            active = int(mask.sum())
            edges = overlap_edges(previous, labels) if previous is not None else []
            # All components are retained in numerical totals; the display
            # filter affects only the summarized top features and flow drawing.
            selected = sorted(range(1, n + 1), key=lambda j: (-int(sizes[j]), j))
            featured = selected[:24]
            records = [{"id": int(j), "sites": int(sizes[j])}
                       for j in featured if sizes[j] >= min_display_sites]
            indegree = np.bincount(
                [e["to"] for e in edges], minlength=n+1) if edges else np.zeros(n+1, int)
            outdegree = np.bincount(
                [e["from"] for e in edges],
                minlength=(int(previous.max())+1 if previous is not None else 1)
            ) if edges else np.zeros(1, int)
            # These refer to the complete voxel-overlap graph, including
            # small components; not just the displayed features.
            births = int(np.count_nonzero(indegree[1:] == 0)) if previous is not None else n
            deaths = (int(np.count_nonzero(outdegree[1:] == 0))
                      if previous is not None else 0)
            splits = int(np.count_nonzero(outdegree[1:] > 1))
            merges = int(np.count_nonzero(indegree[1:] > 1))
            displayed = set(r["id"] for r in records)
            # For the visual graph, preserve every match between top-24
            # components of adjacent samples, sorted by actual overlap.
            previous_displayed = set(series[name][-1]["featured_ids"]) if t else set()
            links = [e for e in edges
                     if e["from"] in previous_displayed and e["to"] in displayed]
            links.sort(key=lambda e: (-e["sites"], e["from"], e["to"]))
            series[name].append({
                "sample_index": t,
                "active_sites": active,
                "component_count": n,
                "largest_component": int(sizes[1:].max()) if n else 0,
                "births": births, "deaths": deaths, "splits": splits, "merges": merges,
                "overlap_links": len(edges),
                "featured_ids": [r["id"] for r in records],
                "featured": records,
                "featured_edges_from_previous": links,
                "small_components": sum(int(sizes[j] < min_display_sites)
                                        for j in range(1, n+1)),
            })
            previous = labels
    return series


def analyze(paths, output, *, min_display_sites=MIN_DISPLAY_SITES):
    if len(paths) != len(SEEDS):
        raise ValueError("Exactly two archived seeds are required")
    snapshots = {}
    for archive, meta in paths:
        data, info, digest = load_fields(archive, meta)
        seed = info["seed"]
        if seed not in SEEDS or seed in snapshots:
            raise ValueError("Unexpected or duplicate seed")
        if info["steps"] != 240 or info["n"] != 16 or list(info["treatments"]) != list(ARMS):
            raise ValueError("Unexpected numerical field scope")
        times = info["sample_steps"]
        if times != list(range(0, 241, 24)):
            raise ValueError("Unmatched or truncated G0033 observation timeline")
        arms = {}
        for arm in ARMS:
            samples = [(data[f"{arm}_v"][i], data[f"{arm}_w"][i])
                       for i in range(len(times))]
            arms[arm] = summarize(samples, min_display_sites=min_display_sites)
        snapshots[str(seed)] = {
            "source_archive_sha256": digest,
            "source_numerical_revision": info["source_sha"],
            "arms": arms,
        }
    if set(snapshots) != {str(i) for i in SEEDS}:
        raise ValueError("Missing expected seed")
    result = {
        "generation": "0034",
        "edition": "periodic-four-dimensional-component-genealogy-pilot-v1",
        "status": "computed from original G0033 native field archives",
        "seeds": list(SEEDS), "arms": list(ARMS),
        "species": list(SPECIES), "times": list(range(0,241,24)),
        "threshold": 0.1, "min_display_sites": min_display_sites,
        "n": 16, "steps": 240,
        "connectivity": "Periodic nearest-neighbor face connectivity along all four numerical axes",
        "lineage_definition": "Overlap of actual occupied sites in consecutive recorded snapshots, without interpolation",
        "limitations": [
            "Component birth and death are threshold events, not biological reproduction or mortality",
            "An observed split or merge is a sampled overlap-graph relationship, not proof of a continuous physical event",
            "No organism identities or cross-snapshot physical trajectories are inferred",
            "Only two previously recorded seeds and the 240-step pilot are analyzed",
            "Displayed nodes use a size filter; full component statistics do not",
        ],
        "source": snapshots,
        "algorithm_revision": os.getenv("GITHUB_SHA", "unversioned"),
    }
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--a", type=Path, required=True)
    p.add_argument("--am", type=Path, required=True)
    p.add_argument("--b", type=Path, required=True)
    p.add_argument("--bm", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--min-display-sites", type=int, default=MIN_DISPLAY_SITES)
    a = p.parse_args()
    result = analyze(((a.a, a.am), (a.b, a.bm)), a.out,
                     min_display_sites=a.min_display_sites)
    for seed, detail in result["source"].items():
        for arm, species in detail["arms"].items():
            print(f"G0034 seed {seed} {arm}: " + ", ".join(
                f"{s} final={values[-1]['component_count']} components"
                for s, values in species.items()), flush=True)


if __name__ == "__main__":
    main()
