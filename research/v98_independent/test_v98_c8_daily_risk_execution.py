"""Synthetic deterministic invariants for C8 daily-risk execution policy."""
import unittest
from unittest.mock import patch
from .v98_c8_daily_risk_execution import replay_c8_daily_risk
from .v98_b0_stream_integration import ASSETS

class C8DailyRiskExecution(unittest.TestCase):
    def setUp(self):
        self.bars={a:[(100.,100.,100.,100.,0.) for _ in range(51)] for a in ASSETS}
        self.funding={a:{} for a in ASSETS}
        self.sleeves=lambda history:{a:(1.,0.,0.,0.) if a==ASSETS[0] else (0.,0.,0.,0.) for a in ASSETS}

    def test_no_intraday_replenishment(self):
        with patch("research.v98_independent.v98_c8_daily_risk_execution.regime_multiplier",return_value=1.), patch("research.v98_independent.v98_c8_daily_risk_execution.governor_multiplier",return_value=1.), patch("research.v98_independent.v98_c8_daily_risk_execution.compose_weights",side_effect=lambda s,r,g:{a:0.4 if a==ASSETS[0] else 0. for a in ASSETS}):
            summary,entries=replay_c8_daily_risk(self.bars,self.funding,self.sleeves)
        self.assertEqual(summary["hours"],51)
        self.assertTrue(all(e["turnover"]==0 for e in entries if e["index"]%24))
        self.assertGreater(entries[23]["turnover"],0)

    def test_intraday_risk_cut_no_reincrease(self):
        def target(s,r,g):
            i=target.counter
            target.counter+=1
            exposure=0.4 if i<25 or i>=30 else 0.1
            return {a:exposure if a==ASSETS[0] else 0. for a in ASSETS}
        target.counter=0
        with patch("research.v98_independent.v98_c8_daily_risk_execution.regime_multiplier",return_value=1.), patch("research.v98_independent.v98_c8_daily_risk_execution.governor_multiplier",return_value=1.), patch("research.v98_independent.v98_c8_daily_risk_execution.compose_weights",side_effect=target):
            _,entries=replay_c8_daily_risk(self.bars,self.funding,self.sleeves)
        self.assertAlmostEqual(entries[25]["weights_after_fill"][ASSETS[0]],0.1)
        self.assertAlmostEqual(entries[29]["weights_after_fill"][ASSETS[0]],0.1)
        self.assertAlmostEqual(entries[47]["weights_after_fill"][ASSETS[0]],0.4)

    def test_cost_scale_and_turnover_reconcile(self):
        with patch("research.v98_independent.v98_c8_daily_risk_execution.regime_multiplier",return_value=1.), patch("research.v98_independent.v98_c8_daily_risk_execution.governor_multiplier",return_value=1.), patch("research.v98_independent.v98_c8_daily_risk_execution.compose_weights",side_effect=lambda s,r,g:{a:0.4 if a==ASSETS[0] else 0. for a in ASSETS}):
            summary,entries=replay_c8_daily_risk(self.bars,self.funding,self.sleeves,cost_scale=4.)
        self.assertAlmostEqual(summary["total_turnover"],sum(e["turnover"] for e in entries))
        for e in entries:
            self.assertAlmostEqual(e["cost_return"],e["turnover"]*(.0004+.0002)*4.)
            self.assertAlmostEqual(e["equity"],e["pre_fill_equity"]*(1-e["cost_return"]))
            self.assertLessEqual(sum(e["weights_after_fill"].values()),0.75)
            self.assertLessEqual(max(e["weights_after_fill"].values()),0.40)

    def test_reject_non_clean4(self):
        with self.assertRaisesRegex(ValueError,"INVALID_CLEAN4_ASSETS"):
            replay_c8_daily_risk({"BTCUSDT":self.bars[ASSETS[0]]},self.funding,self.sleeves)

if __name__=="__main__":
    unittest.main()
