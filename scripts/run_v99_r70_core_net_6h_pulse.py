from __future__ import annotations

import json
from pathlib import Path

import run_v99_r64_severe_medium_hedge_topup as r64

PROJECT = Path(__file__).resolve().parents[1]
REPORT = PROJECT / "reports" / "candidate_v99_r70_core_net_6h_pulse.json"


def main():
    # Duration refinement only. Keep the R63/R64 training-only gate fixed and
    # reuse the R65 predeclared amplitudes; halve the pulse from 12h to 6h.
    r64.REPORT = REPORT
    r64.GATES = (
        {"name": "core_net_q80", "type": "core_net", "threshold": r64.CORE_NET_Q80},
    )
    r64.TOPUPS = (0.05, 0.15, 0.20, 0.25)
    r64.PULSE_HOURS = 6
    r64.main()

    out = json.loads(REPORT.read_text())
    out["study"] = "V99 R70 core-net q80 selective hedge 6h pulse"
    out["objective"] = (
        "test whether halving the fixed R65/R64 core-net selective hedge pulse from 12h to 6h recovers one-year and "
        "severe-cost alpha while retaining tail improvements; gate threshold, parent and amplitudes remain unchanged"
    )
    out["grid_policy"] = (
        "same four R65 amplitudes +0.05/+0.15/+0.20/+0.25 on the exact fixed core_net_q80 gate; only pulse duration "
        "changes from 12h to the structurally predeclared 6h horizon matching the medium fast-loss window; no other retuning"
    )
    out["duration_refinement"] = {"control_hours": 12, "tested_hours": 6, "thresholds_refit": False}
    out["disclosure"] = (
        "Historical research only. The core-net threshold remains frozen from the R63 training split. R70 changes only "
        "the previously predeclared pulse duration to 6h. Decisions remain causal and enter the same next-open replay. "
        "Frozen V99 and official paper remain untouched."
    )
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "selected": out.get("selected")}, indent=2), flush=True)


if __name__ == "__main__":
    main()
