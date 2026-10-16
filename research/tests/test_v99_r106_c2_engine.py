"""C2 synthetic pre-economic causality, firewall, accounting, oracle tests."""
import csv,math,tempfile,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from research.tools import v99_r106_c2_engine as c
from research.tools import v99_r106_c2_oracle as o
UTC=timezone.utc
def synthetic(n=2000,begin=datetime(2021,10,1,tzinfo=UTC)):
    rows=[]
    for i in range(n):
        t=begin+timedelta(hours=i);p=100*math.exp(.00005*i+0.02*math.sin(i/40))
        rows.append((t,p,p*1.01,p*.99,p,1000.))
    return rows
class C2Safety(unittest.TestCase):
    def test_cost_and_partition(self):
        self.assertEqual((c.SEVERE,c.SUPERSEVERE),(.0007,.0014))
        self.assertEqual(c.END,datetime(2023,10,1,tzinfo=UTC))
    def test_causal_mutation(self):
        b=synthetic();e=synthetic();i=900
        base=c.make_features(b,e)[i]
        for k in (i,i+1):
            t,o,h,l,cl,v=b[k];b[k]=(t,o*5,h*5,l*.2,cl*5,v*4)
        self.assertEqual(base,c.make_features(b,e)[i])
    def test_weekly_target_bounded_and_contrarian(self):
        w=c.weekly_target((.5,1.,.1,.10,0.,0.))
        self.assertLessEqual(sum(map(abs,w)),.9+1e-10)
        self.assertGreater(w[1],0)
        self.assertLess(w[0],.7)
        self.assertEqual(c.weekly_target((0.,1.,0.,0.,0.,0.)),(0.,0.))
    def test_no_validation_values_parsed(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"data.csv"
            with p.open("w",newline="") as f:
                w=csv.writer(f);w.writerow(c.FIELDS)
                for r in synthetic(int((c.END-datetime(2021,10,1,tzinfo=UTC)).total_seconds()/3600)):
                    w.writerow((r[0].isoformat(),*r[1:]))
                w.writerow(("2023-10-01T00:00:00+00:00",*["POISON"]*5))
            rows,_=c.load_train(p)
            self.assertEqual(rows[-1][0],c.END-timedelta(hours=1))
    def test_reject_hourly_gap(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"data.csv"
            with p.open("w",newline="") as f:
                w=csv.writer(f);w.writerow(c.FIELDS)
                for j,r in enumerate(synthetic()):
                    if j==1000:r=synthetic()[999]
                    w.writerow((r[0].isoformat(),*r[1:]))
            with self.assertRaisesRegex(ValueError,"gap_or_duplicate"):c.load_train(p)
    def test_reproducible_fixed_target_and_independent_oracle(self):
        b=synthetic(3000);e=synthetic(3000)
        targets=c.path_targets(b,e)
        with tempfile.TemporaryDirectory() as d:
            sfile=Path(d)/"s.csv";vfile=Path(d)/"v.csv"
            s=c.simulate(b,e,targets,c.SEVERE,sfile)
            v=c.simulate(b,e,targets,c.SUPERSEVERE,vfile)
            ws=o.verify(b,e,sfile,c.SEVERE);wv=o.verify(b,e,vfile,c.SUPERSEVERE)
            self.assertEqual(ws["weights_sha256"],wv["weights_sha256"])
            self.assertAlmostEqual(ws["roi"],s["roi"])
            self.assertAlmostEqual(wv["roi"],v["roi"])
            self.assertLessEqual(v["roi"],s["roi"]+1e-10)
            self.assertEqual(len(s["regime_matrix"]),6)
            self.assertEqual(len(s["fold_returns"]),5)
            self.assertEqual(s["journal_rows"],len(targets))
    def test_oracle_detects_tamper(self):
        b=synthetic(3000);e=synthetic(3000)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"s.csv";c.simulate(b,e,c.path_targets(b,e),c.SEVERE,p)
            data=p.read_text();data=data.replace(",0.0,0.0,",",0.0,0.123,",1)
            p.write_text(data)
            with self.assertRaises(ValueError):o.verify(b,e,p,c.SEVERE)
    def test_gate_positive_aggregate_cannot_rescue_folds(self):
        fake={"roi":.9,"positive_folds":2,"hourly_profit_factor":2.,
              "remove_best_day_roi":.5,"max_drawdown":-.1,"active_hours":1000,
              "benchmark_proxies":{"btc_100pct":0,"btc_eth_equal":0},
              "fold_returns":[.1,.2,-.1,-.1,-.1],"regime_matrix":{str(i):{} for i in range(6)}}
        self.assertFalse(c.gates(fake,fake,True)["severe_at_least_4_5_folds"])
if __name__=="__main__":unittest.main()
