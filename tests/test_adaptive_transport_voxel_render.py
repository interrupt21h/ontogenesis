"""Test G0028-style film rendering against genuine low-cost G0029 fields."""
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from adaptive_transport import run_pair
from adaptive_transport_voxel_render import (
    arranged_fields, chapter, cinematic_frame, render,
)
from adaptive_transport_render import at, load


class VoxelEdition(unittest.TestCase):
    def test_channel_mapping(self):
        source = np.broadcast_to(np.arange(5, dtype=np.float32)[:, None, None, None],
                                 (5, 8, 8, 8)).copy()
        remapped = arranged_fields(source)
        np.testing.assert_array_equal(remapped[:, 0, 0, 0], [0, 1, 2, 4, 3])
        self.assertEqual(chapter(.5), 'III  /  MEMORY AND TRANSPORT')
        with self.assertRaises(ValueError):
            arranged_fields(source[:4])

    def test_native_sample_renders_without_new_simulation(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            fields = directory / 'observations.npz'
            meta = directory / 'measurements.json'
            run_pair(fields, meta, n=8, steps=12, stride=3, omega_planes=2)
            states, times, omega, info = load(fields, meta)
            sample = at(states, times, omega, 6., .5)
            frame = cinematic_frame(sample, info, step=6., width=640, height=360)
            self.assertIsInstance(frame, Image.Image)
            self.assertEqual(frame.size, (640, 360))
            self.assertGreater(float(np.asarray(frame).std()), 2.0)

    def test_invalid_image_settings(self):
        with self.assertRaises(ValueError):
            render(Path('/absent'), Path('/absent'), Path('/absent'), Path('/absent'),
                   width=641)


if __name__ == '__main__':
    unittest.main()
