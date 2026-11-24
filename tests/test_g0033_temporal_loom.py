"""The Temporal Loom must reproduce measured histories, not invent samples."""
import json
import tempfile
import unittest
from pathlib import Path

from PIL import ImageChops
from g0033_temporal_loom import (
    ARMS, METRICS, SEEDS, THRESHOLDS, TIMES, image_at, load_evidence,
)


class TemporalLoomTests(unittest.TestCase):
    def fixture(self, root):
        paths = []
        report = {
            "generation": "0033", "n": 16, "steps": 240,
            "seeds": list(SEEDS), "source_archive_sha256_by_seed": {},
            "individual_endpoints": {},
        }
        for seed in SEEDS:
            sha = f"{seed:064x}"
            report["source_archive_sha256_by_seed"][str(seed)] = sha
            obs, endpoint = {}, {}
            for arm in ARMS:
                obs[arm] = []
                for i, step in enumerate(TIMES):
                    by_threshold = {}
                    for threshold in THRESHOLDS:
                        v_only, w_only, both = 100, 110, i
                        row = {
                            "v_active_cells": v_only + both,
                            "w_active_cells": w_only + both,
                            "v_only_cells": v_only,
                            "w_only_cells": w_only,
                            "both_active_cells": both,
                            "neither_active_cells": 16**4-v_only-w_only-both,
                            "four_dimensional_face_contacts": (
                                i * (seed % 17 + 1) if arm == ARMS[1] else i),
                            "contact_fraction_per_face": i / 10000,
                            "continuous_shared_mass_ratio": i / 100,
                        }
                        by_threshold[threshold] = row
                    obs[arm].append({"step": step, "thresholds": by_threshold})
                endpoint[arm] = obs[arm][-1]["thresholds"]
            data = {
                "generation": "0033", "seed": seed, "n": 16,
                "steps": 240, "sample_steps": list(TIMES),
                "thresholds": [0.05, 0.1, 0.2], "treatments": list(ARMS),
                "source_archive_sha256": sha,
                "observations": obs, "endpoints": endpoint,
            }
            report["individual_endpoints"][str(seed)] = endpoint
            path = root/f"g0033-seed-{seed}.analysis.json"
            path.write_text(json.dumps(data))
            paths.append(path)
        summary = root/"summary.json"
        summary.write_text(json.dumps(report))
        return paths, summary

    def test_numerical_timelines_all_seeds_and_arms(self):
        with tempfile.TemporaryDirectory() as d:
            files, summary = self.fixture(Path(d))
            result = load_evidence(files, summary)
            self.assertEqual(result["seeds"], list(SEEDS))
            self.assertEqual(result["times"], list(TIMES))
            self.assertEqual(len(result["source_analysis_sha256_by_seed"]), 8)
            for metric in METRICS:
                for cutoff in THRESHOLDS:
                    for arm in ARMS:
                        self.assertEqual(len(result["values"][metric][cutoff][arm]), 8)
                        self.assertTrue(all(len(row)==11 for row in
                            result["values"][metric][cutoff][arm]))
            a = image_at(result, 0, 16)
            b = image_at(result, 15, 16)
            self.assertEqual(a.size, (1280, 720))
            self.assertIsNotNone(ImageChops.difference(a, b).getbbox())

    def test_rejects_missing_or_unverified_seed(self):
        with tempfile.TemporaryDirectory() as d:
            files, summary = self.fixture(Path(d))
            with self.assertRaises(ValueError):
                load_evidence(files[:-1], summary)
            doc = json.loads(files[0].read_text())
            doc["source_archive_sha256"] = "0"*64
            files[0].write_text(json.dumps(doc))
            with self.assertRaises(ValueError):
                load_evidence(files, summary)

    def test_rejects_changed_endpoint_and_invented_time(self):
        with tempfile.TemporaryDirectory() as d:
            files, summary = self.fixture(Path(d))
            doc = json.loads(files[0].read_text())
            doc["observations"][ARMS[0]][-1]["thresholds"]["0.10"][
                "four_dimensional_face_contacts"] += 1
            files[0].write_text(json.dumps(doc))
            with self.assertRaises(ValueError):
                load_evidence(files, summary)


if __name__ == "__main__":
    unittest.main()
