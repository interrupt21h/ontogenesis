"""G0033 controls: exact 4D threshold and class-preserving shuffle tests."""
import unittest
import numpy as np
from g0033_robustness import categories, describe, permutation_reference
from g0033_aggregate import aggregate


class RobustnessTests(unittest.TestCase):
    def test_native_thresholds_and_periodic_contacts(self):
        v = np.zeros((8,) * 4, dtype=np.float32)
        w = np.zeros_like(v)
        v[..., :4] = .075
        w[..., 4:] = .15
        m = np.zeros_like(v)
        low = describe(v, w, m, .05)
        middle = describe(v, w, m, .10)
        high = describe(v, w, m, .20)
        self.assertEqual(low["four_dimensional_face_contacts"], 2 * 8**3)
        self.assertEqual(middle["four_dimensional_face_contacts"], 0)
        self.assertEqual(high["w_active_cells"], 0)
        self.assertEqual(low["both_active_cells"], 0)

    def test_null_model_retains_joint_class_counts(self):
        v = np.zeros((8,) * 4, dtype=np.float32)
        w = np.zeros_like(v)
        v[..., :4] = .4
        w[..., 4:] = .4
        original = categories(v, w, .1)
        self.assertEqual(set(np.unique(original)), {1, 2})
        a = permutation_reference(v, w, .1, seed=42, repetitions=4)
        b = permutation_reference(v, w, .1, seed=42, repetitions=4)
        self.assertEqual(a, b)
        self.assertEqual(a["permutations"], 4)
        self.assertGreater(a["mean_contact_faces"], 0)

    def test_aggregate_rejects_partial_cohort(self):
        with self.assertRaises(ValueError):
            aggregate([])


if __name__ == "__main__":
    unittest.main()
