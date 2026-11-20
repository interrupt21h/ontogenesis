"""G0028 cinematic numerical integrity, archive and rendering smoke checks."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

import consolidation
from disturbance_cinematic import create_archive
from disturbance_cinematic_render import draw_movie_frame, read_archive


class CinematicTest(unittest.TestCase):
    def test_observer_does_not_change_numerical_integration(self):
        observed_steps = set()
        def inspect(step, fields):
            self.assertEqual(set(fields),
                             {"energy", "matrix", "species_v", "species_w", "pulse",
                              "trait", "recovery"})
            self.assertTrue(all(not array.flags.writeable for array in fields.values()))
            self.assertTrue(all(array.shape == (8, 8, 8, 8) for array in fields.values()))
            observed_steps.add(step)
        without = consolidation.run(seed=42, n=8, steps=24, stride=12,
                                    observe=False)
        with_observer = consolidation.run(
            seed=42, n=8, steps=24, stride=12, observe=False,
            cinematic_observer=inspect, cinematic_steps={0, 12, 24})
        self.assertEqual(without["hashes"], with_observer["hashes"])
        self.assertEqual(observed_steps, {0, 12, 24})

    def test_archive_contract_and_camera(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            data=folder/"sample.npz"
            manifest=folder/"sample.json"
            info=create_archive(data,manifest,n=8,steps=18,seed=42,
                                shock_step=10,sample_every=4)
            states,steps,meta=read_archive(data,manifest)
            self.assertEqual(states.shape[1:], (5,8,8,8))
            self.assertEqual(steps[0],0)
            self.assertEqual(steps[-1],18)
            self.assertIn(10,steps.tolist())
            self.assertIn(9,steps.tolist())
            self.assertEqual(meta["recording"]["dtype"],"float16")
            self.assertFalse(meta["recording"]["restart_checkpoint"])
            self.assertEqual(len(meta["frame_metrics"]),len(steps))
            image=draw_movie_frame(states[0].astype(np.float32),meta,
                                   step=0,frame_number=0,total_frames=72,
                                   width=640,height=360,caption="Test scene")
            self.assertEqual(image.size,(640,360))
            self.assertGreater(len(set(image.getdata())),20)
            altered=json.loads(manifest.read_text())
            altered["archive"]["sha256"]="0"*64
            manifest.write_text(json.dumps(altered))
            with self.assertRaisesRegex(ValueError,"SHA-256"):
                read_archive(data,manifest)


if __name__=="__main__":
    unittest.main()
