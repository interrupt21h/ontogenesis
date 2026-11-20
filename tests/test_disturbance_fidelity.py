"""Tests for G0028 recorded four-dimensional fidelity and ray integration."""
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import consolidation
from disturbance_cinematic_fidelity import CHANNELS, create_fidelity_archive, digest_file
from disturbance_fidelity_render import read_fidelity_archive, observed_volume, volumetric_ray, compose


class FidelityTests(unittest.TestCase):
    def test_observer_numerical_invariance(self):
        seen=set()
        def observer(step, fields):
            self.assertEqual(set(fields), set(CHANNELS))
            self.assertTrue(all(not v.flags.writeable for v in fields.values()))
            seen.add(step)
        reference=consolidation.run(seed=42,n=8,steps=24,observe=False)
        viewed=consolidation.run(seed=42,n=8,steps=24,observe=False,
                                  cinematic_observer=observer,
                                  cinematic_steps={0,12,24})
        self.assertEqual(reference["hashes"],viewed["hashes"])
        self.assertEqual(seen,{0,12,24})

    def test_archive_and_ray(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            data=folder/"source.npz"
            metadata=folder/"source.json"
            m=create_fidelity_archive(data,metadata,n=8,steps=24,
                                      shock_step=16,sample_every=4,
                                      omega_planes=4,max_raw_mib=30)
            self.assertEqual(m["recording"]["channel_order"],list(CHANNELS))
            self.assertEqual(m["recording"]["omega_indices"],[0,2,4,6])
            self.assertEqual(m["recording"]["dense_dtype"],"float32")
            self.assertGreaterEqual(m["sample_count"],11)
            self.assertEqual(digest_file(data),m["archive"]["sha256"])
            with np.load(data,allow_pickle=False) as archive:
                self.assertEqual(archive["states"].dtype,np.float16)
                self.assertEqual(archive["states"].shape[1:],(4,7,8,8,8))
                self.assertEqual(archive["dense_states"].dtype,np.float32)
                self.assertEqual(archive["dense_states"].shape[1:],(7,8,8,8,8))
                self.assertIn(16,archive["dense_steps"].tolist())
                self.assertIn(15,archive["steps"].tolist())
            states,steps,omega,info=read_fidelity_archive(data,metadata)
            field,details=observed_volume(states,steps,omega,12.0,1.5)
            self.assertEqual(field.shape,(7,8,8,8))
            self.assertEqual(details["omega_lower"],2)
            self.assertTrue(np.isfinite(field).all())
            image=volumetric_ray(field,info,.25,rays=24)
            self.assertEqual(image.size,(24,24))
            poster=compose(field,info,12,1.5,640,360,24)
            self.assertEqual(poster.size,(640,360))
            self.assertGreater(len(set(poster.getdata())),20)
            corrupt=json.loads(metadata.read_text())
            corrupt["archive"]["sha256"]="0"*64
            metadata.write_text(json.dumps(corrupt))
            with self.assertRaisesRegex(ValueError,"SHA-256"):
                read_fidelity_archive(data,metadata)

    def test_archive_memory_budget(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)
            with self.assertRaisesRegex(ValueError,"archive budget"):
                create_fidelity_archive(path/"too-big.npz",path/"too-big.json",
                                        n=24,steps=4800,shock_step=2600,
                                        sample_every=4,omega_planes=4,max_raw_mib=2)


if __name__=="__main__":
    unittest.main()
