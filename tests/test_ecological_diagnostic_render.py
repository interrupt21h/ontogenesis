"""Test the G0030 render semantics without rerunning any ecological solver."""
import unittest
from PIL import ImageChops
from ecological_diagnostic_render import validate,draw_frame


def fixture(end,arms):
    times=list(range(0,end+1,end//30))
    times=sorted(set(times)|{end})
    rows=lambda phase:[{"step":t,
                         "v_active":max(0,.09*(1-t/90)),
                         "w_active":min(1,.02+t/end*.6+phase*.03)}
                        for t in times]
    return {"generation":"0030","steps":end,"n":16,"seeds":[42,73],
            "times":times,"observations":{
                str(seed):{arm:rows(i) for i,arm in enumerate(arms)}
                for seed in (42,73)}}


class Diagnostic(unittest.TestCase):
    def setUp(self):
        self.pilot=fixture(1200,("neither","w_to_v_only","v_to_w_only","both"))
        self.pilot["season_switch"]=600
        self.viability=fixture(180,("unchanged","invert_12","invert_24","invert_48"))
        self.viability["cases"]={"unchanged":None,"invert_12":12,
                                  "invert_24":24,"invert_48":48}

    def test_inputs(self):
        validate(self.pilot,self.viability)
        self.pilot["observations"]["42"]["neither"][0]["w_active"]=float("nan")
        with self.assertRaises(ValueError):
            validate(self.pilot,self.viability)

    def test_time_series_different_frames(self):
        a=draw_frame(self.pilot,self.viability,1,20)
        b=draw_frame(self.pilot,self.viability,17,20)
        self.assertEqual(a.size,(1280,720))
        self.assertEqual(b.mode,"RGB")
        self.assertIsNotNone(ImageChops.difference(a,b).getbbox())

    def test_invalid_duration(self):
        with self.assertRaises(ValueError):
            draw_frame(self.pilot,self.viability,0,0)


if __name__=="__main__":
    unittest.main()
