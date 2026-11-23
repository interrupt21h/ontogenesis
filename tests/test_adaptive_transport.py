import tempfile
import unittest
from pathlib import Path
import numpy as np
import consolidation
from adaptive_transport import AdaptiveCurl,run_pair
from adaptive_transport_render import load,at,ray

class G0029(unittest.TestCase):
    def test_discrete_curl(self):
        n=8
        c=AdaptiveCurl(n)
        coord=np.indices((n,)*4,dtype=np.float32)
        m=.2+.2*np.sin(coord[0]*np.pi/4)
        zero=np.zeros_like(m)
        vel=c(0,{"energy":np.ones_like(m),"matrix":m,
                 "species_v":zero,"species_w":zero})
        self.assertEqual(len(vel),4)
        self.assertGreater(c.rms,0.)
        self.assertLess(c.divergence,1e-5)
    def test_default_and_zero_gain_equivalence(self):
        ref=consolidation.run(n=8,steps=12,observe=False)
        alt=consolidation.run(n=8,steps=12,observe=False,
                              velocity_feedback=AdaptiveCurl(8,gain=0.))
        self.assertEqual(ref["hashes"],alt["hashes"])
        self.assertEqual(ref["final"],alt["final"])
    def test_archive_integrity(self):
        with tempfile.TemporaryDirectory() as t:
            f=Path(t)/"fields.npz";m=Path(t)/"metadata.json"
            data=run_pair(f,m,n=8,steps=12,stride=3,omega_planes=2)
            self.assertEqual(data["hashes"]["control"]["0"],data["hashes"]["adaptive"]["0"])
            self.assertEqual(len(data["paired"]),data["sample_count"])
            states,times,omega,meta=load(f,m)
            self.assertEqual(states.shape[2],5)
            vol=at(states,times,omega,6.,.5)
            self.assertTrue(np.isfinite(vol).all())
            self.assertEqual(ray(vol,meta,.4,24).size,(24,24))
if __name__=="__main__": unittest.main()
