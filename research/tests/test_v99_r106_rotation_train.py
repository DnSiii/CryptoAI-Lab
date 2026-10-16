"""Adversarial synthetic-only tests for fixed rotation. No PnL optimization."""
import csv,datetime,tempfile,unittest
from pathlib import Path
from research.tools import v99_r106_rotation_train as x

def market(n=1900):
    start=datetime.datetime(2021,10,1,tzinfo=datetime.timezone.utc)
    b=[];e=[]
    for i in range(n):
        ts=start+datetime.timedelta(hours=i)
        c1=100.*(1.00015**i);c2=50.*(1.00017**i)
        b.append((ts,c1,c1*1.01,c1*.99,c1,1234.))
        e.append((ts,c2,c2*1.01,c2*.99,c2,2468.))
    return b,e

class TestFixedRotation(unittest.TestCase):
    def test_no_short_and_fixed_weekday(self):
        b,e=market()
        target=x.signals(b,e)
        self.assertEqual(x.N,720)
        self.assertTrue(all(wb>=0 and we>=0 and wb+we<=1 for _,_,wb,we in target))
        for i in range(1,len(target)):
            if target[i][2:]!=target[i-1][2:]:
                self.assertEqual(target[i][1].weekday(),0)
                self.assertEqual(target[i][1].hour,0)
    def test_same_hour_close_mutation_cannot_change_target(self):
        b,e=market()
        idx=950
        target=x.signals(b,e)
        k=next((j for j,(i,*_) in enumerate(target) if i==idx))
        b2=list(b);e2=list(e)
        for base,alternative in ((b,b2),(e,e2)):
            t,o,h,l,c,v=base[idx]
            alternative[idx]=(t,o*9,h*11,l*.1,c*9,v*50)
        alt=x.signals(b2,e2)
        self.assertEqual(target[k][2:],alt[k][2:])
    def test_higher_cost_never_increases_total_return(self):
        b,e=market();r=x.evaluate(b,e)
        self.assertLessEqual(r["supersevere"]["return"],r["severe"]["return"]+1e-12)
        self.assertFalse(r["final_holdout_accessed"])
        self.assertFalse(r["promotion_authorized"])
        self.assertEqual(r["economic_trials"],1)
    def test_nonaligned_assets_rejected(self):
        b,e=market();other=list(e);t,*v=other[1000]
        other[1000]=(t+datetime.timedelta(hours=1),*v)
        with self.assertRaisesRegex(ValueError,"unaligned_market_hours"):
            x.signals(b,other)
    def test_future_ohlcv_not_parsed(self):
        b,_=market(920)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"b.csv"
            with path.open("w",newline="") as file:
                w=csv.writer(file);w.writerow(["timestamp","open","high","low","close","volume"])
                for row in b:w.writerow(row)
                w.writerow(["2024-01-18T00:00:00Z","POISON","POISON","POISON","POISON","POISON"])
            values,_=x.load_train(path)
            self.assertEqual(len(values),len(b))
    def test_duplicate_hour_rejected(self):
        b,_=market(920)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"b.csv"
            with path.open("w",newline="") as file:
                w=csv.writer(file);w.writerow(["timestamp","open","high","low","close","volume"])
                for i,row in enumerate(b):w.writerow(b[i-1] if i==600 else row)
            with self.assertRaisesRegex(ValueError,"hourly_gap_or_repeat"):
                x.load_train(path)
    def test_deterministic_evaluation(self):
        b,e=market()
        self.assertEqual(x.evaluate(b,e),x.evaluate(b,e))
if __name__=="__main__":unittest.main()
