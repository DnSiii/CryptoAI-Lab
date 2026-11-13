"""Raw-byte binding adversarial checks; no trading or historical mutation."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from research.tools.v99_r106_forward_raw_receipt_binding import audit
from research.tools.v99_r106_forward_journal_structural_gate import canonical, MODE

class RawBindingTests(unittest.TestCase):
    def test_authentic_vs_forged_and_wrong_kind(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            raw=b'original exchange receipt bytes'
            (root/'receipt.json').write_bytes(raw)
            digest=hashlib.sha256(raw).hexdigest()
            manifest={"mode":MODE,"epoch_id":"forward-2","epoch_start_utc":"2026-11-12T00:00:00Z",
                "receipts":[{"venue":"OKX","symbol":"BTC-USDT-SWAP","kind":"execution",
                "close_utc":"2026-11-12T00:00:00Z","acquired_utc":"2026-11-12T00:00:00Z",
                "source_url_or_archive_id":"immutable-test-source","raw_file":"receipt.json",
                "sha256":digest,"fee_tier":"maker"}]}
            event={"type":"FILL","event_id":"f1","event_utc":"2026-11-12T01:00:00Z",
                "receipt_sha256":digest,"prev_hash":"0"*64,"fill_id":"f1",
                "fee_tier":"maker","executed_qty":"1","executed_price":"100"}
            event["hash"]=hashlib.sha256(canonical(event)).hexdigest()
            journal={"mode":MODE,"epoch_id":"forward-2","epoch_start_utc":"2026-11-12T00:00:00Z",
                "initial_capital":"1000","events":[event],"head_hash":event["hash"]}
            good=audit(journal,manifest,root)
            self.assertEqual(good["status"],"RAW_RECEIPT_BINDING_PRECHECK_ONLY")
            self.assertFalse(good["publication_authorized"])
            (root/'receipt.json').write_bytes(b'forged bytes')
            self.assertEqual(audit(journal,manifest,root)["status"],"BLOCKED")
            (root/'receipt.json').write_bytes(raw)
            # A genuine post-epoch receipt is not an as-of historical receipt.
            manifest["receipts"][0]["close_utc"]="2026-11-12T01:00:00Z"
            manifest["receipts"][0]["acquired_utc"]="2026-11-12T01:00:00Z"
            self.assertEqual(audit(journal,manifest,root)["status"],"RAW_RECEIPT_BINDING_PRECHECK_ONLY")
            # Future acquisition must never be used to justify a past event.
            manifest["receipts"][0]["acquired_utc"]="2026-11-12T02:00:00Z"
            self.assertIn("EVENT_0_RECEIPT_ACQUIRED_AFTER_EVENT",audit(journal,manifest,root)["errors"])
            manifest["receipts"][0]["acquired_utc"]="2026-11-12T01:00:00Z"
            event["receipt_sha256"]="f"*64
            event["hash"]=hashlib.sha256(canonical({k:v for k,v in event.items() if k!="hash"})).hexdigest()
            journal["head_hash"]=event["hash"]
            self.assertIn("EVENT_0_NO_AUTHENTIC_RAW_RECEIPT",audit(journal,manifest,root)["errors"])
            event["receipt_sha256"]=digest
            event["hash"]=hashlib.sha256(canonical({k:v for k,v in event.items() if k!="hash"})).hexdigest()
            journal["head_hash"]=event["hash"]
            manifest["receipts"][0]["kind"]="funding"
            manifest["receipts"][0]["settlement_event_id"]="s1"
            self.assertIn("EVENT_0_WRONG_RECEIPT_KIND",audit(journal,manifest,root)["errors"])

if __name__=="__main__":
    unittest.main()
