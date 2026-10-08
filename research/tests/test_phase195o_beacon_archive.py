"""Phase195-O deterministic archive vs liveness controls."""
import io
import json
import pathlib
import sys
import unittest
import urllib.error

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from v99_phase195o_beacon_archive import OPERATORS, SLOT, probe, run

def header(slot=SLOT, canonical=True):
    return {"data": {"canonical": canonical, "header": {
        "message": {"slot": str(slot), "proposer_index": "1"}
    }}}

class Response:
    def __init__(self, payload):
        self.data = io.BytesIO(payload)
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False
    def read(self, n=-1):
        return self.data.read(n)

class Fake:
    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.urls = []
    def __call__(self, req, timeout):
        self.urls.append(req.full_url)
        item = self.payloads.pop(0)
        if isinstance(item, Exception):
            raise item
        if isinstance(item, dict):
            item = json.dumps(item).encode()
        return Response(item)

def http(status):
    return urllib.error.HTTPError("url", status, "test", None, None)

class TestArchive(unittest.TestCase):
    def test_two_control_and_historical_per_operator(self):
        f = Fake([header(SLOT + 1), header(), header(SLOT + 2), header()])
        result = run(f)
        self.assertEqual(result["decision"], "PROVISIONAL_HEADER_AVAILABILITY_UNANCHORED")
        self.assertEqual(f.urls, [
            base + "/eth/v1/beacon/headers/" + suffix
            for _, base in OPERATORS for suffix in ("finalized", str(SLOT))
        ])
        self.assertFalse(result["independent_consensus_anchor"])
        self.assertFalse(result["promotion_authorized"])
        self.assertEqual(result["economic_trials"], 0)

    def test_liveness_but_archive_missing(self):
        f = Fake([header(SLOT + 100), http(500), header(SLOT + 200), http(404)])
        self.assertEqual(run(f)["decision"], "HOLD_HISTORICAL_ARCHIVE_MISSING")

    def test_both_providers_down(self):
        self.assertEqual(run(Fake([http(503)] * 4))["decision"], "HOLD_PROVIDER_TRANSPORT_OR_SCHEMA")

    def test_wrong_historical_slot_safety_halt(self):
        f = Fake([header(SLOT + 1), header(SLOT + 1), http(500), http(500)])
        self.assertEqual(run(f)["decision"], "SAFETY_HALT_SLOT_MISMATCH")

    def test_historical_canonical_false_holds(self):
        r = probe("test", "https://example.org", str(SLOT), True, Fake([header(canonical=False)]))
        self.assertEqual(r["status"], "HOLD_CANONICALITY_NOT_REPORTED")

    def test_historical_slot_exact(self):
        r = probe("test", "https://example.org", str(SLOT), True, Fake([header()]))
        self.assertEqual(r["reported_slot"], SLOT)

    def test_bad_json_holds(self):
        r = probe("test", "https://example.org", "finalized", False, Fake([b"not json"]))
        self.assertEqual(r["status"], "HOLD_INVALID_RESPONSE")

    def test_bad_schema_holds(self):
        r = probe("test", "https://example.org", "finalized", False, Fake([{}]))
        self.assertEqual(r["status"], "HOLD_INVALID_RESPONSE")

    def test_oversize_holds(self):
        r = probe("test", "https://example.org", "finalized", False, Fake([b"x" * 1_000_001]))
        self.assertEqual(r["reason"], "oversize")

    def test_network_error_holds(self):
        r = probe("test", "https://example.org", "finalized", False, Fake([urllib.error.URLError("offline")]))
        self.assertEqual(r["status"], "HOLD_TRANSPORT")

    def test_deterministic_result(self):
        a = probe("test", "https://example.org", str(SLOT), True, Fake([header()]))
        b = probe("test", "https://example.org", str(SLOT), True, Fake([header()]))
        self.assertEqual(a, b)

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestArchive)
    outcome = unittest.TextTestRunner(verbosity=2).run(suite)
    if not outcome.wasSuccessful():
        raise SystemExit(1)
    print(json.dumps({"phase": "195-O", "controls": outcome.testsRun, "status": "PASS"}))
