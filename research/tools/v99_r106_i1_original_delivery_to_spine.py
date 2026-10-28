"""Bind first-party Deribit TRAIN delivery-calendar fixes to source-only expiry events.

Does NOT authenticate native contract settlement index, fees, margin, fills,
or original options tape. No NAV, PnL, orders or promotion.
Prereg: V99_R106_I1_ORIGINAL_DELIVERY_TO_SPINE_PREREG_20261028.md.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

START = date(2021, 12, 9)
END = date(2023, 10, 1)
DAYS = (END - START).days
START_CLOCK_MS = 1639094399000
DAY_MS = 86_400_000
SCHEMA = "V99_I1_FIRSTPARTY_DELIVERY_CALENDAR_SOURCE_SPINE_V1"
SOURCE_SCHEMA = "V99_I1_SOURCE_DRIVEN_661D_MARK_EVENT_SPINE_V1"
DELIVERY_SCHEMA = "V99_I1_DERIBIT_TRAIN_DELIVERY_PRICE_RECEIPTS_V1"
SOURCE_STATUS = "ORIGINAL_MARKET_SPINE_ONLY_NOT_ECONOMIC_JOURNAL"
DENIED = ("promotion_authorized", "freeze_authorized", "orders_enabled",
          "validation_opened", "holdout_opened", "paper_publication_authorized")


def _price(value):
    if isinstance(value, bool):
        raise ValueError("INVALID_FIRSTPARTY_DELIVERY_PRICE")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("INVALID_FIRSTPARTY_DELIVERY_PRICE") from exc
    if not number.is_finite() or number <= 0:
        raise ValueError("INVALID_FIRSTPARTY_DELIVERY_PRICE")
    return number


def validate_delivery(payload):
    if (not isinstance(payload, dict) or payload.get("schema") != DELIVERY_SCHEMA
            or payload.get("read_only") is not True
            or payload.get("no_orders") is not True
            or payload.get("no_promotion") is not True
            or payload.get("not_executable_quotes") is not True
            or not isinstance(payload.get("assets"), dict)
            or set(payload["assets"]) != {"btc_usd", "eth_usd"}):
        raise ValueError("UNTRUSTED_FIRSTPARTY_DELIVERY_ARTIFACT")
    lookup = {}
    for index in ("btc_usd", "eth_usd"):
        part = payload["assets"][index]
        if (not isinstance(part, dict) or part.get("index") != index
                or part.get("source") != "https://www.deribit.com/api/v2/public/get_delivery_prices"
                or part.get("train_start") != START.isoformat()
                or part.get("train_end_exclusive") != END.isoformat()
                or not isinstance(part.get("pages"), list) or not part["pages"]
                or not isinstance(part.get("records"), list)
                or len(part["records"]) != DAYS):
            raise ValueError("INCOMPLETE_FIRSTPARTY_DELIVERY_CALENDAR:" + index)
        by_day = {}
        for n, record in enumerate(part["records"]):
            if not isinstance(record, dict) or set(record) != {"date", "delivery_price"}:
                raise ValueError("INVALID_FIRSTPARTY_DELIVERY_ROW")
            expected = (START + timedelta(days=n)).isoformat()
            if record["date"] != expected:
                raise ValueError("MISSING_DUPLICATED_OR_SHIFTED_DELIVERY_DATE:" + index)
            by_day[expected] = str(_price(record["delivery_price"]))
        lookup[index] = by_day
    return lookup



def _original_open_lineage(spine):
    """Bind settlement to the same originally selected contracts, not a calendar date alone."""
    opened = {}
    for day in spine["days"]:
        for event in day["market_events"]:
            if event.get("kind") != "OPEN_SOURCE_ONLY":
                continue
            name, asset, at = event.get("position_id"), event.get("asset"), event.get("at_ms")
            if (not isinstance(name, str) or not name or name in opened
                    or asset not in ("BTC", "ETH") or type(at) is not int
                    or not isinstance(event.get("candidate_inventory"), list)
                    or event.get("signal_source") != "ORIGINAL_FIXED_180_GRID"):
                raise ValueError("UNBOUND_DUPLICATE_OR_FORGED_ORIGINAL_OPEN")
            symbols = (event.get("short_symbol_unverified_selection"),
                       event.get("long_symbol_unverified_selection"))
            expiries, strikes = [], []
            for symbol in symbols:
                parts = symbol.split("-") if isinstance(symbol, str) else []
                if len(parts) != 4 or parts[0] != asset or parts[3] != "P":
                    raise ValueError("INVALID_ORIGINAL_OPEN_CONTRACT")
                try:
                    expiry = datetime.strptime(parts[1].upper(), "%d%b%y").replace(
                        hour=8, tzinfo=timezone.utc)
                    strike = _price(parts[2])
                except (ValueError, TypeError) as exc:
                    raise ValueError("INVALID_ORIGINAL_OPEN_CONTRACT") from exc
                expiries.append(int(expiry.timestamp() * 1000))
                strikes.append(strike)
            if (expiries[0] != expiries[1] or strikes[0] <= strikes[1]
                    or not at < expiries[0] or expiries[0] >= int(
                        datetime(END.year, END.month, END.day, tzinfo=timezone.utc).timestamp()*1000)
                    or not set(symbols).issubset({
                        q.get("symbol") for q in event["candidate_inventory"]
                        if isinstance(q, dict)})):
                raise ValueError("ORIGINAL_OPEN_CONTRACT_EXPIRY_OR_INVENTORY_MISMATCH")
            opened[name] = (asset, at, expiries[0])
    if len(opened) != spine.get("unverified_position_plan_count"):
        raise ValueError("MISSING_OR_DUPLICATE_ORIGINAL_OPEN_POSITION")
    return opened


def bind(spine, delivery, delivery_raw_bytes):
    fixes = validate_delivery(delivery)
    if (not isinstance(spine, dict) or spine.get("schema") != SOURCE_SCHEMA
            or spine.get("status") != SOURCE_STATUS
            or spine.get("native_economic_train_executed") is not False
            or spine.get("original_complete_option_lifecycles_certified") != 0
            or any(spine.get(key) is not False for key in DENIED)
            or not isinstance(spine.get("days"), list) or len(spine["days"]) != DAYS):
        raise ValueError("UNVERIFIED_OR_INCOMPLETE_SOURCE_SPINE")
    opened = _original_open_lineage(spine)
    result = copy.deepcopy(spine)
    seen = set()
    bound = 0
    for i, day in enumerate(result["days"]):
        if (not isinstance(day, dict) or day.get("ts_ms") != START_CLOCK_MS + DAY_MS * i
                or not isinstance(day.get("market_events"), list)):
            raise ValueError("INVALID_OR_SHIFTED_SOURCE_SPINE_DAY")
        for event in day["market_events"]:
            if not isinstance(event, dict) or event.get("kind") not in (
                    "OPEN_SOURCE_ONLY", "MARK_SOURCE_ONLY", "SETTLEMENT_DUE_SOURCE_ONLY"):
                raise ValueError("UNREGISTERED_SOURCE_SPINE_EVENT")
            if event["kind"] != "SETTLEMENT_DUE_SOURCE_ONLY":
                continue
            at, asset, name = event.get("at_ms"), event.get("asset"), event.get("position_id")
            if (type(at) is not int or asset not in ("BTC", "ETH")
                    or not isinstance(name, str) or not name
                    or event.get("delivery_index_missing") is not True
                    or set(event) != {"kind", "at_ms", "asset", "position_id",
                                     "delivery_index_missing"}):
                raise ValueError("FORGED_OR_ALREADY_BOUND_SETTLEMENT_EVENT")
            expiry = datetime.fromtimestamp(at / 1000, timezone.utc)
            if (expiry.hour, expiry.minute, expiry.second, expiry.microsecond) != (8, 0, 0, 0):
                raise ValueError("UNVERIFIED_CONTRACT_EXPIRY_CLOCK")
            when = expiry.date()
            if (not START <= when < END
                    or day["ts_ms"] - DAY_MS + 1000 > at
                    or at > day["ts_ms"]):
                raise ValueError("SEALED_OR_SHIFTED_SETTLEMENT_DATE")
            if name in seen:
                raise ValueError("DUPLICATED_SETTLEMENT_POSITION")
            if opened.get(name) != (asset, opened.get(name, (None, None, None))[1], at):
                raise ValueError("SETTLEMENT_NOT_LINKED_TO_ORIGINAL_OPEN_CONTRACT")
            seen.add(name)
            index = asset.lower() + "_usd"
            event.pop("delivery_index_missing")
            event.update({
                "delivery_calendar_index_name": index,
                "delivery_calendar_date": when.isoformat(),
                "delivery_calendar_price_usd": fixes[index][when.isoformat()],
                "delivery_calendar_source_only": True,
                "native_contract_delivery_index_unverified": True,
            })
            bound += 1
    if seen != set(opened):
        raise ValueError("ORIGINAL_OPEN_WITHOUT_CONTRACT_SETTLEMENT")
    if bound != spine.get("expiry_due_count") or bound != spine.get("unverified_position_plan_count"):
        raise ValueError("INCOMPLETE_SOURCE_SETTLEMENT_BINDING")
    result.update({
        "schema": SCHEMA,
        "status": "FIRSTPARTY_DELIVERY_CALENDAR_BOUND_NOT_NATIVE_SETTLEMENT",
        "firstparty_delivery_artifact_sha256": hashlib.sha256(delivery_raw_bytes).hexdigest(),
        "firstparty_calendar_delivery_prices_bound": bound,
        "firstparty_btc_eth_train_calendar_days_each": DAYS,
        "firstparty_delivery_calendar_source_bound": True,
        "original_delivery_index_authenticated": False,
        "native_contract_settlement_terms_authenticated": False,
        "native_economic_train_executed": False,
        "original_complete_option_lifecycles_certified": 0,
        **{key: False for key in DENIED},
    })
    return result


def main(spine_path, delivery_path, output_path):
    source = json.loads(Path(spine_path).read_text(encoding="utf-8"))
    raw = Path(delivery_path).read_bytes()
    result = bind(source, json.loads(raw), raw)
    Path(output_path).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                 encoding="utf-8")
    print(json.dumps({"status": result["status"],
                      "firstparty_delivery_calendar_events": result["firstparty_calendar_delivery_prices_bound"],
                      "native_settlement_certified": False, "economic_train": False,
                      "promotion": False}))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_original_delivery_to_spine SOURCE_SPINE_JSON FIRSTPARTY_DELIVERY_JSON OUT_JSON")
    main(*sys.argv[1:])
