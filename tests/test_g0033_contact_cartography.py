"""Regression tests for authentic four-axis contact cartography."""
import unittest
import numpy as np
from PIL import ImageChops

from g0033_contact_cartography import contact_masks, tile, frame


class ContactCartographyTests(unittest.TestCase):
    def test_periodic_interface_along_each_native_axis(self):
        for axis in range(4):
            with self.subTest(axis=axis):
                v = np.zeros((16,) * 4, np.float32)
                w = np.zeros_like(v)
                a = [slice(None)] * 4
                b = [slice(None)] * 4
                a[axis], b[axis] = slice(0, 8), slice(8, 16)
                v[tuple(a)] = .4
                w[tuple(b)] = .4
                mask, faces, by_axis = contact_masks(v, w)
                self.assertEqual(faces, 2 * 16**3)
                self.assertEqual(by_axis[axis], faces)
                self.assertEqual(sum(by_axis), faces)
                self.assertEqual(np.count_nonzero(mask), 4 * 16**3)
                for boundary in (0, 7, 8, 15):
                    index = [slice(None)] * 4
                    index[axis] = boundary
                    self.assertTrue(mask[tuple(index)].all())
                for interior in (1, 4, 10, 14):
                    index = [slice(None)] * 4
                    index[axis] = interior
                    self.assertFalse(mask[tuple(index)].any())

    def test_overlap_is_not_exclusive_contact(self):
        v = np.ones((16,) * 4, np.float32) * .3
        w = np.ones_like(v) * .3
        mask, faces, axes = contact_masks(v, w)
        self.assertEqual(faces, 0)
        self.assertFalse(mask.any())
        self.assertEqual(axes, [0, 0, 0, 0])

    def test_tile_highlights_real_contact_pixels(self):
        v = np.zeros((16,) * 4, np.float32)
        w = np.zeros_like(v)
        m = np.zeros_like(v)
        v[..., :8] = .5
        w[..., 8:] = .5
        boundaries, faces, _ = contact_masks(v, w)
        self.assertEqual(faces, 2 * 16**3)
        picture = tile(v, w, m, boundaries, 0)
        self.assertEqual(picture.size, (16, 16))
        self.assertEqual(picture.getpixel((7, 3)), (255, 247, 211))
        self.assertNotEqual(picture.getpixel((4, 3)), (255, 247, 211))

    def test_display_animation_does_not_require_intermediate_states(self):
        blank = np.zeros((16,) * 4, np.float32)
        contact = np.zeros_like(blank, dtype=bool)
        snapshots = [{"step": t, "tiles": [
            tile(blank, blank, blank, contact, i).resize((83,83))
            for i in range(16)],
            "faces": 0, "cells_v": 0, "cells_w": 0}
            for t in (0, 24)]
        views = [{"seed": seed, "snapshots": snapshots} for seed in (42, 73)]
        a = frame(views, 0, 16, [0, 24])
        b = frame(views, 15, 16, [0, 24])
        self.assertEqual(a.size, (1280, 720))
        self.assertIsNotNone(ImageChops.difference(a, b).getbbox())


if __name__ == "__main__":
    unittest.main()
