from __future__ import annotations

import json
from pathlib import Path

import run_v99_r64_severe_medium_hedge_topup as r64

PROJECT = Path(__file__).resolve().parents[1]
REPORT = PROJECT / "reports" / "candidate_v99_r65_core_net_topup_amplitude.json"


def main():
    # Keep every causal rule from R64 fixed. Only explore structurally interpretable
    # hedge increments around the promising R64 core-net gate.
    r64.REPORT = REPORT
    r64.GATES = (
        {"name": "core_net_q80", "type": "core_net", "threshold": r64.CORE_NET_Q80},
    )
    r64.TOPUPS = (0.05, 0.15, 0.20, 0.25)
    r64.PULSE_HOURS = 12
    r64.main()

    out = json.loads(REPORT.read_text())
    out["study"] = "V99 R65 core-net q80 selective hedge amplitude frontier"
    out["objective"] = (
        "refine only the promising R64 core_net_q80 severe-medium gate while keeping the R55 hedge-0.15 parent, "
        "R63 training-only q80 threshold and 12h pulse fixed; test whether smaller structural hedge top-ups recover "
        "one-year and severe-cost return while preserving R64 tail improvements"
    )
    out["grid_policy"] = (
        "4 predeclared amplitudes on the fixed R64 core_net_q80 gate: +0.05/+0.15/+0.20/+0.25 BTC opposite-net hedge; "
        "12h pulse fixed; no threshold, signal, parent, horizon or benchmark retuning"
    )
    out["parent_research_reference"] = "R55 hedge-0.15"
    out["gate_research_reference"] = "R63/R64 core_net_q80 training-only threshold"
    out["disclosure"] = (
        "Historical research only. The gate threshold was fixed before this amplitude study from the R63 first-60%-of-events "
        "training split. Candidate target changes are causal and execute through the same next-open replay. Frozen V99 and paper are untouched."
    )
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "selected": out.get("selected")}, indent=2), flush=True)


if __name__ == "__main__":
    main()
