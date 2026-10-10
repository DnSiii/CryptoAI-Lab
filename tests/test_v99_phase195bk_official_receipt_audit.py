"""Adversarial tests for independent official paper provenance comparison."""
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from scripts.v99_phase195bk_official_receipt_audit import (
    TRACKS, audit_zip, compare_archives, strict_json, rows)


def fixture(path, changed=True, rewrite_timestamp='2026-10-01T16:00:00+00:00'):
    before = {'mode': 'PAPER_ONLY', 'equity_curve': [
        {'timestamp': rewrite_timestamp, 'capital_brl': 10000, 'funding_result_brl': 0},
        {'timestamp': '2026-10-01T17:00:00+00:00', 'capital_brl': 10001}]}
    after = json.loads(json.dumps(before))
    if changed:
        after['equity_curve'][0]['capital_brl'] = 9999
        after['equity_curve'][0]['funding_result_brl'] = -1
    after['equity_curve'].append({'timestamp': '2026-10-01T18:00:00+00:00', 'capital_brl': 10002})
    with zipfile.ZipFile(path, 'w') as z:
        for name in TRACKS:
            z.writestr('reports/published_baseline/' + name, json.dumps(before))
            z.writestr('reports/' + name, json.dumps(after))


class TestBK(unittest.TestCase):
    def test_cross_run_rewrite_stable_but_hold(self):
        with tempfile.TemporaryDirectory() as d:
            p, q = Path(d)/'a.zip', Path(d)/'b.zip'
            fixture(p); fixture(q)
            r = compare_archives([p, q])
            self.assertFalse(r['promotion_authorized'])
            self.assertTrue(all(v['same_changed_rows_across_runs'] for v in r['cross_run_invariants'].values()))
            self.assertEqual(r['runs'][0]['tracks'][TRACKS[0]]['appended_hours'], 1)
            self.assertEqual(r['cross_run_invariants'][TRACKS[0]]['candidate_cross_run_drift_hours'], 0)

    def test_inconsistent_rewrites_detected(self):
        with tempfile.TemporaryDirectory() as d:
            p, q = Path(d)/'a.zip', Path(d)/'b.zip'
            fixture(p); fixture(q, changed=False)
            r = compare_archives([p, q])
            self.assertFalse(r['cross_run_invariants'][TRACKS[0]]['same_changed_rows_across_runs'])

    def test_candidate_drift_detected_without_changed_historical_rows(self):
        with tempfile.TemporaryDirectory() as d:
            p, q = Path(d)/'a.zip', Path(d)/'b.zip'
            fixture(p); fixture(q)
            with zipfile.ZipFile(q) as z:
                payload = {name: z.read(name) for name in z.namelist()}
            for name in TRACKS:
                key = 'reports/' + name
                x = json.loads(payload[key]); x['equity_curve'][-1]['capital_brl'] = 20000
                payload[key] = json.dumps(x).encode()
            with zipfile.ZipFile(q, 'w') as z:
                for name, body in payload.items(): z.writestr(name, body)
            r = compare_archives([p, q])
            self.assertTrue(r['cross_run_invariants'][TRACKS[0]]['same_changed_rows_across_runs'])
            self.assertEqual(r['cross_run_invariants'][TRACKS[0]]['candidate_cross_run_drift_hours'], 1)

    def test_rewrite_never_promotion(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'a.zip'; fixture(p)
            self.assertFalse(audit_zip(p)['publication_authorized'])

    def test_duplicate_json(self):
        with self.assertRaises(ValueError): strict_json('{"x":1,"x":2}')

    def test_nonfinite_json(self):
        for v in ('NaN', '1e999'):
            with self.assertRaises(ValueError): strict_json('{"x":'+v+'}')

    def test_out_of_order_and_duplicate(self):
        x = {'equity_curve': [{'timestamp':'2026-10-01T17:00:00Z'},
                              {'timestamp':'2026-10-01T16:00:00Z'}]}
        with self.assertRaises(ValueError): rows(x)

    def test_requires_multiple_archives(self):
        with self.assertRaises(ValueError): compare_archives(['only.zip'])

    def test_no_fabricated_missing_track(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.zip'
            with zipfile.ZipFile(p,'w') as z: z.writestr('unrelated.txt','x')
            with self.assertRaises(KeyError): audit_zip(p)


if __name__ == '__main__': unittest.main()
