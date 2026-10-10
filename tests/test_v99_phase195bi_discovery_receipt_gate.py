import copy
import unittest
from scripts.v99_phase195bi_discovery_receipt_gate import audit, first_safe_hour, strict_json, utc

def dynamic(discovered="2026-10-10T10:11:55+00:00", eligible="2026-10-10T12:00:00+00:00"):
    return {"source": "dynamic_binance_discovery", "start_month": "2026-06",
            "onboard_date": "2026-06-01T00:00:00+00:00",
            "discovered_at_utc": discovered, "eligible_after_timestamp": eligible}

def snap(symbols, new=(), decisions=()):
    return {"universe": {"symbols": symbols}, "sync": {"new_symbols": list(new)},
            "ledger": {"mode": "PAPER_ONLY", "decisions": list(decisions)}}

class TestDiscoveryReceipt(unittest.TestCase):
    def test_strictly_after_receipt(self):
        self.assertEqual(first_safe_hour("2026-10-10T10:00:00Z").isoformat(),
                         "2026-10-10T12:00:00+00:00")
    def test_valid_append_is_observation_only(self):
        r = audit(snap({}), snap({"AAA": dynamic()}, ["AAA"]))
        self.assertEqual(r["status"], "OBSERVED_ONLY_NOT_CERTIFIED")
        self.assertFalse(r["promotion_authorized"])
    def test_backdated_admission(self):
        r = audit(snap({}), snap({"AAA": dynamic(eligible="2026-10-10T09:00:00Z")}, ["AAA"]))
        self.assertIn("AAA", r["retroactive_eligibility"])
        self.assertEqual(r["status"], "DATA_ONLY_HOLD")
    def test_reissued_discovery(self):
        r = audit(snap({"AAA": dynamic()}), snap({"AAA": dynamic()}, ["AAA"]))
        self.assertEqual(r["reissued_new"], ["AAA"])
    def test_immutable_receipt_rewrite(self):
        r = audit(snap({"AAA": dynamic()}),
                  snap({"AAA": dynamic(discovered="2026-10-10T10:30:00Z")}))
        self.assertIn("discovered_at_utc", r["changed_immutable"]["AAA"])
    def test_unsafe_action(self):
        event = {"timestamp": "2026-10-10T10:00:00Z", "adjustments": [{"symbol": "AAA"}]}
        r = audit(snap({}), snap({"AAA": dynamic()}, ["AAA"], [event]))
        self.assertEqual(len(r["premature_observed_actions"]), 1)
    def test_next_hour_not_full_post_discovery_bar(self):
        event = {"timestamp": "2026-10-10T11:00:00Z", "adjustments": [{"symbol": "AAA"}]}
        r = audit(snap({}), snap({"AAA": dynamic()}, ["AAA"], [event]))
        self.assertEqual(len(r["premature_observed_actions"]), 1)
    def test_safe_observed_action_not_certification(self):
        event = {"timestamp": "2026-10-10T12:00:00Z", "adjustments": [{"symbol": "AAA"}]}
        r = audit(snap({}), snap({"AAA": dynamic()}, ["AAA"], [event]))
        self.assertFalse(r["premature_observed_actions"])
        self.assertFalse(r["publication_authorized"])
    def test_missing_receipt(self):
        row = dynamic();del row["discovered_at_utc"]
        with self.assertRaises(KeyError):
            audit(snap({}), snap({"AAA": row}, ["AAA"]))
    def test_unreported_new(self):
        r = audit(snap({}), snap({"AAA": dynamic()}))
        self.assertEqual(r["unreported_new"], ["AAA"])
    def test_removed_symbol(self):
        r = audit(snap({"AAA": dynamic()}), snap({}))
        self.assertEqual(r["removed"], ["AAA"])
    def test_duplicate_decisions(self):
        event = {"timestamp": "2026-10-10T11:00:00Z", "adjustments": []}
        with self.assertRaises(ValueError):
            audit(snap({}), snap({}, decisions=[event, event]))
    def test_utc_reject(self):
        for bad in ("2026-10-10T10:00:00", "2026-10-10T10:00:00-03:00"):
            with self.assertRaises(ValueError): utc(bad)
    def test_json_duplicate_and_nonfinite(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}'):
            with self.assertRaises(ValueError): strict_json(raw)

if __name__ == "__main__":
    unittest.main()
