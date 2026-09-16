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
import run_v99_r106_phase17_blv_leadership_alpha as p17

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase24_orthogonal_flow_alpha_audit.json"
ALPHA_GROSS = 0.20
TOP_N = 2
REBALANCE_HOURS = 24
VOL_LOOKBACK = 168
MIN_TRAIN_ACTIVE_HOURS = 24 * 30
MIN_FOLD_ACTIVE_HOURS = 24 * 5
MIN_HOLDOUT_ACTIVE_HOURS = 24 * 10
EPS = 1e-12


def rebalance_and_hold(targets: pd.DataFrame) -> pd.DataFrame:
    event = pd.Series(np.arange(len(targets)) % REBALANCE_HOURS == 0, index=targets.index)
    return targets.where(event, np.nan).ffill().fillna(0.0)


def market_neutral_inverse_vol(score: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
    sigma = close.pct_change(fill_method=None).rolling(VOL_LOOKBACK, min_periods=96).std().replace(0.0, np.nan)
    long_rank = score.rank(axis=1, ascending=False, method="first")
    short_rank = score.rank(axis=1, ascending=True, method="first")
    longs = score.notna() & long_rank.le(TOP_N)
    shorts = score.notna() & short_rank.le(TOP_N)

    long_raw = longs.astype(float).div(sigma)
    short_raw = shorts.astype(float).div(sigma)
    long_w = long_raw.div(long_raw.sum(axis=1).replace(0.0, np.nan), axis=0).fillna(0.0) * (ALPHA_GROSS / 2.0)
    short_w = short_raw.div(short_raw.sum(axis=1).replace(0.0, np.nan), axis=0).fillna(0.0) * (ALPHA_GROSS / 2.0)
    out = long_w - short_w
    return rebalance_and_hold(out).fillna(0.0)


def safe_ratio(short: pd.DataFrame, long: pd.DataFrame) -> pd.DataFrame:
    return short.div(long.replace(0.0, np.nan)).clip(lower=0.25, upper=4.0)


def fixed_orthogonal_sleeves(data) -> dict[str, pd.DataFrame]:
    """Predeclared non-price/flow alpha families. No numeric search or holdout fitting."""
    close = data.close.astype(float)
    quote = data.frames["quote_volume"].astype(float)
    trades = data.frames["trades"].astype(float)
    funding = data.funding.astype(float)

    # Every feature is known at t-1. The target chosen at close t is therefore causal.
    ret72 = close.pct_change(72, fill_method=None).shift(1)
    funding24 = funding.rolling(24, min_periods=8).sum().shift(1)

    q24 = quote.rolling(24, min_periods=12).mean().shift(1)
    q168 = quote.rolling(168, min_periods=96).mean().shift(1)
    volume_ratio = safe_ratio(q24, q168)

    t24 = trades.rolling(24, min_periods=12).mean().shift(1)
    t168 = trades.rolling(168, min_periods=96).mean().shift(1)
    trade_ratio = safe_ratio(t24, t168)

    avg_size = quote.div(trades.replace(0.0, np.nan))
    s24 = avg_size.rolling(24, min_periods=12).mean().shift(1)
    s168 = avg_size.rolling(168, min_periods=96).mean().shift(1)
    size_ratio = safe_ratio(s24, s168)

    scores = {
        # Economic mechanism: long contracts paying/receiving the more favorable carry,
        # short contracts with the least favorable carry.
        "funding_carry_24h": -funding24,
        # Price direction is only the directional anchor; volume/trade information
        # controls conviction. These families were not used by phases 14-23.
        "volume_confirmed_momentum_72h": ret72 * volume_ratio,
        "trade_activity_confirmed_momentum_72h": ret72 * trade_ratio,
        "trade_size_confirmed_momentum_72h": ret72 * size_ratio,
    }

    return {name: p1.cap(market_neutral_inverse_vol(score, close), ALPHA_GROSS) for name, score in scores.items()}


def sleeve_diag(result, index: pd.DatetimeIndex, train_start: pd.Timestamp, train_end: pd.Timestamp) -> dict:
    train = p17.sleeve_row(result, train_start, train_end)
    folds = []
    valid = good = 0
    for i, (lo, hi) in enumerate(p4.fold_bounds(index, train_start, train_end), 1):
        row = p17.sleeve_row(result, lo, hi)
        eligible = int(row["active_hours"]) >= MIN_FOLD_ACTIVE_HOURS
        healthy = False
        if eligible:
            valid += 1
            healthy = bool(
                float(row["roi"]) > 0.0
                and float(row["profit_factor"]) > 1.0
                and float(row["robust_mean_without_top1pct"]) > 0.0
            )
            good += int(healthy)
        folds.append({"fold": i, "start": lo.isoformat(), "end": hi.isoformat(), "eligible": eligible, "healthy": healthy, **row})

    stable = bool(
        int(train["active_hours"]) >= MIN_TRAIN_ACTIVE_HOURS
        and float(train["roi"]) > 0.0
        and float(train["profit_factor"]) > 1.08
        and float(train["robust_mean_without_top1pct"]) > 0.0
        and valid >= 3
        and good >= 3
    )
    quality = (
        np.log(max(1.0 + float(train["roi"]), 1e-12))
        * max(float(train["profit_factor"]), 0.25)
        / max(float(train["max_drawdown_abs"]), 0.05)
        if stable else -1e9
    )
    return {"stable_train": stable, "quality_score": float(quality), "train": train, "valid_folds": valid, "healthy_folds": good, "folds": folds}


def main() -> None:
    cfg, data, raw, ex, guard, gross, quarantined, metadata = p1.r98.r36.v15_setup()
    severe_cost = float(ex["severe_cost_per_side"])

    benchmarks = p1.r98.r86.r55.benchmark_items(cfg, data, raw, ex, guard, gross)
    common_start = max([data.close.index[0]] + [x["data"].close.index[0] for x in benchmarks.values()])
    common_end = min([data.close.index[-1]] + [x["data"].close.index[-1] for x in benchmarks.values()])
    train_end = min(p1.TRAIN_END, common_end)
    hold_idx = data.close.index[(data.close.index > p1.TRAIN_END) & (data.close.index <= common_end)]
    hold_start = hold_idx[0] if len(hold_idx) else common_end

    sleeves = fixed_orthogonal_sleeves(data)
    results = {name: p1.run_targets(data, target, ex, guard, severe_cost, ALPHA_GROSS) for name, target in sleeves.items()}
    diagnostics = {name: sleeve_diag(result, data.close.index, common_start, train_end) for name, result in results.items()}

    eligible = [name for name, row in diagnostics.items() if row["stable_train"]]
    selected = max(eligible, key=lambda n: diagnostics[n]["quality_score"]) if eligible else None

    holdout = {}
    holdout_pass = False
    if selected:
        holdout = p17.sleeve_row(results[selected], hold_start, common_end)
        holdout_pass = bool(
            int(holdout["active_hours"]) >= MIN_HOLDOUT_ACTIVE_HOURS
            and float(holdout["roi"]) > 0.0
            and float(holdout["profit_factor"]) > 1.05
            and float(holdout["robust_mean_without_top1pct"]) > 0.0
        )

    out = {
        "study": "V99 R106 phase 24 — orthogonal funding/flow alpha audit",
        "status": "DIAGNOSTIC_ONLY_NO_STRATEGY_CHANGE",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "precommitment": {
            "objective": "end the recent price-regime microfilter campaign and test genuinely orthogonal data already present in the canonical feed: funding, quote volume and trade count",
            "families": list(sleeves.keys()),
            "alpha_gross": ALPHA_GROSS,
            "top_n_each_side": TOP_N,
            "rebalance_hours": REBALANCE_HOURS,
            "market_neutral": True,
            "inverse_vol_weighted": True,
            "all_features_causal_t_minus_1": True,
            "selection_uses_train_only": True,
            "holdout_cannot_change_selected_family": True,
            "no_parameter_grid": True,
            "cost_for_selection": "severe",
            "strategy_change_in_phase24": False,
            "next_candidate_allowed_only_if": "one train-selected sleeve is stable in >=3 eligible folds and independently passes untouched holdout",
        },
        "data": {
            "available_orthogonal_fields": ["funding", "quote_volume", "trades"],
            "unavailable_in_current_canonical_model": ["open_interest", "liquidations", "basis"],
            "common_start": common_start.isoformat(),
            "common_end": common_end.isoformat(),
            "train_end": train_end.isoformat(),
            "holdout_start": hold_start.isoformat(),
            "severe_cost_per_side": severe_cost,
        },
        "sleeves": diagnostics,
        "selected_train_only": selected,
        "selected_holdout_descriptive": holdout,
        "selected_holdout_pass": holdout_pass,
        "actionable_for_phase25": bool(selected and holdout_pass),
        "next_phase_policy": "If actionable, Phase25 may add only the exact frozen selected sleeve to F7/F9 and must face full train/holdout/global/severe/supersevere/fold/regime Pareto gates. If not actionable, do not tune these four sleeves; move to another alpha source.",
        "quarantined_symbols": quarantined,
        "metadata": metadata,
        "disclosure": "Historical research only. No real orders. Phase24 cannot promote or alter F7/F9, V99 Frozen, V16 Frozen or paper state.",
    }
    REPORT.write_text(json.dumps(out, indent=2, default=audit.safe_float) + "\n", encoding="utf-8")
    print(json.dumps({
        "selected_train_only": selected,
        "selected_holdout": holdout,
        "selected_holdout_pass": holdout_pass,
        "actionable_for_phase25": out["actionable_for_phase25"],
        "train_summary": {name: {"stable_train": row["stable_train"], "quality_score": row["quality_score"], "train": row["train"], "healthy_folds": row["healthy_folds"], "valid_folds": row["valid_folds"]} for name, row in diagnostics.items()},
    }, indent=2, default=audit.safe_float), flush=True)


if __name__ == "__main__":
    main()
