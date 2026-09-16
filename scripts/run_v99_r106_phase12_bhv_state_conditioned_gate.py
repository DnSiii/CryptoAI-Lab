from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r105_all_regime_structural_audit_fast2  # noqa: F401
import run_v99_r105_all_regime_structural_audit as audit
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase4_bear_subregimes as p4
import run_v99_r106_phase7_train_validated_bhv_short_veto as p7

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase12_bhv_state_conditioned_gate.json"
TRAIN_FOLDS = 4
MIN_STATE_HOURS = 24 * 10
MIN_FOLD_HOURS = 24 * 3
MIN_NEGATIVE_FOLD_FRACTION = 2.0 / 3.0


def compact(a: dict) -> dict:
    m = a["global"]
    return {
        "roi_pct": 100.0 * float(m["roi"]),
        "max_dd_pct": -100.0 * float(m["max_drawdown_abs"]),
        "worst_day_pct": -100.0 * float(m["worst_day_abs"]),
        "win_rate_pct": 100.0 * float(m["trade_win_rate"]),
        "winning_trades": int(m["winning_trades"]),
        "profit_factor": float(m["profit_factor"]),
        "positive_days_pct": 100.0 * float(m["positive_day_ratio"]),
        "avg_win_pct": 100.0 * float(m["avg_winning_trade"]),
        "avg_loss_pct": 100.0 * float(m["avg_losing_trade"]),
        "payoff": float(m["payoff_ratio"]),
        "max_losing_streak": int(m["max_consecutive_losing_trades"]),
    }


def fold_bounds(index: pd.DatetimeIndex, start: pd.Timestamp, end: pd.Timestamp):
    idx = index[(index >= start) & (index <= end)]
    cuts = np.linspace(0, len(idx), TRAIN_FOLDS + 1, dtype=int)
    out = []
    for i in range(TRAIN_FOLDS):
        lo, hi = int(cuts[i]), int(cuts[i + 1] - 1)
        if hi > lo:
            out.append((idx[lo], idx[hi]))
    return out


def build_f7_core(data, raw, ex, guard, gross, cost: float, enable_short_veto: bool):
    r98_targets, r98_result, r98_diag = p1.build_r98_targets(data, raw, ex, guard, gross, cost)
    mask = p7.bhv_mask(data.close.index, *audit.classify_regimes(data.close)[:2])
    targets = p7.short_veto_targets(r98_targets, mask) if enable_short_veto else r98_targets.copy()
    result = p1.run_targets(data, targets, ex, guard, cost, p1.GROSS_CAP)
    return targets, result, r98_result, r98_diag, mask


def choose_short_veto(data, raw, ex, guard, gross, direction, vol, base_cost: float):
    r98_targets, _, _ = p1.build_r98_targets(data, raw, ex, guard, gross, base_cost)
    mask = p7.bhv_mask(data.close.index, direction, vol)
    long_res = p1.run_targets(
        data,
        p7.isolated_side_targets(r98_targets, mask, "long"),
        ex,
        guard,
        base_cost,
        p1.GROSS_CAP,
    )
    short_res = p1.run_targets(
        data,
        p7.isolated_side_targets(r98_targets, mask, "short"),
        ex,
        guard,
        base_cost,
        p1.GROSS_CAP,
    )
    train_start = data.close.index[0]
    train_end = min(p1.TRAIN_END, data.close.index[-1])
    long_train = audit.analyze_result(long_res, data, direction, vol, train_start, train_end)["regimes"]["matrix"]["BEAR__HIGH_VOLATILITY"]
    short_train = audit.analyze_result(short_res, data, direction, vol, train_start, train_end)["regimes"]["matrix"]["BEAR__HIGH_VOLATILITY"]
    enable = bool(
        float(long_train.get("roi", 0.0)) > 0.0
        and float(long_train.get("profit_factor", 0.0)) > 1.0
        and float(short_train.get("roi", 0.0)) < 0.0
        and float(short_train.get("profit_factor", 0.0)) < 1.0
    )
    return enable, {"long_train": long_train, "short_train": short_train}


def state_diagnostics(equity: pd.Series, substates: dict[str, pd.Series], index: pd.DatetimeIndex, train_start: pd.Timestamp, train_end: pd.Timestamp):
    folds = fold_bounds(index, train_start, train_end)
    diag: dict[str, dict] = {}
    veto_states: list[str] = []
    for state, mask in substates.items():
        agg = p4.segment_metrics(equity, mask, train_start, train_end)
        fold_rows = []
        eligible = []
        for i, (lo, hi) in enumerate(folds, 1):
            m = p4.segment_metrics(equity, mask, lo, hi)
            row = {"fold": i, "start": lo.isoformat(), "end": hi.isoformat(), **m}
            fold_rows.append(row)
            if int(m["active_hours"]) >= MIN_FOLD_HOURS:
                eligible.append(m)
        negative = sum(int(float(m["roi"]) < 0.0 and float(m["profit_factor"]) < 1.0) for m in eligible)
        frac = float(negative / len(eligible)) if eligible else 0.0
        veto = bool(
            int(agg["active_hours"]) >= MIN_STATE_HOURS
            and float(agg["roi"]) < 0.0
            and float(agg["profit_factor"]) < 1.0
            and len(eligible) >= 2
            and frac >= MIN_NEGATIVE_FOLD_FRACTION
        )
        if veto:
            veto_states.append(state)
        diag[state] = {
            "train": agg,
            "folds": fold_rows,
            "eligible_folds": len(eligible),
            "negative_pf_folds": int(negative),
            "negative_fold_fraction": frac,
            "veto": veto,
        }
    return veto_states, diag


def apply_state_veto(targets: pd.DataFrame, substates: dict[str, pd.Series], veto_states: list[str]) -> pd.DataFrame:
    out = targets.copy()
    for state in veto_states:
        mask = substates[state].reindex(out.index).fillna(False)
        out.loc[mask, :] = 0.0
    return out


def delta(candidate: dict, base: dict) -> dict:
    c, b = candidate["global"], base["global"]
    return {
        "wealth_ratio": float((1.0 + c["roi"]) / max(1e-12, 1.0 + b["roi"])),
        "roi_delta": float(c["roi"] - b["roi"]),
        "dd_delta": float(c["max_drawdown_abs"] - b["max_drawdown_abs"]),
        "worst_day_delta": float(c["worst_day_abs"] - b["worst_day_abs"]),
        "pf_delta": float(c["profit_factor"] - b["profit_factor"]),
        "win_rate_delta": float(c["trade_win_rate"] - b["trade_win_rate"]),
        "positive_days_delta": float(c["positive_day_ratio"] - b["positive_day_ratio"]),
        "payoff_delta": float(c["payoff_ratio"] - b["payoff_ratio"]),
    }


def strict_pareto(d: dict) -> bool:
    return bool(
        d["wealth_ratio"] > 1.0
        and d["dd_delta"] <= 1e-12
        and d["worst_day_delta"] <= 1e-12
        and d["pf_delta"] >= -1e-12
    )


def main() -> None:
    cfg, data, raw, ex, guard, gross, quarantined, metadata = p1.r98.r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])
    super_cost = severe_cost * 1.5
    direction, vol, _ = audit.classify_regimes(data.close)
    substates = p4.bear_high_vol_substates(data.close, direction, vol)

    train_start = data.close.index[0]
    train_end = min(p1.TRAIN_END, data.close.index[-1])
    enable_short_veto, short_diag = choose_short_veto(data, raw, ex, guard, gross, direction, vol, base_cost)

    f7_targets, f7_base, r98_base, r98_diag, _ = build_f7_core(data, raw, ex, guard, gross, base_cost, enable_short_veto)
    veto_states, state_diag = state_diagnostics(f7_base.equity, substates, data.close.index, train_start, train_end)
    candidate_targets = apply_state_veto(f7_targets, substates, veto_states)
    candidate_base = p1.run_targets(data, candidate_targets, ex, guard, base_cost, p1.GROSS_CAP)

    benchmarks = p1.r98.r86.r55.benchmark_items(cfg, data, raw, ex, guard, gross)
    common_start = max([data.close.index[0]] + [x["data"].close.index[0] for x in benchmarks.values()])
    common_end = min([data.close.index[-1]] + [x["data"].close.index[-1] for x in benchmarks.values()])
    hold_idx = data.close.index[(data.close.index > p1.TRAIN_END) & (data.close.index <= common_end)]
    hold_start = hold_idx[0] if len(hold_idx) else common_end

    def analyze_pair(base_res, cand_res):
        return {
            "f7": audit.analyze_result(base_res, data, direction, vol, common_start, common_end),
            "candidate": audit.analyze_result(cand_res, data, direction, vol, common_start, common_end),
            "f7_holdout": audit.analyze_result(base_res, data, direction, vol, hold_start, common_end),
            "candidate_holdout": audit.analyze_result(cand_res, data, direction, vol, hold_start, common_end),
        }

    base = analyze_pair(f7_base, candidate_base)

    # Freeze both train decisions (BHV short veto + state veto) and only change costs.
    f7_sev_targets, f7_sev, _, _, _ = build_f7_core(data, raw, ex, guard, gross, severe_cost, enable_short_veto)
    cand_sev_targets = apply_state_veto(f7_sev_targets, substates, veto_states)
    cand_sev = p1.run_targets(data, cand_sev_targets, ex, guard, severe_cost, p1.GROSS_CAP)
    severe = analyze_pair(f7_sev, cand_sev)

    f7_super_targets, f7_super, _, _, _ = build_f7_core(data, raw, ex, guard, gross, super_cost, enable_short_veto)
    cand_super_targets = apply_state_veto(f7_super_targets, substates, veto_states)
    cand_super = p1.run_targets(data, cand_super_targets, ex, guard, super_cost, p1.GROSS_CAP)
    super_severe = analyze_pair(f7_super, cand_super)

    train_f7 = audit.analyze_result(f7_base, data, direction, vol, common_start, train_end)
    train_cand = audit.analyze_result(candidate_base, data, direction, vol, common_start, train_end)
    train_delta = delta(train_cand, train_f7)

    fold_rows = []
    for i, (lo, hi) in enumerate(fold_bounds(data.close.index, common_start, train_end), 1):
        fb = audit.analyze_result(f7_base, data, direction, vol, lo, hi)
        cb = audit.analyze_result(candidate_base, data, direction, vol, lo, hi)
        d = delta(cb, fb)
        fold_rows.append({"fold": i, "start": lo.isoformat(), "end": hi.isoformat(), "delta": d, "strict_pareto": strict_pareto(d)})
    pareto_folds = sum(int(x["strict_pareto"]) for x in fold_rows)

    hold_delta = delta(base["candidate_holdout"], base["f7_holdout"])
    severe_delta = delta(severe["candidate"], severe["f7"])
    severe_hold_delta = delta(severe["candidate_holdout"], severe["f7_holdout"])
    super_delta = delta(super_severe["candidate"], super_severe["f7"])
    super_hold_delta = delta(super_severe["candidate_holdout"], super_severe["f7_holdout"])

    accepted = bool(veto_states and strict_pareto(train_delta) and pareto_folds >= 3)

    out = {
        "study": "V99 R106 phase 12 — BHV state-conditioned exposure gate on F7 core",
        "status": "RESEARCH_ONLY_NOT_PROMOTED",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "precommitment": {
            "holdout_used_for_selection": False,
            "no_grid_search": True,
            "short_veto_source": "phase 7 train-only BHV side attribution",
            "state_classifier_source": "phase 4 causal t-1 CRASH_CONTINUATION / BEAR_SQUEEZE / MIXED",
            "state_veto_rule": "veto only if train state ROI<0, PF<1, >=240 active hours, >=2 eligible folds and >=2/3 eligible folds have ROI<0 and PF<1",
            "global_acceptance_rule": "train wealth improves with PF/DD/worst-day non-inferior and >=3/4 chronological train folds pass same strict Pareto test",
        },
        "data": {
            "common_start": common_start.isoformat(),
            "common_end": common_end.isoformat(),
            "train_end": train_end.isoformat(),
            "holdout_start": hold_start.isoformat(),
        },
        "phase7_short_veto_enabled": enable_short_veto,
        "phase7_side_train": short_diag,
        "selected_veto_states": veto_states,
        "state_train_diagnostics": state_diag,
        "base": base,
        "severe": severe,
        "super_severe": super_severe,
        "train_delta": train_delta,
        "holdout_delta": hold_delta,
        "severe_delta": severe_delta,
        "severe_holdout_delta": severe_hold_delta,
        "super_severe_delta": super_delta,
        "super_severe_holdout_delta": super_hold_delta,
        "train_folds": fold_rows,
        "pareto_train_folds": pareto_folds,
        "research_gate": {"accepted": accepted, "reason": "train-only strict Pareto + folds; holdout reported after freeze"},
        "quarantined_symbols": quarantined,
        "metadata": metadata,
        "r98_diagnostics": r98_diag,
        "disclosure": "Historical research and chronological holdout only. No real orders. No profit guarantees.",
    }
    REPORT.write_text(json.dumps(out, indent=2, default=audit.safe_float) + "\n")

    print(json.dumps({
        "selected_veto_states": veto_states,
        "research_gate": out["research_gate"],
        "train_delta": train_delta,
        "pareto_train_folds": pareto_folds,
        "base": {
            "f7": compact(base["f7"]),
            "candidate": compact(base["candidate"]),
            "f7_holdout": compact(base["f7_holdout"]),
            "candidate_holdout": compact(base["candidate_holdout"]),
        },
        "severe": {"f7": compact(severe["f7"]), "candidate": compact(severe["candidate"]), "delta": severe_delta},
        "super_severe": {"f7": compact(super_severe["f7"]), "candidate": compact(super_severe["candidate"]), "delta": super_delta},
        "holdout_delta": hold_delta,
        "state_train_diagnostics": state_diag,
    }, indent=2, default=audit.safe_float), flush=True)


if __name__ == "__main__":
    main()
