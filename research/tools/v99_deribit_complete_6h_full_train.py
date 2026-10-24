"""Full fixed 94-week Deribit 6h option-IV information gate, TRAIN only, no PnL."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from research.tools.v99_deribit_weekly_pit_1000_coverage import decisions
from research.tools.v99_deribit_complete_6h_pit_probe import (
    collect_one, MAX_PAGES, WINDOW, MAX_RECENT_TRADES, FLAGS, BASE,
)
from research.tools.v99_r106_d1_real_train_source_join import START, END, FOLD_EDGES

def main(directory):
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    rows = []
    slots = [(t, f, c) for t, f in decisions() for c in ("BTC", "ETH")]
    assert len(slots) == 188 and len(set(slots)) == 188
    assert all(START < t < END and FOLD_EDGES[f-1] <= t < FOLD_EDGES[f]
               for t, f, _ in slots)
    for decision, fold, currency in slots:
        try:
            # Unique receipt namespace for each of the 188 weekly asset decisions.
            # Reusing f{fold}_{currency}_pageXX would silently overwrite earlier
            # first-party receipts and invalidate independent SHA-256 verification.
            slot_name = f"slot_{decision}_{currency}"
            slot_dir = root / slot_name
            slot_dir.mkdir(parents=True, exist_ok=True)
            row = collect_one(slot_dir, decision, fold, currency)
            for page in row["pages"]:
                page["file"] = slot_name + "/" + page["file"]
        except Exception as exc:
            row = dict(decision_ms=decision, fold=fold, currency=currency,
                       status="SOURCE_ERROR", reason=f"{type(exc).__name__}: {exc}",
                       pages=[], unique_trades=0, near_atm_2strike_4group=False)
        rows.append(row)
        print(json.dumps({k: v for k, v in row.items() if k != "pages"},
                         sort_keys=True), flush=True)
        # Durable intermediate summaries allow source-failure forensics if CI times out.
        (root / "progress.json").write_text(json.dumps(dict(completed_slots=len(rows),
                                source_complete=sum(r["status"] == "SOURCE_COMPLETE" for r in rows),
                                last_fold=fold, last_currency=currency), sort_keys=True) + "\n")
    folds = []
    for fold in range(1, 6):
        for currency in ("BTC", "ETH"):
            group = [r for r in rows if r["fold"] == fold and r["currency"] == currency]
            covered = sum(r["near_atm_2strike_4group"] for r in group)
            complete = sum(r["status"] == "SOURCE_COMPLETE" for r in group)
            folds.append(dict(fold=fold, currency=currency, weeks=len(group),
                              complete_source=complete, near_atm_eligible=covered,
                              fraction=covered / len(group)))
    good = sum(all(next(r for r in folds if r["fold"] == f and r["currency"] == c)["fraction"] >= 0.70
                   for c in ("BTC", "ETH")) for f in range(1, 6))
    report = dict(schema="V99_DERIBIT_COMPLETE_6H_FULL_TRAIN_INFO_V1",
                  start_ms=START, end_exclusive_ms=END, fold_edges=FOLD_EDGES,
                  endpoint=BASE, page_count=MAX_RECENT_TRADES, max_pages=MAX_PAGES,
                  window_ms=WINDOW, rows=rows, folds=folds, good_folds=good,
                  source_complete=sum(r["status"] == "SOURCE_COMPLETE" for r in rows),
                  eligible_weeks=sum(r["near_atm_2strike_4group"] for r in rows),
                  gate="SOURCE_INFORMATION_PASS_FOR_DESIGN" if good >= 4 else "SOURCE_INFORMATION_FAIL",
                  economic_train_executed=False, validation_opened=False,
                  holdout_opened=False, orders_enabled=False, promotion_authorized=False)
    (root / "full_train_summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("FULL TRAIN SOURCE COMPLETE:", report["source_complete"], "/188")
    print("NEAR ATM COMPARABLE:", report["eligible_weeks"], "/188")
    print("GOOD FOLDS:", good, "/5; INFORMATION GATE:", report["gate"])
    print("NO PNL / NO PROMOTION / NO ORDERS")
    return report

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.tools.v99_deribit_complete_6h_full_train OUTPUT_DIR")
    main(sys.argv[1])
