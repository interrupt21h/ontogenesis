"""G0034 rendering regression checks using a complete synthetic numeric graph."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from PIL import ImageChops

from g0034_lineage_cinema import validate_report, diagram, frame, render


class CinemaTests(unittest.TestCase):
    def fixture(self):
        seq = []
        for t in range(11):
            nodes = [{"id": 1, "sites": 32+t}]
            seq.append({
                "sample_index":t, "component_count":1,
                "active_sites":32+t, "largest_component":32+t,
                "featured":nodes,"featured_ids":[1],
                "featured_edges_from_previous":
                    [{"from":1,"to":1,"sites":32+t-1}] if t else [],
                "births":1 if t==0 else 0,
                "deaths":0,"splits":0,"merges":0,"overlap_links":int(t>0),
                "small_components":0,
            })
        return {
            "generation":"0034",
            "edition":"periodic-four-dimensional-component-genealogy-pilot-v1",
            "n":16,"steps":240,"seeds":[42,73],
            "arms":["near_transition","separated_070"],
            "species":["v_only","w_only"],
            "times":list(range(0,241,24)),
            "threshold":.1,
            "source": {
                str(seed):{
                    "source_archive_sha256":hashlib.sha256(str(seed).encode()).hexdigest(),
                    "arms":{
                        arm:{"v_only":json.loads(json.dumps(seq)),
                             "w_only":json.loads(json.dumps(seq))}
                        for arm in ("near_transition","separated_070")
                    }
                } for seed in (42,73)
            }
        }

    def test_diagram_is_real_graph_and_progress_is_distinct(self):
        report=self.fixture()
        validate_report(report)
        art=diagram(report,arm="separated_070")
        a=frame(report,art,0,16,arm="separated_070")
        b=frame(report,art,15,16,arm="separated_070")
        self.assertEqual(a.size,(1280,720))
        self.assertIsNotNone(ImageChops.difference(a,b).getbbox())

    def test_rejects_unrecorded_lineage_endpoint(self):
        report=self.fixture()
        report["source"]["42"]["arms"]["near_transition"]["v_only"][1][
            "featured_edges_from_previous"][0]["from"] = 999
        with self.assertRaises(ValueError):
            validate_report(report)

    def test_short_encoded_movie(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            report=self.fixture()
            result=render(report,root/"short.mp4",root/"poster.png",
                          seconds=2,fps=8)
            self.assertEqual(result["frames"],16)
            self.assertTrue((root/"short.mp4").stat().st_size>8192)
            self.assertFalse(result["interpolated_numerical_states"])


if __name__=="__main__":
    unittest.main()
