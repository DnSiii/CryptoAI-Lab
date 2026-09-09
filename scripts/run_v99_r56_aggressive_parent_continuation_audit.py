from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r48_dd_continuation_audit as r48
import run_v99_r51_offset_gross_audit as r51
import run_v99_r54_aggressive_parent_mild_crash as r54

r36 = r54.r36
REPORT = PROJECT / "reports" / "v99_r56_aggressive_parent_continuation_audit.json"


def main():
    cand, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    cost = float(ex["base_cost_per_side"])
    parent, shadow, targets, hedge_active, parent_diag = r54.build_aggressive_parent(
        data, raw, ex, guard, gross, cost
    )

    base = r48.build_risk_features(targets, data.close, parent.equity, hedge_active)
    extra = r51.offset_features(targets, data.close)
    labels = r48.continuation_labels(parent.equity)
    frame = base[["dd_depth"]].join(extra).join(labels).dropna(
        subset=["future_dd7", "future_dd14"]
    )
    split = int(len(frame) * 0.60)
    train_end = frame.index[max(0, split - 1)]

    cohorts = {
        "early_dd_5_to_12": r51.audit(frame, train_end, 0.05, 0.12),
        "mid_dd_8_to_18": r51.audit(frame, train_end, 0.08, 0.18),
        "deep_dd_12_to_24": r51.audit(frame, train_end, 0.12, 0.24),
    }

    out = {
        "study": "V99 R56 aggressive-parent drawdown-continuation audit",
        "status": "DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION",
        "objective": (
            "verify on the fixed aggressive R30 parent whether dominant-side gross, total gross and net exposure "
            "causally predict further drawdown deepening before designing a side-specific brake; thresholds are "
            "learned only on the first 60% and evaluated unchanged on the last 40%"
        ),
        "parent_fixed": r54.AGGRESSIVE_PARENT,
        "parent_summary": r36.stats(parent.equity),
        "parent_diagnostics": parent_diag,
        "train_end": train_end.isoformat(),
        "cohorts": cohorts,
        "disclosure": (
            "Diagnostic only. Exposure features use target weights and market history available through t; "
            "future data is used only to label continuation outcomes. No candidate is promoted by this report."
        ),
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({
        "study": out["study"],
        "parent_summary": out["parent_summary"],
        "top": {
            cohort: {
                label: body["feature_rankings"][label][:8]
                for label in ("deepen_7d_5pp", "deepen_14d_8pp")
            }
            for cohort, body in cohorts.items()
        },
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
