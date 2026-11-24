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

    def test_contact_on_each_of_four_axes(self):
        # Each cut has two interfaces because all axes are periodic.
        for axis in range(4):
            with self.subTest(axis=axis):
                v=np.zeros((6,)*4,dtype=np.float32)
                w=np.zeros_like(v)
                m=np.zeros_like(v)
                v_indices=[slice(None)]*4
                w_indices=[slice(None)]*4
                v_indices[axis]=slice(0,3)
                w_indices[axis]=slice(3,6)
                v[tuple(v_indices)]=.5
                w[tuple(w_indices)]=.5
                x=metrics(v,w,m)
                self.assertEqual(x["four_dimensional_face_contacts"],2*6**3)
                self.assertEqual(x["both_active_cells"],0)
                self.assertAlmostEqual(x["contact_fraction_per_face"],(2*6**3)/(4*6**4))

    def test_wraparound_contact_without_internal_contact(self):
        # Two isolated active sites meet only across the periodic x boundary.
        v=np.zeros((5,)*4,dtype=np.float32)
        w=np.zeros_like(v)
        m=np.zeros_like(v)
        v[0,0,0,0]=.6
        w[4,0,0,0]=.6
        x=metrics(v,w,m)
        self.assertEqual(x["four_dimensional_face_contacts"],1)
        self.assertEqual(x["v_only_cells"],1)
        self.assertEqual(x["w_only_cells"],1)

    def test_strict_threshold_and_empty_grid(self):
        v=np.full((5,)*4,.1,dtype=np.float32)
        w=np.zeros_like(v)
        m=np.zeros_like(v)
        x=metrics(v,w,m)
        self.assertEqual(x["v_active_cells"],0)
        self.assertEqual(x["four_dimensional_face_contacts"],0)
        self.assertEqual(x["neither_active_cells"],5**4)
        self.assertAlmostEqual(x["continuous_shared_mass_ratio"],0.0)

    def test_mass_overlap_without_threshold_cooccupancy(self):
        v=np.full((5,)*4,.5,dtype=np.float32)
        w=np.full_like(v,.05)
        m=np.zeros_like(v)
        x=metrics(v,w,m)
        self.assertEqual(x["both_active_cells"],0)
        self.assertEqual(x["four_dimensional_face_contacts"],0)
        self.assertAlmostEqual(x["continuous_shared_mass_ratio"],.1,places=6)
if __name__=="__main__":unittest.main()
