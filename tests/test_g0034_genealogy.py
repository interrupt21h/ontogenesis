"""G0034 deterministic 4D periodic component and genealogy invariants."""
import tempfile
import unittest
from pathlib import Path

import numpy as np

from g0034_genealogy import periodic_components, overlap_edges, summarize


class TopologyTests(unittest.TestCase):
    def test_one_component_across_each_periodic_axis(self):
        for axis in range(4):
            with self.subTest(axis=axis):
                mask = np.zeros((8,)*4, bool)
                first = [slice(2, 4)]*4
                last = [slice(2, 4)]*4
                first[axis] = 0
                last[axis] = 7
                mask[tuple(first)] = True
                mask[tuple(last)] = True
                labels, sizes = periodic_components(mask)
                self.assertEqual(len(sizes)-1, 1)
                self.assertEqual(sizes[1], 16)
                self.assertEqual(int(labels.max()), 1)
                self.assertEqual(int(sizes[1:].sum()), int(mask.sum()))

    def test_diagonal_contact_is_not_a_face(self):
        mask = np.zeros((8,)*4, bool)
        mask[1, 1, 1, 1] = True
        mask[2, 2, 1, 1] = True
        labels, sizes = periodic_components(mask)
        self.assertEqual(len(sizes)-1, 2)
        self.assertEqual(sorted(sizes[1:]), [1, 1])

    def test_empty_and_filled_domain(self):
        empty, ecounts = periodic_components(np.zeros((8,)*4, bool))
        self.assertEqual(int(empty.max()), 0)
        self.assertEqual(ecounts.tolist(), [0])
        full, fcounts = periodic_components(np.ones((8,)*4, bool))
        self.assertEqual(int(full.max()), 1)
        self.assertEqual(int(fcounts[1]), 8**4)

    def test_overlap_split_and_merge_count(self):
        old = np.zeros((8,)*4, np.int32)
        now = np.zeros_like(old)
        old[1,1,1,1] = old[1,1,1,2] = 1
        now[1,1,1,1] = 1
        now[1,1,1,2] = 2
        self.assertEqual(overlap_edges(old, now),
                         [{"from":1,"to":1,"sites":1},
                          {"from":1,"to":2,"sites":1}])
        self.assertEqual(overlap_edges(now, old),
                         [{"from":1,"to":1,"sites":1},
                          {"from":2,"to":1,"sites":1}])

    def test_full_numerical_accounting_and_timeline(self):
        a = np.zeros((8,)*4, np.float32)
        b = np.zeros_like(a)
        a[1,1,1,1] = .4
        a[1,1,1,2] = .4
        # One component disconnects by losing its middle voxel.
        c = a.copy();c[1,1,1,2] = 0
        # Add a new independent region, and then remove everything.
        d = c.copy();d[5,5,5,5] = .4
        records = summarize([(a,b),(c,b),(d,b),(b,b)],min_display_sites=1)
        observed = records["v_only"]
        self.assertEqual([r["component_count"] for r in observed], [1,1,2,0])
        self.assertEqual([r["active_sites"] for r in observed], [2,1,2,0])
        self.assertEqual(observed[2]["births"], 1)
        self.assertEqual(observed[3]["deaths"], 2)
        self.assertEqual([r["component_count"] for r in records["w_only"]], [0]*4)

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            periodic_components(np.zeros((8,8,8), bool))
        with self.assertRaises(ValueError):
            overlap_edges(np.zeros((8,)*4), np.zeros((7,)*4))
        with self.assertRaises(ValueError):
            summarize([],min_display_sites=0)


if __name__ == "__main__":
    unittest.main()
