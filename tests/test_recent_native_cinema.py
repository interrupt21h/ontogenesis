"""Small actual numerical field captures and native video regression tests."""
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import ImageChops

from recent_native_archive import capture
from recent_native_cinema import frame, load, render


class RecentCinematicTests(unittest.TestCase):
    def test_real_four_dimensional_samples_and_smoke_movies(self):
        for gen in ("0030", "0031"):
            with self.subTest(gen=gen), tempfile.TemporaryDirectory() as d:
                root = Path(d)
                archive, meta = root / "fields.npz", root / "fields.json"
                info = capture(gen, archive, meta, n=8, steps=48, stride=12)
                self.assertEqual(info["sample_steps"], [0, 12, 24, 36, 48])
                fields, source, digest = load(archive, meta)
                for arm in source["arms"]:
                    for channel in ("v", "w", "m"):
                        self.assertEqual(fields[f"{arm}_{channel}"].shape,
                                         (5, 8, 8, 8, 8))
                        self.assertEqual(fields[f"{arm}_{channel}"].dtype, np.float32)
                a = frame(fields, source, 0, 16)
                b = frame(fields, source, 15, 16)
                self.assertIsNotNone(ImageChops.difference(a, b).getbbox())
                result = render(archive, meta, root / "movie.mp4",
                                root / "poster.png", seconds=2, fps=8)
                self.assertEqual(result["frames"], 16)
                self.assertFalse(result["temporal_interpolation"])
                self.assertTrue(result["camera_motion_presentation_only"])
                self.assertGreater((root / "movie.mp4").stat().st_size, 8192)

    def test_corrupted_numerical_archive_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            archive, meta = root / "fields.npz", root / "fields.json"
            capture("0031", archive, meta, n=8, steps=48, stride=12)
            with archive.open("ab") as f:
                f.write(b"modified")
            with self.assertRaises(ValueError):
                load(archive, meta)

    def test_capture_budget(self):
        with self.assertRaises(ValueError):
            capture("0031", "bad.npz", "bad.json", n=24)


if __name__ == "__main__":
    unittest.main()
