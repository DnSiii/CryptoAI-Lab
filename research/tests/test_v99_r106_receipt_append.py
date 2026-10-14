"""Permanent source-branch append invariants; no paper/holdout/network."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from research.tools import v99_r106_receipt_append as a

RECEIVED="2026-10-14T20:13:15+00:00"
DECISION="2026-10-14T22:00:00+00:00"
CLOSE="2026-10-14T20:00:00+00:00"

def source(dir):
    d=Path(dir);d.mkdir(parents=True,exist_ok=True)
    blobs={name:(name+": first-party fixture").encode() for name in a.EXPECTED if name!="manifest.json"}
    hashes={name:hashlib.sha256(raw).hexdigest() for name,raw in blobs.items()}
    for name,raw in blobs.items(): (d/name).write_bytes(raw)
    manifest={
        "schema":"V99_R106_OKX_PROSPECTIVE_ASOF_V1",
        "mode":"DATA_ONLY",
        "status":"FIRST_PARTY_OKX_HTTP_OBSERVED_DATA_ONLY",
        "last_received_utc":RECEIVED,
        "earliest_candidate_decision_utc":DECISION,
        "real_orders_enabled":False,
        "paper_publication_authorized":False,
        "promotion_authorized":False,
        "original_r106_binance_fee_and_funding_model_transfer_authorized":False,
        "clock_receipts":[{"sha256":hashes["clock_before.raw.json"]},
                          {"sha256":hashes["clock_after.raw.json"]}],
        "server_clock_corrob":{"before_ms":1792000000000,"after_ms":1792000001000},
        "instruments":{x:{"source_raw_sha256":hashes[x+".raw.json"],
                          "received_utc":RECEIVED,
                          "latest_confirmed_close_utc":CLOSE} for x in a.INSTRUMENTS},
    }
    (d/"manifest.json").write_text(json.dumps(manifest))
    return manifest

def save(d,m):
    (Path(d)/"manifest.json").write_text(json.dumps(m))

class AppendOnlyReceiptTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.input=self.root/"input"
        self.rec=self.root/"receipts"
        self.manifest=source(self.input)

    def test_first_receipt_is_appended_with_real_run_id(self):
        result=a.append(self.input,self.rec,"38630182430")
        self.assertEqual(result["status"],"APPENDED_NEW_FIRST_PARTY_RECEIPT")
        self.assertEqual(result["bucket"],"2026-10-14T20")
        self.assertTrue((self.rec/"2026-10-14T20"/"BTC-USDT-SWAP.raw.json").is_file())
        provenance=json.loads((self.rec/result["bucket"]/"receipt_commit_provenance.json").read_text())
        self.assertEqual(provenance["run_id"],"38630182430")
        self.assertFalse(provenance["paper_or_model_changes_allowed"])

    def test_same_hour_is_not_rewritten(self):
        first=a.append(self.input,self.rec,"38630182430")
        existing=(self.rec/first["bucket"]/"manifest.json").read_bytes()
        second=a.append(self.input,self.rec,"38630182431")
        self.assertEqual(second["status"],"ALREADY_PRESENT_UNCHANGED")
        self.assertEqual(existing,(self.rec/first["bucket"]/"manifest.json").read_bytes())

    def test_tampered_raw_json_rejected(self):
        (self.input/"BTC-USDT-SWAP.raw.json").write_bytes(b"tamper")
        with self.assertRaisesRegex(ValueError,"tampered"):
            a.append(self.input,self.rec,"38630182430")

    def test_missing_raw_rejected(self):
        (self.input/"ETH-USDT-SWAP.raw.json").unlink()
        with self.assertRaisesRegex(ValueError,"incomplete"):
            a.verify_source(self.input)

    def test_extra_file_rejected(self):
        (self.input/"unauthorized.conf").write_text("x")
        with self.assertRaisesRegex(ValueError,"unapproved"):
            a.verify_source(self.input)

    def test_no_paper_activation_from_receipt(self):
        m=copy.deepcopy(self.manifest);m["paper_publication_authorized"]=True
        save(self.input,m)
        with self.assertRaisesRegex(ValueError,"cannot authorize"):
            a.verify_source(self.input)

    def test_no_trading_from_receipt(self):
        m=copy.deepcopy(self.manifest);m["real_orders_enabled"]=True
        save(self.input,m)
        with self.assertRaisesRegex(ValueError,"cannot authorize"):
            a.verify_source(self.input)

    def test_no_backdated_eligibility(self):
        m=copy.deepcopy(self.manifest);m["earliest_candidate_decision_utc"]=RECEIVED
        save(self.input,m)
        with self.assertRaisesRegex(ValueError,"t-1"):
            a.verify_source(self.input)

    def test_unknown_instrument_rejected(self):
        m=copy.deepcopy(self.manifest)
        m["instruments"]["LUNA-USDT-SWAP"]=m["instruments"]["BTC-USDT-SWAP"]
        save(self.input,m)
        with self.assertRaisesRegex(ValueError,"five frozen"):
            a.verify_source(self.input)

    def test_invalid_run_id(self):
        with self.assertRaisesRegex(ValueError,"run ID"):
            a.append(self.input,self.rec,"fake")

    def test_non_utc_observation_rejected(self):
        m=copy.deepcopy(self.manifest)
        m["last_received_utc"]="2026-10-14T17:13:15-03:00"
        save(self.input,m)
        with self.assertRaisesRegex(ValueError,"explicit UTC"):
            a.verify_source(self.input)

if __name__=="__main__":
    unittest.main()
