from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import run_v99_r67_dynamic_hedge_router as r67

PROJECT = Path(__file__).resolve().parents[1]
REPORT = PROJECT / "reports" / "candidate_v99_r68_daily_hedge_router.json"
ORIGINAL_GATE_SERIES = r67.gate_series


def daily_gate_series(data, t15: pd.DataFrame, router: dict):
    raw_gate, diag = ORIGINAL_GATE_SERIES(data, t15, router)
    raw_gate = raw_gate.reindex(t15.index).fillna(False).astype(bool)

    # R66 was fitted on one observation every 24 hours. Reproduce that cadence
    # prospectively: decide only on those timestamps and hold the decision until
    # the next daily observation. No future value is used.
    held = pd.Series(np.nan, index=raw_gate.index, dtype=object)
    decision_positions = np.arange(0, len(raw_gate), 24, dtype=int)
    if len(decision_positions):
        held.iloc[decision_positions] = raw_gate.iloc[decision_positions].to_numpy(dtype=bool)
    held = held.ffill().fillna(False).astype(bool)

    out_diag = dict(diag)
    out_diag.update({
        "raw_hourly_gate_fraction": float(raw_gate.mean()),
        "daily_held_gate_fraction": float(held.mean()),
        "decision_count": int(len(decision_positions)),
        "decision_cadence_hours": 24,
    })
    return held, out_diag


def main():
    r67.REPORT = REPORT
    r67.gate_series = daily_gate_series
    r67.main()

    out = json.loads(REPORT.read_text())
    out["study"] = "V99 R68 daily dynamic hedge amplitude router"
    out["objective"] = (
        "route causally between R55 h0.15 and h0.25 using the exact R66 training-only regime thresholds, "
        "but evaluate the router only once every 24h and hold that decision until the next daily observation, "
        "matching the cadence on which R66 was fitted"
    )
    out["grid_policy"] = (
        "same five predeclared R67 routers and exact R66 train-only thresholds; only execution cadence changes "
        "from hourly evaluation to one decision every 24h held until the next decision; no threshold, parent, "
        "benchmark, requested-horizon or signal retuning"
    )
    out["execution_cadence"] = {
        "decision_interval_hours": 24,
        "hold_until_next_decision": True,
        "rationale": "match R66 daily sampling and reduce router churn/distribution mismatch",
    }
    out["disclosure"] = (
        "Historical research only. R66 thresholds were fixed on the first 60% chronological daily sample ending "
        "2024-01-05. R68 changes only routing cadence. Each daily decision uses close-t information and enters the "
        "same causal next-open replay. Frozen V99 and official paper remain untouched."
    )
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "selected": out.get("selected")}, indent=2), flush=True)


if __name__ == "__main__":
    main()
