"""Independent original-byte / algebra oracle for inverse coin collateral stress.

Does NOT import primary calculator or assert tradable returns.
"""
from __future__ import annotations
import hashlib
import json
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

D = lambda x: Decimal(str(x))
Q = Decimal("0.0000000001")
START, STOP = date(2021,12,9), date(2023,10,1)
EDGES = [
    datetime(2021,12,9,tzinfo=timezone.utc),
    datetime(2022,4,20,4,tzinfo=timezone.utc),
    datetime(2022,8,30,9,tzinfo=timezone.utc),
    datetime(2023,1,9,14,tzinfo=timezone.utc),
    datetime(2023,5,21,19,tzinfo=timezone.utc),
    datetime(2023,10,1,tzinfo=timezone.utc),
]


def audit(original, report_path):
    original_bytes = Path(original).read_bytes()
    source = json.loads(original_bytes)
    result = json.loads(Path(report_path).read_bytes())
    assert result["schema"] == "I1_ORIGINAL_INDEX_COIN_COLLATERAL_STRESS_V1"
    assert result["source_sha256"] == hashlib.sha256(original_bytes).hexdigest(), "ORIGINAL_INDEX_BYTES_CHANGED"
    assert source["schema"] == "V99_I1_DERIBIT_TRAIN_DELIVERY_PRICE_RECEIPTS_V1"
    assert all(source[k] is True for k in ("read_only","no_orders","no_promotion","not_executable_quotes"))
    assert set(source["assets"]) == {"btc_usd","eth_usd"}
    assert all(result[k] is False for k in ("economic_train_executed","validation_opened",
        "holdout_opened","promotion_authorized","orders_enabled","option_strikes_quotes_or_fills_historical",
        "native_margin_or_fee_authenticated"))
    calendar = [(START+timedelta(days=i)).isoformat() for i in range((STOP-START).days)]
    index = {}
    for asset in ("btc_usd","eth_usd"):
        part = source["assets"][asset]
        assert part["index"] == asset and part["train_start"] == START.isoformat()
        assert part["train_end_exclusive"] == STOP.isoformat() and part["pages"]
        assert [r["date"] for r in part["records"]] == calendar
        index[asset] = {r["date"]:D(r["delivery_price"]) for r in part["records"]}
        assert all(v.is_finite() and v > 0 for v in index[asset].values())
    expected = []
    for n in range(91):
        day = date(2021,12,13)+timedelta(days=n*7)
        prior = (day-timedelta(days=1)).isoformat()
        future = (day+timedelta(days=21)).isoformat()
        assert START <= date.fromisoformat(prior) < day < date.fromisoformat(future) < STOP
        dt = datetime.combine(day,datetime.min.time(),tzinfo=timezone.utc)
        fold = next(i for i in range(1,6) if EDGES[i-1] <= dt < EDGES[i])
        for asset in ("btc_usd","eth_usd"):
            entry, final = index[asset][prior], index[asset][future]
            # Algebraic piecewise independent of primary intrinsic/payoff formula.
            # Notional is exactly one for 5% capital at 5%-wide spread.
            if final >= D("0.95")*entry:
                owed = D(0)
            elif final <= D("0.90")*entry:
                owed = D("0.05")*entry/final
            else:
                owed = (D("0.95")*entry-final)/final
            ratio = owed/D("0.05")
            expected.append({
                "asset":asset,"decision":day.isoformat(),"entry_index_date":prior,
                "settlement_index_date":future,"fold":fold,
                "coin_obligation_to_reserved_ratio":str(ratio.quantize(Q)),
                "five_percent_coin_reserve_breached":ratio > 1,
            })
    assert result["observations"] == expected, "INDEPENDENT_COIN_STRESS_REPLAY_MISMATCH"
    for asset in ("btc_usd","eth_usd"):
        rows = [r for r in expected if r["asset"]==asset]
        summary = {
            "observations":91,
            "max_obligation_to_reserve":max((r["coin_obligation_to_reserved_ratio"] for r in rows), key=D),
            "breaches":sum(r["five_percent_coin_reserve_breached"] for r in rows),
            "breaches_by_fold":{str(f):sum(r["five_percent_coin_reserve_breached"] for r in rows if r["fold"]==f) for f in range(1,6)},
        }
        assert result["summary"][asset] == summary, "INDEPENDENT_STRESS_SUMMARY_MISMATCH"
    print(json.dumps({"original_index_replay":"INDEPENDENT_VERIFIED",
                      "observations":len(expected),"summary":result["summary"],
                      "option_roi":False,"promotion":False},sort_keys=True))
    return len(expected)


if __name__ == "__main__":
    if len(sys.argv)!=3:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_original_coin_collateral_stress ORIGINAL_INDEX_JSON REPORT_JSON")
    audit(sys.argv[1],sys.argv[2])
