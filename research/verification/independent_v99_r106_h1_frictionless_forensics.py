"""Read-only H1 falsification: zero trading friction on FIXED rejected H1 decisions.

This is not a candidate, retune, model selection, fill simulation or new gate.
Two independent mathematical implementations check the same 15,864 TRAIN hours.
No imports of the H1 execution engine or its accounting helper.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

from research.verification.independent_d1_native_train_receipts import verify
from research.verification.independent_v99_r106_h1_dvol_spot_oracle import (
    START, END, HOUR, HOURS, EDGES, original_dvol, independent_targets,
)

SCHEMA = "V99_REJECTED_H1_READONLY_ZERO_FRICTION_ORACLE_V1"


def close(actual, expected, label, tolerance=1e-8):
    if not (math.isfinite(actual) and math.isfinite(expected)):
        raise ValueError(label + "_NONFINITE")
    if abs(actual - expected) > tolerance * max(1, abs(actual), abs(expected)):
        raise ValueError(label + "_MISMATCH")


def load_spot(root):
    if verify(root)["status"] != "INDEPENDENT_FOUR_LEG_TRAIN_SOURCE_COMPLETE_NO_ECONOMICS":
        raise ValueError("ORIGINAL_OKX_TRAIN_SOURCE_NOT_VERIFIED")
    series = []
    for instrument in ("BTC-USDT", "ETH-USDT"):
        rows = json.loads((Path(root) / instrument / "train_opens.json").read_text())
        if len(rows) != HOURS:
            raise ValueError("SPOT_HOURLY_GRID_INCOMPLETE")
        prices = []
        for i, row in enumerate(rows):
            if row["ts"] != START + i * HOUR:
                raise ValueError("SPOT_HOURLY_GRID_OR_HOLDOUT")
            price = float(row["open"])
            if not math.isfinite(price) or price <= 0:
                raise ValueError("INVALID_ORIGINAL_PRICE")
            prices.append(price)
        series.append(prices)
    return series


def read_original_rejection(root, prices, weekly):
    root = Path(root)
    report_path = root / "h1_train_report.json"
    report = json.loads(report_path.read_text())
    if report["status"] != "PERMANENT_TRAIN_REJECT_NO_RETUNE":
        raise ValueError("H1_NOT_ALREADY_REJECTED")
    if report["schema"] != "H1_PREREG_DVOL_FORWARD_RISK_SPOT_TRAIN_V1":
        raise ValueError("H1_SCHEMA_CHANGED")
    if (report["start_ms"], report["end_exclusive_ms"], report["hours"]) != (START, END, HOURS):
        raise ValueError("H1_TRAIN_PARTITION_CHANGED")
    if report["preregistration_commit"] != "72e301a2f1ff6097188842c9f8bdc5aaa0cd47d9":
        raise ValueError("H1_PREREG_CHANGED")
    if any(report[k] for k in ("validation_opened", "holdout_opened",
                                "orders_enabled", "promotion_authorized")):
        raise ValueError("H1_PROHIBITED_STATE")
    original = {}
    for scenario in ("severe", "supersevere"):
        journal_path = root / ("h1_" + scenario + "_hourly.jsonl")
        raw = journal_path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != report["results"][scenario]["journal_sha256"]:
            raise ValueError("ORIGINAL_H1_JOURNAL_HASH")
        rows = [json.loads(line) for line in raw.splitlines()]
        if len(rows) != HOURS:
            raise ValueError("H1_ORIGINAL_JOURNAL_LENGTH")
        for i, row in enumerate(rows):
            t = START + i * HOUR
            if row["hour_ms"] != t:
                raise ValueError("H1_ORIGINAL_HOLDOUT_OR_GRID")
            close(row["btc_open"], prices[0][i], "H1_BTC_SOURCE")
            close(row["eth_open"], prices[1][i], "H1_ETH_SOURCE")
            is_decision = (t, "BTC") in weekly
            if bool(row["rebalanced"]) != is_decision:
                raise ValueError("H1_ORIGINAL_DECISION_SCHEDULE")
            if is_decision:
                b, e = independent_targets(t, weekly)
                close(row["target_btc"], b, "H1_FIXED_BTC_DECISION")
                close(row["target_eth"], e, "H1_FIXED_ETH_DECISION")
        roi = float(rows[-1]["nav"]) - 1.0
        close(roi, report["results"][scenario]["metrics"]["roi"], "H1_REPORTED_ROI")
        original[scenario] = dict(roi=roi,
                                  positive_folds=report["results"][scenario]["metrics"]["positive_folds"],
                                  sha256=hashlib.sha256(raw).hexdigest())
    return report, original, hashlib.sha256(report_path.read_bytes()).hexdigest()


def two_independent_zero_friction_replays(prices, weekly):
    # First oracle: quantities + cash marked hourly at actual original opens.
    cash, qty = 1.0, [0.0, 0.0]
    navs = []
    decision_count = 0
    for i in range(HOURS):
        t = START + i * HOUR
        b, e = prices[0][i], prices[1][i]
        if (t, "BTC") in weekly:
            w_b, w_e = independent_targets(t, weekly)
            pre = cash + qty[0] * b + qty[1] * e
            qty = [pre * w_b / b, pre * w_e / e]
            cash = pre * (1.0 - w_b - w_e)
            decision_count += 1
        nav = cash + qty[0] * b + qty[1] * e
        if not math.isfinite(nav) or nav <= 0 or cash < -1e-12:
            raise ValueError("INVALID_ZERO_FRICTION_NAV")
        navs.append(nav)

    # Second oracle: independently compound weekly weighted *price ratios*;
    # never reuse quantities, cash, NAV, or a rebalance function from oracle 1.
    second = []
    base_nav, base_index = 1.0, 0
    weights = (0.0, 0.0)
    for i in range(HOURS):
        t = START + i * HOUR
        b, e = prices[0][i], prices[1][i]
        growth = ((1.0 - sum(weights))
                  + weights[0] * b / prices[0][base_index]
                  + weights[1] * e / prices[1][base_index])
        if (t, "BTC") in weekly:
            base_nav *= growth
            base_index = i
            weights = independent_targets(t, weekly)
            growth = 1.0
        second.append(base_nav * growth)
        close(navs[i], second[-1], "TWO_ORACLES_HOUR_" + str(i), 3e-9)

    if decision_count != 94 or len(weekly) != 188:
        raise ValueError("H1_DECISION_COUNT_CHANGED")
    folds = []
    for start, stop in zip(EDGES, EDGES[1:]):
        first = (start - START) // HOUR
        last = (stop - START) // HOUR - 1
        folds.append(navs[last] / navs[first] - 1)
    peak, dd = 1.0, 0.0
    for nav in navs:
        peak = max(peak, nav)
        dd = min(dd, nav / peak - 1)
    return dict(roi=navs[-1] - 1, fold_returns=folds,
                positive_folds=sum(x > 0 for x in folds),
                max_drawdown=dd, decision_count=decision_count,
                hourly_replays_equal=True)


def main(okx_root, dvol_root, h1_root, out_root):
    prices = load_spot(Path(okx_root))
    weekly = original_dvol(Path(dvol_root))
    report, original, report_sha = read_original_rejection(h1_root, prices, weekly)
    zero = two_independent_zero_friction_replays(prices, weekly)
    if zero["roi"] + 1e-8 < max(original[s]["roi"] for s in original):
        raise ValueError("FRICTIONLESS_BELOW_COSTLY_REPLAY")
    result = dict(schema=SCHEMA,
                  status="REJECTED_H1_READ_ONLY_FRICTIONLESS_FORENSICS",
                  start_ms=START, end_exclusive_ms=END, hours=HOURS,
                  source_okx_run=40019588739, source_dvol_run=40072202459,
                  original_h1_run=40072415531,
                  original_h1_report_sha256=report_sha,
                  original_h1_journal_sha256={s: v["sha256"] for s, v in original.items()},
                  decision_count=zero["decision_count"],
                  frictionless_roi=zero["roi"],
                  frictionless_positive_folds=zero["positive_folds"],
                  frictionless_fold_returns=zero["fold_returns"],
                  frictionless_max_drawdown=zero["max_drawdown"],
                  independent_hourly_vs_weekly_ratio_oracles_agree=zero["hourly_replays_equal"],
                  severe_roi=original["severe"]["roi"],
                  supersevere_roi=original["supersevere"]["roi"],
                  severe_positive_folds=original["severe"]["positive_folds"],
                  supersevere_positive_folds=original["supersevere"]["positive_folds"],
                  modeled_friction_roi_drag_severe_pp=100*(zero["roi"]-original["severe"]["roi"]),
                  modeled_friction_roi_drag_supersevere_pp=100*(zero["roi"]-original["supersevere"]["roi"]),
                  zero_cost_folds_below_original_severe_gate=zero["positive_folds"] < 4,
                  original_h1_rejection_unchanged=report["status"]=="PERMANENT_TRAIN_REJECT_NO_RETUNE",
                  actual_account_fills_authenticated=False,
                  historical_account_fee_tier_authenticated=False,
                  validation_opened=False, holdout_opened=False,
                  orders_enabled=False, paper_publication_authorized=False,
                  promotion_authorized=False)
    output = Path(out_root)
    output.mkdir(parents=True, exist_ok=True)
    (output / "h1_frictionless_forensics.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in (
        "status", "frictionless_roi", "frictionless_positive_folds",
        "frictionless_max_drawdown", "severe_roi", "supersevere_roi",
        "modeled_friction_roi_drag_severe_pp", "zero_cost_folds_below_original_severe_gate",
        "promotion_authorized")}, sort_keys=True))
    return result


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_h1_frictionless_forensics OKX DVOL H1 OUT")
    main(*sys.argv[1:])
