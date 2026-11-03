#!/usr/bin/env python3
"""V98 alternate authorized exchange export negative controls; synthetic only."""
import csv
import datetime as dt
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v98_delivery_evidence_gate as gate
from v98_delivery_authorized_exchange_export import validate_export

START=gate.START
SLOT=gate.EIGHT_HOURS_MS
END=START+24*3600*1000
ASSETS=gate.ASSETS

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

class AlternateExchangeExport(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.expected={(a,START+i*SLOT):0.0001 for a in ASSETS for i in range(3)}
        self.rows=[{"symbol":a,"fundingTime":str(START+i*SLOT),
                    "fundingRate":"0.0001","markPrice":"100.00"}
                   for a in ASSETS for i in range(3)]
        self.export=self.root/"original_exchange_export.csv"
        self.attestation=self.root/"separate_custodian_statement.txt"
        self.attestation.write_text("SYNTHETIC TEST ONLY - NOT EXCHANGE PROOF\n")
        self.manifest={"source_type":"authorized_exchange_origin_export",
            "schema":"symbol,fundingTime,fundingRate,markPrice",
            "exchange_issuer":"SYNTHETIC_TEST_NOT_REAL",
            "independent_custodian":"SYNTHETIC_TEST_NOT_REAL",
            "custody_method":"SYNTHETIC_TEST_ONLY",
            "export_reference":"SYNTHETIC_TEST_ONLY",
            "captured_at_utc":"2026-11-02T06:00:00Z",
            "export_file":self.export.name,
            "custody_attestation_file":self.attestation.name,
            "custody_attestation_sha256":digest(self.attestation)}
        self.write()
    def write(self):
        with self.export.open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=["symbol","fundingTime","fundingRate","markPrice"])
            w.writeheader();w.writerows(self.rows)
        self.manifest["export_sha256"]=digest(self.export)
    def validate(self):
        return validate_export(self.root,self.manifest,self.expected,START,END,ASSETS,SLOT)
    def fails(self,code):
        with self.assertRaisesRegex(ValueError,"V98_AUTHORIZED_EXPORT_"+code):
            self.validate()
    def test_complete_alternate_transport_is_only_structural(self):
        meta,marks=self.validate()
        self.assertEqual(len(marks),12)
        self.assertFalse(meta["exchange_origin_independently_authenticated"])
        self.assertFalse(meta["pnl_computed"])
    def test_offset_at_60_seconds_is_valid(self):
        self.rows[0]["fundingTime"]=str(START+60000);self.write()
        self.assertEqual(self.validate()[1][(ASSETS[0],START)][0],START+60000)
    def test_offset_over_60_seconds_rejected(self):
        self.rows[0]["fundingTime"]=str(START+60001);self.write()
        self.fails("OFF_SLOT_GT_60S")
    def test_single_native_rate_tick_conflict_rejected(self):
        self.rows[0]["fundingRate"]="0.00010001";self.write()
        self.fails("NATIVE_FUNDING_RATE_CONFLICT")
    def test_native_rate_tolerance_boundary(self):
        # Match native JSON page gate: deviations <=1e-10 pass, >1e-10 fail.
        self.rows[0]["fundingRate"]="0.0001000001";self.write()
        self.assertEqual(len(self.validate()[1]),12)
        self.rows[0]["fundingRate"]="0.00010000011";self.write()
        self.fails("NATIVE_FUNDING_RATE_CONFLICT")
    def test_duplicate_event_rejected(self):
        self.rows[1]["fundingTime"]=self.rows[0]["fundingTime"];self.write()
        self.fails("OUTSIDE_TRAINING_OR_NONMONOTONIC")
    def test_2026_plus_never_accepted(self):
        self.rows[-1]["fundingTime"]=str(gate.END);self.write()
        self.fails("OUTSIDE_TRAINING_OR_NONMONOTONIC")
    def test_nonfinite_mark_rejected(self):
        self.rows[0]["markPrice"]="NaN";self.write()
        self.fails("MARK_NONFINITE")
    def test_zero_mark_rejected(self):
        self.rows[0]["markPrice"]="0";self.write()
        self.fails("RATE_OR_MARK_GEOMETRY")
    def test_fractional_timestamp_rejected(self):
        self.rows[0]["fundingTime"]=str(START)+".25";self.write()
        self.fails("NONINTEGER_TIMESTAMP")
    def test_export_tamper_rejected(self):
        self.export.write_text(self.export.read_text()+"tampered")
        self.fails("RAW_EXPORT_SHA256")
    def test_attestation_tamper_rejected(self):
        self.attestation.write_text("changed")
        self.fails("ATTESTATION_SHA256")
    def test_missing_custodian_rejected(self):
        self.manifest["independent_custodian"]=""
        self.fails("MISSING_INDEPENDENT_CUSTODIAN")
    def test_impossible_capture_before_source_end_rejected(self):
        self.manifest["captured_at_utc"]="2022-12-01T00:00:00Z"
        self.fails("IMPOSSIBLE_CAPTURE_TIME")
    def test_future_capture_timestamp_rejected(self):
        self.manifest["captured_at_utc"]="2099-01-01T00:00:00Z"
        self.fails("IMPOSSIBLE_CAPTURE_TIME")
    def test_unsafe_export_path_rejected(self):
        self.manifest["export_file"]="../outside.csv"
        self.fails("UNSAFE_PATH")
    def test_missing_event_rejected(self):
        self.rows.pop();self.write()
        self.fails("INCOMPLETE_1")
    def test_integration_requires_costs_before_publishing(self):
        (self.root/"authorized_exchange_export_manifest.json").write_text(json.dumps(self.manifest))
        with patch.object(gate,"expected_events",return_value=self.expected):
            held=gate.evaluate(self.root,self.export,"synthetic")
        self.assertEqual(held["decision"],"HOLD_MISSING_EXTERNAL_EVIDENCE")
        self.assertFalse((self.root/"v98_authorized_native_preflight.csv").exists())
        self._cost_fixture()
        with patch.object(gate,"expected_events",return_value=self.expected):
            passed=gate.evaluate(self.root,self.export,"synthetic")
        self.assertEqual(passed["decision"],"PASS_BYTE_AND_CALENDAR_PREFLIGHT_REQUIRES_INDEPENDENT_AUTHENTICATION")
        self.assertEqual(passed["native"]["event_count"],12)
        self.assertFalse(passed["native"]["exchange_origin_independently_authenticated"])
        self.assertFalse(passed["costs"]["independent_account_provenance_authenticated"])
        self.assertFalse(passed["paper_or_live_authorized"])
        self.assertTrue((self.root/"v98_authorized_native_preflight.csv").is_file())
    def test_integration_rejects_ambiguous_transports(self):
        (self.root/"authorized_exchange_export_manifest.json").write_text(json.dumps(self.manifest))
        (self.root/"authorized_funding_pages.jsonl").write_text("dummy")
        with patch.object(gate,"expected_events",return_value=self.expected):
            held=gate.evaluate(self.root,self.export,"synthetic")
        self.assertEqual(held["decision"],"HOLD_MISSING_EXTERNAL_EVIDENCE")
        self.assertIn("AMBIGUOUS",held["blocker"])
    def _cost_fixture(self):
        m={"fee_periods":[{"start_ms":gate.START,"end_ms":gate.END,
            "spot_taker_bps":1,"perp_taker_bps":1,"spot_spread_bps":1,
            "perp_spread_bps":1,"spot_impact_bps":1,"perp_impact_bps":1}]}
        for name in ("account_fee_schedule","historical_bid_ask_depth","collateral_liquidation_policy"):
            path=self.root/(name+".txt")
            path.write_text("SYNTHETIC TEST - NOT AN ACCOUNT PROOF")
            m[name]={"file":path.name,"sha256":digest(path),
                     "issuer":"SYNTHETIC_TEST","applicable_account_tier":"SYNTHETIC_TEST"}
        (self.root/"account_costs_manifest.json").write_text(json.dumps(m))

if __name__=="__main__":
    unittest.main()
