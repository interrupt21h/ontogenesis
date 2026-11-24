"""G0037 cinematic must render actual sampled states, not invented data."""
import unittest
import numpy as np
from g0037_memory_strata import projected,read_clock,SEEDS,ARMS


class MemoryStrataTests(unittest.TestCase):
    def test_actual_native_omega_projection(self):
        shape=(6,12,12,12,12)
        fields={f"{arm}_{k}":np.zeros(shape,np.float32)
                for arm in ARMS for k in ("v","w","m")}
        fields["high_m"][3,4,1,7,8]=.6
        fields["high_m"][3,4,10,7,8]=.9
        p=projected({"fields":fields},"high",3,4)
        self.assertEqual(p["m"].shape,(12,12))
        self.assertAlmostEqual(float(p["m"][7,8]),.9)
        self.assertEqual(int(np.count_nonzero(p["m"])),1)

    def test_discrete_states_and_act_structure(self):
        states=[read_clock(i,48) for i in range(48)]
        self.assertEqual(states[0][1:],(0,0,0))
        self.assertEqual(states[-1][1:],(2,5,11))
        self.assertEqual({x[1] for x in states},{0,1,2})
        self.assertTrue(all(0<=x[2]<6 and 0<=x[3]<12 for x in states))

    def test_reject_unrecorded_coordinates(self):
        with self.assertRaises(ValueError):read_clock(48,48)
        with self.assertRaises(ValueError):read_clock(0,1)

    def test_distinct_controls(self):
        self.assertEqual(SEEDS,(42,73))
        self.assertEqual(ARMS,("control","low","high"))


if __name__=="__main__":
    unittest.main()
