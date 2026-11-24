"""No simulation needed to test measured animation integrity."""
import unittest
from PIL import ImageChops
from measured_comparison_render import SPECS,validate,frame

def fixture(gen):
    names=SPECS[gen][0];times=list(range(0,241,6))
    return {"generation":gen,"n":16,"steps":240,"seeds":[42,73],
            "source_sha":SPECS[gen][3],"times":times,
            "observations":{seed:{name:[
                {"step":t,"v_active":min(.99,.1+i*.13+t/1000),
                 "w_active":max(0,.8-i*.14-t/1100),"coexistence":0.}
                for t in times] for i,name in enumerate(names)}
                for seed in ("42","73")}}
class EvidenceMovies(unittest.TestCase):
    def test_frames_for_all_generations(self):
        for gen in SPECS:
            with self.subTest(gen=gen):
                d=fixture(gen);validate(d,gen)
                a=frame(d,gen,0,12);b=frame(d,gen,11,12)
                self.assertEqual(a.size,(1280,720))
                self.assertIsNotNone(ImageChops.difference(a,b).getbbox())
    def test_corruption_rejected(self):
        d=fixture("0031");d["observations"]["42"]["historical"][0]["v_active"]=float("nan")
        with self.assertRaises(ValueError):validate(d,"0031")
if __name__=="__main__":unittest.main()
