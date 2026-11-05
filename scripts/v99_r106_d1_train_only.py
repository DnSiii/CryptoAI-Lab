#!/usr/bin/env python3
"""V99 R106 distinct candidate D1: volatility risk-premium carry, TRAIN ONLY.

EXPERIMENTAL / NOT VALIDATED. No order placement. No validation or holdout access.
Ex-ante rule: at each UTC daily close, use only the PREVIOUS completed day's
option-implied variance and preceding 30 completed daily BTC realized returns.
Sell one 1-day delta-hedged ATM straddle only if IV^2 > 1.5 * RV^2,
IV >= 0.35 and daily spread <= 0.015 of premium; otherwise stay cash.
Fixed notional: 10% of equity, never leveraged. No optimization/grid.
Daily marked-to-market payoff must be supplied from ORIGINAL executable
bid/ask fills and hedge ledger; absent evidence => FAIL CLOSED.
This is NOT a substitute for exchange-native funding/fees.
"""
import csv
import datetime as dt
import json
import math
import sys
from pathlib import Path

CUTOFF = dt.date(2023, 10, 1)
FIELDS = ("date", "btc_close", "atm_iv", "relative_spread",
          "straddle_hedged_net_return", "execution_verified", "funding_verified")
def evaluate(path):
    rows = list(csv.DictReader(Path(path).open(encoding="utf-8", newline="")))
    if not rows or not set(FIELDS).issubset(rows[0]):
        raise ValueError("missing complete source/ledger columns")
    dates = []
    for row in rows:
        d = dt.date.fromisoformat(row["date"])
        if d >= CUTOFF or (dates and d <= dates[-1]):
            raise ValueError("sealed boundary or unordered daily data")
        dates.append(d)
        for key in ("btc_close", "atm_iv", "relative_spread",
                    "straddle_hedged_net_return"):
            x = float(row[key])
            if not math.isfinite(x):
                raise ValueError("nonfinite ledger value")
        if float(row["btc_close"]) <= 0 or float(row["atm_iv"]) < 0:
            raise ValueError("invalid price or IV")
        if row["execution_verified"] != "true" or row["funding_verified"] != "true":
            raise ValueError("native execution/funding evidence missing")
    if len(rows) < 180:
        raise ValueError("insufficient TRAIN history for five chronological folds")
    # Signals at day i use strictly completed observations <= i-1.
    # Realized volatility annualized from 30 prior close-to-close returns.
    equity = 1.0
    fold_results = []
    n = len(rows)
    boundaries = [30 + (n-30)*j//5 for j in range(6)]
    for fold in range(5):
        start, end = boundaries[fold], boundaries[fold+1]
        fold_start = equity
        for i in range(start, end):
            prior = rows[i-1]
            returns = [math.log(float(rows[k]["btc_close"]) /
                                float(rows[k-1]["btc_close"]))
                       for k in range(i-30, i)]
            rv2 = 365 * sum(x*x for x in returns) / len(returns)
            iv = float(prior["atm_iv"])
            trade = (iv >= 0.35 and iv*iv > 1.5*rv2 and
                     float(prior["relative_spread"]) <= 0.015)
            # This net return MUST include original bid/ask, hedge fills,
            # native fees and settled funding. No modeled proxy allowed.
            daily = 0.1 * float(rows[i]["straddle_hedged_net_return"]) if trade else 0
            if daily <= -1:
                raise ValueError("invalid equity return")
            equity *= 1 + daily
        fold_results.append(equity/fold_start-1)
    return {"status":"TRAIN_EXPERIMENT_ONLY", "candidate":"D1",
            "fold_returns":fold_results, "positive_folds":sum(x>0 for x in fold_results),
            "train_return":equity-1, "promotion":False,
            "warning":"not independent validation; provenance flags must be externally audited"}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python v99_r106_d1_train_only.py VERIFIED_TRAIN.csv")
    print(json.dumps(evaluate(sys.argv[1]), indent=2))
