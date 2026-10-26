"""Read-only historical inventory tests; synthetic provider responses only."""
import json
import unittest
from types import SimpleNamespace
from research.tools.v99_r106_i1_coinapi_inventory_probe import probe

class CoinAPIInventoryProbeTests(unittest.TestCase):
    def test_no_key_does_not_call_provider(self):
        def forbidden(*args, **kwargs):
            raise AssertionError("unexpected provider request")
        r = probe(api_key="", runner=forbidden)
        self.assertEqual(r["status"], "BLOCKED_NO_COINAPI_API_KEY")
        self.assertFalse(r["economic_train_executed"])

    def test_three_train_date_bounded_listings(self):
        calls = []
        def fake(args, **kwargs):
            calls.append(args)
            prefix = args[args.index("--prefix")+1]
            return SimpleNamespace(returncode=0, stdout=json.dumps({
                "IsTruncated": True,
                "Contents": [{"Key": prefix+"one.csv.gz", "Size": 42}]
            }), stderr="")
        r = probe(api_key="placeholder", runner=fake)
        self.assertEqual(len(calls), 3)
        self.assertEqual([x["date"] for x in r["dates"]],
                         ["2021-12-12", "2022-06-12", "2023-09-24"])
        self.assertEqual(r["status"], "BOUNDED_LISTING_ONLY_NO_HISTORICAL_COVERAGE_PROOF")
        self.assertFalse(r["btc_eth_lifecycle_certified"])
        self.assertFalse(r["promotion_authorized"])

    def test_error_does_not_echo_provider_response(self):
        def fake(*args, **kwargs):
            return SimpleNamespace(returncode=1, stdout="", stderr="PRIVATE")
        r = probe(api_key="placeholder", runner=fake)
        self.assertEqual(r["status"], "BLOCKED_AUTH_OR_PROVIDER_LISTING_ERROR")
        self.assertNotIn("PRIVATE", json.dumps(r))

    def test_wrong_prefix_fails_closed(self):
        def fake(*args, **kwargs):
            return SimpleNamespace(returncode=0, stdout=json.dumps({
                "IsTruncated": False,
                "Contents": [{"Key": "T-TRADES/D-20211212/x.gz", "Size": 4}]
            }), stderr="")
        r = probe(api_key="placeholder", runner=fake)
        self.assertEqual(r["status"], "BLOCKED_UNVERIFIABLE_PROVIDER_RESPONSE")

    def test_malformed_json_fails_closed(self):
        def fake(*args, **kwargs):
            return SimpleNamespace(returncode=0, stdout="<html>ok</html>", stderr="")
        r = probe(api_key="placeholder", runner=fake)
        self.assertEqual(r["status"], "BLOCKED_UNVERIFIABLE_PROVIDER_RESPONSE")

if __name__ == "__main__":
    unittest.main()
