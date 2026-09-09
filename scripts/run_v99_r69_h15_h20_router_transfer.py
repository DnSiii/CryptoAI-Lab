from __future__ import annotations

import json
from pathlib import Path

import run_v99_r55_low_hedge_amplitude_frontier as r55
import run_v99_r67_dynamic_hedge_router as r67

PROJECT = Path(__file__).resolve().parents[1]
REPORT = PROJECT / "reports" / "candidate_v99_r69_h15_h20_router_transfer.json"


def main():
    # Transfer test only: keep every R66/R67 regime threshold fixed and change
    # only the high-hedge endpoint from the already-tested R55 h0.25 to h0.20.
    r67.REPORT = REPORT
    r67.P25 = r55.params(0.20)
    r67.main()

    out = json.loads(REPORT.read_text())
    if "h25" in out:
        out["h20"] = out.pop("h25")
    for row in out.get("finalists", []):
        if "isolated_h25" in row:
            row["isolated_h20"] = row.pop("isolated_h25")
    sel = out.get("selected")
    if isinstance(sel, dict) and "isolated_h25" in sel:
        sel["isolated_h20"] = sel.pop("isolated_h25")

    out["study"] = "V99 R69 h0.15-to-h0.20 dynamic hedge router transfer"
    out["objective"] = (
        "test whether the R66 regimes learned to identify useful stronger-hedge conditions transfer without refitting "
        "to the structurally intermediate R55 h0.20 endpoint, seeking more one-year return retention than the h0.25 router "
        "while preserving historical, severe-cost and drawdown benefits"
    )
    out["router_endpoints"] = {"default": 0.15, "high_regime": 0.20}
    out["grid_policy"] = (
        "same five R67 routers and exact R66 training-only thresholds; only the high-hedge endpoint changes from h0.25 "
        "to the pre-existing R55 h0.20 candidate; no regime, threshold, benchmark, horizon or execution retuning"
    )
    out["transfer_test"] = {
        "source_regime_audit": "R66 h0.25 vs h0.15",
        "source_train_end": r67.TRAIN_END.isoformat(),
        "target_endpoints": [0.15, 0.20],
        "thresholds_refit": False,
    }
    out["disclosure"] = (
        "Historical research only. This is an out-of-family amplitude transfer test: all regime thresholds remain frozen "
        "from R66 training data ending 2024-01-05. Decisions use close-t information and enter the same causal next-open replay. "
        "Frozen V99 and official paper remain untouched."
    )
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "selected": out.get("selected")}, indent=2), flush=True)


if __name__ == "__main__":
    main()
