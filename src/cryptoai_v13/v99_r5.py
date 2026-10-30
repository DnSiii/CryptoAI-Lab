from __future__ import annotations

import pandas as pd

from .data import FuturesData
from .v99 import V99AsymmetricSpec, _cap_gross, _clean_trend
from .v99_r3 import V99R3ControlSpec, _directional_stress, _side_low_churn_factor


def asymmetric_v99_targets_r5(
    data: FuturesData,
    targets: pd.DataFrame,
    proxy_equity: pd.Series,
    spec: V99AsymmetricSpec,
    control: V99R3ControlSpec,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Minimal asymmetric challenger.

    R5 intentionally removes chop, extension and portfolio-shock intervention.
    It changes parent exposure only when a broad systemic move is confirmed,
    and only on the side fighting that move. Clean aligned trends may receive a
    modest boost. This small hypothesis surface is deliberately harder to
    overfit than the earlier V99 variants.
    """
    _ = proxy_equity
    raw = targets.reindex(index=data.close.index, columns=data.close.columns).fillna(0.0)
    close = data.close.reindex_like(raw)
    if spec.market_symbol not in close.columns:
        raise ValueError(f"V99 market symbol {spec.market_symbol} is unavailable")
    market = close[spec.market_symbol]

    long_stress, short_stress, stress_diag = _directional_stress(market, close, spec, control)
    clean_up, clean_down, trend_diag = _clean_trend(market, close, spec)

    long_factor = _side_low_churn_factor(
        long_stress,
        clean_up.fillna(False),
        control.neutral_recovery_hours,
    ).rename("long_risk_factor")
    short_factor = _side_low_churn_factor(
        short_stress,
        clean_down.fillna(False),
        control.neutral_recovery_hours,
    ).rename("short_risk_factor")

    transformed = raw.clip(lower=0.0).mul(long_factor, axis=0) + raw.clip(upper=0.0).mul(short_factor, axis=0)
    long_boost = clean_up.fillna(False) & long_factor.ge(0.999)
    short_boost = clean_down.fillna(False) & short_factor.ge(0.999)
    if long_boost.any():
        part = transformed.loc[long_boost]
        transformed.loc[long_boost] = part.where(part.le(0.0), part * spec.clean_trend_boost)
    if short_boost.any():
        part = transformed.loc[short_boost]
        transformed.loc[short_boost] = part.where(part.ge(0.0), part * spec.clean_trend_boost)
    transformed = _cap_gross(transformed, spec.maximum_gross)

    risk_factor = pd.concat([long_factor, short_factor], axis=1).min(axis=1).rename("risk_factor")
    diagnostics = pd.concat(
        [
            stress_diag,
            trend_diag,
            long_factor,
            short_factor,
            risk_factor,
            long_stress.rename("long_desired_risk_factor"),
            short_stress.rename("short_desired_risk_factor"),
            pd.concat([long_stress, short_stress], axis=1).min(axis=1).rename("desired_risk_factor"),
            long_boost.rename("long_boost_ready"),
            short_boost.rename("short_boost_ready"),
            (long_boost | short_boost).rename("boost_ready"),
            transformed.abs().sum(axis=1).rename("gross"),
        ],
        axis=1,
    )
    # Compatibility diagnostics for the mature reporting framework. These are
    # intentionally inert in R5.
    diagnostics["chop_active"] = False
    diagnostics["damage_factor"] = 1.0
    diagnostics["damage_state"] = "normal"
    diagnostics["smoothed_loss_fraction"] = 0.0
    diagnostics["chop_blocked_count"] = 0
    diagnostics["extension_blocked_count"] = 0
    return transformed, diagnostics
