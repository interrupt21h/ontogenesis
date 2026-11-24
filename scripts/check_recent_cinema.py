"""Audit the released visual coverage of every recent Ontogenesis generation.

This is a release asset inventory gate, *not* a claim of scientific validity
or artistic quality. Verify actual published film AND matching poster names,
not merely committed source code or a passing render step.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

EDITION_PAIRS = {
    "0030": ("ontogenesis-0030-native-cinematic", "ontogenesis-0030-diagnostic"),
    "0031": ("ontogenesis-0031-native-cinematic", "ontogenesis-0031-evidence"),
    "0032": ("ontogenesis-0032-spatial", "ontogenesis-0032-evidence"),
    "0033": ("ontogenesis-0033-contact-cartography", "ontogenesis-0033-temporal-loom"),
    "0034": ("ontogenesis-0034-luminous-habitat", "ontogenesis-0034-lineage-ribbons"),
    "0035": ("ontogenesis-0035-morphogenic-tide-art",
             "ontogenesis-0035-morphogenic-tide-evidence"),
    "0036": ("ontogenesis-0036-feedback-aurora-art",
             "ontogenesis-0036-feedback-aurora-evidence"),
}


def check(release, *, require_all=True):
    assets = release.get("assets", [])
    if not isinstance(assets, list):
        raise ValueError("Release assets must be a list")
    indexed = {}
    for asset in assets:
        name = asset.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("Release contains unnamed asset")
        if name in indexed:
            raise ValueError("Duplicate release asset: " + name)
        indexed[name] = asset
    generations = {}
    missing = []
    for gen, editions in EDITION_PAIRS.items():
        output = {}
        for label, base in zip(("art_or_native", "evidence_or_analytical"), editions):
            result = {}
            for suffix in ("mp4", "png"):
                filename = base+"."+suffix
                asset = indexed.get(filename)
                minimum = 50_000 if suffix == "mp4" else 4_096
                okay = bool(asset and isinstance(asset.get("size"), int)
                            and asset["size"] >= minimum)
                if not okay:
                    missing.append(filename)
                result[suffix] = {
                    "name": filename, "published": okay,
                    "bytes": asset.get("size", 0) if asset else 0,
                    "url": asset.get("browser_download_url") if asset and okay else None
                }
            output[label] = result
        generations[gen] = output
    response = {
        "schema": "ontogenesis-recent-cinematic-coverage-v1",
        "release_tag": release.get("tag_name"),
        "generations": generations,
        "missing": missing,
        "complete": not missing,
        "scope": "G0030-G0036 two published editions and posters per generation",
        "qualifier": "Completeness of release assets, not numerical or artistic validation"
    }
    if require_all and missing:
        raise ValueError("Required cinematic release assets missing: " + ", ".join(missing))
    return response


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--release", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--allow-incomplete", action="store_true")
    a = p.parse_args()
    report = check(json.loads(a.release.read_text()),
                   require_all=not a.allow_incomplete)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"complete":report["complete"],"missing":report["missing"],
                      "generations":len(report["generations"])},indent=2))
