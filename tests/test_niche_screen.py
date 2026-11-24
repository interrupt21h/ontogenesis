"""G0032: verify read-only spatial observations and baseline invariance."""
import tempfile
import unittest
from pathlib import Path
import numpy as np
import consolidation
from niche_screen import ARMS,run_screen


class HabitatScreen(unittest.TestCase):
    def test_original_numeric_default_unchanged(self):
        reference=consolidation.run(n=8,steps=20,observe=False)
        candidate=consolidation.run(n=8,steps=20,observe=False,
                                    niche_strength=0.0,v_decay_multiplier=1.0)
        self.assertEqual(reference["hashes"],candidate["hashes"])
        self.assertEqual(reference["final"],candidate["final"])

    def test_niche_value_bounds_and_readonly_habitat(self):
        for strength in (-.01,.76,float("nan")):
            with self.assertRaises(ValueError):
                consolidation.run(n=8,steps=2,observe=False,
                                  niche_strength=strength)
        seen=[]
        def observer(step,fields):
            self.assertFalse(fields["habitat_bias"].flags.writeable)
            self.assertEqual(fields["habitat_bias"].shape,(8,8,8,8))
            seen.append(step)
        base=consolidation.run(n=8,steps=20,observe=False,
                               ecology_observer=observer,ecology_steps={0,20})
        self.assertEqual(seen,[0,20])
        self.assertEqual(base["hashes"],consolidation.run(n=8,steps=20,observe=False)["hashes"])

    def test_four_arm_8cubed4_smoke(self):
        with tempfile.TemporaryDirectory() as temp:
            tmp=Path(temp)
            data=run_screen(tmp/"result.json",tmp/"measured.png",
                            n=8,steps=90,stride=6,seeds=(42,))
            self.assertEqual(set(data["observations"]["42"]),set(ARMS))
            self.assertEqual(len({x["0"] for x in data["hashes"]["42"].values()}),1)
            self.assertGreater((tmp/"measured.png").stat().st_size,4096)
            for rows in data["observations"]["42"].values():
                self.assertEqual([r["step"] for r in rows],data["times"])

if __name__=="__main__":
    unittest.main()
