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


def independent_exact_folds(rows, snapshots, initial, edges):
    """Reference recomposition of returns across original fold timestamps."""
    by_day = {}
    for snapshot in snapshots:
        stamp = snapshot.get("ts_ms")
        if type(stamp) is not int or stamp not in edges or stamp in by_day:
            raise AssertionError("INDEPENDENT_FORGED_FOLD_SNAPSHOT_CLOCK")
        by_day[stamp] = dec(snapshot.get("equity_usd"))
    factors = [Decimal(1)] * 5
    prior = initial
    for row in rows:
        close = row["ts_ms"]
        value = dec(row["equity_usd"])
        intraday = next((t for t in edges[1:-1]
                         if datetime.fromtimestamp(t/1000, timezone.utc).date() ==
                            datetime.fromtimestamp(close/1000, timezone.utc).date()), None)
        if intraday is not None and intraday in by_day:
            edge_value = by_day[intraday]
            old = next(j for j in range(5) if edges[j] <= intraday-1 < edges[j+1])
            new = next(j for j in range(5) if edges[j] <= intraday < edges[j+1])
            factors[old] *= edge_value/prior
            factors[new] *= value/edge_value
        else:
            j = next(j for j in range(5) if edges[j] <= close < edges[j+1])
            factors[j] *= value/prior
        prior = value
    return [str(f-1) for f in factors]


def verify(source, report):
    provisional = source.get("fixture") is False
    expected_status = ("PROVISIONAL_NONFIXTURE_NUMERIC_DIAGNOSTIC_NOT_CERTIFIED"
                       if provisional else "FIXTURE_NUMERIC_SCREEN_ONLY_NOT_ORIGINAL_ECONOMICS")
    if (source.get("fixture") is not (False if provisional else True)
            or report.get("source_fixture") is not (not provisional)
            or report.get("status") != expected_status
            or report.get("numeric_screen_descriptive_only") is not provisional
            or report.get("schema") != "V99_I1_TRAIN_NUMERIC_GATE_RESULT_V1"
            or report.get("original_options_economic_train_certified") is not False
            or report.get("independent_original_trade_replay_verified") is not False
            or any(report.get(key) is not False for key in (
                "promotion_authorized", "freeze_authorized",
                "validation_opened", "holdout_opened", "orders_enabled",
                "paper_publication_authorized"))):
        raise AssertionError("FORGED_ECONOMIC_CERTIFICATION")
    if provisional:
        flags = ("original_source_receipts_independently_authenticated",
                 "original_options_economic_train_certified",
                 "independent_original_trade_replay_verified",
                 "historical_native_fee_certified",
                 "original_historical_economic_train_executed",
                 "freeze_authorized", "promotion_authorized",
                 "validation_opened", "holdout_opened", "orders_enabled",
                 "paper_publication_authorized")
        if (source.get("status") != "PROVISIONAL_UNCERTIFIED_NATIVE_EVENT_EQUITY"
                or any(source.get(k) is not False for k in flags)):
            raise AssertionError("FORGED_PROVISIONAL_SOURCE")
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
    # Independent chronology: daily end-of-day samples cannot resolve the
    # four original intraday fold edges. Never certify exact 5-fold gates.
    daily_clocks = {
        int(datetime((start + timedelta(days=i)).year,
                     (start + timedelta(days=i)).month,
                     (start + timedelta(days=i)).day, 23, 59, 59,
                     tzinfo=timezone.utc).timestamp() * 1000)
        for i in range(n)
    }
    if any(t in daily_clocks for t in folds[1:-1]):
        raise AssertionError("UNEXPECTED_DAILY_BOUNDARY_ALIGNMENT")
    source_edges = source.get("fold_edge_snapshots", {s: [] for s in scenarios})
    if not isinstance(source_edges, dict) or set(source_edges) != set(scenarios):
        raise AssertionError("INDEPENDENT_INCOMPLETE_FOLD_SCENARIOS")
    found = {}
    for scenario in scenarios:
        snapshots = source_edges[scenario]
        if not isinstance(snapshots, list):
            raise AssertionError("INDEPENDENT_INVALID_FOLD_SNAPSHOTS")
        stamps = [e.get("ts_ms") for e in snapshots if isinstance(e, dict)]
        if (len(stamps) != len(snapshots) or len(set(stamps)) != len(stamps)
                or any(t not in folds[1:-1] for t in stamps)):
            raise AssertionError("INDEPENDENT_FORGED_FOLD_SNAPSHOT_CLOCK")
        found[scenario] = set(stamps)
    if found["severe"] != found["supersevere"]:
        raise AssertionError("INDEPENDENT_FOLD_EDGE_PATH_MISMATCH")
    missing = [t for t in folds[1:-1] if t not in found["severe"]]
    complete = not missing
    if (source.get("exact_fold_edge_nav_available", complete) is not complete
            or report.get("fold_attribution") != (
                "EXACT_NATIVE_EVENT_EDGE_PROVISIONAL_NOT_CERTIFIED"
                if complete else "DAILY_PROXY_NOT_EXACT")
            or report.get("missing_intraday_fold_boundary_utc") != [
                datetime.fromtimestamp(t/1000, timezone.utc).isoformat() for t in missing]
            or report.get("exact_chronological_fold_gate_evaluable") is not complete
            or report.get("exact_chronological_fold_gate_pass") is not False
            or report.get("formal_train_freeze_blocked_by_missing_intraday_nav") is not (not complete)
            or report.get("formal_numeric_train_pass_both_scenarios") is not False):
        raise AssertionError("INDEPENDENT_EXACT_FOLD_BOUNDARY_UNRESOLVED")
    exact_passes = []
    if complete:
        benchmarks = [[dec(x["benchmark_usd"]) for x in source_edges[s]]
                      for s in scenarios]
        if benchmarks[0] != benchmarks[1]:
            raise AssertionError("INDEPENDENT_EXACT_FOLD_BENCHMARK_MISMATCH")
        for scenario in scenarios:
            expected = independent_exact_folds(source["scenarios"][scenario],
                                               source_edges[scenario], initial, folds)
            got = report["scenarios"][scenario]
            count = sum(Decimal(x)>0 for x in expected)
            passed = count >= (4 if scenario == "severe" else 3)
            if (got.get("exact_fold_roi_descriptive_only") != expected
                    or got.get("exact_positive_folds") != count
                    or got.get("exact_fold_screen_pass") is not passed):
                raise AssertionError("INDEPENDENT_EXACT_FOLD_RECOMPOSITION_MISMATCH")
            exact_passes.append(passed)
    if report.get("exact_fold_screen_pass_both_scenarios") is not (
            complete and all(exact_passes)):
        raise AssertionError("INDEPENDENT_EXACT_FOLD_SCREEN_FORGERY")
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
    return {"status": ("INDEPENDENT_PROVISIONAL_NUMERIC_REPLAY_MATCH_NOT_CERTIFIED"
                       if provisional else "INDEPENDENT_FIXTURE_NUMERIC_REPLAY_MATCH"),
            "days_per_scenario": n, "scenario_path_divergence_days": divergent,
            "original_options_economic_train_certified": False,
            "promotion_authorized": False}
