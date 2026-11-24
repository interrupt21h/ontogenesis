"""G0032 native 4D field recording and spatial film integrity tests."""
import tempfile
import unittest
from pathlib import Path
import numpy as np
from PIL import ImageChops
from niche_spatial_archive import capture,ARMS
from niche_spatial_render import load_fields,image_at,render

class G0032NativeFieldTests(unittest.TestCase):
    def test_native_snapshot_and_actual_small_film(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            p=root/"fields.npz";meta=root/"fields.json"
            info=capture(p,meta,n=8,steps=48,stride=12,seed=73)
            arrays,source,digest=load_fields(p,meta)
            self.assertEqual(source["sample_steps"],[0,12,24,36,48])
            for arm in ARMS:
                self.assertEqual(arrays[f"{arm}_v"].shape,(5,8,8,8,8))
                self.assertEqual(arrays[f"{arm}_v"].dtype,np.float32)
                self.assertTrue(np.isfinite(arrays[f"{arm}_w"]).all())
            a=image_at(arrays,source,0,2)
            b=image_at(arrays,source,1.5,2)
            self.assertEqual(a.size,(1280,720))
            self.assertIsNotNone(ImageChops.difference(a,b).getbbox())
            result=render(p,meta,root/"movie.mp4",root/"poster.png",seconds=2,fps=8)
            self.assertEqual(result["frames"],16)
            self.assertFalse(result["interpolated_numerical_states"])
            self.assertTrue(result["featured_G0028_preserved"])
            self.assertGreater((root/"poster.png").stat().st_size,4096)

    def test_corrupt_archive_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            p=root/"fields.npz";meta=root/"fields.json"
            capture(p,meta,n=8,steps=48,stride=12,seed=73)
            with p.open("ab") as f:f.write(b"extra bytes")
            with self.assertRaises(ValueError):
                load_fields(p,meta)

    def test_budget_bounds(self):
        with self.assertRaises(ValueError):
            capture("bad.npz","bad.json",n=24)

if __name__=="__main__":
    unittest.main()
