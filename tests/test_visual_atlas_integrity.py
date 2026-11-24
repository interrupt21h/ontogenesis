"""Local tests for the source-linked visual atlas parser."""
import unittest
from pathlib import Path
from visual_atlas_integrity import Parser,verify

class AtlasIntegrity(unittest.TestCase):
    def setUp(self):
        self.html=Path("docs/visual-atlas.html").read_text()
        import json
        self.films=json.loads(Path("report/videos.json").read_text())
        parser=Parser();parser.feed(self.html)
        self.available=parser.assets|{"ontogenesis-visual-poster-manifest.json"}
    def test_all_32_galleries_accounted_for(self):
        report=verify(self.html,self.films,self.available)
        self.assertEqual(report["generation_count"],32)
        self.assertTrue(report["g0032_native_spatial_edition"])
        self.assertEqual(report["visual_types"]["measured-plot"],1)
    def test_broken_media_asset_fails(self):
        missing=self.available-{"ontogenesis-0032-spatial.mp4"}
        with self.assertRaises(ValueError):verify(self.html,self.films,missing)
    def test_missing_generation_fails(self):
        with self.assertRaises(ValueError):
            verify(self.html.replace('data-title="g0027','data-title="g9999',1),
                   self.films,self.available)

if __name__=="__main__":unittest.main()
