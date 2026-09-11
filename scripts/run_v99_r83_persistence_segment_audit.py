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
import run_v99_r67_dynamic_hedge_router as r67

REPORT = PROJECT / "reports" / "v99_r83_persistence_segment_audit.json"
THRESHOLD = 0.4478403629219058


def rel_adv(a0, a1, b0, b1):
    ar = a1 / a0
    br = b1 / b0
    return ar / br - 1.0


def stats(x: pd.Series) -> dict:
    y = x.replace([np.inf, -np.inf], np.nan).dropna().astype(float)
    if y.empty:
        return {"n": 0, "mean": 0.0, "median": 0.0, "positive_rate": 0.0, "material_20bp_rate": 0.0}
    return {
        "n": int(len(y)),
        "mean": float(y.mean()),
        "median": float(y.median()),
        "positive_rate": float((y > 0).mean()),
        "material_20bp_rate": float((y > 0.002).mean()),
    }


def fold_stats(frame: pd.DataFrame, col: str) -> list[dict]:
    if frame.empty:
        return []
    edges = np.linspace(0, len(frame), 6, dtype=int)
    out = []
    for i in range(5):
        f = frame.iloc[edges[i]:edges[i+1]]
        out.append({
            "fold": i + 1,
            "start": f.index[0].isoformat() if len(f) else None,
            "end": f.index[-1].isoformat() if len(f) else None,
            **stats(f[col] if len(f) else pd.Series(dtype=float)),
        })
    return out


def main():
    cand, data, raw, ex, guard, gross, quarantined, metadata = r55.r36.v15_setup()
    cost = float(ex["base_cost_per_side"])
    shadow = r55.r36.run(data, raw, ex, cost, gross, guard)
    p15, p25 = r55.params(0.15), r55.params(0.25)
    res15, _, t15, _ = r55.build_with_shadow(data, raw, ex, guard, gross, cost, p15, shadow=shadow)
    res25, _, _, _ = r55.build_with_shadow(data, raw, ex, guard, gross, cost, p25, shadow=shadow)

    idx = res15.equity.index.intersection(res25.equity.index)
    e15 = res15.equity.reindex(idx).astype(float)
    e25 = res25.equity.reindex(idx).astype(float)
    g15 = t15.reindex(idx).abs().sum(axis=1)
    raw_gate = (g15 <= THRESHOLD).fillna(False)

    daily_idx = idx[::24]
    rows = []
    for t in daily_idx:
        if not bool(raw_gate.loc[t]):
            continue
        pos = idx.get_loc(t)
        if not isinstance(pos, (int, np.integer)) or pos + 96 >= len(idx):
            continue
        t24, t48, t72, t96 = idx[pos+24], idx[pos+48], idx[pos+72], idx[pos+96]
        rows.append({
            "t": t,
            "gate_t24": bool(raw_gate.loc[t24]),
            "gate_t48": bool(raw_gate.loc[t48]),
            "adv_0_24": float(rel_adv(e25.loc[t], e25.loc[t24], e15.loc[t], e15.loc[t24])),
            "adv_24_48": float(rel_adv(e25.loc[t24], e25.loc[t48], e15.loc[t24], e15.loc[t48])),
            "adv_48_72": float(rel_adv(e25.loc[t48], e25.loc[t72], e15.loc[t48], e15.loc[t72])),
            "adv_72_96": float(rel_adv(e25.loc[t72], e25.loc[t96], e15.loc[t72], e15.loc[t96])),
        })
    frame = pd.DataFrame(rows).set_index("t").sort_index() if rows else pd.DataFrame()

    segments = {}
    for col in ("adv_0_24", "adv_24_48", "adv_48_72", "adv_72_96"):
        segments[col] = {
            "full": stats(frame[col]),
            "folds": fold_stats(frame, col),
        }

    conditional = {
        "24_48_if_gate_persists_at_24": stats(frame.loc[frame["gate_t24"], "adv_24_48"]),
        "24_48_if_gate_clears_at_24": stats(frame.loc[~frame["gate_t24"], "adv_24_48"]),
        "48_72_if_gate_persists_at_48": stats(frame.loc[frame["gate_t48"], "adv_48_72"]),
        "48_72_if_gate_clears_at_48": stats(frame.loc[~frame["gate_t48"], "adv_48_72"]),
    }

    cond_folds = {}
    for name, mask, col in (
        ("24_48_if_gate_persists_at_24", frame["gate_t24"], "adv_24_48"),
        ("24_48_if_gate_clears_at_24", ~frame["gate_t24"], "adv_24_48"),
        ("48_72_if_gate_persists_at_48", frame["gate_t48"], "adv_48_72"),
        ("48_72_if_gate_clears_at_48", ~frame["gate_t48"], "adv_48_72"),
    ):
        cond_folds[name] = fold_stats(frame.loc[mask], col)

    out = {
        "study": "V99 R83 R73 persistence segment audit",
        "status": "DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION",
        "objective": "decompose the frozen h15-gross-low h0.25-vs-h0.15 advantage into 24h segments and test whether continuing the strong hedge remains beneficial after the frozen raw gate clears at the next daily decision",
        "threshold": THRESHOLD,
        "threshold_source": "R66 first-60% training, unchanged",
        "trigger_count": int(len(frame)),
        "segments": segments,
        "conditional": conditional,
        "conditional_folds": cond_folds,
        "disclosure": "Diagnostic only. The gate threshold is frozen; future equity is used only to measure segment advantage. No persistence duration or exit rule is promoted here. Frozen V99 and paper remain untouched.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "segments": segments, "conditional": conditional}, indent=2), flush=True)


if __name__ == "__main__":
    main()
