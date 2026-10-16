"""Synthetic forensic tests; no alternative parameters and no price search."""
import copy,unittest
from research.tools import v99_r106_c1_failure_forensics as f
def fake():
    return [
      {"time":"2022-01-01T00:00:00+00:00","regime":"BULL__LOW_VOLATILITY",
       "net":"-0.02","fee":"0.001","btc_weight":"0.5","eth_weight":"0",
       "lock_remaining":"0"},
      {"time":"2022-01-01T01:00:00+00:00","regime":"BEAR__HIGH_VOLATILITY",
       "net":"-0.03","fee":"0.0","btc_weight":"0","eth_weight":"0",
       "lock_remaining":"166"},
    ]
class ForensicTests(unittest.TestCase):
 def test_no_promotion_and_correct_simple_additive_attribution(self):
    r=f.forensic(fake(),fake())
    self.assertEqual(r["aligned_hours_per_scenario"],2)
    self.assertEqual(r["scenario_different_exposure_hours"],0)
    self.assertAlmostEqual(r["scenarios"]["severe"]["net_simple_sum"],-.05)
    self.assertAlmostEqual(r["scenarios"]["severe"]["gross_pnl_sum_pre_funding"],-.049)
    self.assertEqual(r["scenarios"]["severe"]["cash_lock_hours"],1)
    self.assertFalse(r["promotion_authorized"])
 def test_path_difference_count(self):
    changed=copy.deepcopy(fake());changed[1]["btc_weight"]="0.2"
    r=f.forensic(fake(),changed)
    self.assertEqual(r["scenario_different_exposure_hours"],1)
 def test_no_scenario_time_splice(self):
    changed=copy.deepcopy(fake());changed[1]["time"]="2022-01-02T01:00:00+00:00"
    with self.assertRaisesRegex(ValueError,"scenarios_not_same_train_hours"):f.forensic(fake(),changed)
 def test_nonfinite_record_denied(self):
    bad=copy.deepcopy(fake());bad[0]["net"]="nan"
    with self.assertRaisesRegex(ValueError,"invalid_forensic_economic_record"):f.forensic(bad,fake())
if __name__=="__main__":unittest.main()
