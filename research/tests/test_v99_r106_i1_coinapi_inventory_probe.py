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

class FixedTargetCoinAPIListingTests(unittest.TestCase):
    """Preselected 2022-01-23 original source listing; fixtures are NOT quotes."""

    @staticmethod
    def obj(asset):
        symbol = asset + "-25FEB22-" + ("50000" if asset == "BTC" else "3000") + "-P"
        return {
            "Key": "T-QUOTES/D-20220123/E-DERIBIT/"
                   "IDDI-123+SC-DERIBIT_OPT_" + asset + "_USD+S-" + symbol + ".csv.gz",
            "Size": 1048576,
        }

    def test_missing_key_makes_no_network_call(self):
        from research.tools.v99_r106_i1_coinapi_inventory_probe import probe_target
        def forbidden(*a, **kw):
            raise AssertionError("MUST_NOT_CALL_PROVIDER_WITHOUT_KEY")
        result = probe_target(api_key="", runner=forbidden)
        self.assertEqual(result["status"], "BLOCKED_NO_COINAPI_API_KEY")
        self.assertEqual(result["target_utc_day"], "2022-01-23")
        self.assertFalse(result["economic_train_executed"])

    def test_complete_paginated_btc_eth_put_inventory_is_only_listing(self):
        from research.tools.v99_r106_i1_coinapi_inventory_probe import probe_target
        calls = []
        def fake(args, **kw):
            calls.append(args)
            self.assertEqual(args[1:3], ["s3api", "list-objects-v2"])
            self.assertIn("T-QUOTES/D-20220123/E-DERIBIT/", args)
            self.assertNotIn("get-object", args)
            self.assertNotIn("s3", args)
            if len(calls) == 1:
                payload = {"IsTruncated": True, "NextContinuationToken": "NEXT",
                           "Contents": [self.obj("BTC")]}
            else:
                self.assertIn("--continuation-token", args)
                payload = {"IsTruncated": False, "Contents": [self.obj("ETH")]}
            return SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")
        result = probe_target(api_key="secret-coinapi", runner=fake)
        self.assertEqual(result["pages_listed"], 2)
        self.assertEqual(result["objects_listed"], 2)
        self.assertEqual(result["compressed_bytes_listed"], 2097152)
        self.assertEqual(result["btc_put_files_listed"], 1)
        self.assertEqual(result["eth_put_files_listed"], 1)
        self.assertTrue(result["listing_complete"])
        self.assertEqual(result["status"],
                         "BTC_ETH_PUT_OBJECTS_BUT_NO_FIXED_TENOR_PAIR_PROOF")
        self.assertFalse(result["fixed_tenor_pair_inventory_shown"])
        self.assertFalse(result["original_24h_bbo_and_size_certified"])
        self.assertFalse(result["historical_license_and_fee_terms_certified"])
        self.assertFalse(result["promotion_authorized"])
        self.assertNotIn("secret-coinapi", json.dumps(result))

    def test_ex_ante_28_35d_same_expiry_two_strike_presence_only(self):
        from research.tools.v99_r106_i1_coinapi_inventory_probe import probe_target
        def obj(asset, expiry, strike):
            name = asset + "-" + expiry + "-" + str(strike) + "-P"
            return {"Key": "T-QUOTES/D-20220123/E-DERIBIT/"
                    "IDDI-123+SC-DERIBIT_OPT_" + asset + "_USD+S-" + name + ".csv.gz",
                    "Size": 500}
        # 21FEB22 expires at 08:00 UTC: 28d8h after fixed 24JAN 00:00.
        # 28FEB22 expires at 35d8h and is therefore ineligible.
        items = [obj(a, "21FEB22", k) for a in ("BTC", "ETH")
                 for k in ((50000, 49000) if a == "BTC" else (3000, 2900))]
        items += [obj("BTC", "28FEB22", 48000)]
        def fake(*a, **kw):
            return SimpleNamespace(returncode=0, stdout=json.dumps({
                "IsTruncated": False, "Contents": items}), stderr="")
        result = probe_target(api_key="key", runner=fake)
        self.assertEqual(result["fixed_tenor_candidate_files_by_asset"],
                         {"BTC": 2, "ETH": 2})
        self.assertEqual(result["fixed_tenor_two_strike_expiries_by_asset"],
                         {"BTC": 1, "ETH": 1})
        self.assertTrue(result["fixed_tenor_pair_inventory_shown"])
        self.assertEqual(result["status"],
                         "FIXED_TENOR_PAIR_OBJECTS_LISTED_NOT_QUOTES_OR_FILLS")
        self.assertFalse(result["original_24h_bbo_and_size_certified"])
        self.assertFalse(result["promotion_authorized"])

    def test_two_strikes_on_different_expiries_do_not_make_vertical(self):
        from research.tools.v99_r106_i1_coinapi_inventory_probe import probe_target
        items = []
        for asset in ("BTC", "ETH"):
            for expiry, strike in (("21FEB22", 50000), ("25FEB22", 49000)):
                items.append({"Key": "T-QUOTES/D-20220123/E-DERIBIT/"
                              "IDDI-123+SC-DERIBIT_OPT_" + asset + "_USD+S-"
                              + asset + "-" + expiry + "-" + str(strike) + "-P.csv.gz",
                              "Size": 100})
        def fake(*a, **kw):
            return SimpleNamespace(returncode=0, stdout=json.dumps({
                "IsTruncated": False, "Contents": items}), stderr="")
        result = probe_target(api_key="key", runner=fake)
        self.assertEqual(result["fixed_tenor_two_strike_expiries_by_asset"],
                         {"BTC": 0, "ETH": 0})
        self.assertFalse(result["fixed_tenor_pair_inventory_shown"])
        self.assertEqual(result["status"],
                         "BTC_ETH_PUT_OBJECTS_BUT_NO_FIXED_TENOR_PAIR_PROOF")

    def test_wrong_exchange_and_duplicate_key_fail_closed(self):
        from research.tools.v99_r106_i1_coinapi_inventory_probe import probe_target
        bad = dict(self.obj("BTC"))
        bad["Key"] = bad["Key"].replace("E-DERIBIT", "E-BINANCE")
        for objects in ([bad], [self.obj("BTC"), self.obj("BTC")]):
            with self.subTest(objects=objects):
                def fake(*a, **kw):
                    return SimpleNamespace(returncode=0, stdout=json.dumps({
                        "IsTruncated": False, "Contents": objects}), stderr="")
                result = probe_target(api_key="key", runner=fake)
                self.assertEqual(result["status"],
                                 "BLOCKED_UNVERIFIABLE_TARGET_PROVIDER_LISTING")
                self.assertFalse(result["listing_complete"])

    def test_truncation_without_token_and_page_cap_do_not_claim_complete(self):
        from research.tools.v99_r106_i1_coinapi_inventory_probe import probe_target
        def fake(*a, **kw):
            return SimpleNamespace(returncode=0, stdout=json.dumps({
                "IsTruncated": True, "Contents": [self.obj("BTC")],
                "NextContinuationToken": "NEXT"}), stderr="")
        result = probe_target(api_key="key", runner=fake, max_pages=1)
        self.assertEqual(result["status"], "BLOCKED_TARGET_LISTING_PAGE_CAP")
        self.assertFalse(result["listing_complete"])
        def no_token(*a, **kw):
            return SimpleNamespace(returncode=0, stdout=json.dumps({
                "IsTruncated": True, "Contents": [self.obj("BTC")]}), stderr="")
        result = probe_target(api_key="key", runner=no_token)
        self.assertEqual(result["status"],
                         "BLOCKED_UNVERIFIABLE_TARGET_PROVIDER_LISTING")
        self.assertFalse(result["listing_complete"])

    def test_nonoption_and_single_asset_are_not_btc_eth_presence(self):
        from research.tools.v99_r106_i1_coinapi_inventory_probe import probe_target
        item = self.obj("BTC")
        def fake(*a, **kw):
            return SimpleNamespace(returncode=0, stdout=json.dumps({
                "IsTruncated": False, "Contents": [item, {
                    "Key": "T-QUOTES/D-20220123/E-DERIBIT/"
                           "IDDI-12+SC-DERIBIT_PERP_BTC+S-BTC-PERPETUAL.csv.gz",
                    "Size": 300}]}), stderr="")
        result = probe_target(api_key="key", runner=fake)
        self.assertEqual(result["btc_put_files_listed"], 1)
        self.assertEqual(result["eth_put_files_listed"], 0)
        self.assertEqual(result["status"],
                         "TARGET_BTC_ETH_PUT_OBJECT_PRESENCE_NOT_SHOWN")
        self.assertFalse(result["economic_train_executed"])


if __name__ == "__main__":
    unittest.main()
