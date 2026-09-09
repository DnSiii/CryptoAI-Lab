from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import run_v99_r67_dynamic_hedge_router as r67

PROJECT = Path(__file__).resolve().parents[1]
REPORT = PROJECT / "reports" / "candidate_v99_r73_gross_low_72h_persistence.json"
ORIGINAL_GATE_SERIES = r67.gate_series


def persistent_gate_series(data, t15: pd.DataFrame, router: dict):
    raw, diag = ORIGINAL_GATE_SERIES(data, t15, router)
    raw = raw.reindex(t15.index).fillna(False).astype(bool)

    # Match the R66/R71 daily observation cadence. A positive observation is a
    # causal trigger whose validated label horizon is 72h; keep the stronger
    # hedge active for that horizon, without looking at future returns.
    trigger = pd.Series(False, index=raw.index)
    positions = np.arange(0, len(raw), 24, dtype=int)
    if len(positions):
        trigger.iloc[positions] = raw.iloc[positions].to_numpy(dtype=bool)
    active = trigger.astype(float).rolling(72, min_periods=1).max().gt(0.0)

    out_diag = dict(diag)
    out_diag.update({
        "raw_hourly_gate_fraction": float(raw.mean()),
        "daily_trigger_fraction": float(trigger.mean()),
        "persistent_gate_fraction": float(active.mean()),
        "decision_count": int(len(positions)),
        "persistence_hours": 72,
    })
    return active, out_diag


def main():
    r67.REPORT = REPORT
    r67.ROUTERS = ({"name": "h15_gross_low", "rule": "gross"},)
    r67.gate_series = persistent_gate_series
    r67.main()

    out = json.loads(REPORT.read_text())
    out["study"] = "V99 R73 h15-gross-low daily trigger with 72h hedge persistence"
    out["objective"] = (
        "align the strongest R71 temporally stable h15_gross_low regime with the exact 72h forward horizon used by R66/R71: "
        "observe once daily, switch from h0.15 to h0.25 when triggered, and hold the stronger hedge for 72h"
    )
    out["grid_policy"] = (
        "one fixed router only: h15_gross_low at the unchanged R66 training-only threshold 0.4478403629219058; "
        "daily observations and 72h causal persistence; h0.15/h0.25 endpoints unchanged; no threshold or horizon tuning"
    )
    out["persistence_design"] = {
        "decision_cadence_hours": 24,
        "persistence_hours": 72,
        "rationale": "match the R66/R71 material-advantage label horizon",
        "thresholds_refit": False,
    }
    out["disclosure"] = (
        "Historical research only. The h15-gross threshold remains frozen from R66 training data ending 2024-01-05 and R71 "
        "only audited its temporal stability. Daily triggers use close-t data; the 72h hold is fixed by the original label horizon, "
        "not optimized on results. Frozen V99 and official paper remain untouched."
    )
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "selected": out.get("selected")}, indent=2), flush=True)


if __name__ == "__main__":
    main()
