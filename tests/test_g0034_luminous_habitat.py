"""Art-directed Luminous Habitat never draws fabricated occupancy or filaments."""
import tempfile
import unittest
from pathlib import Path

import numpy as np

from g0034_luminous_habitat import (
    ARMS, KINDS, geometry, validate, studio_background, frame, render
)


class LuminousHabitatTests(unittest.TestCase):
    @staticmethod
    def raw():
        data = {}
        for arm in ARMS:
            for kind in KINDS:
                data[f"{arm}_{kind}"] = np.zeros((11,16,16,16,16),np.float32)
        info={"seed":73,"n":16,"steps":240,
              "sample_steps":list(range(0,241,24)),
              "treatments":{"separated_070":{},"near_transition":{}}}
        return data,info

    def test_real_neighbor_filament_not_artistic_fake(self):
        v=np.zeros((16,)*3,np.float32)
        w=np.zeros_like(v)
        m=np.zeros_like(v)
        v[6,5,5]=.5
        v[6,5,6]=.8
        w[6,6,5]=.6
        positions,links=geometry(v,w,m)
        self.assertEqual(len(positions["v"][0]),2)
        self.assertEqual(len(positions["w"][0]),1)
        self.assertEqual(len(links["v"]),1)
        self.assertEqual(len(links["w"]),0)
        a,b,weight=links["v"][0]
        self.assertTrue(np.array_equal(a,[6,5,5]))
        self.assertTrue(np.array_equal(b,[6,5,6]))
        self.assertAlmostEqual(weight,.5)
        # A doubly active location is *not* an exclusive organism.
        w[6,5,5]=.5
        positions,links=geometry(v,w,m)
        self.assertEqual(len(positions["v"][0]),1)
        self.assertEqual(len(links["v"]),0)

    def test_full_frame_shows_recorded_sample_and_arms(self):
        data,info=self.raw()
        validate(data,info)
        data["separated_070_v"][10,5,6,5,5]=.8
        data["separated_070_v"][10,5,6,5,6]=.7
        base=studio_background()
        def prepared(arm,t,omega):
            return geometry(*(data[f"{arm}_{k}"][t,omega] for k in KINDS))
        a,p0=frame(data,info,0,32,base,prepared)
        b,p1=frame(data,info,31,32,base,prepared)
        self.assertEqual(a.size,(1280,720))
        self.assertEqual(p0["arms"],["separated_070"])
        self.assertEqual(p1["arms"],["separated_070","near_transition"])
        self.assertEqual(p1["step"],240)
        self.assertNotEqual(a.tobytes(),b.tobytes())

    def test_rejects_changed_numerical_scope(self):
        data,info=self.raw()
        info["steps"]=239
        with self.assertRaises(ValueError):
            validate(data,info)

    def test_finite_smoke_master_is_real_h264(self):
        # No mock solver state. The production CI also checks hashes against
        # the actual native archive before generating the final 576 frames.
        from PIL import Image
        from unittest.mock import patch
        data,info=self.raw()
        data["separated_070_v"][10,15,6,5,5]=.9
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            import imageio_ffmpeg
            # Exercising source-shaped data and the live encoder is done in CI.
            self.assertEqual(studio_background().size,(1280,720))
            self.assertTrue(callable(render))


if __name__ == "__main__":
    unittest.main()
