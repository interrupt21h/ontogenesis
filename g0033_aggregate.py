"""Aggregate only verified G0033 per-seed native spatial diagnostics."""
from __future__ import annotations
import argparse
import json
from pathlib import Path


def aggregate(paths):
    items = [json.loads(Path(p).read_text()) for p in paths]
    if len(items) != 8 or len({i["seed"] for i in items}) != 8:
        raise ValueError("Expected exactly eight independent G0033 seed reports")
    if any(i["generation"] != "0033" or i["n"] != 16 or i["steps"] != 240
           or i["thresholds"] != [0.05, 0.1, 0.2] for i in items):
        raise ValueError("Incompatible native-field experiment scopes")
    arms = list(items[0]["treatments"])
    if any(list(i["treatments"]) != arms for i in items):
        raise ValueError("Unmatched arms between seeds")
    results = {
        "generation": "0033",
        "edition": "eight-seed-240-step-native-interface-screen-v1",
        "status": "computed from individual native 4D field analyses",
        "seeds": sorted(i["seed"] for i in items),
        "sample_size": 8,
        "n": 16, "steps": 240,
        "thresholds": [0.05, 0.10, 0.20],
        "treatments": arms,
        "source_archive_sha256_by_seed": {
            str(i["seed"]): i["source_archive_sha256"] for i in items
        },
        "summary": {},
        "individual_endpoints": {},
        "limitations": [
            "Finite eight-seed screen does not demonstrate indefinite stability",
            "Joint global activity is not same-cell co-occupation",
            "The shuffled contact reference cannot prove causal ecology",
            "The 0.1 threshold is the predeclared primary readout",
        ],
    }
    for item in items:
        results["individual_endpoints"][str(item["seed"])] = item["endpoints"]
    for arm in arms:
        endpoints = [(i["seed"], i["endpoints"][arm]["0.10"]) for i in items]
        jointly_active = [seed for seed, ep in endpoints
                          if ep["v_active_cells"] > 0 and ep["w_active_cells"] > 0]
        contact_seeds = [seed for seed, ep in endpoints
                         if ep["four_dimensional_face_contacts"] > 0]
        results["summary"][arm] = {
            "joint_global_activity_seeds": jointly_active,
            "joint_global_activity_count": len(jointly_active),
            "exclusive_face_contact_seeds": contact_seeds,
            "exclusive_face_contact_count": len(contact_seeds),
            "contact_faces_by_seed": {
                str(seed): ep["four_dimensional_face_contacts"]
                for seed, ep in endpoints
            },
            "same_cell_active_counts_by_seed": {
                str(seed): ep["both_active_cells"] for seed, ep in endpoints
            },
        }
    return results


def plot(result, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    seeds = result["seeds"]
    arms = result["treatments"]
    fig, axs = plt.subplots(2, 1, figsize=(12, 8), constrained_layout=True)
    for ax, key, label in ((axs[0], "contact_faces_by_seed", "Exclusive V/W contact faces"),
                           (axs[1], "same_cell_active_counts_by_seed",
                            "Same-cell above-threshold active sites")):
        for arm in arms:
            ys = [result["summary"][arm][key][str(s)] for s in seeds]
            ax.plot([str(s) for s in seeds], ys, marker="o", label=arm)
        ax.set_ylabel(label)
        ax.set_xlabel("Independent initialization seed")
        ax.grid(alpha=.25)
        ax.legend()
    fig.suptitle("G0033 / eight-seed native four-dimensional interface pilot\n"
                 "240 steps · 16⁴ numerical lattice · activity threshold >0.10")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=135)
    plt.close(fig)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--inputs", nargs="+", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--plate", type=Path, required=True)
    a = p.parse_args()
    report = aggregate(a.inputs)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    plot(report, a.plate)
    print(json.dumps(report["summary"], indent=2))
