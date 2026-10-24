"""Independent original-byte audit of full weekly PIT options source; no economic code."""
from __future__ import annotations
import hashlib
import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from research.tools.v99_deribit_weekly_pit_1000_coverage import decisions
from research.tools.v99_r106_d1_real_train_source_join import START, END, FOLD_EDGES

WINDOW = 21_600_000

def independently_verify(directory):
    root = Path(directory)
    report = json.loads((root / "full_train_summary.json").read_text())
    assert report["schema"] == "V99_DERIBIT_COMPLETE_6H_FULL_TRAIN_INFO_V1"
    assert (report["start_ms"], report["end_exclusive_ms"]) == (START, END)
    assert report["fold_edges"] == list(FOLD_EDGES)
    assert report["window_ms"] == WINDOW and report["page_count"] == 1000
    assert all(not report[k] for k in ("economic_train_executed", "validation_opened",
                                       "holdout_opened", "orders_enabled",
                                       "promotion_authorized"))
    expected = {(t, f, c) for t, f in decisions() for c in ("BTC", "ETH")}
    assert len(expected) == 188 and len(report["rows"]) == 188
    assert {(r["decision_ms"], r["fold"], r["currency"]) for r in report["rows"]} == expected
    tallies = defaultdict(lambda: [0, 0, 0])
    full = 0
    eligible = 0
    for row in report["rows"]:
        t, fold, currency = row["decision_ms"], row["fold"], row["currency"]
        key = fold, currency
        tallies[key][0] += 1
        if row["status"] == "SOURCE_ERROR":
            assert not row["near_atm_2strike_4group"]
            assert row["reason"]
            continue
        all_trades = {}
        cursor = t - 1
        previous_boundary = None
        for i, page in enumerate(row["pages"]):
            assert page["page"] == i
            assert page["query_start_ms"] == t - WINDOW
            assert page["query_end_ms"] == cursor
            raw = (root / page["file"]).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == page["sha256"]
            payload = json.loads(raw)
            assert not payload.get("error")
            data = payload["result"]
            trades = data["trades"]
            assert len(trades) == page["source_count"] <= 1000
            ids = [str(v["trade_id"]) for v in trades]
            stamps = [int(v["timestamp"]) for v in trades]
            assert len(ids) == len(set(ids))
            assert stamps == sorted(stamps, reverse=True)
            assert all(t-WINDOW <= x <= cursor for x in stamps)
            if previous_boundary is not None:
                assert previous_boundary.intersection(ids)
            new = 0
            for ident, trade in zip(ids, trades):
                if ident in all_trades:
                    assert all_trades[ident] == trade
                else:
                    all_trades[ident] = trade
                    new += 1
            assert new == page["new_unique"] and new > 0
            assert min(stamps) == page["oldest_ms"]
            assert max(stamps) == page["newest_ms"]
            assert bool(data.get("has_more")) == page["has_more"]
            previous_boundary = {ident for ident, stamp in zip(ids, stamps)
                                 if stamp == min(stamps)}
            assert sorted(previous_boundary) == page["boundary_ids"]
            if page["has_more"]:
                assert min(stamps) < cursor
                cursor = min(stamps)
            else:
                assert i == len(row["pages"]) - 1
        assert len(all_trades) == row["unique_trades"]
        if row["status"] == "SOURCE_COMPLETE":
            assert row["pages"] and not row["pages"][-1]["has_more"]
            full += 1
            tallies[key][1] += 1
        else:
            assert row["status"] == "SOURCE_INCOMPLETE"
            assert len(row["pages"]) == 30
        groups = defaultdict(set)
        for trade in all_trades.values():
            try:
                iv = float(trade["iv"])
                index = float(trade["index_price"])
            except (KeyError, ValueError, TypeError):
                continue
            if not (math.isfinite(iv) and 0 < iv <= 1000 and
                    math.isfinite(index) and index > 0):
                continue
            symbol = str(trade.get("instrument_name", "")).split("-")
            if len(symbol) != 4 or symbol[0] != currency or symbol[3] not in ("C", "P"):
                continue
            try:
                strike = float(symbol[2])
                expiry = datetime.strptime(symbol[1].upper(), "%d%b%y").replace(tzinfo=timezone.utc)
            except (ValueError, OverflowError):
                continue
            if not (math.isfinite(strike) and strike > 0):
                continue
            if abs(math.log(strike / index)) > 0.15:
                continue
            dte = (int(expiry.timestamp()*1000) + 28_800_000 - t) / 86_400_000
            band = "short" if 7 <= dte <= 45 else ("long" if 46 <= dte <= 120 else None)
            if band:
                groups[(band, symbol[3])].add(strike)
        own = {band+"_"+side: len(groups[(band, side)])
               for band in ("short", "long") for side in ("C", "P")}
        assert own == row["diagnostic_counts"]
        qualifies = row["status"] == "SOURCE_COMPLETE" and all(v >= 2 for v in own.values())
        assert qualifies == row["near_atm_2strike_4group"]
        eligible += int(qualifies)
        tallies[key][2] += int(qualifies)
    assert full == report["source_complete"] and eligible == report["eligible_weeks"]
    for r in report["folds"]:
        n, full_count, covered = tallies[(r["fold"], r["currency"])]
        assert (n, full_count, covered) == (r["weeks"], r["complete_source"], r["near_atm_eligible"])
        assert abs(r["fraction"] - covered/n) < 1e-12
    good = sum(all(tallies[(f, c)][2] / tallies[(f, c)][0] >= 0.70
                   for c in ("BTC", "ETH")) for f in range(1, 6))
    assert good == report["good_folds"]
    assert report["gate"] == ("SOURCE_INFORMATION_PASS_FOR_DESIGN" if good >= 4
                               else "SOURCE_INFORMATION_FAIL")
    print("INDEPENDENT ORIGINAL HASH, TIMESTAMP, PAGINATION AND 5 FOLD ORACLE: PASS")
    print("SOURCE COMPLETE", full, "/188; NEAR ATM", eligible, "/188")
    print("FOLD FRACTIONS", [(r["fold"], r["currency"], r["near_atm_eligible"],
                             r["weeks"]) for r in report["folds"]])
    print("GOOD FOLDS", good, "/5; INFORMATION GATE", report["gate"])
    print("NO PNL / NO PROMOTION / NO ORDERS")
    return report

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.tools.v99_deribit_complete_6h_full_train_oracle SOURCE_DIR")
    independently_verify(sys.argv[1])
