from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

# Neutral shared infrastructure only. No legacy alpha/strategy module is imported.
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data, point_in_time_liquid_view, validate_data

CONFIG_PATH = PROJECT / "config" / "v98_independent.json"
STATE_PATH = PROJECT / "state" / "v98_independent_state.json"
REPORT_PATH = PROJECT / "reports" / "v98_independent_phase003_dispersion_neutral.json"
POSITIONS_PATH = PROJECT / "reports" / "v98_independent_phase003_dispersion_neutral_positions.csv"

# One predeclared economically-motivated architecture. No grid/search.
PHASE = {
    "id": "phase_003_dispersion_neutral",
    "liquidity_top_n": 10,
    "liquidity_lookback_hours": 720,
    "minimum_history_hours": 2160,
    "beta_lookback_hours": 1440,
    "residual_fast_hours": 336,
    "residual_slow_hours": 1440,
    "dispersion_reference_hours": 4320,
    "dispersion_reference_min_hours": 2160,
    "long_count": 4,
    "short_count": 4,
    "volatility_lookback_hours": 720,
    "rebalance_hours": 48,
    "gross_target": 1.0,
    "gross_cap": 1.0,
}


def _rank01(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.rank(axis=1, pct=True, method="average")


def _daily_returns(equity: pd.Series) -> pd.Series:
    daily = equity.resample("1D").last().dropna()
    return daily.pct_change(fill_method=None).dropna()


def build_targets(data, membership: pd.DataFrame) -> pd.DataFrame:
    """Causal market-neutral residual-dispersion architecture.

    Economic hypothesis:
    1) persistent cross-sectional residual momentum can survive when broad market beta is removed;
    2) the spread is only deployed when cross-sectional dispersion is above its own trailing median,
       because relative-value opportunity should be stronger when names separate;
    3) broader 4x4 baskets, 48h rebalancing and a 1.0 gross target reduce concentration/cost fragility;
    4) each rebalance portfolio is projected to both dollar-neutral and BTC-beta-neutral constraints.

    All price inputs are shifted by one hour before feature construction.
    """
    c = PHASE
    close = data.close
    lagged = close.shift(1)
    valid = membership & close.notna()
    eligible = valid.copy()
    if "BTCUSDT" in eligible.columns:
        eligible["BTCUSDT"] = False

    hourly = lagged.pct_change(fill_method=None)
    btc_ret = hourly["BTCUSDT"]
    beta_var = btc_ret.rolling(c["beta_lookback_hours"], min_periods=720).var()
    beta = hourly.rolling(c["beta_lookback_hours"], min_periods=720).cov(btc_ret).div(beta_var, axis=0)
    residual = hourly.sub(beta.mul(btc_ret, axis=0))

    fast = residual.rolling(c["residual_fast_hours"], min_periods=c["residual_fast_hours"]).sum()
    slow = residual.rolling(c["residual_slow_hours"], min_periods=c["residual_slow_hours"]).sum()
    score = (0.45 * _rank01(fast) + 0.55 * _rank01(slow)).where(eligible)

    # Causal opportunity gate: current residual dispersion vs trailing historical median.
    dispersion = fast.where(eligible).std(axis=1)
    dispersion_ref = dispersion.rolling(
        c["dispersion_reference_hours"], min_periods=c["dispersion_reference_min_hours"]
    ).median().shift(1)
    active = (dispersion > dispersion_ref) & dispersion_ref.notna()

    vol = hourly.rolling(c["volatility_lookback_hours"], min_periods=360).std()
    inv_vol = (1.0 / vol.replace(0.0, np.nan)).clip(upper=50.0).where(eligible)

    long_rank = score.rank(axis=1, ascending=False, method="first")
    short_rank = score.rank(axis=1, ascending=True, method="first")
    long_mask = (long_rank <= c["long_count"]) & eligible
    short_mask = (short_rank <= c["short_count"]) & eligible

    targets = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    event_positions = np.arange(len(targets)) % c["rebalance_hours"] == 0
    event_index = targets.index[event_positions]

    for ts in event_index:
        if not bool(active.get(ts, False)):
            continue
        selected = (long_mask.loc[ts] | short_mask.loc[ts])
        names = selected.index[selected.fillna(False)]
        if len(names) < 4:
            continue

        s = score.loc[ts, names]
        iv = inv_vol.loc[ts, names]
        b = beta.loc[ts, names]
        ok = s.notna() & iv.notna() & b.notna() & np.isfinite(s) & np.isfinite(iv) & np.isfinite(b)
        names = names[ok]
        if len(names) < 4:
            continue

        raw = pd.Series(0.0, index=names, dtype=float)
        lnames = names[long_mask.loc[ts, names].fillna(False)]
        snames = names[short_mask.loc[ts, names].fillna(False)]
        if len(lnames) == 0 or len(snames) == 0:
            continue
        raw.loc[lnames] = (0.25 + (s.loc[lnames] - 0.5).abs()) * iv.loc[lnames]
        raw.loc[snames] = -(0.25 + (s.loc[snames] - 0.5).abs()) * iv.loc[snames]

        # Project the selected-basket raw alpha onto the null space of
        # [constant, BTC beta], enforcing dollar neutrality and beta neutrality.
        x = np.column_stack([np.ones(len(names)), b.loc[names].to_numpy(dtype=float)])
        y = raw.loc[names].to_numpy(dtype=float)
        coef, *_ = np.linalg.lstsq(x, y, rcond=None)
        neutral = y - x @ coef
        gross = float(np.abs(neutral).sum())
        if not np.isfinite(gross) or gross <= 1e-12:
            continue
        neutral *= c["gross_target"] / gross
        targets.loc[ts, names] = neutral

    targets = targets.where(pd.Series(event_positions, index=targets.index), np.nan).ffill().fillna(0.0)
    gross = targets.abs().sum(axis=1)
    scale = (c["gross_cap"] / gross.replace(0.0, np.nan)).clip(upper=1.0).fillna(0.0)
    return targets.mul(scale, axis=0)


def metrics(result, start: str, end: str) -> dict:
    equity = result.equity.loc[start:end].dropna()
    positions = result.positions.loc[start:end]
    turnover = result.turnover.loc[start:end]
    if len(equity) < 2:
        return {"error": "insufficient_data"}
    total = float(equity.iloc[-1] / equity.iloc[0] - 1.0)
    years = (equity.index[-1] - equity.index[0]).total_seconds() / (365.25 * 86400)
    cagr = float((equity.iloc[-1] / equity.iloc[0]) ** (1.0 / years) - 1.0) if years > 0 and equity.iloc[0] > 0 else np.nan
    dd = equity.div(equity.cummax()).sub(1.0)
    daily = _daily_returns(equity)
    wins = daily[daily > 0]
    losses = daily[daily < 0]
    pf = float(wins.sum() / abs(losses.sum())) if abs(losses.sum()) > 0 else np.inf
    payoff = float(wins.mean() / abs(losses.mean())) if len(wins) and len(losses) and losses.mean() != 0 else np.nan
    q05 = float(daily.quantile(0.05)) if len(daily) else np.nan
    return {
        "total_return": total,
        "cagr": cagr,
        "max_drawdown": float(dd.min()),
        "worst_day": float(daily.min()) if len(daily) else np.nan,
        "best_day": float(daily.max()) if len(daily) else np.nan,
        "p01_day": float(daily.quantile(0.01)) if len(daily) else np.nan,
        "p05_day": q05,
        "cvar05_day": float(daily[daily <= q05].mean()) if len(daily) else np.nan,
        "profit_factor_daily": pf,
        "payoff_daily": payoff,
        "win_rate_daily": float((daily > 0).mean()) if len(daily) else np.nan,
        "positive_days": int((daily > 0).sum()),
        "negative_days": int((daily < 0).sum()),
        "days": int(len(daily)),
        "turnover_sum": float(turnover.sum()),
        "avg_gross": float(positions.abs().sum(axis=1).mean()),
        "max_gross": float(positions.abs().sum(axis=1).max()),
        "avg_net": float(positions.sum(axis=1).mean()),
        "max_abs_net": float(positions.sum(axis=1).abs().max()),
        "ruin": bool(result.ruin),
    }


def evaluate(data, targets, cfg: dict, scenario: str):
    stress = cfg["funding_stress"][scenario]
    return exact_fast(
        data,
        targets,
        cost_per_side=cfg["costs"][f"{scenario}_per_side"],
        gross_guard_cap=PHASE["gross_cap"],
        funding_debit_multiplier=stress["debit_multiplier"],
        funding_credit_multiplier=stress["credit_multiplier"],
    )


def concentration_metrics(result, start: str, end: str) -> dict:
    pos = result.positions.loc[start:end].abs()
    gross = pos.sum(axis=1).replace(0, np.nan)
    shares = pos.div(gross, axis=0)
    active = (pos > 1e-10).sum(axis=1)
    return {
        "mean_top1_weight_share": float(shares.max(axis=1).mean()),
        "p95_top1_weight_share": float(shares.max(axis=1).quantile(0.95)),
        "mean_active_assets": float(active.mean()),
    }


def beta_neutrality_metrics(result, data, start: str, end: str) -> dict:
    pos = result.positions.loc[start:end]
    lagged = data.close.shift(1)
    hourly = lagged.pct_change(fill_method=None)
    btc = hourly["BTCUSDT"]
    beta = hourly.rolling(PHASE["beta_lookback_hours"], min_periods=720).cov(btc).div(
        btc.rolling(PHASE["beta_lookback_hours"], min_periods=720).var(), axis=0
    )
    aligned = beta.reindex(pos.index).reindex(columns=pos.columns)
    port_beta = (pos * aligned).sum(axis=1)
    return {
        "mean_abs_portfolio_beta": float(port_beta.abs().mean()),
        "p95_abs_portfolio_beta": float(port_beta.abs().quantile(0.95)),
        "max_abs_portfolio_beta": float(port_beta.abs().max()),
    }


def regime_metrics(result, data, start: str, end: str, training_end: str) -> dict:
    btc = data.close["BTCUSDT"].shift(1)
    trend90 = btc.pct_change(24 * 90, fill_method=None)
    vol30 = btc.pct_change(fill_method=None).rolling(24 * 30, min_periods=24 * 15).std()
    vol_median = vol30.loc[:training_end].median()
    labels = pd.Series("sideways", index=btc.index, dtype=object)
    labels[trend90 > 0.15] = "bull"
    labels[trend90 < -0.15] = "bear"
    high = vol30 > vol_median * 1.5
    labels[high] = labels[high] + "_highvol"
    out = {}
    eq_ret = result.equity.pct_change(fill_method=None)
    for label in sorted(labels.dropna().unique()):
        mask = (labels == label) & (labels.index >= pd.Timestamp(start)) & (labels.index <= pd.Timestamp(end))
        r = eq_ret.reindex(labels.index[mask]).dropna()
        if len(r) < 48:
            continue
        out[label] = {
            "hours": int(len(r)),
            "return_sum_approx": float(r.sum()),
            "positive_hour_ratio": float((r > 0).mean()),
        }
    return out


def training_gate(train: dict, folds: dict, severe: dict, supersevere: dict, concentration: dict) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if train["profit_factor_daily"] < 1.15:
        failures.append("training_pf_below_1.15")
    if train["max_drawdown"] < -0.45:
        failures.append("training_drawdown_below_-45pct")
    if train["worst_day"] < -0.12:
        failures.append("training_worst_day_below_-12pct")
    for name, m in folds.items():
        if m["total_return"] <= 0:
            failures.append(f"fold_{name}_nonpositive_return")
        if m["profit_factor_daily"] < 1.05:
            failures.append(f"fold_{name}_pf_below_1.05")
    if severe["profit_factor_daily"] < 1.10:
        failures.append("severe_pf_below_1.10")
    if supersevere["profit_factor_daily"] < 1.03:
        failures.append("supersevere_pf_below_1.03")
    if supersevere["max_drawdown"] < -0.55:
        failures.append("supersevere_drawdown_below_-55pct")
    if concentration["p95_top1_weight_share"] > 0.45:
        failures.append("concentration_p95_top1_above_45pct")
    if train["ruin"] or severe["ruin"] or supersevere["ruin"]:
        failures.append("ruin_detected")
    return (len(failures) == 0), failures


def holdout_gate(base: dict, severe: dict, supersevere: dict) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if base["total_return"] <= 0:
        failures.append("holdout_nonpositive_return")
    if base["profit_factor_daily"] < 1.05:
        failures.append("holdout_pf_below_1.05")
    if base["max_drawdown"] < -0.40:
        failures.append("holdout_drawdown_below_-40pct")
    if severe["total_return"] <= 0:
        failures.append("holdout_severe_nonpositive_return")
    if supersevere["profit_factor_daily"] < 1.00 or supersevere["ruin"]:
        failures.append("holdout_supersevere_not_surviving")
    return (len(failures) == 0), failures


def main() -> None:
    cfg = json.loads(CONFIG_PATH.read_text())
    state = json.loads(STATE_PATH.read_text())
    data = load_data(PROJECT, cfg["data_config"])
    validation = validate_data(data)
    if validation["errors"]:
        raise RuntimeError(f"data validation failed: {validation['errors'][:5]}")

    liquid, membership = point_in_time_liquid_view(
        data,
        top_n=PHASE["liquidity_top_n"],
        lookback_hours=PHASE["liquidity_lookback_hours"],
        minimum_history_hours=PHASE["minimum_history_hours"],
    )
    targets = build_targets(liquid, membership)

    results = {name: evaluate(liquid, targets, cfg, name) for name in ("base", "severe", "supersevere")}
    train = metrics(results["base"], cfg["research_start"], cfg["training_end"])
    folds = {fold["name"]: metrics(results["base"], fold["start"], fold["end"]) for fold in cfg["folds"]}
    severe_train = metrics(results["severe"], cfg["research_start"], cfg["training_end"])
    super_train = metrics(results["supersevere"], cfg["research_start"], cfg["training_end"])
    concentration = concentration_metrics(results["base"], cfg["research_start"], cfg["training_end"])
    beta_neutrality = beta_neutrality_metrics(results["base"], liquid, cfg["research_start"], cfg["training_end"])
    train_pass, train_failures = training_gate(train, folds, severe_train, super_train, concentration)

    holdout = None
    holdout_stress = None
    holdout_pass = False
    holdout_failures: list[str] = []
    # Holdout is opened only after the architecture passes the fully predeclared training gate.
    if train_pass:
        holdout = metrics(results["base"], cfg["holdout_start"], cfg["holdout_end"])
        holdout_stress = {
            "severe": metrics(results["severe"], cfg["holdout_start"], cfg["holdout_end"]),
            "supersevere": metrics(results["supersevere"], cfg["holdout_start"], cfg["holdout_end"]),
        }
        holdout_pass, holdout_failures = holdout_gate(holdout, holdout_stress["severe"], holdout_stress["supersevere"])

    if not train_pass:
        status = "training_rejected"
    elif not holdout_pass:
        status = "holdout_rejected"
    else:
        status = "provisional_champion"

    report = {
        "engine": "V98 Independent",
        "version": PHASE["id"],
        "status": status,
        "selection_policy": {
            "parameter_search": "none; one predeclared architecture",
            "holdout_opened_only_after_training_gate": True,
            "holdout_used_for_selection": False,
            "v99_used_for_selection": False,
            "information_lag": "all market features use close shifted by one hour",
        },
        "architecture": PHASE,
        "data_validation": {"error_count": len(validation["errors"]), "symbols": list(data.symbols)},
        "training": train,
        "folds": folds,
        "stress_training": {"severe": severe_train, "supersevere": super_train},
        "concentration_training": concentration,
        "beta_neutrality_training": beta_neutrality,
        "regimes_training": regime_metrics(results["base"], liquid, cfg["research_start"], cfg["training_end"], cfg["training_end"]),
        "training_gate": {"passed": train_pass, "failures": train_failures},
        "holdout_validation": holdout,
        "holdout_stress_validation": holdout_stress,
        "holdout_gate": {"evaluated": train_pass, "passed": holdout_pass if train_pass else None, "failures": holdout_failures},
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, allow_nan=True) + "\n")
    targets.to_csv(POSITIONS_PATH, index_label="timestamp")

    state["phase"] = "phase_003_complete"
    state["last_experiment"] = {
        "id": PHASE["id"],
        "hypothesis": "Market-neutral residual momentum deployed only in elevated cross-sectional dispersion, using broader baskets and explicit dollar/BTC-beta neutralization, should reduce regime dependence, concentration and cost fragility diagnosed in baseline_zero_001.",
        "status": status,
        "parameters": "single predeclared architecture; no grid",
        "report": str(REPORT_PATH.relative_to(PROJECT)),
        "training_summary": train,
        "folds": folds,
        "stress_training": {"severe": severe_train, "supersevere": super_train},
        "training_gate": report["training_gate"],
        "holdout_validation_recorded_but_not_for_selection": holdout,
        "holdout_gate": report["holdout_gate"],
    }
    if status == "provisional_champion":
        state["champion"] = PHASE["id"]
        state["next_action"] = "run adversarial temporal/regime/stress validation of phase_003 without parameter changes before any V99 comparison"
    elif status == "holdout_rejected":
        state["champion"] = None
        state["next_action"] = "diagnose the train-to-holdout transfer failure without tuning to holdout; formulate a new training-only economic hypothesis"
    else:
        state["champion"] = None
        state["next_action"] = "diagnose phase_003 training/fold/stress failure mechanisms before proposing a different architecture"
    state["holdout_locked"] = True
    state["holdout_evaluated_for_validation"] = bool(train_pass)
    state["v99_benchmark_locked_until_final"] = True
    STATE_PATH.write_text(json.dumps(state, indent=2, allow_nan=True) + "\n")

    print(json.dumps(report, indent=2, allow_nan=True))


if __name__ == "__main__":
    main()
