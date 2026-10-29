"""Ex-ante numeric I1 full-TRAIN gate; never source/fee/fill certification.

Requires 661 original-date daily USD-equivalent NAVs for BOTH scenarios.
The caller must independently authenticate/replay all option lifecycle bytes,
native fees, margin, liquidation, delivery and marks. No validation/holdout.
Prereg: research/V99_R106_I1_TRAIN_ECONOMIC_NUMERIC_GATE_PREREG_20261028.md
"""
from __future__ import annotations

import json
import math
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from research.tools.v99_r106_d1_real_train_source_join import FOLD_EDGES

FIRST = date(2021, 12, 9)
END = date(2023, 10, 1)
DAYS = (END - FIRST).days
SCENARIOS = ("severe", "supersevere")
REGIMES = tuple(a + "_" + v for a in ("BULL", "BEAR", "SIDEWAYS")
                for v in ("LOW_VOL", "HIGH_VOL"))
NO_AUTHORIZATION = dict(
    original_options_economic_train_certified=False,
    independent_original_trade_replay_verified=False,
    freeze_authorized=False, promotion_authorized=False,
    validation_opened=False, holdout_opened=False,
    orders_enabled=False, paper_publication_authorized=False,
)


def _money(value):
    if isinstance(value, bool):
        raise ValueError("BOOLEAN_NOT_EQUITY")
    try:
        number = Decimal(str(value))
    except (ValueError, InvalidOperation, TypeError) as exc:
        raise ValueError("INVALID_EQUITY") from exc
    if not number.is_finite() or number <= 0:
        raise ValueError("NONPOSITIVE_OR_NONFINITE_EQUITY")
    return number


def _expected_clock(i):
    d = FIRST + timedelta(days=i)
    return int(datetime(d.year, d.month, d.day, 23, 59, 59,
                        tzinfo=timezone.utc).timestamp() * 1000)


def _fold(clock):
    return next((i for i in range(1, 6)
                 if FOLD_EDGES[i-1] <= clock < FOLD_EDGES[i]), None)


def _one_scenario(rows, initial, scenario):
    if not isinstance(rows, list) or len(rows) != DAYS:
        raise ValueError("INCOMPLETE_661_DAY_TRAIN_EQUITY")
    previous = initial
    peak = initial
    worst_drawdown = Decimal(0)
    positives, negatives = [], []
    fold_factors = [Decimal(1)] * 5
    regime_factors = {name: Decimal(1) for name in REGIMES}
    regime_counts = {name: 0 for name in REGIMES}
    factors, keys, benchmarks, regimes = [], [], [], []
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError("INVALID_DAILY_EQUITY_ROW")
        clock = _expected_clock(i)
        fold = _fold(clock)
        if (type(row.get("ts_ms")) is not int or row["ts_ms"] != clock
                or type(row.get("fold")) is not int or row["fold"] != fold
                or row.get("regime") not in REGIMES
                or not isinstance(row.get("actual_exposure_key"), str)
                or not row["actual_exposure_key"]):
            raise ValueError("MISSING_DUPLICATE_SEALED_OR_FORGED_DAILY_GRID")
        equity = _money(row.get("equity_usd"))
        benchmark = _money(row.get("benchmark_usd"))
        change = equity - previous
        (positives if change > 0 else negatives if change < 0 else []).append(
            abs(change)) if change else None
        factor = equity / previous
        factors.append(factor)
        fold_factors[fold-1] *= factor
        regime_factors[row["regime"]] *= factor
        regime_counts[row["regime"]] += 1
        peak = max(peak, equity)
        worst_drawdown = min(worst_drawdown, equity / peak - 1)
        previous = equity
        keys.append(row["actual_exposure_key"])
        benchmarks.append(benchmark)
        regimes.append(row["regime"])
    total = previous / initial - 1
    best_factor = max(factors)
    remove_best = (previous / initial) / best_factor - 1
    fold_roi = [factor - 1 for factor in fold_factors]
    top_n = math.ceil(DAYS / 100)
    gain_total = sum(positives, Decimal(0))
    loss_total = sum(negatives, Decimal(0))
    gain_concentration = (sum(sorted(positives, reverse=True)[:top_n], Decimal(0))
                          / gain_total if gain_total > 0 else Decimal(1))
    loss_concentration = (sum(sorted(negatives, reverse=True)[:top_n], Decimal(0))
                          / loss_total if loss_total > 0 else Decimal(0))
    pf = (gain_total / loss_total if loss_total > 0 else
          None if gain_total > 0 else Decimal(0))
    benchmark_roi = benchmarks[-1] / initial - 1
    gates = {
        "positive_total": total > 0,
        "fold_positive": sum(x > 0 for x in fold_roi) >=
                         (4 if scenario == "severe" else 3),
        "profit_factor": pf is None or pf > 1,
        "remove_best_day_positive": remove_best > 0,
        "max_drawdown": worst_drawdown >= Decimal("-0.35"),
        "top_1pct_gain_concentration": gain_concentration <= Decimal("0.40"),
        "worst_1pct_loss_concentration": loss_concentration <= Decimal("0.50"),
        "original_benchmark_excess": total > benchmark_roi,
        "six_regimes_present": all(regime_counts.values()),
    }
    return {
        "scenario": scenario, "total_roi": str(total),
        "positive_folds": sum(x > 0 for x in fold_roi),
        "fold_roi": [str(x) for x in fold_roi],
        "profit_factor": str(pf) if pf is not None else "infinite",
        "remove_best_day_roi": str(remove_best),
        "max_drawdown": str(worst_drawdown),
        "top_1pct_positive_gain_share": str(gain_concentration),
        "worst_1pct_loss_share": str(loss_concentration),
        "benchmark_roi": str(benchmark_roi),
        "regime_days": regime_counts,
        "regime_roi_descriptive_only":
            {k: str(v-1) for k, v in regime_factors.items()},
        "gates": gates, "numeric_pass": all(gates.values()),
        "_keys": keys, "_benchmarks": benchmarks, "_regimes": regimes,
    }


def _evaluate(document, *, provisional=False):
    # A provisional diagnostic is deliberately NOT the official economic gate.
    # It cannot turn original-input claims into source certification.
    if (not isinstance(document, dict)
            or document.get("schema") != "V99_I1_FIXED_90W_DAILY_TRAIN_EQUITY_INPUT_V1"
            or document.get("fixture") is not (False if provisional else True)
            or set(document.get("scenarios", {})) != set(SCENARIOS)):
        raise ValueError("ORIGINAL_ECONOMIC_SOURCE_PROVENANCE_NOT_CERTIFIED")
    if provisional:
        required_false = (
            "original_source_receipts_independently_authenticated",
            "original_options_economic_train_certified",
            "independent_original_trade_replay_verified",
            "historical_native_fee_certified",
            "original_historical_economic_train_executed",
            "freeze_authorized", "promotion_authorized",
            "validation_opened", "holdout_opened", "orders_enabled",
            "paper_publication_authorized",
        )
        if (document.get("status") != "PROVISIONAL_UNCERTIFIED_NATIVE_EVENT_EQUITY"
                or any(document.get(k) is not False for k in required_false)):
            raise ValueError("PROVISIONAL_SOURCE_OR_CERTIFICATION_FORGERY")
    initial = _money(document.get("initial_capital_usd"))
    results = {
        name: _one_scenario(document["scenarios"][name], initial, name)
        for name in SCENARIOS
    }
    s, x = (results[name] for name in SCENARIOS)
    if (s["_benchmarks"] != x["_benchmarks"]
            or s["_regimes"] != x["_regimes"]):
        raise ValueError("SCENARIO_BENCHMARK_OR_REGIME_PATH_MISMATCH")
    different = sum(a != b for a, b in zip(s["_keys"], x["_keys"]))
    for value in results.values():
        for key in ("_keys", "_benchmarks", "_regimes"):
            del value[key]
    # The four internal R106 fold edges are intraday (04/09/14/19 UTC).
    # 661 end-of-day NAVs cannot establish the exact original five folds.
    # The descriptive daily-proxy fold screen is retained for reproducibility,
    # but must NEVER be interpreted as a formal chronological TRAIN gate.
    missing_intraday_edges = [
        datetime.fromtimestamp(edge / 1000, timezone.utc).isoformat()
        for edge in FOLD_EDGES[1:-1]
        if edge not in {_expected_clock(i) for i in range(DAYS)}
    ]
    if len(missing_intraday_edges) != 4:
        raise ValueError("UNEXPECTED_EXACT_FOLD_BOUNDARY_GEOMETRY")
    return {
        "schema": "V99_I1_TRAIN_NUMERIC_GATE_RESULT_V1",
        "fold_attribution": "DAILY_PROXY_NOT_EXACT",
        "missing_intraday_fold_boundary_utc": missing_intraday_edges,
        "exact_chronological_fold_gate_evaluable": False,
        "exact_chronological_fold_gate_pass": False,
        "formal_train_freeze_blocked_by_missing_intraday_nav": True,
        "status": ("PROVISIONAL_NONFIXTURE_NUMERIC_DIAGNOSTIC_NOT_CERTIFIED"
                   if provisional else "FIXTURE_NUMERIC_SCREEN_ONLY_NOT_ORIGINAL_ECONOMICS"),
        "days_per_scenario": DAYS,
        "source_fixture": not provisional,
        "numeric_screen_descriptive_only": provisional,
        "scenario_path_divergence_days": different,
        "higher_cost_scenario_more_profitable_not_alpha_evidence":
            Decimal(x["total_roi"]) > Decimal(s["total_roi"]),
        "numeric_train_pass_both_scenarios":
            all(value["numeric_pass"] for value in results.values()),
        "scenarios": results, **NO_AUTHORIZATION,
    }


def evaluate(document):
    """Official fixture-only gate. Historical economic certification stays locked."""
    return _evaluate(document, provisional=False)


def evaluate_provisional(document):
    """Read-only nonfixture TRAIN diagnostic; never source certification or promotion.

    Accepts only the explicitly uncertified native event replay contract.
    An independently authenticated original source-to-event builder is still
    required before any historical TRAIN result can be certified.
    """
    return _evaluate(document, provisional=True)


def main(input_file, output_file, *, provisional=False):
    source = json.loads(Path(input_file).read_text(encoding="utf-8"))
    report = (evaluate_provisional(source) if provisional else evaluate(source))
    Path(output_file).write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8")
    print(json.dumps({"status": report["status"],
                      "numeric_screen_descriptive_only":
                      report["numeric_screen_descriptive_only"],
                      "numeric_train_pass_both_scenarios":
                      report["numeric_train_pass_both_scenarios"],
                      "original_options_economic_train_certified": False,
                      "promotion_authorized": False}, sort_keys=True))
    return report


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4) or (len(sys.argv) == 4 and sys.argv[3] != "provisional"):
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_train_numeric_gate INPUT_EQUITY_JSON OUT_JSON [provisional]")
    main(sys.argv[1], sys.argv[2], provisional=len(sys.argv) == 4)
