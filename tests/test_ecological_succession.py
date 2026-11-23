"""Regression tests for independent four-arm G0030 ecological controls."""
import tempfile
import unittest
from pathlib import Path
import numpy as np
import consolidation
from ecological_succession import ARMS,run_screen,snapshot


class G0030(unittest.TestCase):
    def test_unchanged_default(self):
        original=consolidation.run(n=8,steps=12,observe=False)
        explicit=consolidation.run(n=8,steps=12,observe=False,
                                   crossfeed=(True,True),season_switch=None)
        self.assertEqual(original["hashes"],explicit["hashes"])
        self.assertEqual(original["final"],explicit["final"])

    def test_validation(self):
        with self.assertRaises(ValueError):
            consolidation.run(n=8,steps=12,crossfeed=(True,1))
        with self.assertRaises(ValueError):
            consolidation.run(n=8,steps=12,season_switch=12)

    def test_readonly_ecology_observer(self):
        rows=[]
        def capture(step,fields):
            self.assertFalse(fields["energy"].flags.writeable)
            self.assertFalse(fields["genotypes_v"].flags.writeable)
            self.assertEqual(fields["genotypes_v"].shape,(8,8,8,8,8))
            rows.append(snapshot(step,fields))
        monitored=consolidation.run(n=8,steps=24,observe=False,
                                    ecology_observer=capture,
                                    ecology_steps={0,12,24})
        unmonitored=consolidation.run(n=8,steps=24,observe=False)
        self.assertEqual(monitored["hashes"],unmonitored["hashes"])
        self.assertEqual([r["step"] for r in rows],[0,12,24])

    def test_matched_four_arm_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/"result.json"
            plate=Path(tmp)/"plate.png"
            result=run_screen(out,plate,seeds=(42,),n=8,steps=60,stride=6)
            self.assertEqual(set(result["observations"]["42"]),set(ARMS))
            self.assertEqual(len({h["0"] for h in result["state_hashes"]["42"].values()}),1)
            self.assertTrue(all([r["step"] for r in history]==result["times"]
                for history in result["observations"]["42"].values()))
            self.assertGreater(plate.stat().st_size,4096)
            self.assertTrue(np.isfinite(result["endpoints"]["42"]["both"]["energy_mean"]))


if __name__=="__main__":
    unittest.main()
