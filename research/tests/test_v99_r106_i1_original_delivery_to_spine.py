"""Source-only delivery-calendar join controls. Synthetic prices are NOT economics."""
import copy
import json
import unittest
from datetime import date, datetime, timedelta, timezone
from research.tools.v99_r106_i1_original_delivery_to_spine import bind
from research.verification.independent_v99_r106_i1_delivery_spine_oracle import verify

FIRST = date(2021, 12, 9)
DAYS = 661
CLOCK = 1639094399000
DAY_MS = 86_400_000


def make_spine():
    rows = [{"ts_ms": CLOCK+i*DAY_MS, "market_events": []} for i in range(DAYS)]
    expiry_ms = 1642147200000  # 2022-01-14 08:00:00 UTC
    i = (date(2022, 1, 14)-FIRST).days
    open_day = date(2021, 12, 13)
    open_i = (open_day-FIRST).days
    open_ms = int(datetime(2021, 12, 13, tzinfo=timezone.utc).timestamp()*1000)
    short, long = "BTC-14JAN22-50000-P", "BTC-14JAN22-45000-P"
    rows[open_i]["market_events"].append({
        "kind": "OPEN_SOURCE_ONLY", "at_ms": open_ms, "asset": "BTC",
        "position_id": "BTC-W1", "signal_source": "ORIGINAL_FIXED_180_GRID",
        "candidate_inventory": [{"symbol": short}, {"symbol": long}],
        "short_symbol_unverified_selection": short,
        "long_symbol_unverified_selection": long,
    })
    rows[i]["market_events"].append({
        "kind": "SETTLEMENT_DUE_SOURCE_ONLY", "at_ms": expiry_ms,
        "asset": "BTC", "position_id": "BTC-W1", "delivery_index_missing": True})
    return {
        "schema": "V99_I1_SOURCE_DRIVEN_661D_MARK_EVENT_SPINE_V1",
        "status": "ORIGINAL_MARKET_SPINE_ONLY_NOT_ECONOMIC_JOURNAL",
        "days": rows, "expiry_due_count": 1,
        "unverified_position_plan_count": 1,
        "native_economic_train_executed": False,
        "original_complete_option_lifecycles_certified": 0,
        "promotion_authorized": False, "freeze_authorized": False,
        "orders_enabled": False, "validation_opened": False,
        "holdout_opened": False, "paper_publication_authorized": False,
    }


def make_delivery():
    return {
        "schema": "V99_I1_DERIBIT_TRAIN_DELIVERY_PRICE_RECEIPTS_V1",
        "read_only": True, "no_orders": True, "no_promotion": True,
        "not_executable_quotes": True,
        "assets": {index: {
            "index": index,
            "source": "https://www.deribit.com/api/v2/public/get_delivery_prices",
            "train_start": FIRST.isoformat(),
            "train_end_exclusive": (FIRST+timedelta(days=DAYS)).isoformat(),
            "pages": [{"offset": 0, "sha256_canonical_data_rows": "f"*64, "records": 100}],
            "records": [{"date": (FIRST+timedelta(days=i)).isoformat(),
                         "delivery_price": 42000.0 if index == "btc_usd" else 3000.0}
                        for i in range(DAYS)],
        } for index in ("btc_usd", "eth_usd")},
    }


def raw_bytes(delivery):
    return json.dumps(delivery, sort_keys=True).encode("utf-8")


class DeliverySourceSpineTests(unittest.TestCase):
    def setUp(self):
        self.spine = make_spine()
        self.delivery = make_delivery()

    def test_calendar_join_and_independent_replay(self):
        raw = raw_bytes(self.delivery)
        result = bind(self.spine, self.delivery, raw)
        i = (date(2022,1,14)-FIRST).days
        e = result["days"][i]["market_events"][0]
        self.assertEqual(e["delivery_calendar_index_name"], "btc_usd")
        self.assertEqual(e["delivery_calendar_date"], "2022-01-14")
        self.assertEqual(e["delivery_calendar_price_usd"], "42000.0")
        self.assertFalse(result["original_delivery_index_authenticated"])
        self.assertFalse(result["promotion_authorized"])
        self.assertEqual(verify(self.spine, raw, result)["independent_calendar_settlement_events"], 1)

    def test_independent_oracle_rejects_forged_delivery(self):
        raw = raw_bytes(self.delivery)
        result = bind(self.spine, self.delivery, raw)
        i = (date(2022,1,14)-FIRST).days
        result["days"][i]["market_events"][0]["delivery_calendar_price_usd"] = "999999"
        with self.assertRaisesRegex(ValueError, "ORACLE_BOUND_SPINE"):
            verify(self.spine, raw, result)

    def test_missing_duplicate_and_shifted_firstparty_calendar(self):
        for mutation in ("missing", "duplicate", "shift"):
            payload = copy.deepcopy(self.delivery)
            rows = payload["assets"]["btc_usd"]["records"]
            if mutation == "missing":
                rows.pop(10)
            elif mutation == "duplicate":
                rows[10]["date"] = rows[9]["date"]
            else:
                rows[10]["date"] = "2024-01-18"
            with self.subTest(mutation=mutation):
                with self.assertRaisesRegex(ValueError, "INCOMPLETE_FIRSTPARTY|MISSING_DUPLICATED"):
                    bind(self.spine, payload, raw_bytes(payload))

    def test_nonfinite_price_and_false_source_claim(self):
        for value in ("NaN", "Infinity", "-1", "0", True):
            payload = copy.deepcopy(self.delivery)
            payload["assets"]["eth_usd"]["records"][10]["delivery_price"] = value
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "INVALID_FIRSTPARTY_DELIVERY_PRICE"):
                    bind(self.spine, payload, raw_bytes(payload))
        self.spine["promotion_authorized"] = True
        with self.assertRaisesRegex(ValueError, "UNVERIFIED_OR_INCOMPLETE_SOURCE_SPINE"):
            bind(self.spine, self.delivery, raw_bytes(self.delivery))

    def test_expiry_shift_and_duplicate_settlement_rejected(self):
        i = (date(2022,1,14)-FIRST).days
        e = self.spine["days"][i]["market_events"][0]
        e["at_ms"] += DAY_MS
        with self.assertRaisesRegex(ValueError, "SEALED_OR_SHIFTED_SETTLEMENT_DATE"):
            bind(self.spine, self.delivery, raw_bytes(self.delivery))
        e["at_ms"] -= DAY_MS
        self.spine["days"][i]["market_events"].append(copy.deepcopy(e))
        self.spine["expiry_due_count"] = 2
        self.spine["unverified_position_plan_count"] = 2
        with self.assertRaisesRegex(ValueError, "DUPLICATED_SETTLEMENT_POSITION"):
            bind(self.spine, self.delivery, raw_bytes(self.delivery))

    def test_settlement_requires_original_open_contract_lineage(self):
        raw = raw_bytes(self.delivery)
        open_i = (date(2021, 12, 13)-FIRST).days
        expiry_i = (date(2022, 1, 14)-FIRST).days
        for mutation in ("no_open", "wrong_expiry", "wrong_asset", "not_in_inventory"):
            spine = copy.deepcopy(self.spine)
            opening = spine["days"][open_i]["market_events"]
            if mutation == "no_open":
                opening.clear()
            elif mutation == "wrong_expiry":
                opening[0]["long_symbol_unverified_selection"] = "BTC-21JAN22-45000-P"
                opening[0]["candidate_inventory"].append({"symbol": "BTC-21JAN22-45000-P"})
            elif mutation == "wrong_asset":
                opening[0]["asset"] = "ETH"
            else:
                opening[0]["candidate_inventory"].pop()
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    bind(spine, self.delivery, raw)
                with self.assertRaises(ValueError):
                    verify(spine, raw, bind(self.spine, self.delivery, raw))
        changed = copy.deepcopy(self.spine)
        changed["days"][expiry_i]["market_events"][0]["position_id"] = "INVENTED"
        with self.assertRaisesRegex(ValueError, "SETTLEMENT_NOT_LINKED"):
            bind(changed, self.delivery, raw)
        with self.assertRaisesRegex(ValueError, "ORACLE_SETTLEMENT_CONTRACT"):
            verify(changed, raw, bind(self.spine, self.delivery, raw))

    def test_missing_firstparty_artifact_rejected(self):
        with self.assertRaisesRegex(ValueError, "UNTRUSTED_FIRSTPARTY"):
            bind(self.spine, {}, b"{}")


if __name__ == "__main__":
    unittest.main()
