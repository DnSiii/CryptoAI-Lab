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
REPORT_PATH = PROJECT / "reports" / "v98_independent_phase004_tail_risk_budget.json"
POSITIONS_PATH = PROJECT / "reports" / "v98_independent_phase004_tail_risk_budget_positions.csv"

# Predeclared single hypothesis, not a grid.  Phase003 alpha is left untouched.
PHASE = {
    "id": "phase_004_tail_risk_budget",
    "btc_vol_hours": 720,
    "btc_vol_reference_hours": 4320,
    "btc_vol_reference_min_hours": 2160,
    "stress_gross_multiplier": 0.60,
    "gross_cap": 1.0,
}


def build_targets(data, membership: pd.DataFrame) -> pd.DataFrame:
    """Apply a causal portfolio risk budget to the untouched Phase003 alpha.

    Diagnosis from Phase003: alpha/folds/cost stress were acceptable and the only
    training gate failure was a -13.10% worst day.  Rather than tuning momentum,
    dispersion or basket parameters, this experiment tests a distinct economic
    mechanism: systemic volatility clusters raise cross-sectional spread tail risk.
    Exposure is therefore reduced to 60% only when lagged BTC 30d realized hourly
    volatility is above 1.5x its own trailing 180d median.  Every input is t-1.
    """
    base = p3.build_targets(data, membership)
    lagged = data.close["BTCUSDT"].shift(1)
    ret = lagged.pct_change(fill_method=None)
    vol = ret.rolling(PHASE["btc_vol_hours"], min_periods=360).std()
    ref = vol.rolling(
        PHASE["btc_vol_reference_hours"],
        min_periods=PHASE["btc_vol_reference_min_hours"],
    ).median().shift(1)
    systemic_stress = (vol > 1.5 * ref) & ref.notna()
    scale = pd.Series(1.0, index=base.index)
    scale.loc[systemic_stress] = PHASE["stress_gross_multiplier"]
    return base.mul(scale, axis=0)


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


def main() -> None:
    cfg = json.loads(CONFIG_PATH.read_text())
    state = json.loads(STATE_PATH.read_text())
    data = load_data(PROJECT, cfg["data_config"])
    validation = validate_data(data)
    if validation["errors"]:
        raise RuntimeError(f"data validation failed: {validation['errors'][:5]}")

    liquid, membership = point_in_time_liquid_view(
        data,
        top_n=p3.PHASE["liquidity_top_n"],
        lookback_hours=p3.PHASE["liquidity_lookback_hours"],
        minimum_history_hours=p3.PHASE["minimum_history_hours"],
    )
    targets = build_targets(liquid, membership)
    results = {name: evaluate(liquid, targets, cfg, name) for name in ("base", "severe", "supersevere")}

    start, end = cfg["research_start"], cfg["training_end"]
    train = p3.metrics(results["base"], start, end)
    folds = {f["name"]: p3.metrics(results["base"], f["start"], f["end"]) for f in cfg["folds"]}
    severe = p3.metrics(results["severe"], start, end)
    supersevere = p3.metrics(results["supersevere"], start, end)
    concentration = p3.concentration_metrics(results["base"], start, end)
    beta_neutrality = p3.beta_neutrality_metrics(results["base"], liquid, start, end)
    regimes = p3.regime_metrics(results["base"], liquid, start, end, end)
    passed, failures = p3.training_gate(train, folds, severe, supersevere, concentration)

    report = {
        "engine": "V98 Independent",
        "phase": PHASE,
        "hypothesis": "Systemic-volatility risk budgeting can remove Phase003 tail failure without altering its cross-sectional alpha or selecting on holdout.",
        "selection_policy": "single predeclared risk architecture; training/folds/stress only; holdout remains untouched unless training gate passes",
        "training": train,
        "folds": folds,
        "stress_training": {"severe": severe, "supersevere": supersevere},
        "concentration_training": concentration,
        "beta_neutrality_training": beta_neutrality,
        "regimes_training": regimes,
        "training_gate": {"passed": passed, "failures": failures},
        "holdout": None,
    }

    # Only after a clean training gate may holdout be opened once for validation.
    if passed:
        h0, h1 = cfg["holdout_start"], cfg["holdout_end"]
        hb = p3.metrics(results["base"], h0, h1)
        hs = p3.metrics(results["severe"], h0, h1)
        hss = p3.metrics(results["supersevere"], h0, h1)
        hp, hf = p3.holdout_gate(hb, hs, hss)
        report["holdout"] = {"base": hb, "severe": hs, "supersevere": hss, "gate": {"passed": hp, "failures": hf}}

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str) + "\n")
    results["base"].positions.to_csv(POSITIONS_PATH)

    state["phase"] = "phase_004_complete"
    state["last_experiment"] = {
        "id": PHASE["id"],
        "hypothesis": report["hypothesis"],
        "status": "training_passed_holdout_validated" if passed and report["holdout"] and report["holdout"]["gate"]["passed"] else ("training_passed_holdout_rejected" if passed else "training_rejected"),
        "parameters": "single predeclared architecture; no grid",
        "report": str(REPORT_PATH.relative_to(PROJECT)),
        "training_summary": train,
        "folds": folds,
        "stress_training": report["stress_training"],
        "training_gate": report["training_gate"],
        "holdout_validation_recorded_but_not_for_selection": report["holdout"],
    }
    state["holdout_evaluated_for_validation"] = bool(passed)
    state["next_action"] = "diagnose phase004 evidence and promote only if materially robust; otherwise change hypothesis, not thresholds"
    STATE_PATH.write_text(json.dumps(state, indent=2, default=str) + "\n")
    print(json.dumps({"phase": PHASE["id"], "training_gate": report["training_gate"], "training": train, "folds": folds, "stress": report["stress_training"], "holdout": report["holdout"]}, indent=2, default=str))


if __name__ == "__main__":
    main()
