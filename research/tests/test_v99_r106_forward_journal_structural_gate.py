"""Adversarial structural checks only; never publish or create trades."""
import hashlib
import unittest
from research.tools.v99_r106_forward_journal_structural_gate import canonical, verify, MODE

class JournalGateTests(unittest.TestCase):
    def setUp(self):
        self.provenance = {"epoch_id":"forward-2","epoch_start_utc":"2026-11-12T00:00:00Z",
            "status":"RECEIPTS_PRECHECK_PASS_NOT_PUBLICATION_AUTHORIZATION","errors":[]}
        self.journal = {"epoch_id":"forward-2","epoch_start_utc":"2026-11-12T00:00:00Z",
            "mode":MODE,"initial_capital":"1000","events":[],"head_hash":"0"*64}

    def test_empty_journal_never_authorizes_publication(self):
        r=verify(self.journal,self.provenance)
        self.assertFalse(r["publication_authorized"])
        self.assertFalse(r["economic_validation_complete"])

    def test_bad_capital(self):
        for x in ["NaN","Infinity","-1","0","garbage"]:
            with self.subTest(x=x):
                self.journal["initial_capital"]=x
                self.assertIn("INVALID_INITIAL_CAPITAL",verify(self.journal,self.provenance)["errors"])

    def test_provenance_failure(self):
        self.provenance["status"]="BLOCKED"
        self.assertIn("PROVENANCE_NOT_VERIFIED",verify(self.journal,self.provenance)["errors"])

    def test_real_order_mode_rejected(self):
        self.journal["mode"]="LIVE"
        self.assertIn("UNSAFE_MODE",verify(self.journal,self.provenance)["errors"])

    def test_hash_chain_tampering(self):
        e={"type":"MARK","event_id":"a","event_utc":"2026-11-12T01:00:00Z",
           "receipt_sha256":"a"*64,"prev_hash":"0"*64}
        e["hash"]=hashlib.sha256(canonical(e)).hexdigest()
        self.journal["events"]=[e]
        self.journal["head_hash"]=e["hash"]
        self.assertEqual(verify(self.journal,self.provenance)["status"],"STRUCTURAL_PRECHECK_ONLY")
        e["event_id"]="tampered"
        self.assertIn("EVENT_0_HASH_MISMATCH",verify(self.journal,self.provenance)["errors"])

    def test_unsettled_funding(self):
        e={"type":"FUNDING","event_id":"f","event_utc":"2026-11-12T01:00:00Z",
           "receipt_sha256":"b"*64,"prev_hash":"0"*64}
        e["hash"]=hashlib.sha256(canonical(e)).hexdigest()
        self.journal["events"]=[e]
        self.journal["head_hash"]=e["hash"]
        self.assertIn("EVENT_0_UNSETTLED_FUNDING",verify(self.journal,self.provenance)["errors"])


    def test_malformed_receipt_hash_rejected_even_when_length_is_64(self):
        e={"type":"MARK","event_id":"bad-hash","event_utc":"2026-11-12T01:00:00Z",
           "receipt_sha256":"z"*64,"prev_hash":"0"*64}
        e["hash"]=hashlib.sha256(canonical(e)).hexdigest()
        self.journal["events"]=[e]
        self.journal["head_hash"]=e["hash"]
        self.assertIn("EVENT_0_MISSING_RECEIPT_HASH",verify(self.journal,self.provenance)["errors"])

    def test_invalid_utc_calendar_timestamp_rejected(self):
        e={"type":"MARK","event_id":"bad-time","event_utc":"2026-99-99T01:00:00Z",
           "receipt_sha256":"a"*64,"prev_hash":"0"*64}
        e["hash"]=hashlib.sha256(canonical(e)).hexdigest()
        self.journal["events"]=[e]
        self.journal["head_hash"]=e["hash"]
        self.assertIn("EVENT_0_INVALID_ORDER",verify(self.journal,self.provenance)["errors"])

if __name__=="__main__":
    unittest.main()
