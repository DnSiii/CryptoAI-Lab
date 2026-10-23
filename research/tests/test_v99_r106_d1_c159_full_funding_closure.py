"""C159 independent full-TRAIN funding calendar negative controls, synthetic only."""
import unittest
from datetime import timedelta
from research.verification.independent_d1_full_train_schedule_gate_cycle133 import (
    TRAIN_START, TRAIN_END, TRAIN_HOURS, verify_full_train_funding_closure,
)


def fixture():
    frames = [{'time': TRAIN_START + timedelta(hours=i), 'funding': []}
              for i in range(TRAIN_HOURS)]
    schedule = {asset: [] for asset in ('BTC', 'ETH')}
    for i in range(0, TRAIN_HOURS, 8):
        t = frames[i]['time']
        for asset in schedule:
            schedule[asset].append(t)
            frames[i]['funding'].append({'asset': asset, 'time': t})
    return frames, schedule


class TestC159FullTrainFundingClosure(unittest.TestCase):
    def setUp(self):
        self.frames, self.schedule = fixture()

    def test_exact_full_train_is_structural_not_authenticated(self):
        r = verify_full_train_funding_closure(self.frames, self.schedule)
        self.assertEqual(r['journal_hours'], 15864)
        self.assertEqual(r['scheduled_funding_fixes_per_asset'], 1983)
        self.assertEqual(r['observed_funding_events'], 3966)
        self.assertEqual(len(r['fold_hours']), 5)
        self.assertEqual(sum(r['fold_hours']), 15864)
        for key in ('schedule_source_authenticated','account_settlement_authenticated',
                    'native_fee_tier_authenticated','execution_fills_authenticated',
                    'historical_roi_authorized','validation_opened',
                    'holdout_opened','promotion_authorized','orders_enabled'):
            self.assertIs(r[key], False, key)

    def test_missing_one_settlement_is_rejected(self):
        self.frames[800]['funding'] = [r for r in self.frames[800]['funding']
                                      if r['asset'] != 'ETH']
        with self.assertRaisesRegex(ValueError, 'MISSING_FUNDING_FIX'):
            verify_full_train_funding_closure(self.frames, self.schedule)

    def test_duplicate_settlement_is_rejected(self):
        self.frames[800]['funding'].append(dict(self.frames[800]['funding'][0]))
        with self.assertRaisesRegex(ValueError, 'DUPLICATE_FUNDING_EVENT'):
            verify_full_train_funding_closure(self.frames, self.schedule)

    def test_shifted_schedule_is_rejected(self):
        self.schedule['BTC'] = [t + timedelta(hours=1) for t in self.schedule['BTC']]
        with self.assertRaisesRegex(ValueError, 'UNSCHEDULED_OR_MISSING_FUNDING_FIX'):
            verify_full_train_funding_closure(self.frames, self.schedule)

    def test_non_eight_hour_schedule_is_rejected(self):
        self.schedule['ETH'][1] += timedelta(hours=1)
        with self.assertRaisesRegex(ValueError, 'FUNDING_INTERVAL_MISMATCH'):
            verify_full_train_funding_closure(self.frames, self.schedule)

    def test_partial_journal_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'FULL_TRAIN_15864H_REQUIRED'):
            verify_full_train_funding_closure(self.frames[:-1], self.schedule)

    def test_validation_hour_injection_is_rejected(self):
        self.frames[-1]['time'] = TRAIN_END
        with self.assertRaisesRegex(ValueError, 'TRAIN_BOUNDARY_MISMATCH'):
            verify_full_train_funding_closure(self.frames, self.schedule)

    def test_fake_schedule_count_is_rejected(self):
        self.schedule['BTC'].pop()
        with self.assertRaisesRegex(ValueError, 'FUNDING_CADENCE_COUNT_MISMATCH'):
            verify_full_train_funding_closure(self.frames, self.schedule)


if __name__ == '__main__':
    unittest.main()
