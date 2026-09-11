from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import run_v99_r67_dynamic_hedge_router as r67

PROJECT = Path(__file__).resolve().parents[1]
REPORT = PROJECT / "reports" / "candidate_v99_r84_daily_release_router.json"
ORIGINAL_GATE_SERIES = r67.gate_series


def daily_release_gate_series(data, t15: pd.DataFrame, router: dict):
    raw, diag = ORIGINAL_GATE_SERIES(data, t15, router)
    raw = raw.reindex(t15.index).fillna(False).astype(bool)

    # R83 showed that the h0.25 advantage remains positive when the frozen gate
    # is still present at the next daily decision, but turns negative/flat after
    # the gate clears. Observe once every 24h and hold only the latest observed
    # state for the following day; there is no fixed 72h persistence.
    decision = pd.Series(np.nan, index=raw.index, dtype=float)
    positions = np.arange(0, len(raw), 24, dtype=int)
    if len(positions):
        decision.iloc[positions] = raw.iloc[positions].astype(float).to_numpy()
    active = decision.ffill(limit=23).fillna(0.0).gt(0.0)

    out_diag = dict(diag)
    out_diag.update({
        "raw_hourly_gate_fraction": float(raw.mean()),
        "daily_active_fraction": float(active.mean()),
        "decision_count": int(len(positions)),
        "decision_cadence_hours": 24,
        "release_policy": "release at next daily decision if frozen raw gate is false",
    })
    return active, out_diag


def main():
    r67.REPORT = REPORT
    r67.ROUTERS = ({"name": "h15_gross_low", "rule": "gross"},)
    r67.gate_series = daily_release_gate_series
    r67.main()

    out = json.loads(REPORT.read_text())
    out["study"] = "V99 R84 h15-gross-low daily release router"
    out["objective"] = (
        "keep the frozen R66 h15-gross-low threshold and R55 h0.15/h0.25 endpoints, but replace R73 fixed 72h persistence "
        "with a causal daily state: use h0.25 for the next 24h only when the gate is true at the current daily decision, and "
        "release back to h0.15 at the next daily decision when it clears"
    )
    out["grid_policy"] = (
        "one fixed router only; no threshold, amplitude or persistence grid. Daily cadence is inherited from the R66/R71/R83 "
        "validation protocol and release-on-clear follows the R83 segment audit"
    )
    out["release_design"] = {
        "decision_cadence_hours": 24,
        "max_hold_without_reconfirmation_hours": 24,
        "thresholds_refit": False,
        "r83_evidence": {
            "24_48_if_gate_persists_mean_advantage": 0.000650178302761077,
            "24_48_if_gate_clears_mean_advantage": -0.00031810526370302806,
            "48_72_if_gate_persists_mean_advantage": 0.00048327727407417986,
            "48_72_if_gate_clears_mean_advantage": -9.951862836273182e-06,
        },
    }
    out["disclosure"] = (
        "Historical research only. The h15-gross threshold remains frozen from R66 training data. R83 was diagnostic and "
        "motivates only release-on-clear; no candidate outcome is used to fit a new threshold, amplitude or duration. Frozen "
        "V99 and official paper remain untouched."
    )
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "selected": out.get("selected")}, indent=2), flush=True)


if __name__ == "__main__":
    main()
