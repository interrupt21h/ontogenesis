"""G0032 persistence: verify replay hashes instead of trusting curve similarity."""
import json
import tempfile
import unittest
from pathlib import Path

import consolidation
from niche_screen import ARMS
from niche_persistence import CASES,run_extension,verify_source


def saved_small_source(n=8,checkpoint=120,seeds=(42,)):
    original={"generation":"0032","n":n,"steps":checkpoint,"seeds":list(seeds),
              "source_sha":"test","arms":{arm:dict(ARMS[arm]) for arm in CASES},
              "hashes":{}}
    for seed in seeds:
        original["hashes"][str(seed)]={}
        for arm in CASES:
            original["hashes"][str(seed)][arm]=consolidation.run(
                seed=seed,n=n,steps=checkpoint,observe=False,
                **ARMS[arm])["hashes"]
    return original


class Continuation(unittest.TestCase):
    def test_reject_mismatched_archives(self):
        source=saved_small_source()
        verify_source(source,8,120,(42,))
        source["arms"]["separated_070"]["niche_strength"]=0
        with self.assertRaises(ValueError):
            verify_source(source,8,120,(42,))

    def test_checkpoint_replay_and_measured_plot(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            source=root/"source.json"
            source.write_text(json.dumps(saved_small_source()))
            payload=run_extension(source,root/"extended.json",root/"plot.png",
                                  steps=240,stride=12)
            self.assertTrue(payload["source_checkpoint_verified"])
            self.assertEqual(set(payload["endpoints"]["42"]),set(CASES))
            self.assertIn("42",payload["both_species_active_at_extended_endpoint"])
            self.assertGreater((root/"plot.png").stat().st_size,4096)

    def test_detect_divergence(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            original=saved_small_source()
            original["hashes"]["42"]["near_transition"]["0"]="0"*64
            source=root/"bad.json"
            source.write_text(json.dumps(original))
            with self.assertRaises(AssertionError):
                run_extension(source,root/"extended.json",root/"plot.png",
                              steps=240,stride=12)


if __name__=="__main__":
    unittest.main()
