from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data, point_in_time_liquid_view, validate_data
import v98_independent_phase003_dispersion_neutral as p3

CONFIG_PATH = PROJECT / "config" / "v98_independent.json"
STATE_PATH = PROJECT / "state" / "v98_independent_state.json"
REPORT_PATH = PROJECT / "reports" / "v98_independent_phase005_dual_sleeve.json"
POSITIONS_PATH = PROJECT / "reports" / "v98_independent_phase005_dual_sleeve_positions.csv"

# Phase004 passed training but failed its one-shot holdout. We do not tune that
# architecture against holdout. Phase005 is a new, predeclared training hypothesis:
# diversify residual momentum with an independent residual trend sleeve.
PHASE = {
    "id": "phase_005_dual_sleeve",
    "liquidity_top_n": 10,
    "liquidity_lookback_hours": 720,
    "minimum_history_hours": 2160,
    "beta_lookback_hours": 1440,
    "trend_fast_hours": 168,
    "trend_slow_hours": 720,
    "volatility_lookback_hours": 720,
    "rebalance_hours": 48,
    "sleeve_gross": 0.50,
    "long_count": 3,
    "short_count": 3,
    "gross_cap": 1.0,
}


def _rank01(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.rank(axis=1, pct=True, method="average")


def residual_components(data, membership: pd.DataFrame):
    c = PHASE
    close = data.close
    lagged = close.shift(1)
    eligible = membership & close.notna()
    if "BTCUSDT" in eligible.columns:
        eligible["BTCUSDT"] = False
    hourly = lagged.pct_change(fill_method=None)
    btc = hourly["BTCUSDT"]
    var = btc.rolling(c["beta_lookback_hours"], min_periods=720).var()
    beta = hourly.rolling(c["beta_lookback_hours"], min_periods=720).cov(btc).div(var, axis=0)
    residual = hourly.sub(beta.mul(btc, axis=0))
    return hourly, beta, residual, eligible


def _neutral_event_weights(score, inv_vol, beta, eligible, ts) -> pd.Series:
    c = PHASE
    s = score.loc[ts].where(eligible.loc[ts])
    lr = s.rank(ascending=False, method="first")
    sr = s.rank(ascending=True, method="first")
    selected = ((lr <= c["long_count"]) | (sr <= c["short_count"])) & s.notna()
    names = selected.index[selected]
    if len(names) < 4:
        return pd.Series(dtype=float)
    iv = inv_vol.loc[ts, names]
    b = beta.loc[ts, names]
    ok = iv.notna() & b.notna() & np.isfinite(iv) & np.isfinite(b)
    names = names[ok]
    if len(names) < 4:
        return pd.Series(dtype=float)
    raw = pd.Series(0.0, index=names, dtype=float)
    longs = names[lr.loc[names] <= c["long_count"]]
    shorts = names[sr.loc[names] <= c["short_count"]]
    if len(longs) == 0 or len(shorts) == 0:
        return pd.Series(dtype=float)
    raw.loc[longs] = iv.loc[longs]
    raw.loc[shorts] = -iv.loc[shorts]
    x = np.column_stack([np.ones(len(names)), b.loc[names].to_numpy(float)])
    y = raw.to_numpy(float)
    coef, *_ = np.linalg.lstsq(x, y, rcond=None)
    neutral = y - x @ coef
    gross = float(np.abs(neutral).sum())
    if not np.isfinite(gross) or gross <= 1e-12:
        return pd.Series(dtype=float)
    return pd.Series(neutral * (c["sleeve_gross"] / gross), index=names)


def build_targets(data, membership: pd.DataFrame) -> pd.DataFrame:
    """Two independent beta-neutral residual sleeves, all inputs t-1.

    Sleeve A: Phase003-style persistent residual momentum, but only half gross.
    Sleeve B: residual trend acceleration (7d minus 30d rate) at half gross.
    The combination is intended to diversify temporal failure modes rather than
    filter Phase004 using holdout information. No holdout-derived threshold exists.
    """
    hourly, beta, residual, eligible = residual_components(data, membership)
    vol = hourly.rolling(PHASE["volatility_lookback_hours"], min_periods=360).std()
    inv_vol = (1.0 / vol.replace(0.0, np.nan)).clip(upper=50.0).where(eligible)

    mom_fast = residual.rolling(336, min_periods=336).sum()
    mom_slow = residual.rolling(1440, min_periods=1440).sum()
    score_a = (0.45 * _rank01(mom_fast) + 0.55 * _rank01(mom_slow)).where(eligible)

    trend_fast = residual.rolling(PHASE["trend_fast_hours"], min_periods=PHASE["trend_fast_hours"]).sum()
    trend_slow = residual.rolling(PHASE["trend_slow_hours"], min_periods=PHASE["trend_slow_hours"]).sum()
    # Acceleration relative to the longer residual trend; economically distinct horizon.
    accel = trend_fast - trend_slow * (PHASE["trend_fast_hours"] / PHASE["trend_slow_hours"])
    score_b = _rank01(accel).where(eligible)

    targets = pd.DataFrame(0.0, index=data.close.index, columns=data.close.columns)
    events = np.arange(len(targets)) % PHASE["rebalance_hours"] == 0
    for ts in targets.index[events]:
        wa = _neutral_event_weights(score_a, inv_vol, beta, eligible, ts)
        wb = _neutral_event_weights(score_b, inv_vol, beta, eligible, ts)
        if len(wa):
            targets.loc[ts, wa.index] += wa
        if len(wb):
            targets.loc[ts, wb.index] += wb
    targets = targets.where(pd.Series(events, index=targets.index), np.nan).ffill().fillna(0.0)
    gross = targets.abs().sum(axis=1)
    scale = (PHASE["gross_cap"] / gross.replace(0.0, np.nan)).clip(upper=1.0).fillna(0.0)
    return targets.mul(scale, axis=0)


def evaluate(data, targets, cfg, scenario):
    stress = cfg["funding_stress"][scenario]
    return exact_fast(data, targets, cost_per_side=cfg["costs"][f"{scenario}_per_side"], gross_guard_cap=PHASE["gross_cap"], funding_debit_multiplier=stress["debit_multiplier"], funding_credit_multiplier=stress["credit_multiplier"])


def main():
    cfg = json.loads(CONFIG_PATH.read_text())
    state = json.loads(STATE_PATH.read_text())
    data = load_data(PROJECT, cfg["data_config"])
    validation = validate_data(data)
    if validation["errors"]:
        raise RuntimeError(f"data validation failed: {validation['errors'][:5]}")
    liquid, membership = point_in_time_liquid_view(data, top_n=PHASE["liquidity_top_n"], lookback_hours=PHASE["liquidity_lookback_hours"], minimum_history_hours=PHASE["minimum_history_hours"])
    targets = build_targets(liquid, membership)
    results = {x: evaluate(liquid, targets, cfg, x) for x in ("base", "severe", "supersevere")}
    start, end = cfg["research_start"], cfg["training_end"]
    train = p3.metrics(results["base"], start, end)
    folds = {f["name"]: p3.metrics(results["base"], f["start"], f["end"]) for f in cfg["folds"]}
    severe = p3.metrics(results["severe"], start, end)
    supersevere = p3.metrics(results["supersevere"], start, end)
    concentration = p3.concentration_metrics(results["base"], start, end)
    beta_neutrality = p3.beta_neutrality_metrics(results["base"], liquid, start, end)
    regimes = p3.regime_metrics(results["base"], liquid, start, end, end)
    passed, failures = p3.training_gate(train, folds, severe, supersevere, concentration)
    report = {"engine":"V98 Independent","phase":PHASE,"hypothesis":"Diversifying persistent residual momentum with an independent residual-trend-acceleration sleeve improves temporal robustness without holdout-conditioned filtering.","selection_policy":"single predeclared dual-sleeve architecture; training/folds/stress only; holdout opened once only after training gate","training":train,"folds":folds,"stress_training":{"severe":severe,"supersevere":supersevere},"concentration_training":concentration,"beta_neutrality_training":beta_neutrality,"regimes_training":regimes,"training_gate":{"passed":passed,"failures":failures},"holdout":None}
    if passed:
        h0,h1=cfg["holdout_start"],cfg["holdout_end"]
        hb=p3.metrics(results["base"],h0,h1); hs=p3.metrics(results["severe"],h0,h1); hss=p3.metrics(results["supersevere"],h0,h1)
        hp,hf=p3.holdout_gate(hb,hs,hss)
        report["holdout"]={"base":hb,"severe":hs,"supersevere":hss,"gate":{"passed":hp,"failures":hf}}
    REPORT_PATH.parent.mkdir(parents=True,exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report,indent=2,default=str)+"\n")
    results["base"].positions.to_csv(POSITIONS_PATH)
    final_pass = bool(passed and report["holdout"] and report["holdout"]["gate"]["passed"])
    state["phase"]="phase_005_complete"
    state["champion"] = PHASE["id"] if final_pass else state.get("champion")
    state["last_experiment"]={"id":PHASE["id"],"hypothesis":report["hypothesis"],"status":"validated_candidate" if final_pass else ("training_passed_holdout_rejected" if passed else "training_rejected"),"parameters":"single predeclared dual-sleeve architecture; no grid","report":str(REPORT_PATH.relative_to(PROJECT)),"training_summary":train,"folds":folds,"stress_training":report["stress_training"],"training_gate":report["training_gate"],"holdout_validation_recorded_but_not_for_selection":report["holdout"]}
    state["holdout_evaluated_for_validation"]=bool(passed)
    state["next_action"]="If phase005 fails, diagnose training mechanism without using holdout to tune; change architecture rather than thresholds. If validated, run frozen robustness gate before external benchmark."
    STATE_PATH.write_text(json.dumps(state,indent=2,default=str)+"\n")
    print(json.dumps({"phase":PHASE["id"],"training_gate":report["training_gate"],"training":train,"folds":folds,"stress":report["stress_training"],"holdout":report["holdout"]},indent=2,default=str))

if __name__ == "__main__":
    main()
