"""Adversarial C1 safety and causal software tests. No historical profit experiments here."""
import csv,datetime,math,tempfile,unittest
from pathlib import Path
from research.tools import v99_r106_c1_core as c
from research.tools import v99_r106_c1_accounting as a
from research.tools import v99_r106_c1_train_gate as gate
UTC=datetime.timezone.utc
def synthetic(n=1250):
    begin=datetime.datetime(2021,10,1,tzinfo=UTC)
    out=[]
    for k in range(n):
        t=begin+datetime.timedelta(hours=k);x=100*math.exp(k*.00013)
        out.append((t,x,x*1.005,x*.995,x,1000.))
    return out
class EngineTests(unittest.TestCase):
    def test_sealed_dates_and_fixed_cost(self):
        self.assertEqual(c.END,datetime.datetime(2023,10,1,tzinfo=UTC))
        self.assertEqual(c.FINAL_HOLDOUT,datetime.datetime(2024,1,18,tzinfo=UTC))
        self.assertEqual((c.SEVERE,c.SUPERSEVERE),(.0007,.0014))
    def test_current_and_future_price_mutation_does_not_change_decision(self):
        b=synthetic();i=900;base=c.features(b)[i]
        altered=b.copy()
        for j in (i,i+1):
            t,o,h,l,cl,v=altered[j];altered[j]=(t,o*2,h*2,l*.5,cl*2,v*99)
        self.assertEqual(base,c.features(altered)[i])
        self.assertEqual(c.signal(base),c.signal(c.features(altered)[i]))
    def test_six_regimes_and_gross(self):
        for direction in ("BULL","BEAR","SIDEWAYS"):
            for vol in ("HIGH_VOLATILITY","LOW_VOLATILITY"):
                w,lock,armed=c.governor((.65,-.65),direction+"__"+vol,0,0,True)
                self.assertLessEqual(sum(map(abs,w)),1.30+1e-12)
                self.assertEqual(lock,0)
    def test_drawdown_lock_and_latch_not_infinite(self):
        w,lock,armed=c.governor((.4,-.4),"BEAR__LOW_VOLATILITY",-.21,0,True)
        self.assertEqual((w,lock,armed),((0.,0.),167,False))
        for _ in range(167):
            w,lock,armed=c.governor((.4,-.4),"BEAR__LOW_VOLATILITY",-.21,lock,armed)
        self.assertEqual(lock,0)
        w,lock,armed=c.governor((.4,-.4),"BEAR__LOW_VOLATILITY",-.21,lock,armed)
        self.assertEqual(lock,0);self.assertEqual(w,(.2,-.2))
    def test_stop_before_validation_market_values(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"bars.csv"
            with p.open("w",newline="") as file:
                wr=csv.writer(file);wr.writerow(c.FIELDS)
                for row in synthetic():wr.writerow((row[0].isoformat(),*row[1:]))
                wr.writerow(("2023-10-01T00:00:00+00:00","POISON","POISON","POISON","POISON","POISON"))
            rows,_=c.load_train(p);self.assertEqual(len(rows),1250)
    def test_repeated_timestamp_denied(self):
        rows=synthetic()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"bars.csv"
            with p.open("w",newline="") as f:
                w=csv.writer(f);w.writerow(c.FIELDS)
                for i,row in enumerate(rows):
                    if i==900:row=rows[i-1]
                    w.writerow((row[0].isoformat(),*row[1:]))
            with self.assertRaisesRegex(ValueError,"gap_or_duplicate"):c.load_train(p)
    def test_integrated_accounting_regime_matrix(self):
        rows=synthetic(2200);other=[(t,o*.5,h*.5,l*.5,cl*.5,v) for t,o,h,l,cl,v in rows]
        result=a.simulate(rows,other,c.SEVERE)
        self.assertEqual(len(result["regime_matrix"]),6)
        self.assertEqual(len(result["fold_returns"]),5)
        self.assertGreaterEqual(result["modeled_transaction_cost_sum"],0)
    def test_reject_positive_aggregate_if_fold_gate_fails(self):
        fake={"roi":.8,"positive_folds":2,"hourly_profit_factor":1.2,
          "remove_best_day_roi":.5,"max_drawdown":-.1,"active_hours":1000,
          "fold_returns":[.1,.2,-.1,-.1,-.1],"regime_matrix":{i:{} for i in range(6)},
          "benchmark_proxies":{"btc_100pct":0,"btc_eth_equal":0}}
        result=gate.gates(fake,fake)
        self.assertFalse(result["at_least_4_5_positive_severe_folds"])
        self.assertFalse(all(result.values()))
    def test_train_source_requires_full_coverage(self):
        with self.assertRaisesRegex(ValueError,"incomplete_preregistered_train_end"):
            c.assert_train_coverage(synthetic(2200))
if __name__=="__main__":unittest.main()
