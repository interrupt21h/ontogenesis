"""Low-cost validity checks for the G0030 early-viability comparison."""
import tempfile
import unittest
from pathlib import Path
import consolidation
from ecological_viability import CASES,run_screen

class PreSeason(unittest.TestCase):
    def test_four_cases_initially_matched(self):
        with tempfile.TemporaryDirectory() as t:
            folder=Path(t)
            d=run_screen(folder/"result.json",folder/"plot.png",
                         n=8,steps=60,stride=6,seeds=(42,))
            self.assertEqual(set(d["observations"]["42"]),set(CASES))
            self.assertEqual(len({r["0"] for r in d["state_hashes"]["42"].values()}),1)
            self.assertEqual(set(d["comparisons_vs_unchanged"]["42"]),set(CASES)-{"unchanged"})
            for name,rows in d["observations"]["42"].items():
                self.assertEqual([r["step"] for r in rows],d["times"])
            self.assertGreater((folder/"plot.png").stat().st_size,4096)

    def test_default_has_no_model_changes(self):
        a=consolidation.run(n=8,steps=12,observe=False)
        b=consolidation.run(n=8,steps=12,observe=False,
                            crossfeed=(True,True),season_switch=None)
        self.assertEqual(a["hashes"],b["hashes"])

    def test_budget_is_bounded(self):
        with self.assertRaises(ValueError):
            run_screen("unused.json","unused.png",n=24,steps=180)

if __name__=="__main__":
    unittest.main()
