from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from run_v99_r25_trisleeve_meta import cap
import run_v99_r37_crash_shield as r37

REPORT = PROJECT / "reports" / "candidate_v99_r47_band_rebalanced_crash_shield.json"
BAND = 0.05


def combine_band_rebalanced(
    growth_equity: pd.Series,
    v13_equity: pd.Series,
    v16_equity: pd.Series,
    active: pd.Series,
    safe_weight: float,
    mode: str,
    transfer_cost_per_side: float,
) -> tuple[pd.Series, dict]:
    aligned = pd.concat(
        [
            growth_equity.rename("growth"),
            v13_equity.rename("v13"),
            v16_equity.rename("v16"),
            active.rename("active"),
        ],
        axis=1,
        join="inner",
    ).dropna(subset=["growth", "v13", "v16"])

    rg = aligned["growth"].pct_change(fill_method=None).fillna(0.0)
    r13 = aligned["v13"].pct_change(fill_method=None).fillna(0.0)
    r16 = aligned["v16"].pct_change(fill_method=None).fillna(0.0)
    requested_active = aligned["active"].fillna(False).astype(bool).shift(1).fillna(False)

    if mode == "v16":
        choose16 = pd.Series(1.0, index=aligned.index)
    elif mode == "cash":
        choose16 = pd.Series(0.0, index=aligned.index)
    elif mode == "adaptive":
        choose16 = (
            r37.adaptive_safe_choice(aligned["v13"], aligned["v16"])
            .reindex(aligned.index)
            .fillna(1.0)
            .shift(1)
            .fillna(1.0)
        )
    else:
        raise ValueError(mode)

    growth_cap = 1.0
    v13_cap = 0.0
    v16_cap = 0.0
    cash_cap = 0.0
    in_event = False

    equity = pd.Series(index=aligned.index, dtype=float)
    realized_safe = pd.Series(index=aligned.index, dtype=float)
    equity.iloc[0] = 1.0
    realized_safe.iloc[0] = 0.0

    transfer_cost_total = 0.0
    route_changes = 0
    event_entries = 0
    event_exits = 0
    band_rebalances = 0

    def desired_weights(i: int, sw: float) -> np.ndarray:
        if mode == "cash":
            return np.array([1.0 - sw, 0.0, 0.0, sw], dtype=float)
        if mode == "v16":
            return np.array([1.0 - sw, 0.0, sw, 0.0], dtype=float)
        c16 = float(choose16.iloc[i])
        return np.array([1.0 - sw, sw * (1.0 - c16), sw * c16, 0.0], dtype=float)

    def rebalance(desired: np.ndarray) -> None:
        nonlocal growth_cap, v13_cap, v16_cap, cash_cap
        nonlocal transfer_cost_total, route_changes
        total = growth_cap + v13_cap + v16_cap + cash_cap
        if total <= 0.0:
            return
        current = np.array([growth_cap, v13_cap, v16_cap, cash_cap], dtype=float) / total
        moved = 0.5 * float(np.abs(current - desired).sum())
        if moved <= 1e-10:
            return
        route_changes += 1
        cost = total * moved * 2.0 * float(transfer_cost_per_side)
        transfer_cost_total += cost
        total = max(0.0, total - cost)
        growth_cap, v13_cap, v16_cap, cash_cap = (total * desired).tolist()

    for i in range(1, len(aligned)):
        total = growth_cap + v13_cap + v16_cap + cash_cap
        if total <= 0.0:
            equity.iloc[i:] = 0.0
            realized_safe.iloc[i:] = 0.0
            break

        want_event = bool(requested_active.iloc[i])
        sw = float(safe_weight)

        if want_event and not in_event:
            event_entries += 1
            in_event = True
            rebalance(desired_weights(i, sw))
        elif (not want_event) and in_event:
            event_exits += 1
            in_event = False
            rebalance(np.array([1.0, 0.0, 0.0, 0.0], dtype=float))
        elif want_event and in_event:
            current_safe = (v13_cap + v16_cap + cash_cap) / max(total, 1e-12)
            if abs(current_safe - sw) > BAND:
                band_rebalances += 1
                rebalance(desired_weights(i, sw))

        growth_cap *= 1.0 + float(rg.iloc[i])
        v13_cap *= 1.0 + float(r13.iloc[i])
        v16_cap *= 1.0 + float(r16.iloc[i])

        total_after = growth_cap + v13_cap + v16_cap + cash_cap
        equity.iloc[i] = total_after
        realized_safe.iloc[i] = (v13_cap + v16_cap + cash_cap) / max(total_after, 1e-12)

    return equity.ffill().fillna(1.0), {
        "transfer_cost_multiple": float(transfer_cost_total),
        "route_changes": int(route_changes),
        "event_entries": int(event_entries),
        "event_exits": int(event_exits),
        "band_rebalances": int(band_rebalances),
        "band_absolute": BAND,
        "average_safe_weight": float(realized_safe.ffill().fillna(0.0).mean()),
        "maximum_safe_weight": float(realized_safe.ffill().fillna(0.0).max()),
        "execution_policy": "entry/exit rebalance plus maintenance only when realized safe allocation deviates by more than 5 percentage points",
    }


def main() -> None:
    r37.r36.cap = cap
    r37.REPORT = REPORT
    r37.combine_shield = combine_band_rebalanced
    r37.main()

    report = json.loads(REPORT.read_text())
    report["study"] = "V99 R47 5pp band-rebalanced crash shield"
    report["status"] = "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER"
    report["parent"] = "R37 signal/grid with fixed valid cap; R47 changes only capital-routing maintenance policy"
    report["objective"] = (
        "preserve more of R37 continuous crash-tail protection than R46 while avoiding hourly target-weight "
        "maintenance: always rebalance on event entry/exit, and during an active event only when realized safe "
        "allocation drifts more than 5 percentage points from target"
    )
    report["execution_change"] = (
        "Same R37 27-combination signal grid, same next-interval causal timing, same benchmark engines and cost "
        "model. The 5pp maintenance band is fixed before the run and is the only execution change."
    )
    report["grid_policy"] = "same predeclared R37 27-combination grid with a fixed 5pp maintenance band; no signal retuning"
    report["maintenance_band"] = BAND
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
