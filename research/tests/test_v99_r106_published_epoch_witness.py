"""Read-only independently auditable published R106 epoch witness tests."""
import copy
import hashlib
import json
import unittest

from research.tools.v99_r106_published_epoch_witness import inspect
from research.tests.test_v99_phase195gb_paper_epoch_audit import fixture,iso

AUDIT_AT=iso(5)


class TestPublishedWitness(unittest.TestCase):
    def sample(self):
        return json.dumps(fixture(),sort_keys=True).encode()

    def test_quarantine_and_provenance(self):
        raw=self.sample()
        r=inspect(raw,AUDIT_AT)
        self.assertEqual(r["status"],"DATA_ONLY_HOLD")
        self.assertEqual(r["raw_published_sha256"],hashlib.sha256(raw).hexdigest())
        self.assertEqual(r["distinct_forward_traces"],3)
        self.assertEqual(r["forward_duplicate_groups"],[["r98","f7","f12"]])
        for field in ("publication_authorized","promotion_authorized",
                      "independent_exchange_receipts_authenticated",
                      "full_trading_costs_authenticated",
                      "holdout_accessed_for_selection"):
            self.assertFalse(r[field],field)
        self.assertEqual(r["economic_trials"],0)

    def test_no_orders(self):
        data=fixture();data["real_orders_enabled"]=True
        with self.assertRaises(ValueError):
            inspect(json.dumps(data).encode(),AUDIT_AT)

    def test_missing_track_rejected(self):
        data=fixture();del data["variants"]["f1"]
        with self.assertRaises(ValueError):
            inspect(json.dumps(data).encode(),AUDIT_AT)

    def test_invalid_latest_hour_rejected(self):
        data=fixture();data["latest_data_timestamp"]=iso(-1)
        with self.assertRaises(ValueError):
            inspect(json.dumps(data).encode(),AUDIT_AT)

    def test_nonfinite_json_rejected(self):
        with self.assertRaises(ValueError):
            inspect(b'{"bad":NaN}',AUDIT_AT)

    def test_duplicate_keys_rejected(self):
        raw=self.sample()
        with self.assertRaises(ValueError):
            inspect(b'{"x":1,"x":2}',AUDIT_AT)

    def test_non_utc_observation_rejected(self):
        with self.assertRaises(ValueError):
            inspect(self.sample(),"2026-10-14T11:00:00-03:00")

    def test_input_must_be_bytes(self):
        with self.assertRaises(ValueError):
            inspect(self.sample().decode(),AUDIT_AT)

    def test_does_not_mutate_baseline(self):
        data=fixture();original=copy.deepcopy(data)
        inspect(json.dumps(data).encode(),AUDIT_AT)
        self.assertEqual(data,original)


if __name__=="__main__":unittest.main()
