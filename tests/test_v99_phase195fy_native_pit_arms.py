import unittest
import pandas as pd
import numpy as np
from v99_phase195fy_native_pit_arms import build_arms, audit_arms, _decision_after_receipt

INDEX = pd.date_range("2026-10-14T01:00:00Z", periods=8, freq="h")
TRAIN_END = "2026-10-14T04:00:00Z"
UNIVERSE = {
    "BTCUSDT": {"source": "v14_legacy_universe"},
    "EARLYUSDT": {"source": "dynamic_binance_discovery", "discovered_at_utc": "2026-10-14T02:27:00Z"},
    "LATEUSDT": {"source": "dynamic_binance_discovery", "discovered_at_utc": "2026-10-14T05:30:00Z"},
}

def sample():
    return pd.DataFrame({"BTCUSDT": [0.1]*8, "EARLYUSDT": [0.2]*8, "LATEUSDT": [-0.3]*8}, index=INDEX)

class TestNativePIT(unittest.TestCase):
    def test_receipt_tminus1(self):
        arms = build_arms(sample(), UNIVERSE, TRAIN_END)
        self.assertEqual(arms["receipt_tminus1"]["EARLYUSDT"].iloc[2], 0)
        self.assertEqual(arms["receipt_tminus1"]["EARLYUSDT"].iloc[3], 0.2)
        self.assertEqual(arms["receipt_tminus1"]["LATEUSDT"].iloc[5], 0)
        self.assertEqual(arms["receipt_tminus1"]["LATEUSDT"].iloc[6], -0.3)

    def test_fixed_train_membership(self):
        arms = build_arms(sample(), UNIVERSE, TRAIN_END)
        self.assertTrue((arms["fixed_train_universe"]["LATEUSDT"] == 0).all())
        self.assertTrue((arms["fixed_and_receipt"]["LATEUSDT"] == 0).all())
        self.assertTrue((arms["legacy_as_is"]["LATEUSDT"] == -0.3).all())

    def test_input_immutability(self):
        frame = sample()
        original = frame.copy(deep=True)
        build_arms(frame, UNIVERSE, TRAIN_END)
        pd.testing.assert_frame_equal(frame, original)

    def test_append_only_prefix(self):
        baseline = build_arms(sample(), UNIVERSE, TRAIN_END)
        extra = sample().iloc[:2].copy()
        extra.index = pd.date_range(INDEX[-1]+pd.Timedelta(hours=1), periods=2, freq="h")
        extended = build_arms(pd.concat([sample(), extra]), UNIVERSE, TRAIN_END)
        for name in baseline:
            pd.testing.assert_frame_equal(baseline[name], extended[name].loc[INDEX])

    def test_missing_receipt_fails_closed(self):
        broken = dict(UNIVERSE)
        broken["LATEUSDT"] = {"source": "dynamic_binance_discovery"}
        with self.assertRaises(ValueError):
            build_arms(sample(), broken, TRAIN_END)

    def test_bad_index_fails_closed(self):
        broken = sample()
        broken.index = pd.DatetimeIndex([INDEX[0]]*len(broken))
        with self.assertRaises(ValueError):
            build_arms(broken, UNIVERSE, TRAIN_END)

    def test_nan_fails_closed(self):
        broken = sample()
        broken.iloc[0,0] = np.nan
        with self.assertRaises(ValueError):
            build_arms(broken, UNIVERSE, TRAIN_END)

    def test_audit_never_promotes(self):
        verdict = audit_arms(sample(), UNIVERSE, TRAIN_END)
        self.assertFalse(verdict["publication_authorized"])
        self.assertFalse(verdict["promotion_authorized"])
        self.assertFalse(verdict["source_receipts_independently_authenticated"])

    def test_exact_receipt_boundary_is_conservative(self):
        self.assertEqual(_decision_after_receipt("2026-10-14T02:00:00Z"), pd.Timestamp("2026-10-14T04:00:00Z"))

if __name__ == "__main__":
    unittest.main()
