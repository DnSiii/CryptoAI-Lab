"""Independent original-byte, day-by-day overlap oracle; no primary import."""
from __future__ import annotations
import hashlib
import json
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

N = lambda x: Decimal(str(x))
Q = Decimal("0.0000000001")
START, END = date(2021, 12, 9), date(2023, 10, 1)
FIRST = date(2021, 12, 13)
BOUNDARIES = [
    datetime(2021, 12, 9, tzinfo=timezone.utc),
    datetime(2022, 4, 20, 4, tzinfo=timezone.utc),
    datetime(2022, 8, 30, 9, tzinfo=timezone.utc),
    datetime(2023, 1, 9, 14, tzinfo=timezone.utc),
    datetime(2023, 5, 21, 19, tzinfo=timezone.utc),
    datetime(2023, 10, 1, tzinfo=timezone.utc),
]


def audit(source_path, result_path):
    raw = Path(source_path).read_bytes()
    original = json.loads(raw)
    reported = json.loads(Path(result_path).read_bytes())
    assert original["schema"] == "V99_I1_DERIBIT_TRAIN_DELIVERY_PRICE_RECEIPTS_V1"
    assert all(original[k] is True for k in ("read_only", "no_orders",
                                             "no_promotion", "not_executable_quotes"))
    assert set(original["assets"]) == {"btc_usd", "eth_usd"}
    assert reported["schema"] == "I1_ORIGINAL_INDEX_OVERLAPPING_COIN_RISK_V1"
    assert reported["source_sha256"] == hashlib.sha256(raw).hexdigest()
    assert reported["original_index_first_party"] is True
    assert reported["status"] == "HISTORICAL_UNDERLYING_SYNTHETIC_STRIKES_INTRINSIC_ONLY_NO_ECONOMICS"
    assert all(reported[k] is False for k in (
        "option_quotes_fills_or_native_margin", "economic_train_executed",
        "validation_opened", "holdout_opened", "promotion_authorized", "orders_enabled"))
    calendar = [(START + timedelta(days=n)).isoformat()
                for n in range((END - START).days)]
    series = {}
    for asset in ("btc_usd", "eth_usd"):
        part = original["assets"][asset]
        assert part["index"] == asset and part["train_start"] == START.isoformat()
        assert part["train_end_exclusive"] == END.isoformat() and part["pages"]
        assert [r["date"] for r in part["records"]] == calendar
        prices = [N(r["delivery_price"]) for r in part["records"]]
        assert all(p.is_finite() and p > 0 for p in prices)
        series[asset] = dict(zip(calendar, prices))
    firsts = [FIRST + timedelta(days=7 * n) for n in range(91)]
    assert all(d + timedelta(days=21) < END for d in firsts)
    last = firsts[-1] + timedelta(days=21)
    expected_rows = []
    expected_summary = {}
    for asset in ("btc_usd", "eth_usd"):
        positions = {}
        for i, entry in enumerate(firsts):
            ref = series[asset][(entry - timedelta(days=1)).isoformat()]
            positions[i] = (entry, entry + timedelta(days=21),
                            ref * N("0.95"), ref * N("0.90"))
        maxima = {str(i): N(0) for i in range(1, 6)}
        peak = N(0)
        worst = N(0)
        breaches = 0
        exp_breaches = 0
        ever = set()
        max_active = 0
        for offset in range((last - FIRST).days + 1):
            day = FIRST + timedelta(days=offset)
            spot = series[asset][day.isoformat()]
            current = [(i, p) for i, p in positions.items()
                       if p[0] <= day <= p[1]]
            assert current
            total = N(0)
            for i, (opened, expiry, short, long) in current:
                # Independent piecewise intrinsic identity.
                if spot >= short:
                    usd = N(0)
                elif spot <= long:
                    usd = short - long
                else:
                    usd = short - spot
                coins = usd / spot
                total += coins
                if coins > N("0.05"):
                    ever.add(i)
                    if day == expiry:
                        exp_breaches += 1
            reserved = N("0.05") * len(current)
            ratio = total / reserved
            instant = datetime(day.year, day.month, day.day, 8, tzinfo=timezone.utc)
            fold = next(i for i in range(1, 6)
                        if BOUNDARIES[i-1] <= instant < BOUNDARIES[i])
            maxima[str(fold)] = max(maxima[str(fold)], ratio)
            max_active = max(max_active, len(current))
            peak = max(peak, total)
            worst = max(worst, ratio)
            breaches += int(ratio > 1)
            expected_rows.append({
                "asset": asset, "snapshot_date": day.isoformat(), "fold": fold,
                "active_positions": len(current),
                "aggregate_intrinsic_coin": str(total.quantize(Q)),
                "aggregate_to_earmarked_reserve": str(ratio.quantize(Q)),
                "earmarked_coin": str(reserved.quantize(Q)),
                "earmark_breached": ratio > 1,
            })
        expected_summary[asset] = {
            "daily_snapshots": (last - FIRST).days + 1,
            "max_active_positions": max_active,
            "max_aggregate_intrinsic_coin": str(peak.quantize(Q)),
            "max_aggregate_to_earmarked_reserve": str(worst.quantize(Q)),
            "earmark_breached_snapshots": breaches,
            "distinct_spreads_ever_exceeding_own_earmark": len(ever),
            "expiry_only_breaches": exp_breaches,
            "max_ratio_by_snapshot_fold": {
                k: str(v.quantize(Q)) for k, v in maxima.items()},
        }
    assert expected_summary["btc_usd"]["expiry_only_breaches"] == 25
    assert expected_summary["eth_usd"]["expiry_only_breaches"] == 27
    assert reported["daily"] == expected_rows, "INDEPENDENT_DAILY_OVERLAP_MISMATCH"
    assert reported["summary"] == expected_summary, "INDEPENDENT_OVERLAP_SUMMARY_MISMATCH"
    print(json.dumps({"independent_replay": "VERIFIED", "rows": len(expected_rows),
                      "summary": expected_summary, "option_roi": False,
                      "promotion": False}, sort_keys=True))
    return expected_summary


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_overlapping_coin_exposure ORIGINAL_JSON RESULT_JSON")
    audit(sys.argv[1], sys.argv[2])
