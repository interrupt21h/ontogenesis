"""G0036 rendering keeps real measured feedback difference separate from art."""
import unittest
import numpy as np
from g0036_feedback_aurora import projection,observation,film_state,palette_plate


class FeedbackAuroraTests(unittest.TestCase):
    def test_native_z_max_projection(self):
        a=np.zeros((12,12,12),np.float32)
        a[2,5,7]=.3;a[10,5,7]=.9
        out=projection(a)
        self.assertEqual(out.shape,(12,12))
        self.assertAlmostEqual(float(out[5,7]),.9)
        self.assertEqual(int(np.count_nonzero(out)),1)

    def test_zero_source_difference_has_no_fabricated_delta(self):
        fields={}
        for arm in ("control","feedback"):
            for kind in ("v","w","m"):
                fields[f"{arm}_{kind}"]=np.zeros((11,12,12,12,12),np.float32)
        sample={"fields":fields}
        obs=observation(sample,10,7)
        self.assertTrue(all(not np.any(obs[f"delta_{kind}"])
                            for kind in ("v","w","m")))
        plate=palette_plate(obs,"delta",{"v":1.,"w":1.,"m":1.},
                            width=120,height=120)
        self.assertEqual(plate.size,(120,120))

    def test_real_intervention_is_difference_of_matched_states(self):
        fields={}
        for arm in ("control","feedback"):
            for kind in ("v","w","m"):
                fields[f"{arm}_{kind}"]=np.zeros((11,12,12,12,12),np.float32)
        fields["control_v"][10,4,8,2,3]=.25
        fields["feedback_v"][10,4,8,2,3]=.7
        obs=observation({"fields":fields},10,4)
        self.assertAlmostEqual(float(obs["delta_v"][2,3]),.45)
        self.assertEqual(int(np.count_nonzero(obs["delta_v"])),1)

    def test_discrete_recorded_time_and_bounded_camera(self):
        a=[film_state(i,48) for i in range(48)]
        self.assertEqual(a[-1][1:],(2,10,11))
        self.assertEqual(sorted({v[1] for v in a}),[0,1,2])
        self.assertTrue(all(0<=p[2]<11 and 0<=p[3]<12 for p in a))
        with self.assertRaises(ValueError):film_state(48,48)


if __name__=="__main__":
    unittest.main()
