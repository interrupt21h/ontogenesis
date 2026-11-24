"""G0031 rate-frontier checks; ensure G0026 historical numerical invariance."""
import tempfile
import unittest
from pathlib import Path

import consolidation
from viability_frontier import ARMS,run_screen


class G0031(unittest.TestCase):
    def test_baseline_remains_identical(self):
        old=consolidation.run(n=8,steps=18,observe=False)
        new=consolidation.run(n=8,steps=18,observe=False,
                              v_decay_multiplier=1.0)
        self.assertEqual(old["hashes"],new["hashes"])
        self.assertEqual(old["final"],new["final"])

    def test_invalid_rates_rejected(self):
        with self.assertRaises(ValueError):
            consolidation.run(n=8,steps=12,observe=False,v_decay_multiplier=0)
        with self.assertRaises(ValueError):
            consolidation.run(n=8,steps=12,observe=False,v_decay_multiplier=float("nan"))

    def test_small_four_arm_screen(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)
            result=run_screen(folder/"test.json",folder/"test.png",
                              n=8,steps=60,stride=6,seeds=(42,))
            self.assertEqual(set(result["observations"]["42"]),set(ARMS))
            self.assertEqual(len({x["0"] for x in result["hashes"]["42"].values()}),1)
            self.assertTrue(all([row["step"] for row in records]==result["times"]
                 for records in result["observations"]["42"].values()))
            self.assertGreater((folder/"test.png").stat().st_size,4096)
            self.assertIsInstance(result["any_endpoint_both_active"],bool)

if __name__=="__main__":
    unittest.main()
