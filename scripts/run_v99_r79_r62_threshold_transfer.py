from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r55_low_hedge_amplitude_frontier as r55
import run_v99_r62_asset_damage_precursor_audit as r62
import run_v99_r67_dynamic_hedge_router as r67
import run_v99_r75_hedged_recovery_alpha as r75

REPORT = PROJECT / "reports" / "v99_r79_r62_threshold_transfer.json"
r36 = r67.r36

SPECS = {
    "mid_dd_8_to_18": {
        "lo": 0.08,
        "hi": 0.18,
        "feature": "worst_loss_share_168h",
        "threshold": 0.7337173889408508,
        "label": "deepen_14d_8pp",
        "source": "R62 train q80; old train lift 1.4540 / holdout lift 1.4757",
    },
    "deep_dd_12_to_24": {
        "lo": 0.12,
        "hi": 0.24,
        "feature": "worst_loss_share_168h",
        "threshold": 0.7295387859445592,
        "label": "deepen_14d_8pp",
        "source": "R62 train q80; old train lift 1.1150 / holdout lift 1.6135",
    },
}


def stats(frame: pd.DataFrame, spec: dict) -> dict:
    cohort = frame.loc[(frame["dd_depth"] >= spec["lo"]) & (frame["dd_depth"] < spec["hi"])].copy()
    if cohort.empty:
        return {"rows":0,"selected":0,"coverage":0.0,"base_rate":0.0,"gated_rate":0.0,"lift":0.0,"event_capture":0.0}
    mask = cohort[spec["feature"]] >= spec["threshold"]
    base = float(cohort[spec["label"]].mean())
    rate = float(cohort.loc[mask, spec["label"]].mean()) if mask.any() else 0.0
    total_events = int(cohort[spec["label"]].sum())
    captured = int(cohort.loc[mask, spec["label"]].sum()) if mask.any() else 0
    return {
        "rows": int(len(cohort)),
        "selected": int(mask.sum()),
        "coverage": float(mask.mean()),
        "base_rate": base,
        "gated_rate": rate,
        "lift": float(rate/base) if base > 0 else 0.0,
        "event_capture": float(captured/total_events) if total_events > 0 else 0.0,
    }


def main():
    cand, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    cost = float(ex["base_cost_per_side"])
    parent, _, parent_diag = r75.build_variant(data, raw, ex, guard, gross, cost, False)

    f = r62.damage_features(parent)
    labels = r62.r61.continuation_labels(parent.equity)
    frame = f.join(labels).dropna(subset=["future_dd7","future_dd14"])
    split = int(len(frame)*0.60)
    train = frame.iloc[:split]
    hold = frame.iloc[split:]

    results = {}
    for name, spec in SPECS.items():
        full = stats(frame, spec)
        tr = stats(train, spec)
        ho = stats(hold, spec)
        cohort = frame.loc[(frame["dd_depth"] >= spec["lo"]) & (frame["dd_depth"] < spec["hi"])]
        folds = []
        if len(cohort):
            for i, ids in enumerate(np.array_split(cohort.index, 5), 1):
                sub = cohort.loc[ids]
                row = stats(sub, spec)
                row.update({"fold":i,"start":ids[0].isoformat() if len(ids) else None,"end":ids[-1].isoformat() if len(ids) else None})
                folds.append(row)
        results[name] = {
            "spec": spec,
            "full": full,
            "chronological_60pct": tr,
            "chronological_40pct": ho,
            "folds": folds,
            "positive_lift_folds": int(sum(x["lift"] > 1.0 for x in folds)),
            "fold_count": int(len(folds)),
            "transfer_pass": bool(tr["lift"] > 1.0 and ho["lift"] > 1.0 and sum(x["lift"] > 1.0 for x in folds) >= 4),
        }

    out = {
        "study": "V99 R79 transfer of frozen R62 concentrated-damage thresholds to R73",
        "status": "DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION",
        "objective": "test whether two R62 train-derived worst-asset 168h loss-share thresholds retain predictive value for further drawdown deepening on the newer R73 architecture, with zero threshold refitting",
        "thresholds_refit": False,
        "parent_r73_summary": r36.stats(parent.equity),
        "parent_diagnostics": parent_diag,
        "frame_rows": int(len(frame)),
        "current_split_timestamp": frame.index[max(0,split-1)].isoformat() if len(frame) else None,
        "results": results,
        "disclosure": "Diagnostic historical research only. Thresholds were frozen in the older R62 h0.15 parent and are transferred unchanged. Future equity is used only for continuation labels. A future guard may use a shadow R73 path so the realized-damage signal stays causal and independent of the guarded portfolio. Frozen V99 and official paper remain untouched.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps({"study":out["study"],"results":results},indent=2),flush=True)


if __name__ == "__main__":
    main()
