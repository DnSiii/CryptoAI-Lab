from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class OpportunityBudget:
    """Independent risk budget for an opportunistic strategy sleeve.

    The frozen core is never rescaled by this allocator.  The opportunity
    sleeve may use only the explicitly reserved gross exposure and the spare
    room below the combined portfolio cap.
    """

    maximum_overlay_gross: float
    maximum_portfolio_gross: float

    def __post_init__(self) -> None:
        if self.maximum_overlay_gross < 0.0:
            raise ValueError("maximum_overlay_gross must be non-negative")
        if self.maximum_portfolio_gross <= 0.0:
            raise ValueError("maximum_portfolio_gross must be positive")


def _row_gross(targets: pd.DataFrame) -> pd.Series:
    return targets.abs().sum(axis=1)


def additive_opportunity_targets(
    core_targets: pd.DataFrame,
    opportunity_targets: pd.DataFrame,
    budget: OpportunityBudget,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Add a bounded opportunity sleeve without diluting the frozen core.

    Both inputs are portfolio weights known at the same signal timestamp.  The
    opportunity sleeve is first limited to its own gross budget and then to the
    conservative spare room under the combined cap.  Opposing positions may
    net after allocation, but that netting is not counted as extra capacity.

    Returns ``(combined_targets, allocated_opportunity_targets)``.
    """

    opportunity_targets = opportunity_targets.reindex(
        index=core_targets.index,
        columns=core_targets.columns,
    ).fillna(0.0)
    core_targets = core_targets.fillna(0.0)

    core_gross = _row_gross(core_targets)
    if bool((core_gross > budget.maximum_portfolio_gross + 1e-12).any()):
        raise ValueError(
            "frozen core exceeds maximum_portfolio_gross; refusing to rescale it"
        )

    requested_gross = _row_gross(opportunity_targets)
    sleeve_scale = (
        budget.maximum_overlay_gross
        / requested_gross.replace(0.0, np.nan)
    ).clip(upper=1.0).fillna(0.0)
    sleeve_limited = opportunity_targets.mul(sleeve_scale, axis=0)

    spare_gross = (budget.maximum_portfolio_gross - core_gross).clip(lower=0.0)
    sleeve_gross = _row_gross(sleeve_limited)
    portfolio_scale = (
        spare_gross / sleeve_gross.replace(0.0, np.nan)
    ).clip(upper=1.0).fillna(0.0)
    allocated = sleeve_limited.mul(portfolio_scale, axis=0)
    combined = core_targets.add(allocated, fill_value=0.0)

    # Allocation is deliberately conservative: gross before cross-sleeve
    # netting is bounded, therefore combined netted gross is bounded as well.
    if bool((_row_gross(combined) > budget.maximum_portfolio_gross + 1e-10).any()):
        raise AssertionError("combined opportunity allocation exceeded gross cap")
    return combined, allocated
