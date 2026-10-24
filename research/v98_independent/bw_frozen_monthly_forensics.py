#!/usr/bin/env python3
"""BW rejected-engine, immutable, native per-asset/month attribution. No refit."""
from __future__ import annotations
import argparse
import datetime as dt
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
import bw_90cell as engine

ASSETS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")
PATHS = ("BW_full", "BW_core_only", "BW_minus_opportunity",
         "BW_minus_RV", "BW_minus_stress")
FEES = ("base", "severe")
ORDER = "carried_before_fill"
FIELDS = ("funding", "fees", "slippage", "turnover", "gap", "intrabar")
ORIGIN = dt.datetime(2022, 12, 1, tzinfo=dt.timezone.utc)

def close(a, b):
    return math.isclose(float(a), float(b), rel_tol=1e-9, abs_tol=1e-6)

def main():
    frames, manifest = engine.load_official()
    o, h, l, c, q, r, e, ml, mh = frames
    assert c.shape == (18288, 4) and int(e.sum()) == 9144
    source = engine.source_bundle(c, q, r, e)
    risks = engine.prepare_risk(frames)
    original = engine.settle_hour
    results = []
    for path in PATHS:
        decisions = engine.preregistered_decisions(path, frames, source)
        for fee in FEES:
            count = 0
            monthly = {}
            by_asset = defaultdict(lambda: {field: 0. for field in FIELDS})
            def traced(previous, old, prev_close, opening, high, low, closing,
                       target, rate, event, mark_low, mark_high,
                       fee_mode, funding_order):
                nonlocal count
                assert fee_mode == fee and funding_order == ORDER
                t = engine.START_EXECUTION + count
                if t >= engine.HOURS:
                    raise ValueError("BW_FORENSIC_EXTRA_HOUR")
                old = np.asarray(old, dtype=float)
                target = np.asarray(target, dtype=float)
                opening = np.asarray(opening, dtype=float)
                closing = np.asarray(closing, dtype=float)
                for supplied, pinned in (
                    (opening, o[t]), (closing, c[t]), (rate, r[t]),
                    (event, e[t]), (mark_low, ml[t]), (mark_high, mh[t])):
                    if not np.array_equal(supplied, pinned):
                        raise ValueError("BW_FORENSIC_SOURCE_MISMATCH_T" + str(t))
                turnover = np.abs(target - old) * opening
                f, slip = engine.FEES[fee]
                obligations = old * rate * event
                marks = np.where(obligations >= 0, mark_high, mark_low)
                funding = -obligations * marks
                gap = old * (opening - prev_close)
                intrabar = target * (closing - opening)
                arrays = {"funding": funding, "fees": turnover * f,
                          "slippage": turnover * slip, "turnover": turnover,
                          "gap": gap, "intrabar": intrabar}
                month = (ORIGIN + dt.timedelta(hours=t)).strftime("%Y-%m")
                if month not in monthly:
                    monthly[month] = {
                        "start_nav": float(previous),
                        "end_nav": float(previous),
                        "by_asset": {a: {field: 0. for field in FIELDS}
                                     for a in ASSETS}}
                bucket = monthly[month]
                for j, asset in enumerate(ASSETS):
                    for field in FIELDS:
                        value = float(arrays[field][j])
                        bucket["by_asset"][asset][field] += value
                        by_asset[asset][field] += value
                expected = float(previous) + sum(
                    float(np.sum(arrays[k])) * (-1. if k in ("fees", "slippage") else 1.)
                    for k in ("funding", "fees", "slippage", "gap", "intrabar"))
                out = original(previous, old, prev_close, opening, high, low,
                               closing, target, rate, event, mark_low, mark_high,
                               fee_mode=fee_mode, funding_order=funding_order)
                if not close(expected, out["cash"]):
                    raise ValueError("BW_FORENSIC_CASHFLOW_T" + str(t))
                bucket["end_nav"] = float(out["cash"])
                count += 1
                return out
            engine.settle_hour = traced
            try:
                receipt = engine.cell(path, "immediate", fee, ORDER,
                                      frames, risks, decisions)
            finally:
                engine.settle_hour = original
            if count != engine.HOURS - engine.START_EXECUTION:
                raise ValueError("BW_FORENSIC_INCOMPLETE")
            sums = {k: sum(v[k] for v in by_asset.values()) for k in FIELDS}
            for k in ("funding", "fees", "slippage", "turnover"):
                if not close(sums[k], receipt[k]):
                    raise ValueError("BW_FORENSIC_RECEIPT_" + k)
            net = sums["funding"] - sums["fees"] - sums["slippage"] + sums["gap"] + sums["intrabar"]
            if not close(receipt["initial_nav"] + net, receipt["final_nav"]):
                raise ValueError("BW_FORENSIC_NAV_IDENTITY")
            if not close(sum(
                sum(b["by_asset"][a]["funding"] - b["by_asset"][a]["fees"]
                    - b["by_asset"][a]["slippage"] + b["by_asset"][a]["gap"]
                    + b["by_asset"][a]["intrabar"] for a in ASSETS)
                for b in monthly.values()), net):
                raise ValueError("BW_FORENSIC_MONTHLY_IDENTITY")
            if not close(monthly["2023-01"]["start_nav"], receipt["initial_nav"]):
                raise ValueError("BW_FORENSIC_FIRST_MONTH")
            if not close(monthly["2024-12"]["end_nav"], receipt["final_nav"]):
                raise ValueError("BW_FORENSIC_LAST_MONTH")
            for year in ("2023", "2024"):
                ym = [m for m in sorted(monthly) if m.startswith(year)]
                if not close(monthly[ym[-1]]["end_nav"], receipt["annual"][year]["end_nav"]):
                    raise ValueError("BW_FORENSIC_YEAR_END_" + year)
                for left, right in zip(ym, ym[1:]):
                    if not close(monthly[left]["end_nav"], monthly[right]["start_nav"]):
                        raise ValueError("BW_FORENSIC_MONTH_CHAIN")
            results.append({"path": path, "fee": fee, "order": ORDER,
                            "hours": count, "initial_nav": receipt["initial_nav"],
                            "final_nav": receipt["final_nav"],
                            "two_year_cagr": receipt["two_year_cagr"],
                            "totals": sums, "by_asset": dict(by_asset),
                            "monthly": monthly, "receipt_reconciled": True})
            print("BW_FROZEN_ATTRIBUTION", path, fee, "NAV",
                  round(receipt["final_nav"], 2), "funding",
                  round(sums["funding"], 2), "friction",
                  round(sums["fees"] + sums["slippage"], 2))
    index = {(case["path"], case["fee"]): case for case in results}
    ablations = {}
    for fee in FEES:
        full = index["BW_full", fee]
        for sleeve, removed in (("Opportunity", "BW_minus_opportunity"),
                                ("RV", "BW_minus_RV"),
                                ("Stress", "BW_minus_stress")):
            other = index[removed, fee]
            monthly = {}
            for month in sorted(full["monthly"]):
                f = full["monthly"][month]
                a = other["monthly"][month]
                delta_log = math.log(f["end_nav"] / f["start_nav"]) - math.log(
                    a["end_nav"] / a["start_nav"])
                monthly[month] = float(delta_log)
            ablations[fee + "|" + sleeve] = {
                "year_2023_marginal_log_growth": float(sum(v for k, v in monthly.items() if k.startswith("2023"))),
                "year_2024_marginal_log_growth": float(sum(v for k, v in monthly.items() if k.startswith("2024"))),
                "worst_months": sorted(monthly.items(), key=lambda kv: kv[1])[:5],
                "best_months": sorted(monthly.items(), key=lambda kv: kv[1], reverse=True)[:5],
                "monthly_marginal_log_growth": monthly}
    return {"architecture": "BW", "rejected_engine_not_rescued": True,
            "training_only": True, "validation_2025_read": False,
            "external_benchmarks_used": False, "cases": results,
            "ablation_monthly_attribution": ablations,
            "decision": "PASS_BW_FROZEN_POST_REJECTION_MONTHLY_NATIVE_ATTRIBUTION_NOT_TRADING_APPROVAL"}

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    args = p.parse_args()
    result = main()
    Path(args.output).write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    for k, v in result["ablation_monthly_attribution"].items():
        print("BW_FROZEN_MONTHLY_MARGINAL", k, "2023",
              round(v["year_2023_marginal_log_growth"], 6), "2024",
              round(v["year_2024_marginal_log_growth"], 6),
              "worst", v["worst_months"][:3])
    print(result["decision"])
