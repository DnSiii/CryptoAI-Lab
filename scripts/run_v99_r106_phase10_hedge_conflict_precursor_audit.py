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
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase4_bear_subregimes as p4
import run_v99_r105_all_regime_structural_audit as audit

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase10_hedge_conflict_precursor_audit.json"
EPS = 1e-12
FUTURE_HOURS = 3
TRAIN_FOLDS = 4


def forward_sum(series: pd.Series, hours: int) -> pd.Series:
    return sum((series.shift(-k) for k in range(1, hours + 1)), start=pd.Series(0.0, index=series.index))


def net_asset_pnl(result) -> pd.DataFrame:
    return result.asset_gross.fillna(0.0) - result.asset_fees.fillna(0.0) - result.asset_funding.fillna(0.0)


def candidate_rules(short_pnl: pd.Series, btc_r3: pd.Series, btc_r6: pd.Series) -> dict[str, pd.Series]:
    s3 = short_pnl.rolling(3, min_periods=3).sum() > 0.0
    s6 = short_pnl.rolling(6, min_periods=6).sum() > 0.0
    s12 = short_pnl.rolling(12, min_periods=12).sum() > 0.0
    return {
        "short3_positive": s3,
        "short6_positive": s6,
        "short12_positive": s12,
        "short3_positive_and_btc3_down": s3 & btc_r3.lt(0.0),
        "short6_positive_and_btc6_down": s6 & btc_r6.lt(0.0),
    }


def evaluate_rule(rule: pd.Series, eligible: pd.Series, harmful: pd.Series, btc_future: pd.Series, start: pd.Timestamp, end: pd.Timestamp) -> dict:
    window = (eligible.index >= start) & (eligible.index <= end)
    e = eligible & window
    r = rule.reindex(eligible.index).fillna(False) & e
    y = harmful.reindex(eligible.index).fillna(False)
    base_n = int(e.sum())
    selected_n = int(r.sum())
    base_rate = float(y.loc[e].mean()) if base_n else 0.0
    selected_rate = float(y.loc[r].mean()) if selected_n else 0.0
    lift = float(selected_rate / base_rate) if base_rate > EPS else 0.0
    btc_mean = float(btc_future.loc[r].mean()) if selected_n else 0.0
    btc_total = float(btc_future.loc[r].sum()) if selected_n else 0.0
    return {
        "eligible_hours": base_n,
        "selected_hours": selected_n,
        "coverage": float(selected_n / base_n) if base_n else 0.0,
        "base_harm_rate": base_rate,
        "selected_harm_rate": selected_rate,
        "lift": lift,
        "mean_future_btc_pnl": btc_mean,
        "total_future_btc_pnl": btc_total,
        "expected_hedge_removal_gain": float(-btc_mean),
    }


def folds(index: pd.DatetimeIndex, start: pd.Timestamp, end: pd.Timestamp):
    idx = index[(index >= start) & (index <= end)]
    cuts = np.linspace(0, len(idx), TRAIN_FOLDS + 1, dtype=int)
    out = []
    for i in range(TRAIN_FOLDS):
        lo = int(cuts[i]); hi = int(cuts[i+1] - 1)
        if hi > lo:
            out.append((idx[lo], idx[hi]))
    return out


def main():
    cfg, data, raw, ex, guard, gross, quarantined, metadata = p1.r98.r36.v15_setup()
    cost = float(ex["base_cost_per_side"])
    direction, vol, _ = audit.classify_regimes(data.close)
    crash = p4.bear_high_vol_substates(data.close, direction, vol)["CRASH_CONTINUATION"]
    _, result, _ = p1.build_r98_targets(data, raw, ex, guard, gross, cost)

    pos = result.open_positions.fillna(0.0)
    pnl = net_asset_pnl(result)
    ex_cols = [c for c in pos.columns if c != "BTCUSDT"]
    ex_net = pos[ex_cols].sum(axis=1)
    btc_pos = pos["BTCUSDT"]
    btc_pnl = pnl["BTCUSDT"]
    short_hour = pnl[ex_cols].where(pos[ex_cols] < -EPS, 0.0).sum(axis=1)

    btc_close = data.close["BTCUSDT"].reindex(pos.index)
    btc_r3 = btc_close.pct_change(3, fill_method=None)
    btc_r6 = btc_close.pct_change(6, fill_method=None)

    eligible = crash.reindex(pos.index).fillna(False) & ex_net.lt(-0.05) & btc_pos.gt(0.02)
    future_short = forward_sum(short_hour, FUTURE_HOURS)
    future_btc = forward_sum(btc_pnl, FUTURE_HOURS)
    future_valid = future_short.notna() & future_btc.notna()
    eligible = eligible & future_valid
    harmful = eligible & future_short.gt(0.0) & future_btc.lt(0.0)

    rules = candidate_rules(short_hour, btc_r3, btc_r6)

    benchmarks = p1.r98.r86.r55.benchmark_items(cfg, data, raw, ex, guard, gross)
    start = max([data.close.index[0]] + [x["data"].close.index[0] for x in benchmarks.values()])
    end = min([data.close.index[-1]] + [x["data"].close.index[-1] for x in benchmarks.values()])
    train_end = min(p1.TRAIN_END, end)
    hold_idx = pos.index[(pos.index > p1.TRAIN_END) & (pos.index <= end)]
    hold_start = hold_idx[0] if len(hold_idx) else end

    train_rows = {
        name: evaluate_rule(rule, eligible, harmful, future_btc, start, train_end)
        for name, rule in rules.items()
    }
    # Train-only selection. Require useful coverage; then rank expected removable BTC loss,
    # with lift as tie-breaker. Holdout is not consulted.
    eligible_train = [
        (name, row) for name, row in train_rows.items()
        if row["selected_hours"] >= 30 and row["coverage"] >= 0.05
    ]
    eligible_train.sort(
        key=lambda x: (x[1]["expected_hedge_removal_gain"], x[1]["lift"]), reverse=True
    )
    selected_name = eligible_train[0][0] if eligible_train else None

    hold_rows = {
        name: evaluate_rule(rule, eligible, harmful, future_btc, hold_start, end)
        for name, rule in rules.items()
    }
    fold_rows = {}
    for i, (lo, hi) in enumerate(folds(pos.index, start, train_end), 1):
        fold_rows[str(i)] = {
            name: evaluate_rule(rule, eligible, harmful, future_btc, lo, hi)
            for name, rule in rules.items()
        }

    selected_train = train_rows.get(selected_name, {}) if selected_name else {}
    selected_hold = hold_rows.get(selected_name, {}) if selected_name else {}
    selected_folds = [fold_rows[k].get(selected_name, {}) for k in sorted(fold_rows)] if selected_name else []
    fold_positive = sum(
        int(r.get("lift", 0.0) > 1.0 and r.get("expected_hedge_removal_gain", 0.0) > 0.0)
        for r in selected_folds
        if r.get("selected_hours", 0) > 0
    )
    fold_eligible = sum(int(r.get("selected_hours", 0) > 0) for r in selected_folds)
    pass_gate = bool(
        selected_name
        and selected_train.get("lift", 0.0) > 1.05
        and selected_train.get("expected_hedge_removal_gain", 0.0) > 0.0
        and selected_hold.get("lift", 0.0) > 1.0
        and selected_hold.get("expected_hedge_removal_gain", 0.0) > 0.0
        and fold_eligible >= 3
        and fold_positive >= 3
    )

    out = {
        "study": "V99 R106 phase 10 — causal hedge-conflict precursor audit",
        "status": "DIAGNOSTIC_ONLY_NO_STRATEGY_CHANGE",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "precommitment": {
            "future_label_hours": FUTURE_HOURS,
            "candidate_rules": list(rules),
            "no_numeric_threshold_grid": True,
            "selection_uses_train_only": True,
            "holdout_never_used_for_selection": True,
            "eligible_context": "crash continuation AND ex-BTC net short < -0.05 AND BTC long > 0.02",
            "harm_label": "next 3h non-BTC short PnL > 0 AND next 3h BTC PnL < 0",
        },
        "selected_rule": selected_name,
        "selected_passed": pass_gate,
        "train": train_rows,
        "holdout": hold_rows,
        "folds": fold_rows,
        "selected_summary": {
            "train": selected_train,
            "holdout": selected_hold,
            "positive_folds": fold_positive,
            "eligible_folds": fold_eligible,
        },
        "context": {
            "full_eligible_hours": int(eligible.loc[(eligible.index >= start) & (eligible.index <= end)].sum()),
            "full_harmful_hours": int(harmful.loc[(harmful.index >= start) & (harmful.index <= end)].sum()),
            "train_eligible_hours": int(eligible.loc[(eligible.index >= start) & (eligible.index <= train_end)].sum()),
            "holdout_eligible_hours": int(eligible.loc[(eligible.index >= hold_start) & (eligible.index <= end)].sum()),
        },
        "data": {"start": start.isoformat(), "end": end.isoformat(), "train_end": train_end.isoformat(), "holdout_start": hold_start.isoformat()},
        "disclosure": "Diagnostic causal precursor audit only. Future PnL is label-only and never used in live features. No strategy changes or real orders.",
        "quarantined_symbols": quarantined,
        "metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2, default=audit.safe_float) + "\n")
    print(json.dumps({
        "selected_rule": selected_name,
        "selected_passed": pass_gate,
        "selected_summary": out["selected_summary"],
        "context": out["context"],
        "all_train": train_rows,
        "all_holdout": hold_rows,
    }, indent=2, default=audit.safe_float), flush=True)


if __name__ == "__main__":
    main()
