"""Independent 661-day fixture numeric gate reexecution (NO original options).

Does not import the primary numeric evaluator or its constants.
No historical fee/fill/source/portfolio certification and no holdout.
"""
from __future__ import annotations

import math
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation


def dec(x):
    if isinstance(x, bool):
        raise AssertionError("BOOLEAN_REFERENCE_VALUE")
    try:
        value = Decimal(str(x))
    except (TypeError, ValueError, InvalidOperation) as exc:
        raise AssertionError("BAD_REFERENCE_NUMBER") from exc
    if not value.is_finite() or value <= 0:
        raise AssertionError("NONPOSITIVE_REFERENCE_EQUITY")
    return value


def verify(source, report):
    if (source.get("fixture") is not True or
            report.get("source_fixture") is not True or
            report.get("schema") != "V99_I1_TRAIN_NUMERIC_GATE_RESULT_V1" or
            report.get("original_options_economic_train_certified") is not False or
            report.get("independent_original_trade_replay_verified") is not False or
            any(report.get(key) is not False for key in (
                "promotion_authorized", "freeze_authorized",
                "validation_opened", "holdout_opened", "orders_enabled"))):
        raise AssertionError("FORGED_ECONOMIC_CERTIFICATION")
    scenarios = ("severe", "supersevere")
    if set(source.get("scenarios", {})) != set(scenarios) or set(
            report.get("scenarios", {})) != set(scenarios):
        raise AssertionError("INCOMPLETE_REFERENCE_SCENARIOS")
    initial = dec(source["initial_capital_usd"])
    start = date(2021, 12, 9)
    stop = date(2023, 10, 1)
    n = (stop - start).days
    folds = [int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp()*1000)
             for s in ("2021-12-09T00:00:00", "2022-04-20T04:00:00",
                       "2022-08-30T09:00:00", "2023-01-09T14:00:00",
                       "2023-05-21T19:00:00", "2023-10-01T00:00:00")]
    regimes = {a + "_" + v for a in ("BULL", "BEAR", "SIDEWAYS")
               for v in ("LOW_VOL", "HIGH_VOL")}
    aligned = []
    exposure = []
    passes = []
    for scenario in scenarios:
        rows = source["scenarios"][scenario]
        got = report["scenarios"][scenario]
        if len(rows) != n or got.get("scenario") != scenario:
            raise AssertionError("INCOMPLETE_REFERENCE_DAYS")
        prev = initial
        peak = initial
        dd = Decimal(0)
        gains, losses, factors = [], [], []
        fold_factors = [Decimal(1)]*5
        regime_factors = {r: Decimal(1) for r in regimes}
        counts = {r: 0 for r in regimes}
        stamps = []
        for i, row in enumerate(rows):
            day = start + timedelta(days=i)
            t = int(datetime(day.year, day.month, day.day, 23, 59, 59,
                             tzinfo=timezone.utc).timestamp()*1000)
            fold = next((j for j in range(1,6)
                         if folds[j-1] <= t < folds[j]), None)
            if (type(row.get("ts_ms")) is not int or row["ts_ms"] != t or
                    type(row.get("fold")) is not int or row["fold"] != fold or
                    row.get("regime") not in regimes or
                    not isinstance(row.get("actual_exposure_key"), str) or
                    not row["actual_exposure_key"]):
                raise AssertionError("FORGED_REFERENCE_CLOCK_OR_REGIME")
            value = dec(row["equity_usd"])
            benchmark = dec(row["benchmark_usd"])
            change = value - prev
            if change > 0:
                gains.append(change)
            elif change < 0:
                losses.append(-change)
            factor = value / prev
            factors.append(factor)
            fold_factors[fold-1] *= factor
            regime_factors[row["regime"]] *= factor
            counts[row["regime"]] += 1
            peak = max(peak, value)
            dd = min(dd, value/peak-1)
            prev = value
            stamps.append((benchmark, row["regime"]))
        aligned.append(stamps)
        exposure.append([r["actual_exposure_key"] for r in rows])
        roi = prev/initial-1
        remove = (prev/initial)/max(factors)-1
        profit = sum(gains, Decimal(0))
        loss = sum(losses, Decimal(0))
        top = math.ceil(n/100)
        gain_share = sum(sorted(gains, reverse=True)[:top], Decimal(0))/profit if profit else Decimal(1)
        loss_share = sum(sorted(losses, reverse=True)[:top], Decimal(0))/loss if loss else Decimal(0)
        pf = profit/loss if loss else None if profit else Decimal(0)
        expected = {
            "total_roi": roi, "remove_best_day_roi": remove,
            "max_drawdown": dd, "top_1pct_positive_gain_share": gain_share,
            "worst_1pct_loss_share": loss_share,
            "benchmark_roi": stamps[-1][0]/initial-1,
        }
        for key, number in expected.items():
            if Decimal(got[key]) != number:
                raise AssertionError("INDEPENDENT_NUMERIC_METRIC_MISMATCH:" + key)
        if (got.get("profit_factor") != ("infinite" if pf is None else str(pf))
                or [Decimal(x) for x in got.get("fold_roi", [])] !=
                [x-1 for x in fold_factors]
                or got.get("positive_folds") != sum(x>1 for x in fold_factors)
                or got.get("regime_days") != counts
                or {k: Decimal(v) for k,v in got.get("regime_roi_descriptive_only", {}).items()}
                != {k:v-1 for k,v in regime_factors.items()}):
            raise AssertionError("INDEPENDENT_FOLD_REGIME_OR_PF_MISMATCH")
        gates = {
            "positive_total": roi > 0,
            "fold_positive": sum(x>1 for x in fold_factors) >=
                             (4 if scenario == "severe" else 3),
            "profit_factor": pf is None or pf > 1,
            "remove_best_day_positive": remove > 0,
            "max_drawdown": dd >= Decimal("-0.35"),
            "top_1pct_gain_concentration": gain_share <= Decimal("0.40"),
            "worst_1pct_loss_concentration": loss_share <= Decimal("0.50"),
            "original_benchmark_excess": roi > stamps[-1][0]/initial-1,
            "six_regimes_present": all(counts.values()),
        }
        if got.get("gates") != gates or got.get("numeric_pass") is not all(gates.values()):
            raise AssertionError("INDEPENDENT_GATE_DECISION_MISMATCH")
        passes.append(all(gates.values()))
    if aligned[0] != aligned[1]:
        raise AssertionError("REFERENCE_SCENARIO_REGIME_BENCHMARK_MISMATCH")
    divergent = sum(a != b for a,b in zip(*exposure))
    if (report.get("days_per_scenario") != n or
            report.get("scenario_path_divergence_days") != divergent or
            report.get("numeric_train_pass_both_scenarios") is not all(passes) or
            report.get("higher_cost_scenario_more_profitable_not_alpha_evidence") is not (
                Decimal(report["scenarios"]["supersevere"]["total_roi"]) >
                Decimal(report["scenarios"]["severe"]["total_roi"]))):
        raise AssertionError("INDEPENDENT_PAIRED_SCENARIO_MISMATCH")
    return {"status": "INDEPENDENT_FIXTURE_NUMERIC_REPLAY_MATCH",
            "days_per_scenario": n, "scenario_path_divergence_days": divergent,
            "original_options_economic_train_certified": False,
            "promotion_authorized": False}
