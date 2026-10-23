"""Read-only D1 original-TRAIN signal falsification, not a PnL backtest.

Original OKX ZIPs and four-leg HTTP pages are independently verified first.
The optimistic three-settlement funding envelope ignores basis/cadence vetoes,
so a failure to reach the *frozen* threshold proves no D1 entries could occur
on those observed settlements. Missing history remains UNKNOWN, never zero.
No trades, no fee claims, no validation/holdout, no model selection.
"""
from __future__ import annotations

import bisect
import json
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from research.tools.v99_r106_d1_real_train_source_join import (
    START, END, HOUR, FOLD_EDGES, PRICE_INST, FUND_INST, strict_json,
)
from research.tools.v99_r106_d1_basis_carry_preregistered import (
    COST_SHOCKS, ENTRY_FUNDING_TO_STRESS_COST, FUNDING_LOOKBACK,
    BASIS_ENTRY_ABS, LOOKBACK_HOURS, PairedBar, FundingFix, decide,
)
from research.verification.independent_d1_native_train_receipts import verify
from research.verification.independent_d1_okx_bulk_funding import check


def fold_number(ms):
    for i, (a, b) in enumerate(zip(FOLD_EDGES, FOLD_EDGES[1:]), 1):
        if a <= ms < b:
            return i
    raise ValueError("D1_FOLD_OUTSIDE_TRAIN")


def replay(price_root, funding_root, output):
    price_root, funding_root, output = map(Path, (price_root, funding_root, output))
    if verify(price_root)["status"] != "INDEPENDENT_FOUR_LEG_TRAIN_SOURCE_COMPLETE_NO_ECONOMICS":
        raise ValueError("UNVERIFIED_OKX_PRICE_RECEIPTS")
    if check(funding_root)["status"] != "INDEPENDENT_PARTIAL_FIRST_PARTY_FUNDING_NO_ECONOMICS":
        raise ValueError("UNVERIFIED_OKX_FUNDING_RECEIPTS")

    opens = {}
    expected = list(range(START, END, HOUR))
    for inst in PRICE_INST:
        rows = strict_json(price_root / inst / "train_opens.json")
        if [r["ts"] for r in rows] != expected:
            raise ValueError("NONCANONICAL_TRAIN_PRICE_GRID")
        opens[inst] = [float(r["open"]) for r in rows]

    rates = {}
    for inst in FUND_INST:
        rows = strict_json(funding_root / inst / "funding_rows.json")
        ts = [r["settlement_ms"] for r in rows]
        if ts != sorted(set(ts)) or any(t < START or t >= END for t in ts):
            raise ValueError("UNSAFE_FUNDING_TIMESTAMPS")
        rates[inst] = (ts, [Decimal(r["venue_rate"]) for r in rows])

    # The 24h projected funding is EXACTLY sum(last 3 rates). The upper
    # envelope allows even triples that D1 would veto for cadence/staleness,
    # and ignores the price-basis filter: it cannot undercount eligibility
    # conditional on the published source being complete.
    envelopes = {str(f): {asset: {
        "observed_settlement_triples": 0, "max_optimistic_projected_24h": None,
        "triples_above_severe_threshold": 0,
        "triples_above_supersevere_threshold": 0,
    } for asset in ("BTC", "ETH")} for f in range(1, 6)}
    thresholds = {name: Decimal(str(ENTRY_FUNDING_TO_STRESS_COST * 4 * cost))
                  for name, cost in COST_SHOCKS.items()}
    for asset in ("BTC", "ETH"):
        ts, values = rates[asset + "-USDT-SWAP"]
        for i in range(FUNDING_LOOKBACK - 1, len(ts)):
            fold = str(fold_number(ts[i]))
            d = envelopes[fold][asset]
            projected = sum(values[i - 2:i + 1], Decimal(0))
            d["observed_settlement_triples"] += 1
            prev = d["max_optimistic_projected_24h"]
            if prev is None or projected > Decimal(prev):
                d["max_optimistic_projected_24h"] = str(projected)
            for name, threshold in thresholds.items():
                if projected > threshold:
                    key = "triples_above_" + ("severe" if name == "severe_model_only" else "supersevere") + "_threshold"
                    d[key] += 1

    days = {str(f): {asset: {"eligible_causal_days_severe": 0,
                             "eligible_causal_days_supersevere": 0,
                             "veto_missing_or_irregular_funding": 0,
                             "valid_funding_days": 0}
                     for asset in ("BTC", "ETH")} for f in range(1, 6)}
    complete_pair_days = 0
    paired_decisions_checked = 0
    for hour_idx in range(LOOKBACK_HOURS, len(expected), 24):
        now_ms = expected[hour_idx]
        if now_ms % (24 * HOUR):
            raise ValueError("DECISION_NOT_UTC_MIDNIGHT")
        fold = str(fold_number(now_ms))
        now = datetime.fromtimestamp(now_ms / 1000, timezone.utc)
        paired_bars = {}
        paired_fixes = {}
        ready = True
        for asset in ("BTC", "ETH"):
            inst = asset + "-USDT-SWAP"
            spot = asset + "-USDT"
            ts, values = rates[inst]
            ix = bisect.bisect_right(ts, now_ms - HOUR)
            recent_ts = ts[max(0, ix - 3):ix]
            recent_rates = values[max(0, ix - 3):ix]
            # Strict D1 cadence is never relaxed to conceal +1s/+2s.
            valid = (len(recent_ts) == 3 and
                     recent_ts[1] - recent_ts[0] == 8 * HOUR and
                     recent_ts[2] - recent_ts[1] == 8 * HOUR and
                     now_ms - recent_ts[-1] <= 9 * HOUR)
            d = days[fold][asset]
            if not valid:
                d["veto_missing_or_irregular_funding"] += 1
                ready = False
                continue
            d["valid_funding_days"] += 1
            projected = sum(recent_rates, Decimal(0))
            basis = opens[inst][hour_idx - 1] / opens[spot][hour_idx - 1] - 1
            positive = all(x > 0 for x in recent_rates)
            for name, threshold in thresholds.items():
                if projected > threshold and positive and abs(basis) < BASIS_ENTRY_ABS:
                    key = ("eligible_causal_days_severe" if name == "severe_model_only"
                           else "eligible_causal_days_supersevere")
                    d[key] += 1
            paired_bars[asset] = [PairedBar(
                time=datetime.fromtimestamp(expected[j] / 1000, timezone.utc),
                asset=asset, spot_open=opens[spot][j], perp_open=opens[inst][j],
                source_spot="OKX", source_perp="OKX",
                observed_at=datetime.fromtimestamp(expected[j] / 1000, timezone.utc))
                for j in range(hour_idx - LOOKBACK_HOURS, hour_idx)]
            paired_fixes[asset] = [FundingFix(
                asset=asset, announced_at=datetime.fromtimestamp(t / 1000, timezone.utc),
                settled_at=datetime.fromtimestamp(t / 1000, timezone.utc),
                rate=float(r), source="OKX", instrument=inst)
                for t, r in zip(recent_ts, recent_rates)]
        if ready:
            complete_pair_days += 1
            for name, cost in COST_SHOCKS.items():
                result = decide(now, paired_bars, paired_fixes, cost)
                for asset in ("BTC", "ETH"):
                    key = ("eligible_causal_days_severe" if name == "severe_model_only"
                           else "eligible_causal_days_supersevere")
                    expected_weight = .25 if (
                        days[fold][asset][key] and
                        # independently recompute THIS day's decision, not cumulative
                        sum(rates[asset + "-USDT-SWAP"][1][
                            bisect.bisect_right(rates[asset + "-USDT-SWAP"][0], now_ms - HOUR) - 3:
                            bisect.bisect_right(rates[asset + "-USDT-SWAP"][0], now_ms - HOUR)
                        ], Decimal(0)) > thresholds[name] and
                        all(x > 0 for x in [f.rate for f in paired_fixes[asset]]) and
                        abs(opens[asset + "-USDT-SWAP"][hour_idx - 1] /
                            opens[asset + "-USDT"][hour_idx - 1] - 1) < BASIS_ENTRY_ABS
                    ) else 0.
                    actual = result.btc_pair_weight if asset == "BTC" else result.eth_pair_weight
                    if actual != expected_weight:
                        raise ValueError("INDEPENDENT_CAUSAL_DECISION_MISMATCH")
                paired_decisions_checked += 1

    # No funding in the first 2021-12..2022-02 block: this is UNKNOWN,
    # not evidence of a losing strategy or of zero funding.
    observed_folds_without_severe_threshold = [
        int(f) for f in ("2", "3", "4", "5")
        if all(envelopes[f][asset]["triples_above_severe_threshold"] == 0
               for asset in ("BTC", "ETH"))
    ]
    report = {
        "schema": "D1_ACTUAL_OKX_TRAIN_FUNDING_SIGNAL_FALSIFICATION_V1",
        "status": "SOURCE_ONLY_SIGNAL_PROBE_NOT_ECONOMICS",
        "original_price_oracle_pass": True,
        "original_funding_oracle_pass": True,
        "train_end_exclusive_ms": END,
        "fee_thresholds_four_leg_round_trip_x2": {k: str(v) for k, v in thresholds.items()},
        "optimistic_observed_funding_envelope": envelopes,
        "causal_daily_source_coverage": days,
        "both_assets_funding_valid_days": complete_pair_days,
        "original_d1_paired_decisions_independently_checked": paired_decisions_checked,
        "folds_2_to_5_without_even_optimistic_severe_funding_threshold": observed_folds_without_severe_threshold,
        "source_completeness_caveat": "The optimistic envelope is conditional on the archived post-March-2022 published funding rates being complete; pre-March-2022 remains unknown.",
        "historical_economic_trial_run": False,
        "native_fee_tier_authenticated": False,
        "actual_account_fills_authenticated": False,
        "actual_account_funding_cash_authenticated": False,
        "validation_opened": False, "holdout_opened": False,
        "paper_publication_authorized": False, "orders_enabled": False,
        "promotion_authorized": False,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "d1_actual_train_signal_probe.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"], "thresholds": report["fee_thresholds_four_leg_round_trip_x2"],
        "folds_no_optimistic_severe_threshold": observed_folds_without_severe_threshold,
        "funding_valid_pair_days": complete_pair_days,
        "d1_decisions_verified": paired_decisions_checked,
        "envelope": envelopes, "causal": days,
        "promotion_authorized": False,
    }, sort_keys=True), flush=True)
    return report


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python -m research.tools.v99_r106_d1_actual_train_signal_falsification PRICE FUND OUT")
    replay(*sys.argv[1:])
