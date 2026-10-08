"""Phase195-N adversarial synthetic controls; no network, no economic data."""
import copy
import io
import json
import pathlib
import sys
import unittest
import urllib.error

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from v99_phase195m_beacon_core import GENESIS
from v99_phase195n_beacon_probe import PROVIDERS, probe_one, run_probes

SLOT = 7_000_000
TS = GENESIS + SLOT * 12
BLOCK = {"timestamp": hex(TS), "hash": "0x" + "11" * 32, "receiptsRoot": "0x" + "22" * 32}

def beacon():
    return {
        "finalized": True, "execution_optimistic": False,
        "data": {"message": {"slot": str(SLOT), "body": {
            "execution_payload": {"block_number": "17000000", "timestamp": str(TS),
                                  "block_hash": BLOCK["hash"],
                                  "receipts_root": BLOCK["receiptsRoot"]}
        }}},
    }

class Response:
    def __init__(self, payload):
        self.payload = io.BytesIO(payload)
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False
    def read(self, n=-1):
        return self.payload.read(n)

class Fake:
    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.urls = []
    def __call__(self, req, timeout):
        self.urls.append(req.full_url)
        p = self.payloads.pop(0)
        if isinstance(p, Exception):
            raise p
        if isinstance(p, dict):
            p = json.dumps(p).encode()
        return Response(p)

class Controls(unittest.TestCase):
    def test_two_operator_parity_is_not_consensus_anchor(self):
        f = Fake([beacon(), beacon()])
        r = run_probes(BLOCK, f)
        self.assertEqual(r["decision"], "PROVISIONAL_TWO_PROVIDER_PARITY_UNANCHORED")
        self.assertFalse(r["independent_consensus_anchor"])
        self.assertFalse(r["promotion_authorized"])
        self.assertFalse(r["holdout_accessed"])
        self.assertEqual(r["economic_trials"], 0)
        self.assertEqual(f.urls, [base + "/eth/v2/beacon/blocks/" + str(SLOT) for _, base in PROVIDERS])

    def test_one_provider_does_not_claim_two(self):
        f = Fake([beacon(), urllib.error.HTTPError("url", 403, "forbidden", None, None)])
        r = run_probes(BLOCK, f)
        self.assertEqual(r["decision"], "PROVISIONAL_ONE_PROVIDER_PARITY_UNANCHORED")
        self.assertEqual(r["operators"][1]["http_status"], 403)

    def test_both_unavailable_hold(self):
        f = Fake([urllib.error.HTTPError("url", 404, "missing", None, None)] * 2)
        self.assertEqual(run_probes(BLOCK, f)["decision"], "HOLD_BEACON_ARCHIVE_UNAVAILABLE")

    def test_root_mismatch_halts_even_if_other_matches(self):
        x = beacon()
        x["data"]["message"]["body"]["execution_payload"]["receipts_root"] = "0x" + "33" * 32
        r = run_probes(BLOCK, Fake([beacon(), x]))
        self.assertEqual(r["decision"], "SAFETY_HALT_BEACON_MISMATCH")

    def test_hash_mismatch_halts(self):
        x = beacon()
        x["data"]["message"]["body"]["execution_payload"]["block_hash"] = "0x" + "33" * 32
        self.assertEqual(probe_one("x", "https://example.org", SLOT, BLOCK, Fake([x]))["status"], "SAFETY_HALT_MISMATCH")

    def test_wrong_slot_halts(self):
        x = beacon()
        x["data"]["message"]["slot"] = str(SLOT + 1)
        self.assertEqual(probe_one("x", "https://example.org", SLOT, BLOCK, Fake([x]))["status"], "SAFETY_HALT_MISMATCH")

    def test_wrong_height_halts(self):
        x = beacon()
        x["data"]["message"]["body"]["execution_payload"]["block_number"] = "17000001"
        self.assertEqual(probe_one("x", "https://example.org", SLOT, BLOCK, Fake([x]))["status"], "SAFETY_HALT_MISMATCH")

    def test_unfinalized_does_not_pass(self):
        x = beacon()
        x["finalized"] = False
        self.assertEqual(probe_one("x", "https://example.org", SLOT, BLOCK, Fake([x]))["status"], "HOLD_INVALID_RESPONSE")

    def test_optimistic_does_not_pass(self):
        x = beacon()
        x["execution_optimistic"] = True
        self.assertEqual(probe_one("x", "https://example.org", SLOT, BLOCK, Fake([x]))["status"], "HOLD_INVALID_RESPONSE")

    def test_bad_json_does_not_pass(self):
        self.assertEqual(probe_one("x", "https://example.org", SLOT, BLOCK, Fake([b"{"] ))["status"], "HOLD_INVALID_RESPONSE")

    def test_oversized_does_not_pass(self):
        self.assertEqual(probe_one("x", "https://example.org", SLOT, BLOCK, Fake([b"x" * 8_000_001]))["reason"], "oversize")

    def test_network_error_does_not_pass(self):
        r = probe_one("x", "https://example.org", SLOT, BLOCK, Fake([urllib.error.URLError("offline")]))
        self.assertEqual(r["status"], "HOLD_TRANSPORT")

    def test_reproducible_hash(self):
        a = probe_one("x", "https://example.org", SLOT, BLOCK, Fake([beacon()]))
        b = probe_one("x", "https://example.org", SLOT, BLOCK, Fake([beacon()]))
        self.assertEqual(a, b)

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Controls)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(json.dumps({"phase": "195-N", "synthetic_controls": result.testsRun, "status": "PASS", "economic_trials": 0}))
