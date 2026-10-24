"""Original Deribit TRAIN index-only inverse coin collateral stress. NOT option PnL.

Ex-ante rules: research/V99_R106_I1_ORIGINAL_COIN_COLLATERAL_STRESS_PREREG_20261024.md.
The actual Deribit historical option quotes, margin and fee tiers remain absent.
"""
from __future__ import annotations
import hashlib
import json
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

START = date(2021, 12, 9)
STOP = date(2023, 10, 1)
MONDAY = date(2021, 12, 13)
EDGES = [
    datetime(2021,12,9,tzinfo=timezone.utc),
    datetime(2022,4,20,4,tzinfo=timezone.utc),
    datetime(2022,8,30,9,tzinfo=timezone.utc),
    datetime(2023,1,9,14,tzinfo=timezone.utc),
    datetime(2023,5,21,19,tzinfo=timezone.utc),
    datetime(2023,10,1,tzinfo=timezone.utc),
]
D = lambda x: Decimal(str(x))
ROUND = Decimal("0.0000000001")


def original_index(path):
    raw = Path(path).read_bytes()
    payload = json.loads(raw)
    if payload.get("schema") != "V99_I1_DERIBIT_TRAIN_DELIVERY_PRICE_RECEIPTS_V1":
        raise ValueError("UNTRUSTED_INDEX_SCHEMA")
    if not (payload.get("read_only") is True and payload.get("no_orders") is True
            and payload.get("no_promotion") is True
            and payload.get("not_executable_quotes") is True):
        raise ValueError("UNTRUSTED_SOURCE_CLASSIFICATION")
    if set(payload.get("assets", {})) != {"btc_usd", "eth_usd"}:
        raise ValueError("MISSING_OR_EXTRA_INDEX")
    calendar = [START + timedelta(days=i) for i in range((STOP-START).days)]
    data = {}
    for asset, part in payload["assets"].items():
        if part.get("index") != asset or part.get("train_start") != START.isoformat() or part.get("train_end_exclusive") != STOP.isoformat():
            raise ValueError("UNBOUND_OR_FUTURE_INDEX")
        records = part.get("records", [])
        if [r.get("date") for r in records] != [x.isoformat() for x in calendar]:
            raise ValueError("INDEX_GAP_DUPLICATE_OR_FUTURE")
        if len(part.get("pages", [])) < 1:
            raise ValueError("MISSING_ORIGINAL_PAGE_PROVENANCE")
        data[asset] = {}
        for row in records:
            val = D(row["delivery_price"])
            if not val.is_finite() or val <= 0:
                raise ValueError("INVALID_DELIVERY_PRICE")
            data[asset][date.fromisoformat(row["date"])] = val
    return hashlib.sha256(raw).hexdigest(), data


def run(source):
    sha, data = original_index(source)
    out = []
    for n in range(91):
        decision = MONDAY + timedelta(days=7*n)
        entry_day = decision - timedelta(days=1)  # 08:00 Sunday known before Monday 00:00
        expiry_day = decision + timedelta(days=21)  # Monday 08:00, strictly inside TRAIN
        if not (START <= entry_day < decision < expiry_day < STOP):
            raise ValueError("SEALED_EXPIRY_OR_NONCAUSAL_ENTRY")
        fold = next(i for i in range(1,6) if EDGES[i-1] <= datetime.combine(decision, datetime.min.time(), tzinfo=timezone.utc) < EDGES[i])
        for asset in ("btc_usd", "eth_usd"):
            entry, settle = data[asset][entry_day], data[asset][expiry_day]
            high, low = D("0.95")*entry, D("0.90")*entry
            quantity = (D("0.05")*entry)/(high-low)
            due_usd = quantity*(max(high-settle,D(0))-max(low-settle,D(0)))
            due_coin = due_usd/settle
            ratio = due_coin/D("0.05")
            out.append({
                "asset":asset, "decision":decision.isoformat(), "entry_index_date":entry_day.isoformat(),
                "settlement_index_date":expiry_day.isoformat(), "fold":fold,
                "coin_obligation_to_reserved_ratio":str(ratio.quantize(ROUND)),
                "five_percent_coin_reserve_breached":ratio > 1,
            })
    if len(out) != 182:
        raise ValueError("MISSING_ORIGINAL_TRAIN_STRESS_WINDOWS")
    summary = {}
    for asset in ("btc_usd","eth_usd"):
        rows = [r for r in out if r["asset"] == asset]
        summary[asset] = {
            "observations":len(rows),
            "max_obligation_to_reserve":max((r["coin_obligation_to_reserved_ratio"] for r in rows), key=D),
            "breaches":sum(r["five_percent_coin_reserve_breached"] for r in rows),
            "breaches_by_fold":{str(f):sum(r["five_percent_coin_reserve_breached"] for r in rows if r["fold"]==f) for f in range(1,6)},
        }
    return {
        "schema":"I1_ORIGINAL_INDEX_COIN_COLLATERAL_STRESS_V1",
        "source_sha256":sha,
        "status":"HISTORICAL_INDEX_SYNTHETIC_STRIKES_NOT_ECONOMICS",
        "source_index_first_party":True,
        "option_strikes_quotes_or_fills_historical":False,
        "native_margin_or_fee_authenticated":False,
        "economic_train_executed":False,
        "validation_opened":False, "holdout_opened":False,
        "promotion_authorized":False, "orders_enabled":False,
        "summary":summary, "observations":out,
    }


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_original_coin_collateral_stress ORIGINAL_INDEX_JSON OUTPUT_JSON")
    result = run(sys.argv[1])
    dest = Path(sys.argv[2])
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":result["status"],"summary":result["summary"],
                      "economic_train":False,"promotion":False},sort_keys=True))
