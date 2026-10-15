"""Adversarial synthetic atomic pair fixture tests, no network."""
import json,tempfile,unittest
from pathlib import Path
from research.tests import test_v99_r106_receipt_append as mfix
from research.tests import test_v99_r106_terms_append as tfix
from research.tools import v99_r106_atomic_source_pair as pair

class TestAtomicPair(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        root=Path(tmp.name);self.m=root/"market";self.t=root/"terms";self.dest=root/"receipt"
        mfix.source(self.m);tfix.prepare(self.t)
    def test_append_both_same_hour_and_run_id(self):
        out=pair.append_pair(self.m,self.t,self.dest,"38800000000")
        self.assertEqual(out["status"],"ATOMIC_PAIRED_RECEIPT_APPENDED")
        self.assertEqual(out["bucket"],"2026-10-14T20")
        self.assertFalse(out["promotion_authorized"]);self.assertEqual(out["economic_trials"],0)
        for stream in ("v99_r106_okx","v99_r106_okx_terms"):
            p=self.dest/stream/"2026-10-14T20"/"receipt_commit_provenance.json"
            self.assertEqual(json.loads(p.read_text())["run_id"],"38800000000")
    def test_second_capture_never_overwrites(self):
        pair.append_pair(self.m,self.t,self.dest,"38800000000")
        p=self.dest/"v99_r106_okx"/"2026-10-14T20"/"manifest.json"
        old=p.read_bytes()
        out=pair.append_pair(self.m,self.t,self.dest,"38800000001")
        self.assertEqual(out["status"],"ALREADY_PAIRED_UNCHANGED")
        self.assertFalse(out["changed"]);self.assertEqual(p.read_bytes(),old)
    def test_partial_hour_must_not_be_backfilled(self):
        p=self.dest/"v99_r106_okx"/"2026-10-14T20"
        p.mkdir(parents=True);(p/"marker").write_text("immutable")
        out=pair.append_pair(self.m,self.t,self.dest,"38800000000")
        self.assertEqual(out["status"],"DATA_ONLY_HOLD_PARTIAL_PREEXISTING_HOUR")
        self.assertFalse((self.dest/"v99_r106_okx_terms"/"2026-10-14T20").exists())
    def test_wrong_hour_fails_closed(self):
        p=self.t/"manifest.json";j=json.loads(p.read_text())
        j["acquisition_last_utc"]="2026-10-14T21:01:28+00:00"
        j["earliest_safe_decision_utc"]="2026-10-14T23:00:00+00:00"
        for x in j["contracts"].values():
            x["contract_received_utc"]=j["acquisition_last_utc"]
            x["funding_received_utc"]=j["acquisition_last_utc"]
        p.write_text(json.dumps(j))
        with self.assertRaisesRegex(ValueError,"crossed_utc_hour"):
            pair.append_pair(self.m,self.t,self.dest,"38800000000")
        self.assertFalse(self.dest.exists())
    def test_corrupt_source_denied(self):
        (self.m/"BTC-USDT-SWAP.raw.json").write_bytes(b"corrupt")
        with self.assertRaisesRegex(ValueError,"tampered"):
            pair.append_pair(self.m,self.t,self.dest,"38800000000")
    def test_tminus1_mismatch_denied(self):
        p=self.t/"manifest.json";j=json.loads(p.read_text());j["earliest_safe_decision_utc"]=j["acquisition_last_utc"]
        p.write_text(json.dumps(j))
        with self.assertRaisesRegex(ValueError,"t-1"):
            pair.append_pair(self.m,self.t,self.dest,"38800000000")
    def test_fake_run_denied(self):
        with self.assertRaisesRegex(ValueError,"real_actions_run_id"):
            pair.append_pair(self.m,self.t,self.dest,"fake")
if __name__=="__main__":unittest.main()
