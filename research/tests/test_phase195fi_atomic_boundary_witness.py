"""Adversarial Phase195-FI tests: boundary parity never certifies PIT or publication."""
import copy
import importlib.util
import io
import json
import pathlib
import tempfile
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('witness', ROOT/'tools'/'v99_phase195fi_atomic_boundary_witness.py')
witness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(witness)

H0='2026-10-01T15:00:00+00:00'
H1='2026-10-01T16:00:00+00:00'
H2='2026-10-01T17:00:00+00:00'
H3='2026-10-01T18:00:00+00:00'

def fixture():
    universe={'mode':'PUBLIC_DATA_ONLY','verified_boundary':H1,
              'updated_at_utc':H3,'symbols':{'BTCUSDT':{'source':'legacy'}}}
    sync={'mode':'PUBLIC_DATA_ONLY','private_api_used':False,
          'target_latest_closed_hour':H1,'expected_latest_closed_hour':H1,
          'generated_at_utc':H3}
    ledgers={t:{'mode':'PAPER_ONLY','real_orders_enabled':False,
                'latest_data_timestamp':H1,'equity_curve':[
                    {'timestamp':H0,'capital_brl':10000},
                    {'timestamp':H1,'capital_brl':10001}]}
             for t in witness.TRACKS}
    snapshots={t:{'mode':'PAPER_ONLY','real_orders_enabled':False,
                  'latest_data_timestamp':H1} for t in witness.TRACKS}
    return universe,sync,ledgers,snapshots

def verdict(*data):return witness.inspect(*data)

def pack(artifacts, duplicate=None):
    u,s,ledgers,snapshots=artifacts
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('state/paper_v15_universe.json',json.dumps(u))
        z.writestr('reports/paper_data_sync_v15.json',json.dumps(s))
        for name in witness.TRACKS:
            z.writestr('reports/paper_'+name+'_ledger.json',json.dumps(ledgers[name]))
            z.writestr('reports/paper_'+name+'_snapshot.json',json.dumps(snapshots[name]))
        if duplicate:
            z.writestr(duplicate,'{}')
    return buf.getvalue()


class BoundaryWitness(unittest.TestCase):
    def test_consistent_is_never_source_attestation(self):
        result=verdict(*fixture())
        self.assertEqual(result['status'],'OBSERVED_BOUNDARY_CONSISTENT_NOT_AUTHENTICATED')
        for gate in ('source_time_authenticated','append_only_prefix_certified','publication_authorized','promotion_authorized','holdout_accessed'):
            self.assertFalse(result[gate],gate)
        self.assertEqual(result['economic_trials'],0)
        self.assertEqual(len(result['tracks']),8)

    def test_universe_lag(self):
        x=fixture();x[0]['verified_boundary']=H0
        self.assertIn('universe_verified:not_equal_sync_target',verdict(*x)['boundary_issues'])

    def test_universe_ahead(self):
        x=fixture();x[0]['verified_boundary']=H2
        self.assertIn('universe_verified:not_equal_sync_target',verdict(*x)['boundary_issues'])

    def test_sync_expected_mismatch(self):
        x=fixture();x[1]['expected_latest_closed_hour']=H2
        self.assertIn('sync_expected:not_equal_sync_target',verdict(*x)['boundary_issues'])

    def test_one_track_future(self):
        x=fixture();x[2]['v99']['latest_data_timestamp']=H2
        self.assertIn('v99:ledger_latest_not_sync_target',verdict(*x)['boundary_issues'])

    def test_one_track_stale(self):
        x=fixture();x[2]['v16']['latest_data_timestamp']=H0
        self.assertIn('v16:ledger_latest_not_sync_target',verdict(*x)['boundary_issues'])

    def test_final_curve_conflict(self):
        x=fixture();x[2]['v15']['equity_curve'][-1]['timestamp']=H2
        self.assertIn('v15:curve_end_not_latest',verdict(*x)['boundary_issues'])

    def test_hole_in_hourly_curve(self):
        x=fixture();x[2]['v15']['equity_curve'][0]['timestamp']='2026-10-01T14:00:00Z'
        self.assertTrue(any('v15:curve_gap_or_reorder_at:' in issue for issue in verdict(*x)['boundary_issues']))

    def test_reverse_order(self):
        x=fixture();x[2]['v99']['equity_curve'].reverse()
        self.assertTrue(any('curve_gap_or_reorder' in issue for issue in verdict(*x)['boundary_issues']))

    def test_duplicate_hour(self):
        x=fixture();x[2]['v13']['equity_curve'].append(copy.deepcopy(x[2]['v13']['equity_curve'][-1]))
        self.assertTrue(any('curve_gap_or_reorder' in issue for issue in verdict(*x)['boundary_issues']))

    def test_snapshot_drift(self):
        x=fixture();x[3]['v14']['latest_data_timestamp']=H2
        self.assertIn('v14:snapshot_latest_not_ledger',verdict(*x)['boundary_issues'])

    def test_private_flag(self):
        x=fixture();x[1]['private_api_used']=True
        with self.assertRaises(ValueError): verdict(*x)

    def test_wrong_trade_mode(self):
        x=fixture();x[2]['v16']['real_orders_enabled']=True
        self.assertIn('v16:paper_only_required',verdict(*x)['boundary_issues'])

    def test_capture_timestamp_too_early(self):
        x=fixture();x[1]['generated_at_utc']=H1
        self.assertIn('sync_generated:before_hour_close',verdict(*x)['boundary_issues'])

    def test_universe_timestamp_too_early(self):
        x=fixture();x[0]['updated_at_utc']=H1
        self.assertIn('universe_updated:before_hour_close',verdict(*x)['boundary_issues'])

    def test_no_timezone(self):
        x=fixture();x[0]['verified_boundary']='2026-10-01T16:00:00'
        self.assertTrue(any('explicit_utc_required' in i for i in verdict(*x)['boundary_issues']))

    def test_minute_boundary(self):
        x=fixture();x[1]['target_latest_closed_hour']='2026-10-01T16:15:00Z'
        self.assertTrue(any('not_whole_hour' in i for i in verdict(*x)['boundary_issues']))

    def test_unauthorized_extra_track(self):
        x=fixture();x[2]['extra']={'mode':'PAPER_ONLY'}
        with self.assertRaises(ValueError):verdict(*x)

    def test_strict_json(self):
        for raw in ('{"a":1,"a":2}','{"bad":NaN}','{"bad":1e999}','[]'):
            with self.subTest(raw=raw),self.assertRaises(ValueError):witness.strict_json(raw)

    def test_zip_roundtrip(self):
        with tempfile.NamedTemporaryFile(suffix='.zip') as out:
            out.write(pack(fixture()));out.flush()
            x=witness.inspect_zip(out.name)
            self.assertEqual(len(x['tracks']),8)
            self.assertFalse(x['publication_authorized'])

    def test_zip_duplicate_paths(self):
        with tempfile.NamedTemporaryFile(suffix='.zip') as out:
            out.write(pack(fixture(),duplicate='reports/paper_v16_ledger.json'));out.flush()
            with self.assertRaisesRegex(ValueError,'duplicate_zip_paths'):
                witness.inspect_zip(out.name)


if __name__=='__main__':unittest.main()
