"""Regression tests for release-wide cinematic coverage requirements."""
import unittest
from scripts.check_recent_cinema import EDITION_PAIRS,check


class CoverageTests(unittest.TestCase):
    def fixture(self):
        assets=[]
        for editions in EDITION_PAIRS.values():
            for base in editions:
                for ext,size in (("mp4",100_000),("png",10_000)):
                    name=base+"."+ext
                    assets.append({"name":name,"size":size,
                                   "browser_download_url":"https://example.invalid/"+name})
        return {"tag_name":"atlas-media","assets":assets}

    def test_every_recent_generation_has_two_published_film_and_poster_pairs(self):
        report=check(self.fixture())
        self.assertTrue(report["complete"])
        self.assertFalse(report["missing"])
        self.assertEqual(len(report["generations"]),8)

    def test_reject_missing_or_tiny_video(self):
        release=self.fixture()
        release["assets"][0]["size"]=12
        with self.assertRaisesRegex(ValueError,"Required cinematic"):
            check(release)
        report=check(release,require_all=False)
        self.assertFalse(report["complete"])
        self.assertEqual(len(report["missing"]),1)

    def test_reject_duplicate_assets(self):
        release=self.fixture()
        release["assets"].append(release["assets"][0].copy())
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            check(release)


if __name__=="__main__":
    unittest.main()
