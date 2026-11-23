"""Checkpoint provenance and carry-state contract tests (synthetic only)."""
import unittest
from .phase243_native_funding_cashflow import ASSETS
from .v98_c27_training_checkpoint import build_checkpoint

class TestTrainingCheckpoint(unittest.TestCase):
    def setUp(self):
        self.bars = {a: [(100.,101.,99.,100.,1000.)] * 27048 for a in ASSETS}
        self.ledger = [
            dict(index=i, equity=10000., pre_fill_equity=10000.,
                 weights_after_fill={a:0. for a in ASSETS},
                 queued_next_open_sell_fractions={a:0. for a in ASSETS})
            for i in range(1,27048)
        ]
    def test_exact_next_open_checkpoint(self):
        state=build_checkpoint(self.bars,self.ledger)
        self.assertEqual(state["absolute_index"],27048)
        self.assertEqual(state["previous_open"]["BTCUSDT"],100.)
        self.assertEqual(len(state["histories"]["SOLUSDT"]),27048)
        self.assertEqual(state["decision_equity"],10000.)
    def test_missing_hour_rejected(self):
        self.bars["BTCUSDT"]=self.bars["BTCUSDT"][:-1]
        with self.assertRaisesRegex(ValueError,"INCOMPLETE_SOURCE"):
            build_checkpoint(self.bars,self.ledger)
    def test_corrupt_ledger_clock_rejected(self):
        self.ledger[-1]["index"]=0
        with self.assertRaisesRegex(ValueError,"LEDGER_CLOCK"):
            build_checkpoint(self.bars,self.ledger)
    def test_unbounded_position_rejected(self):
        self.ledger[-1]["weights_after_fill"]["BTCUSDT"]=.99
        with self.assertRaisesRegex(ValueError,"WEIGHTS"):
            build_checkpoint(self.bars,self.ledger)
    def test_peak_includes_prefill(self):
        self.ledger[100]["pre_fill_equity"]=11000.
        self.assertEqual(build_checkpoint(self.bars,self.ledger)["peak"],11000.)

if __name__=="__main__":
    unittest.main()
