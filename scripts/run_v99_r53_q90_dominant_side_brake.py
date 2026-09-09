from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r49_continuation_gross_brake as r49

REPORT = PROJECT / "reports" / "candidate_v99_r53_q90_dominant_side_brake.json"

# Fixed from R51 first-60%-chronological q90 thresholds only. q95 is excluded
# because it did not show stable train/holdout lift in the mid-DD cohort.
PRESETS = (
    {
        "name": "early_q90_dominant",
        "dd_min": 0.05,
        "dd_max": 0.12,
        "dominant_min": 1.1244949855178232,
        "gross_min": None,
        "net_min": None,
        "min_votes": 1,
        "r51_train_lift": 1.5324125917630955,
        "r51_holdout_lift": 1.7109833949811115,
    },
    {
        "name": "mid_q90_dominant",
        "dd_min": 0.08,
        "dd_max": 0.18,
        "dominant_min": 1.1605475800068423,
        "gross_min": None,
        "net_min": None,
        "min_votes": 1,
        "r51_train_lift": 1.3046295110579909,
        "r51_holdout_lift": 2.0203335891154213,
    },
    {
        "name": "mid_q90_two_of_three",
        "dd_min": 0.08,
        "dd_max": 0.18,
        "dominant_min": 1.1605475800068423,
        "gross_min": 1.35,
        "net_min": 1.0940762487227464,
        "min_votes": 2,
        "r51_component_train_lifts": {
            "dominant": 1.3046295110579909,
            "gross": 1.781616892103031,
            "net": 1.6419377709258227,
        },
        "r51_component_holdout_lifts": {
            "dominant": 2.0203335891154213,
            "gross": 2.115317310539627,
            "net": 2.028263478303753,
        },
    },
)


def q90_gate(
    r30_equity: pd.Series,
    r30_targets: pd.DataFrame,
    close: pd.DataFrame,
    p: dict,
):
    idx = r30_equity.index.intersection(r30_targets.index).intersection(close.index)
    eq = r30_equity.reindex(idx).astype(float)
    t = r30_targets.reindex(index=idx, columns=close.columns).fillna(0.0)

    dd_depth = (1.0 - eq / eq.cummax()).clip(lower=0.0)
    gross = t.abs().sum(axis=1)
    net_abs = t.sum(axis=1).abs()
    positive = t.clip(lower=0.0).sum(axis=1)
    negative = (-t.clip(upper=0.0)).sum(axis=1)
    dominant = pd.concat([positive, negative], axis=1).max(axis=1)

    state = (dd_depth >= float(p["dd_min"])) & (dd_depth < float(p["dd_max"]))
    votes = pd.Series(0, index=idx, dtype=int)
    if p.get("dominant_min") is not None:
        votes = votes + (dominant >= float(p["dominant_min"])).astype(int)
    if p.get("gross_min") is not None:
        votes = votes + (gross >= float(p["gross_min"])).astype(int)
    if p.get("net_min") is not None:
        votes = votes + (net_abs >= float(p["net_min"])).astype(int)

    instant = (state & (votes >= int(p.get("min_votes", 1)))).fillna(False)
    active = instant.astype(float).rolling(int(p["cooldown"]), min_periods=1).max().gt(0.0)

    return active, {
        "instant_fraction": float(instant.mean()),
        "active_fraction": float(active.mean()),
        "median_dd_depth": float(dd_depth.loc[instant].median()) if instant.any() else 0.0,
        "median_dominant_side_gross": float(dominant.loc[instant].median()) if instant.any() else 0.0,
        "median_gross": float(gross.loc[instant].median()) if instant.any() else 0.0,
        "median_net_abs": float(net_abs.loc[instant].median()) if instant.any() else 0.0,
        "mean_votes": float(votes.loc[instant].mean()) if instant.any() else 0.0,
    }


def main() -> None:
    r49.REPORT = REPORT
    r49.GATE_PRESETS = PRESETS
    r49.continuation_gate = q90_gate
    r49.main()

    report = json.loads(REPORT.read_text())
    report["study"] = "V99 R53 q90 dominant-side continuation brake"
    report["status"] = "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER"
    report["parent"] = "fixed R40; R51 q90 continuation features only"
    report["objective"] = (
        "test whether stable q90 dominant-side/gross/net continuation signals can reduce the chance that a "
        "moderate drawdown deepens while preserving R40 compounding; q95 thresholds are deliberately excluded"
    )
    report["threshold_source"] = (
        "R51 first-60%-chronological q90 thresholds with positive lift in both train and holdout; no q95 threshold"
    )
    report["grid_policy"] = (
        "3 predeclared R51 q90 gate structures x R49 fixed risk scales 0.70/0.82/0.90 x fixed cooldowns 24/48/72h; "
        "validation horizons are not optimizer inputs"
    )
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
