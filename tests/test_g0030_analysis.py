"""G0030 archived-trajectory analysis regression tests; no simulation required."""
import unittest
from scripts.analyze_g0030 import ARMS,METRICS,analyze,loss_window,time_average,markdown

def row(t,v,w):
    d={key:0. for key in METRICS}
    d.update(step=t,v_active=v,w_active=w,coexistence=min(v,w),
             energy_mean=.9,genotype_entropy_bits=2.)
    return d

def sample():
    times=[0,5,10,11,15,20]
    vs=(.2,.11,.02,0.,0.,0.)
    arr=[row(t,v,.4+.01*i) for i,(t,v) in enumerate(zip(times,vs))]
    observations={arm:[dict(a) for a in arr] for arm in ARMS}
    for r in observations["both"]:
        r["w_active"]+=.05
    return {"generation":"0030","n":8,"steps":20,"season_switch":10,
            "source_sha":"test","seeds":[42],"times":times,
            "observations":{"42":observations}}

class G0030Analysis(unittest.TestCase):
    def test_loss_window(self):
        rows=sample()["observations"]["42"]["both"]
        self.assertEqual(loss_window(rows,"v_active"),
                         {"ever_above_threshold":True,
                          "last_active_sample":10,
                          "first_persistently_inactive_sample":11})
        self.assertIsNone(loss_window([row(0,.1,0),row(5,.2,0)],
                                      "v_active")["first_persistently_inactive_sample"])
        self.assertFalse(loss_window([row(0,0,0),row(5,0,0)],
                                     "v_active")["ever_above_threshold"])

    def test_trapezoids(self):
        self.assertAlmostEqual(time_average([row(0,0,0),row(10,1,0)],"v_active"),.5)
        with self.assertRaises(ValueError):
            time_average([row(0,0,0)],"v_active")

    def test_synthetic_archive(self):
        a=analyze(sample())
        self.assertTrue(a["all_endpoints_v_inactive_by_threshold"])
        self.assertTrue(a["all_endpoints_cooccupancy_inactive_by_threshold"])
        self.assertAlmostEqual(a["analysis"]["42"]["both"]
            ["w_endpoint_delta_vs_neither_percentage_points"],5)
        self.assertIn("First later persistently inactive sample",markdown(a))
        self.assertIn("11 |",markdown(a))

    def test_unmatched_timeline_rejected(self):
        x=sample()
        x["observations"]["42"]["both"].pop()
        with self.assertRaisesRegex(ValueError,"Unmatched observation"):
            analyze(x)

    def test_wrong_generation_rejected(self):
        x=sample()
        x["generation"]="0029"
        with self.assertRaisesRegex(ValueError,"not a G0030"):
            analyze(x)

if __name__=="__main__":
    unittest.main()
