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
import v98_independent_phase005_dual_sleeve as p5

CONFIG_PATH = PROJECT / "config" / "v98_independent.json"
STATE_PATH = PROJECT / "state" / "v98_independent_state.json"
REPORT_PATH = PROJECT / "reports" / "v98_independent_phase006_consensus_residual.json"
POSITIONS_PATH = PROJECT / "reports" / "v98_independent_phase006_consensus_residual_positions.csv"

PHASE = {
    "id": "phase_006_consensus_residual",
    "liquidity_top_n": 10,
    "liquidity_lookback_hours": 720,
    "minimum_history_hours": 2160,
    "beta_lookback_hours": 1440,
    "volatility_lookback_hours": 720,
    "medium_hours": 336,
    "long_hours": 1440,
    "rebalance_hours": 72,
    "long_count": 3,
    "short_count": 3,
    "gross_cap": 0.85,
}


def build_targets(data, membership: pd.DataFrame) -> pd.DataFrame:
    """Persistent residual-momentum consensus, using only information through t-1.

    Phase005 showed that a fast acceleration sleeve amplified tails and turnover.
    Phase006 changes architecture rather than nudging thresholds: positions require
    medium- and long-horizon residual momentum to agree directionally, while the
    cross-sectional score rewards agreement. A slower rebalance and lower gross are
    predeclared economic consequences of targeting persistent rather than transient
    relative trends; they are not holdout-selected.
    """
    hourly, beta, residual, eligible = p5.residual_components(data, membership)
    vol = hourly.rolling(PHASE["volatility_lookback_hours"], min_periods=360).std()
    inv_vol = (1.0 / vol.replace(0.0, np.nan)).clip(upper=50.0).where(eligible)
    med = residual.rolling(PHASE["medium_hours"], min_periods=PHASE["medium_hours"]).sum()
    long = residual.rolling(PHASE["long_hours"], min_periods=PHASE["long_hours"]).sum()
    rmed = med.rank(axis=1, pct=True, method="average")
    rlong = long.rank(axis=1, pct=True, method="average")
    consensus = ((med > 0) & (long > 0)) | ((med < 0) & (long < 0))
    score = (0.5 * rmed + 0.5 * rlong).where(consensus & eligible)

    targets = pd.DataFrame(0.0, index=data.close.index, columns=data.close.columns)
    events = np.arange(len(targets)) % PHASE["rebalance_hours"] == 0
    old_gross = p5.PHASE["sleeve_gross"]
    old_longs = p5.PHASE["long_count"]
    old_shorts = p5.PHASE["short_count"]
    try:
        p5.PHASE["sleeve_gross"] = PHASE["gross_cap"]
        p5.PHASE["long_count"] = PHASE["long_count"]
        p5.PHASE["short_count"] = PHASE["short_count"]
        for ts in targets.index[events]:
            w = p5._neutral_event_weights(score, inv_vol, beta, eligible, ts)
            if len(w):
                targets.loc[ts, w.index] = w
    finally:
        p5.PHASE["sleeve_gross"] = old_gross
        p5.PHASE["long_count"] = old_longs
        p5.PHASE["short_count"] = old_shorts
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
    report = {"engine":"V98 Independent","phase":PHASE,"hypothesis":"Require directional agreement between medium- and long-horizon residual momentum to isolate persistent relative trends and reduce Phase005 transient-tail/turnover failures.","selection_policy":"single predeclared consensus architecture; training/folds/stress only; no holdout selection","training":train,"folds":folds,"stress_training":{"severe":severe,"supersevere":supersevere},"concentration_training":concentration,"beta_neutrality_training":beta_neutrality,"regimes_training":regimes,"training_gate":{"passed":passed,"failures":failures},"holdout":None}
    if passed:
        h0,h1=cfg["holdout_start"],cfg["holdout_end"]
        hb=p3.metrics(results["base"],h0,h1); hs=p3.metrics(results["severe"],h0,h1); hss=p3.metrics(results["supersevere"],h0,h1)
        hp,hf=p3.holdout_gate(hb,hs,hss)
        report["holdout"]={"base":hb,"severe":hs,"supersevere":hss,"gate":{"passed":hp,"failures":hf}}
    REPORT_PATH.parent.mkdir(parents=True,exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report,indent=2,default=str)+"\n")
    results["base"].positions.to_csv(POSITIONS_PATH)
    final_pass = bool(passed and report["holdout"] and report["holdout"]["gate"]["passed"])
    state["phase"]="phase_006_complete"
    state["champion"] = PHASE["id"] if final_pass else state.get("champion")
    state["last_experiment"]={"id":PHASE["id"],"hypothesis":report["hypothesis"],"status":"validated_candidate" if final_pass else ("training_passed_holdout_rejected" if passed else "training_rejected"),"parameters":"single predeclared consensus residual architecture; no grid","report":str(REPORT_PATH.relative_to(PROJECT)),"training_summary":train,"folds":folds,"stress_training":report["stress_training"],"training_gate":report["training_gate"],"holdout_validation_recorded_but_not_for_selection":report["holdout"]}
    state["holdout_evaluated_for_validation"]=bool(passed)
    state["next_action"]="Diagnose phase006 from training evidence only. If rejected, change alpha family or portfolio construction rather than tuning consensus horizons. If validated, run frozen robustness gate before V99 benchmark."
    STATE_PATH.write_text(json.dumps(state,indent=2,default=str)+"\n")
    print(json.dumps({"phase":PHASE["id"],"training_gate":report["training_gate"],"training":train,"folds":folds,"stress":report["stress_training"],"holdout":report["holdout"]},indent=2,default=str))

if __name__ == "__main__":
    main()
