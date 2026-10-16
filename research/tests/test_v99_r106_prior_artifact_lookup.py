"""Adversarial source discovery tests: synthetic metadata, no PnL or holdout."""
import unittest
from datetime import datetime, timezone
from research.tools.v99_r106_prior_artifact_lookup import choose


def run(i, name='V99 R106 hourly OKX as-of source receipts', event='schedule', conclusion='success'):
    return dict(id=i, name=name, event=event, conclusion=conclusion,
                status='completed', head_branch='main',
                created_at=f'2026-10-16T{(i % 24):02d}:00:00Z')


def artifact(i, prefix='v99-r106-okx-firstparty-', **kwargs):
    return dict(name=prefix + str(i), expired=False, size_in_bytes=100, **kwargs)


class TestLookup(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 16, 9, 0, tzinfo=timezone.utc)

    def test_ignores_newer_paper_and_uses_source(self):
        r = choose([run(4), run(5, name='CryptoAI multi-engine paper refresh')],
                   lambda i: [artifact(i)], current_run_id=9, now_utc=self.now)
        self.assertEqual(r['run_id'], 4)
        self.assertFalse(r['promotion_authorized'])

    def test_skips_missing_archive_and_finds_older_source(self):
        r = choose([run(7), run(6)], lambda i: [] if i == 7 else [artifact(i)],
                   current_run_id=9, now_utc=self.now)
        self.assertEqual(r['run_id'], 6)

    def test_never_accepts_fixed_old_baseline(self):
        with self.assertRaisesRegex(ValueError, 'fail_closed'):
            choose([run(7)], lambda i: [], current_run_id=9, now_utc=self.now)

    def test_rejects_wrong_artifact_id_and_expired(self):
        with self.assertRaisesRegex(ValueError, 'fail_closed'):
            choose([run(7)], lambda i: [artifact(6), dict(name='v99-r106-hourly-okx-7',
                       expired=True, size_in_bytes=100)], current_run_id=9, now_utc=self.now)

    def test_rejects_duplicate_matching_artifacts(self):
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            choose([run(7)], lambda i: [artifact(7), artifact(7, prefix='v99-r106-hourly-okx-')],
                   current_run_id=9, now_utc=self.now)

    def test_filters_manual_failed_branch_and_self(self):
        with self.assertRaisesRegex(ValueError, 'fail_closed'):
            choose([run(7, event='workflow_dispatch'), run(8, conclusion='failure'), run(9)],
                   lambda i: [artifact(i)], current_run_id=9, now_utc=self.now)

    def test_rejects_invalid_created_time(self):
        bad = run(7); bad['created_at'] = '2026-10-16T01:00:00+01:00'
        with self.assertRaisesRegex(ValueError, 'invalid_source_run_time'):
            choose([bad], lambda i: [artifact(i)], current_run_id=9, now_utc=self.now)

    def test_rejects_stale_even_if_artifact_is_present(self):
        with self.assertRaisesRegex(ValueError, 'fail_closed'):
            choose([run(1)], lambda i: [artifact(i)], current_run_id=9, now_utc=self.now)

    def test_rejects_future_run(self):
        with self.assertRaisesRegex(ValueError, 'fail_closed'):
            choose([run(10)], lambda i: [artifact(i)], current_run_id=9, now_utc=self.now)

    def test_supports_atomic_source_archive(self):
        r = choose([run(7, name='V99 R106 atomic paired OKX market and terms DATA_ONLY')],
                   lambda i: [artifact(i, prefix='v99-r106-hourly-okx-')], current_run_id=9, now_utc=self.now)
        self.assertEqual(r['run_id'], 7)


if __name__ == '__main__':
    unittest.main()
