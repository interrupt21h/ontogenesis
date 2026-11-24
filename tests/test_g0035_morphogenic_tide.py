"""G0035: native morphology must remain measurable under artistic resampling."""
import unittest
import numpy as np
from PIL import ImageChops

from g0035_morphogenic_tide import (
    projection,native_contours,artistic_field,make_plate,scene_state,
    state_at,art_frame,evidence_frame,gradient_background,validate,ARMS
)


class MorphogenicTideTests(unittest.TestCase):
    @staticmethod
    def fixture():
        data={f"{arm}_{k}":np.zeros((11,16,16,16,16),np.float32)
              for arm in ARMS for k in ("v","w","m")}
        info={"seed":73,"n":16,"steps":240,
              "sample_steps":list(range(0,241,24)),
              "treatments":{a:{} for a in ARMS}}
        data["separated_070_v"][10,0,3,5,6]=.65
        data["separated_070_v"][10,0,10,5,6]=.9
        data["separated_070_w"][10,0,4,7,9]=.6
        data["near_transition_w"][10,0,4,7,9]=.7
        return data,info

    def test_z_projection_only_uses_recorded_fields(self):
        v=np.zeros((16,)*3,np.float32);w=v.copy();m=v.copy()
        v[1,5,6]=.3;v[11,5,6]=.9
        w[2,4,7]=.7
        p=projection(v,w,m)
        self.assertEqual(p["v"].shape,(16,16))
        self.assertAlmostEqual(float(p["v"][5,6]),.9)
        self.assertAlmostEqual(float(p["w"][4,7]),.7)
        self.assertEqual(p["native_v_active"],2)
        self.assertEqual(p["native_w_active"],1)
        self.assertEqual(p["native_joint"],0)
        bands=native_contours(p["v"])
        self.assertEqual(bands.shape,(4,16,16))
        self.assertTrue((bands[:,5,6]==1).all())
        self.assertEqual(int(bands[:,0,0].sum()),0)

    def test_no_concentration_in_empty_native_plane(self):
        zero=np.zeros((16,16),np.float32)
        interpolated=artistic_field(zero,(121,121))
        self.assertEqual(float(interpolated.max()),0.)
        p={k:zero.copy() for k in ("v","w","m")}
        plate=make_plate(p,size=(160,160))
        self.assertEqual(plate.size,(160,160))
        # Artistic background exists, but an empty field creates no
        # numerical contour rings.
        self.assertTrue(np.isfinite(interpolated).all())

    def test_art_and_evidence_use_exact_same_source(self):
        data,info=self.fixture()
        validate(data,info)
        base=gradient_background()
        def numerical(a,t,o):return scene_state(data,a,t,o)
        def tile(a,t,o):return make_plate(numerical(a,t,o),(120,120))
        a,am=art_frame(data,info,0,16,base,tile)
        b,bm=art_frame(data,info,15,16,base,tile)
        c,cm=evidence_frame(data,info,15,16,base,numerical)
        self.assertEqual(a.size,(1280,720))
        self.assertEqual(b.size,(1280,720))
        self.assertEqual(c.size,(1280,720))
        self.assertEqual(am["arms"],["separated_070"])
        self.assertEqual(bm["arms"],list(ARMS))
        self.assertEqual(cm["step"],240)
        self.assertIsNotNone(ImageChops.difference(a,b).getbbox())

    def test_sample_clocks_are_discrete(self):
        observations=[state_at(i,32) for i in range(32)]
        self.assertTrue(all(0<=t<=10 and 0<=omega<=15
                            for _,_,t,omega in observations))
        self.assertEqual(observations[-1][1:],(2,10,15))
        self.assertEqual(sorted({a for _,a,_,_ in observations}),[0,1,2])

    def test_reject_changed_source_scope(self):
        data,info=self.fixture()
        info["steps"]=480
        with self.assertRaises(ValueError):validate(data,info)
        with self.assertRaises(ValueError):
            projection(np.zeros((15,16,16)),np.zeros((15,16,16)),
                       np.zeros((15,16,16)))


if __name__=="__main__":
    unittest.main()
