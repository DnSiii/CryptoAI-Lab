from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r50_crash_deleveraging_overlay as r50

r36 = r50.r36
r37 = r50.r37
REPORT = PROJECT / "reports" / "candidate_v99_r54_aggressive_parent_mild_crash.json"

AGGRESSIVE_PARENT = {
    "dd_trigger": 0.10,
    "hedge_size": 0.25,
    "cooldown": 48,
    "market_level": 3,
    "min_net": 0.10,
    "gross_cap": 1.90,
}

CRASH_PRESETS = (
    {"name": "medium", "r6_trigger": -0.035, "dd_trigger": -0.070, "r24_trigger": -0.055, "btc24_trigger": -0.045, "btc72_trigger": -0.090, "cooldown": 12},
    {"name": "deep", "r6_trigger": -0.045, "dd_trigger": -0.090, "r24_trigger": -0.070, "btc24_trigger": -0.055, "btc72_trigger": -0.110, "cooldown": 24},
)
RISK_SCALES = (0.85, 0.90, 0.95)


def build_aggressive_parent(data, raw, ex, guard, gross, cost):
    shadow = r36.run(data, raw, ex, cost, gross, guard)
    targets, hedge_active = r37.r30_targets(
        raw, shadow.equity, data.close, AGGRESSIVE_PARENT
    )
    parent = r36.run(
        data, targets, ex, cost, float(AGGRESSIVE_PARENT["gross_cap"]), guard
    )
    diag = {
        "parent": "R30 aggressive fixed finalist",
        "hedge_active_fraction": float(hedge_active.mean()),
        "params": AGGRESSIVE_PARENT,
    }
    return parent, shadow, targets, hedge_active, diag


def main() -> None:
    r50.REPORT = REPORT
    r50.R40_FIXED = dict(AGGRESSIVE_PARENT)
    r50.CRASH_PRESETS = CRASH_PRESETS
    r50.RISK_SCALES = RISK_SCALES
    r50.build_parent = build_aggressive_parent
    r50.main()

    report = json.loads(REPORT.read_text())
    report["study"] = "V99 R54 aggressive R30 parent + mild crash deleveraging"
    report["status"] = "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER"
    report["parent"] = "R30 aggressive finalist fixed before R54"
    report["parent_fixed"] = AGGRESSIVE_PARENT
    report["objective"] = (
        "start from the strongest validated 365d-return R30 finalist and spend only a small amount of "
        "its one-year return margin on causal crash protection; exclude the broad early detector and "
        "test only mild 5%, 10% and 15% gross reductions under the pre-existing medium/deep R37 signals"
    )
    report["grid_policy"] = (
        "6 predeclared combinations = exact R37 medium/deep crash detectors x mild risk scales "
        "0.85/0.90/0.95; parent parameters are frozen from the prior R30 finalist and validation "
        "horizons are not optimizer inputs"
    )
    report["risk_scales"] = list(RISK_SCALES)
    report["crash_presets"] = [p["name"] for p in CRASH_PRESETS]
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
