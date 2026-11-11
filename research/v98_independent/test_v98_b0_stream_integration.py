import unittest
from datetime import datetime, timedelta, timezone
from research.v98_independent.v98_b0_stream_integration import ASSETS, HourBar, replay_b0

def stream(n=4, start=datetime(2025, 1, 1, tzinfo=timezone.utc)):
    for i in range(n):
        yield HourBar(start + timedelta(hours=i),
                      {a: 100.0 + i for a in ASSETS},
                      {a: 0.0 for a in ASSETS})

def sleeves(_history):
    return {a: (0.1, 0.05, 0.05, 0.05) for a in ASSETS}

class B0StreamTests(unittest.TestCase):
    def test_warmup_fails_closed_without_future(self):
        state, audit = replay_b0(stream(), sleeves)
        self.assertEqual(len(audit), 3)
        self.assertEqual(state.equity, 10000)
        self.assertTrue(all(x["governor"] == 1 for x in audit))
        self.assertTrue(all(sum(x["weights"].values()) == 0 for x in audit))

    def test_2026_forbidden(self):
        with self.assertRaisesRegex(ValueError, "TRAINING_CUTOFF"):
            replay_b0(stream(2, datetime(2025,12,31,23,tzinfo=timezone.utc)), sleeves)

    def test_hour_gap_forbidden(self):
        rows = list(stream(3))
        rows[2] = HourBar(rows[2].timestamp + timedelta(hours=1), rows[2].closes, rows[2].funding)
        with self.assertRaisesRegex(ValueError, "NONCONTIGUOUS"):
            replay_b0(rows, sleeves)

    def test_missing_asset_forbidden(self):
        rows = list(stream(2))
        rows[1].funding.pop("BNBUSDT")
        with self.assertRaisesRegex(ValueError, "CLEAN4_GRID"):
            replay_b0(rows, sleeves)

    def test_decisions_only_see_completed_closes(self):
        seen = []
        def spy(history):
            seen.append(len(history["BTCUSDT"]))
            return sleeves(history)
        replay_b0(stream(4), spy)
        self.assertEqual(seen, [2,3,4])

if __name__ == "__main__":
    unittest.main()
