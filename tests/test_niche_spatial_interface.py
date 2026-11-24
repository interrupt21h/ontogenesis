"""Verify four-dimensional face contacts without any image approximations."""
import unittest
import numpy as np
from niche_spatial_interface import metrics
class NativeInterface(unittest.TestCase):
    def test_known_four_dimensional_partition(self):
        v=np.zeros((8,8,8,8),dtype=np.float32)
        w=np.zeros_like(v);m=np.zeros_like(v)
        v[:,:,:,:4]=.6
        w[:,:,:,4:]=.6
        x=metrics(v,w,m)
        self.assertEqual(x["v_only_cells"],2048)
        self.assertEqual(x["w_only_cells"],2048)
        self.assertEqual(x["both_active_cells"],0)
        self.assertEqual(x["four_dimensional_face_contacts"],2*8*8*8)
    def test_cooccupancy_and_mutual_exclusion_are_distinct(self):
        v=np.full((8,8,8,8),.3,dtype=np.float32)
        w=np.full_like(v,.3);m=np.zeros_like(v)
        x=metrics(v,w,m)
        self.assertEqual(x["both_active_cells"],8**4)
        self.assertEqual(x["four_dimensional_face_contacts"],0)
        self.assertAlmostEqual(x["continuous_shared_mass_ratio"],1.0)
if __name__=="__main__":unittest.main()
