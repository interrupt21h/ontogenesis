"""Regress the actual 4D feedback law and its matched-control invariants."""
import unittest
import numpy as np
from g0036_structural_feedback import feedback, measured


class StructuralFeedbackTests(unittest.TestCase):
    def test_divergence_free_on_four_axes(self):
        rng=np.random.default_rng(36)
        matrix=rng.uniform(0,.5,(8,)*4).astype(np.float32)
        v=rng.uniform(0,.7,(8,)*4).astype(np.float32)
        w=rng.uniform(0,.7,(8,)*4).astype(np.float32)
        state={"matrix":matrix,"species_v":v,"species_w":w}
        vectors=feedback(12,state)
        self.assertEqual(len(vectors),4)
        self.assertTrue(all(a.shape==(8,)*4 for a in vectors))
        self.assertTrue(any(float(np.abs(a).max())>1e-4 for a in vectors))
        divergence=sum(a-np.roll(a,1,axis=i) for i,a in enumerate(vectors))
        self.assertLess(float(np.abs(divergence).max()),3e-7)
        self.assertTrue(all(abs(float(a.sum(dtype=np.float64)))<1e-3
                            for a in vectors))

    def test_exact_zero_control_and_current_state_dependency(self):
        rng=np.random.default_rng(2)
        data={k:rng.uniform(0,.3,(8,)*4).astype(np.float32)
              for k in ("matrix","species_v","species_w")}
        disabled=feedback(0,data,gain=0)
        self.assertTrue(all(np.array_equal(a,np.zeros_like(a)) for a in disabled))
        enabled=feedback(0,data)
        changed={k:v.copy() for k,v in data.items()}
        changed["matrix"][2,3,4,5]+=.5
        current=feedback(1,changed)
        self.assertTrue(any(not np.array_equal(a,b)
                            for a,b in zip(enabled,current)))

    def test_true_periodic_contact_metric(self):
        shape=(8,)*4
        v=np.zeros(shape,np.float32);w=np.zeros_like(v)
        v[:4]=.3;w[4:]=.3
        result=measured(v,w,np.zeros_like(v),np.ones_like(v))
        self.assertEqual(result["exclusive_contacts"],2*8**3)
        self.assertEqual(result["joint_active"],0)
        self.assertEqual(result["v_active"],4*8**3)

    def test_reject_bad_gain_and_mismatched_dimension(self):
        shape=(8,)*4
        data={k:np.zeros(shape,np.float32)
              for k in ("matrix","species_v","species_w")}
        with self.assertRaises(ValueError):feedback(0,data,gain=-.1)
        with self.assertRaises(ValueError):feedback(0,data,gain=.09)
        data["matrix"]=np.zeros((8,8,8),np.float32)
        with self.assertRaises(ValueError):feedback(0,data)


if __name__=="__main__":
    unittest.main()
