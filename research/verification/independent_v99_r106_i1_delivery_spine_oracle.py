"""Independent re-execution of Deribit TRAIN delivery-calendar/source-spine join.

No production binder imports; not a native contract settlement attestation.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

FIRST = date(2021, 12, 9)
LAST_EXCLUSIVE = date(2023, 10, 1)
N = 661
START_CLOCK = 1639094399000
DAY_MS = 86_400_000
SOURCE_SCHEMA = "V99_I1_SOURCE_DRIVEN_661D_MARK_EVENT_SPINE_V1"
BOUND_SCHEMA = "V99_I1_FIRSTPARTY_DELIVERY_CALENDAR_SOURCE_SPINE_V1"



def _independent_open_contracts(source):
    """Reconstruct native option expiry from original OPEN identifiers independently."""
    positions = {}
    for day in source["days"]:
        for e in day.get("market_events", []):
            if e.get("kind") != "OPEN_SOURCE_ONLY":
                continue
            pid, asset, start = e.get("position_id"), e.get("asset"), e.get("at_ms")
            if (not isinstance(pid, str) or not pid or pid in positions
                    or asset not in ("BTC", "ETH") or type(start) is not int
                    or e.get("signal_source") != "ORIGINAL_FIXED_180_GRID"
                    or not isinstance(e.get("candidate_inventory"), list)):
                raise ValueError("ORACLE_UNBOUND_OR_DUPLICATED_OPEN")
            selected = [e.get("short_symbol_unverified_selection"),
                        e.get("long_symbol_unverified_selection")]
            dates = []
            strikes = []
            for symbol in selected:
                parts = symbol.split("-") if isinstance(symbol, str) else []
                if len(parts) != 4 or parts[0] != asset or parts[3] != "P":
                    raise ValueError("ORACLE_INVALID_OPEN_CONTRACT")
                try:
                    expiry = datetime.strptime(parts[1].upper(), "%d%b%y").replace(
                        hour=8, tzinfo=timezone.utc)
                    strike = Decimal(parts[2])
                except Exception as exc:
                    raise ValueError("ORACLE_INVALID_OPEN_CONTRACT") from exc
                if not strike.is_finite() or strike <= 0:
                    raise ValueError("ORACLE_INVALID_OPEN_STRIKE")
                dates.append(int(expiry.timestamp() * 1000))
                strikes.append(strike)
            original_ids = {q.get("symbol") for q in e["candidate_inventory"]
                            if isinstance(q, dict)}
            if (dates[0] != dates[1] or not start < dates[0]
                    or dates[0] >= int(datetime(2023, 10, 1, tzinfo=timezone.utc).timestamp()*1000)
                    or strikes[0] <= strikes[1]
                    or not set(selected).issubset(original_ids)):
                raise ValueError("ORACLE_ORIGINAL_OPEN_EXPIRY_INVENTORY_MISMATCH")
            positions[pid] = (asset, dates[0])
    if len(positions) != source.get("unverified_position_plan_count"):
        raise ValueError("ORACLE_OPEN_POSITION_COUNT_MISMATCH")
    return positions


def verify(source, original_delivery_bytes, bound):
    receipt = json.loads(original_delivery_bytes)
    if (receipt.get("schema") != "V99_I1_DERIBIT_TRAIN_DELIVERY_PRICE_RECEIPTS_V1"
            or receipt.get("read_only") is not True
            or receipt.get("no_orders") is not True
            or receipt.get("no_promotion") is not True
            or receipt.get("not_executable_quotes") is not True
            or set(receipt.get("assets", {})) != {"btc_usd", "eth_usd"}):
        raise ValueError("ORACLE_UNTRUSTED_DELIVERY_SOURCE")
    prices = {}
    for asset in ("BTC", "ETH"):
        key = asset.lower() + "_usd"
        part = receipt["assets"][key]
        if (part.get("index") != key
                or part.get("source") != "https://www.deribit.com/api/v2/public/get_delivery_prices"
                or part.get("train_start") != FIRST.isoformat()
                or part.get("train_end_exclusive") != LAST_EXCLUSIVE.isoformat()
                or not isinstance(part.get("pages"), list) or not part["pages"]
                or len(part.get("records", [])) != N):
            raise ValueError("ORACLE_MISSING_DELIVERY_DAYS")
        prices[key] = {}
        for i, row in enumerate(part["records"]):
            day = (FIRST + timedelta(days=i)).isoformat()
            if not isinstance(row, dict) or set(row) != {"date", "delivery_price"} or row["date"] != day:
                raise ValueError("ORACLE_DUPLICATE_SHIFTED_DELIVERY_DAY")
            if isinstance(row["delivery_price"], bool):
                raise ValueError("ORACLE_INVALID_DELIVERY_PRICE")
            try:
                val = Decimal(str(row["delivery_price"]))
            except Exception as exc:
                raise ValueError("ORACLE_INVALID_DELIVERY_PRICE") from exc
            if not val.is_finite() or val <= 0:
                raise ValueError("ORACLE_INVALID_DELIVERY_PRICE")
            prices[key][day] = str(val)

    if (source.get("schema") != SOURCE_SCHEMA
            or source.get("status") != "ORIGINAL_MARKET_SPINE_ONLY_NOT_ECONOMIC_JOURNAL"
            or source.get("native_economic_train_executed") is not False
            or source.get("original_complete_option_lifecycles_certified") != 0
            or len(source.get("days", [])) != N
            or bound.get("schema") != BOUND_SCHEMA
            or bound.get("status") != "FIRSTPARTY_DELIVERY_CALENDAR_BOUND_NOT_NATIVE_SETTLEMENT"
            or bound.get("firstparty_delivery_artifact_sha256") != hashlib.sha256(original_delivery_bytes).hexdigest()
            or bound.get("firstparty_btc_eth_train_calendar_days_each") != N
            or bound.get("firstparty_delivery_calendar_source_bound") is not True
            or bound.get("original_delivery_index_authenticated") is not False
            or bound.get("native_contract_settlement_terms_authenticated") is not False
            or bound.get("native_economic_train_executed") is not False
            or bound.get("original_complete_option_lifecycles_certified") != 0):
        raise ValueError("ORACLE_FORGED_DELIVERY_SOURCE_CERTIFICATION")
    forbidden = ("promotion_authorized", "freeze_authorized", "orders_enabled",
                 "validation_opened", "holdout_opened", "paper_publication_authorized")
    if any(source.get(k) is not False or bound.get(k) is not False for k in forbidden):
        raise ValueError("ORACLE_FALSE_PROMOTION_OR_SEALED_ACCESS")

    original_opens = _independent_open_contracts(source)
    expected = copy.deepcopy(source)
    total = 0
    names = set()
    for i, row in enumerate(expected["days"]):
        if row.get("ts_ms") != START_CLOCK + i * DAY_MS:
            raise ValueError("ORACLE_SHIFTED_SOURCE_CLOCK")
        for e in row.get("market_events", []):
            if e.get("kind") != "SETTLEMENT_DUE_SOURCE_ONLY":
                continue
            when = datetime.fromtimestamp(e["at_ms"] / 1000, timezone.utc)
            if (when.hour, when.minute, when.second, when.microsecond) != (8, 0, 0, 0):
                raise ValueError("ORACLE_INVALID_EXPIRY_CLOCK")
            day = when.date().isoformat()
            asset = e.get("asset")
            name = e.get("position_id")
            if (asset not in ("BTC", "ETH") or not isinstance(name, str)
                    or not name or name in names or e.get("delivery_index_missing") is not True
                    or set(e) != {"kind", "at_ms", "asset", "position_id", "delivery_index_missing"}
                    or not FIRST <= when.date() < LAST_EXCLUSIVE
                    or not row["ts_ms"] - DAY_MS + 1000 <= e["at_ms"] <= row["ts_ms"]):
                raise ValueError("ORACLE_FORGED_SOURCE_SETTLEMENT")
            if original_opens.get(name) != (asset, e["at_ms"]):
                raise ValueError("ORACLE_SETTLEMENT_CONTRACT_NOT_ORIGINALLY_OPENED")
            names.add(name)
            index = asset.lower() + "_usd"
            del e["delivery_index_missing"]
            e.update({
                "delivery_calendar_index_name": index,
                "delivery_calendar_date": day,
                "delivery_calendar_price_usd": prices[index][day],
                "delivery_calendar_source_only": True,
                "native_contract_delivery_index_unverified": True,
            })
            total += 1
    if names != set(original_opens):
        raise ValueError("ORACLE_ORIGINAL_OPEN_MISSING_SETTLEMENT")
    if (total != source.get("expiry_due_count")
            or total != source.get("unverified_position_plan_count")
            or bound.get("firstparty_calendar_delivery_prices_bound") != total):
        raise ValueError("ORACLE_MISSING_SETTLEMENT_EVENTS")
    expected.update({
        "schema": BOUND_SCHEMA,
        "status": "FIRSTPARTY_DELIVERY_CALENDAR_BOUND_NOT_NATIVE_SETTLEMENT",
        "firstparty_delivery_artifact_sha256": hashlib.sha256(original_delivery_bytes).hexdigest(),
        "firstparty_calendar_delivery_prices_bound": total,
        "firstparty_btc_eth_train_calendar_days_each": N,
        "firstparty_delivery_calendar_source_bound": True,
        "original_delivery_index_authenticated": False,
        "native_contract_settlement_terms_authenticated": False,
        "native_economic_train_executed": False,
        "original_complete_option_lifecycles_certified": 0,
        **{key: False for key in forbidden},
    })
    if bound != expected:
        raise ValueError("ORACLE_BOUND_SPINE_NOT_EQUAL_INDEPENDENT_REPLAY")
    return {"independent_original_delivery_calendar_days_each": N,
            "independent_calendar_settlement_events": total,
            "native_contract_settlement_certified": False,
            "economic_train": False, "promotion": False}


def main(source_path, delivery_path, bound_path):
    source = json.loads(Path(source_path).read_text(encoding="utf-8"))
    raw = Path(delivery_path).read_bytes()
    bound = json.loads(Path(bound_path).read_text(encoding="utf-8"))
    print(json.dumps(verify(source, raw, bound), sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_delivery_spine_oracle SOURCE_SPINE_JSON FIRSTPARTY_DELIVERY_JSON BOUND_JSON")
    main(*sys.argv[1:])
