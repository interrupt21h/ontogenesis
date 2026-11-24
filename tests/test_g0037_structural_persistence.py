"""G0037 periodic native overlap accounting and matched 4D solver controls."""
import unittest
import numpy as np
from g0037_structural_persistence import persistence,GAINS,TIMES,THRESHOLD


class StructuralPersistenceTests(unittest.TestCase):
    def test_exact_four_dimensional_overlap(self):
        a=np.zeros((8,)*4,np.float32);b=a.copy()
        a[0,1,2,3]=.2;a[7,1,2,3]=.2
        b[7,1,2,3]=.3;b[4,5,6,7]=.3
        observed=persistence(a,b)
        self.assertEqual(observed["intersection"],1)
        self.assertEqual(observed["union"],3)
        self.assertAlmostEqual(observed["jaccard"],1/3)
        self.assertFalse(observed["both_empty"])

    def test_both_empty_is_explicitly_undefined(self):
        z=np.zeros((8,)*4,np.float32)
        result=persistence(z,z)
        self.assertTrue(result["both_empty"])
        self.assertIsNone(result["jaccard"])
        self.assertEqual(result["union"],0)

    def test_exact_strict_cutoff_and_identical_masks(self):
        a=np.zeros((8,)*4,np.float32)
        a[1,2,3,4]=THRESHOLD
        a[1,2,3,5]=THRESHOLD+.00001
        result=persistence(a,a)
        self.assertEqual(result["intersection"],1)
        self.assertEqual(result["union"],1)
        self.assertEqual(result["jaccard"],1.)

    def test_invalid_shapes(self):
        a=np.zeros((8,)*4,np.float32)
        with self.assertRaises(ValueError):persistence(a,np.zeros((7,)*4))
        with self.assertRaises(ValueError):persistence(a,np.zeros((8,)*3))

    def test_protocol_has_matched_control_and_bounded_arms(self):
        self.assertEqual(GAINS,{"control":0.,"low":.0175,"high":.07})
        self.assertEqual(TIMES,(0,24,48,72,96,120))


if __name__=="__main__":
    unittest.main()
