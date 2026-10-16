"""Synthetic-only adversarial tests for frozen growth breakout mapping."""
import csv
import datetime
import tempfile
import unittest
from pathlib import Path
from research.tools import v99_r106_growth_breakout_train as x

def sample(n=1100):
    start=datetime.datetime(2021,11,1,tzinfo=datetime.timezone.utc)
    b=[];e=[]
    for i in range(n):
        t=start+datetime.timedelta(hours=i)
        v=100*(1.00035**i)
        w=50*(1.00023**i)
        b.append((t,v,v*1.005,v*0.995,v,1234.))
        e.append((t,w,w*1.006,w*0.994,w,2345.))
    return b,e

class TestGrowth(unittest.TestCase):
    def test_fixed_config_and_exposure_bounds(self):
        b,e=sample()
        targets=x.targets(b,e)
        self.assertEqual((x.BREAKOUT,x.EXIT,x.VOL), (168,72,168))
        self.assertEqual((x.SEVERE,x.SUPERSEVERE),(.0007,.0014))
        self.assertTrue(all(abs(pb)+abs(pe)<=1.25 for _,_,pb,pe in targets))
    def test_mutating_decision_hour_ohlcv_cannot_change_signal(self):
        b,e=sample()
        idx=x.BREAKOUT+1+24
        pb=x.position(b,idx,0);pe=x.position(e,idx,0)
        b2=list(b);e2=list(e)
        for src,dest in ((b,b2),(e,e2)):
            t,o,h,l,c,v=src[idx]
            dest[idx]=(t,o*10,h*10,l*0.5,c*10,v*100)
        self.assertEqual(pb,x.position(b2,idx,0))
        self.assertEqual(pe,x.position(e2,idx,0))
    def test_fixed_cost_increase_must_not_improve_total(self):
        b,e=sample()
        r=x.evaluate(b,e)
        self.assertLessEqual(r["supersevere"]["return"],r["severe"]["return"]+1e-12)
        self.assertFalse(r["promotion_authorized"])
        self.assertFalse(r["final_holdout_accessed"])
    def test_crossasset_timestamps_must_align(self):
        b,e=sample()
        shifted=list(e)
        t,*v=shifted[500]
        shifted[500]=(t+datetime.timedelta(hours=1),*v)
        with self.assertRaisesRegex(ValueError,"timestamp_mismatch"):
            x.targets(b,shifted)
    def test_holdout_stops_before_numeric_parse(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"bars.csv"
            with p.open("w",newline="") as f:
                w=csv.writer(f);w.writerow(["timestamp","open","high","low","close","volume"])
                for t,o,h,l,c,v in sample(600)[0]:
                    w.writerow([t.isoformat(),o,h,l,c,v])
                w.writerow(["2024-01-18T00:00:00Z","BAD","BAD","BAD","BAD","BAD"])
            rows,_=x.load_train(p)
            self.assertEqual(len(rows),600)
    def test_bad_order_and_timegap_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"bars.csv"
            with p.open("w",newline="") as f:
                w=csv.writer(f);w.writerow(["timestamp","open","high","low","close","volume"])
                for i,(t,o,h,l,c,v) in enumerate(sample(600)[0]):
                    if i==400: t=t+datetime.timedelta(hours=1)
                    w.writerow([t.isoformat(),o,h,l,c,v])
            with self.assertRaisesRegex(ValueError,"gapped_repeated"):
                x.load_train(p)
    def test_determinism(self):
        b,e=sample()
        self.assertEqual(x.evaluate(b,e),x.evaluate(b,e))
if __name__=="__main__":unittest.main()
