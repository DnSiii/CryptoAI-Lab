from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r36_safe_core_router as r36


def combine_router_next_open(
    v15_equity: pd.Series,
    v16_equity: pd.Series,
    safe_active: pd.Series,
    safe_weight: float,
    transfer_cost_per_side: float,
) -> tuple[pd.Series, pd.Series, float]:
    """Route at the next open: close-t signal sets capital before interval t+1."""
    aligned = pd.concat(
        [v15_equity.rename("v15"), v16_equity.rename("v16"), safe_active.rename("safe")],
        axis=1,
        join="inner",
    ).dropna(subset=["v15", "v16"])
    r15 = aligned["v15"].pct_change(fill_method=None).fillna(0.0)
    r16 = aligned["v16"].pct_change(fill_method=None).fillna(0.0)
    desired = (
        aligned["safe"].fillna(False).astype(float).shift(1).fillna(0.0)
        * float(safe_weight)
    )

    cap15 = 1.0
    cap16 = 0.0
    equity = pd.Series(index=aligned.index, dtype=float)
    realized = pd.Series(index=aligned.index, dtype=float)
    equity.iloc[0] = 1.0
    realized.iloc[0] = 0.0
    transfer_cost_total = 0.0

    for i in range(1, len(aligned)):
        total_before = cap15 + cap16
        if total_before <= 0.0:
            equity.iloc[i:] = 0.0
            realized.iloc[i:] = 0.0
            break

        wanted = float(desired.iloc[i])
        current = cap16 / total_before
        if abs(current - wanted) > 1e-10:
            moved = abs(current - wanted)
            cost = total_before * moved * 2.0 * float(transfer_cost_per_side)
            transfer_cost_total += cost
            total_after_cost = max(0.0, total_before - cost)
            cap16 = total_after_cost * wanted
            cap15 = total_after_cost * (1.0 - wanted)

        cap15 *= 1.0 + float(r15.iloc[i])
        cap16 *= 1.0 + float(r16.iloc[i])
        total_after_return = cap15 + cap16
        equity.iloc[i] = total_after_return
        realized.iloc[i] = cap16 / max(total_after_return, 1e-12)

    return (
        equity.ffill().fillna(1.0),
        realized.ffill().fillna(0.0),
        float(transfer_cost_total),
    )


r36.combine_router = combine_router_next_open

if __name__ == "__main__":
    r36.main()
