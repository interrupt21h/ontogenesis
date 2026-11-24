"""Independent replication aggregator requires a complete matched cohort."""
import json
import tempfile
import unittest
from pathlib import Path
from g0036_replication_aggregate import aggregate, SEEDS, FIELDS


class EightSeedReplicationTests(unittest.TestCase):
    def fixture(self,root):
        paths=[]
        for seed in SEEDS:
            observations=[]
            for step in (0,60,120):
                d={k:(step/120)*seed*.00001 for k in FIELDS}
                observations.append({"step":step,"mean_absolute_differences":d,
                                     "control":{},"feedback":{}})
            report={
                "generation":"0036","n":12,"steps":120,
                "feedback_gain":.035,"seed":seed,
                "sample_steps":[0,60,120],
                "initial_hash_matches":True,"endpoint_hashes_differ":True,
                "observations":observations}
            p=root/f'{seed}.json';p.write_text(json.dumps(report));paths.append(p)
        return paths

    def test_complete_cohort_and_nonzero_medians(self):
        with tempfile.TemporaryDirectory() as folder:
            files=self.fixture(Path(folder))
            report=aggregate(files)
            self.assertEqual(report["seeds"],list(SEEDS))
            self.assertEqual(len(report["observations_by_seed"]),8)
            self.assertEqual(report["results"]["v"]["endpoint_nonzero_seeds"],8)
            self.assertGreater(report["results"]["v"]["endpoint_median"],0)

    def test_reject_partial_cohort(self):
        with tempfile.TemporaryDirectory() as folder:
            files=self.fixture(Path(folder))
            with self.assertRaises(ValueError):aggregate(files[:-1])

    def test_reject_changed_initial_condition(self):
        with tempfile.TemporaryDirectory() as folder:
            files=self.fixture(Path(folder))
            d=json.loads(files[0].read_text())
            d["observations"][0]["mean_absolute_differences"]["v"]=.01
            files[0].write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError,"initial states"):
                aggregate(files)

    def test_reject_duplicate_seed(self):
        with tempfile.TemporaryDirectory() as folder:
            files=self.fixture(Path(folder))
            with self.assertRaises(ValueError):
                aggregate(files[:-1]+[files[0]])


if __name__=="__main__":
    unittest.main()
