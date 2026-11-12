"""Regression guards for V98 B0 annual accounting attribution; no holdout."""
import math
import unittest
from unittest.mock import patch
from research.v98_independent import v98_b0_regime_attribution as module

class AttributionTests(unittest.TestCase):
    def _entries(self):
        return [
            dict(index=i, gross_return=0.001, funding_return=-0.0001,
                 cost_return=0.0002, pre_fill_equity=0.,
                 equity=0., turnover=0.3,
                 gross_by_asset={"BTCUSDT":0.001,"ETHUSDT":0.0,"BNBUSDT":0.0,"SOLUSDT":0.0},
                 funding_by_asset={"BTCUSDT":-0.0001,"ETHUSDT":0.0,"BNBUSDT":0.0,"SOLUSDT":0.0},
                 weights_after_fill={"BTCUSDT":0.4,"ETHUSDT":0.2,
                                     "BNBUSDT":0.0,"SOLUSDT":0.0})
            for i in range(1,27048)
        ]

    def test_complete_ledger_reconciles_with_terminal_mark(self):
        entries=self._entries()
        previous=10000.
        for e in entries:
            e["pre_fill_equity"]=previous*(1+e["gross_return"]+e["funding_return"])
            e["equity"]=e["pre_fill_equity"]*(1-e["cost_return"])
            previous=e["equity"]
        final=previous*1.002
        result=module.attribute(entries,final)
        years=result["annual_attribution"]
        self.assertEqual(result["holdout_accessed"],False)
        self.assertAlmostEqual(sum(y["net_log"] for y in years.values()),
                               math.log(final/10000.),places=8)
        for row in years.values():
            self.assertLess(abs(row["log_decomposition_residual"]),1e-8)
            self.assertAlmostEqual(row["mean_gross_exposure"],0.6,places=10)

    def test_invalid_turnover_and_exposure_rejected(self):
        entries=self._entries()
        previous=10000.
        for e in entries:
            e["pre_fill_equity"]=previous*(1+e["gross_return"]+e["funding_return"])
            e["equity"]=e["pre_fill_equity"]*(1-e["cost_return"])
            previous=e["equity"]
        entries[0]["turnover"]=-0.1
        with self.assertRaisesRegex(ValueError,"INVALID_TURNOVER"):
            module.attribute(entries,previous)
        entries[0]["turnover"]=0.3
        entries[0]["weights_after_fill"]["BTCUSDT"]=float("nan")
        with self.assertRaisesRegex(ValueError,"INVALID_EXPOSURE"):
            module.attribute(entries,previous)

    def test_asset_contribution_mismatch_rejected(self):
        entries=self._entries()
        previous=10000.
        for e in entries:
            e["pre_fill_equity"]=previous*(1+e["gross_return"]+e["funding_return"])
            e["equity"]=e["pre_fill_equity"]*(1-e["cost_return"])
            previous=e["equity"]
        entries[0]["gross_by_asset"]["BTCUSDT"]=0.5
        with self.assertRaisesRegex(ValueError,"ASSET_CONTRIBUTION_MISMATCH"):
            module.attribute(entries,previous)

    def test_missing_hour_rejected(self):
        with self.assertRaisesRegex(ValueError,"INCOMPLETE_TRAINING_LEDGER"):
            module.attribute([],10000.)

    def test_accounting_mismatch_rejected(self):
        entries=self._entries()
        with self.assertRaisesRegex(ValueError,"ACCOUNTING_MISMATCH"):
            module.attribute(entries,10000.)

if __name__=="__main__":
    unittest.main()
