from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from .data import FuturesData
from .signals import StrategySpec, build_targets


@dataclass(frozen=True)
class ConvexCaptureSpec:
    """Causal multi-speed directional capture for the V16 research gate.

    V16 deliberately does not inherit the permanent BTC/ETH concentration of
    V14/V15.  It blends two independently stopped impulse horizons with a
    slower trend sleeve, then scales direction from BTC *and* market breadth.
    Every input is known at close t and can execute only at open t+1.
    """

    fast_lookback: int = 24
    slow_lookback: int = 72
    rebalance_hours: int = 3
    top_n: int = 2
    fast_threshold: float = 0.0125
    slow_threshold: float = 0.025
    fast_volume_multiple: float = 1.5
    slow_volume_multiple: float = 1.25
    volume_fast_hours: int = 12
    volume_baseline_hours: int = 168
    volatility_lookback_hours: int = 168
    signal_volatility_target: float = 0.90
    sleeve_leverage_cap: float = 1.25
    trend_fast_hours: int = 24
    trend_slow_hours: int = 336
    trend_threshold: float = 0.004
    stop_loss: float = 0.03
    trailing_stop: float = 0.14
    fast_max_holding_hours: int = 96
    slow_max_holding_hours: int = 240
    cooldown_hours: int = 12
    fast_weight: float = 0.45
    slow_weight: float = 0.35
    trend_weight: float = 0.20
    breadth_lookback_hours: int = 72
    bull_breadth: float = 0.58
    bear_breadth: float = 0.42
    aligned_multiplier: float = 1.35
    countertrend_multiplier: float = 0.35
    neutral_multiplier: float = 0.70
    minimum_conviction: float = 0.55
    maximum_conviction: float = 1.45

    def __post_init__(self) -> None:
        if self.fast_lookback <= 1 or self.slow_lookback <= self.fast_lookback:
            raise ValueError("slow_lookback must exceed fast_lookback")
        if self.top_n <= 0 or self.rebalance_hours <= 0:
            raise ValueError("top_n and rebalance_hours must be positive")
        if not np.isclose(
            self.fast_weight + self.slow_weight + self.trend_weight, 1.0
        ):
            raise ValueError("V16 sleeve weights must sum to one")
        if not 0.0 < self.bear_breadth < self.bull_breadth < 1.0:
            raise ValueError("invalid breadth boundaries")
        if not 0.0 <= self.countertrend_multiplier <= self.aligned_multiplier:
            raise ValueError("invalid direction multipliers")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class AdaptiveTrendSpec:
    """Intermediate-frequency long/short trend portfolio for V16 research."""

    bar_hours: int = 6
    momentum_bars: int = 8
    entry_threshold: float = 0.035
    atr_bars: int = 14
    atr_multiplier: float = 2.5
    selection_days: int = 30
    long_candidates: int = 12
    short_candidates: int = 12
    long_count: int = 5
    short_count: int = 3
    long_sharpe_threshold: float = 0.5
    short_sharpe_threshold: float = 0.8
    long_fraction: float = 0.70
    maximum_gross: float = 1.85

    def __post_init__(self) -> None:
        if self.bar_hours <= 0 or self.momentum_bars <= 1 or self.atr_bars <= 1:
            raise ValueError("invalid AdaptiveTrend lookback")
        if not 0.5 <= self.long_fraction < 1.0:
            raise ValueError("long_fraction must be between 0.5 and 1")
        if min(self.long_count, self.short_count, self.long_candidates, self.short_candidates) <= 0:
            raise ValueError("candidate and position counts must be positive")
        if self.maximum_gross <= 0.0 or self.atr_multiplier <= 0.0:
            raise ValueError("gross and ATR multiplier must be positive")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RegimeSwitchSpec:
    """Causal market-regime allocation between attack and defense sleeves."""

    momentum_hours: int = 24 * 45
    fast_ema_hours: int = 24 * 14
    slow_ema_hours: int = 24 * 90
    breadth_hours: int = 24 * 30
    bull_momentum: float = 0.08
    bear_momentum: float = -0.08
    bull_breadth: float = 0.55
    bear_breadth: float = 0.45
    shock_hours: int = 24 * 7
    shock_return: float = -0.10
    bull_attack: float = 1.00
    neutral_attack: float = 0.70
    bear_attack: float = 0.20
    bull_core: float = 0.15
    neutral_core: float = 0.55
    bear_core: float = 1.00
    rebalance_hours: int = 24
    maximum_gross: float = 1.85

    def __post_init__(self) -> None:
        if min(
            self.momentum_hours,
            self.fast_ema_hours,
            self.slow_ema_hours,
            self.breadth_hours,
            self.shock_hours,
            self.rebalance_hours,
        ) <= 0:
            raise ValueError("regime lookbacks and rebalance must be positive")
        if self.fast_ema_hours >= self.slow_ema_hours:
            raise ValueError("fast EMA must be shorter than slow EMA")
        if not self.bear_momentum < self.bull_momentum:
            raise ValueError("bear momentum must be below bull momentum")
        if not 0.0 < self.bear_breadth < self.bull_breadth < 1.0:
            raise ValueError("invalid regime breadth boundaries")
        if min(
            self.bull_attack,
            self.neutral_attack,
            self.bear_attack,
            self.bull_core,
            self.neutral_core,
            self.bear_core,
        ) < 0.0:
            raise ValueError("regime sleeve weights cannot be negative")
        if self.maximum_gross <= 0.0:
            raise ValueError("maximum_gross must be positive")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _cap_gross(targets: pd.DataFrame, maximum_gross: float) -> pd.DataFrame:
    gross = targets.abs().sum(axis=1)
    scale = (
        maximum_gross / gross.replace(0.0, np.nan)
    ).clip(upper=1.0).fillna(0.0)
    return targets.mul(scale, axis=0).fillna(0.0)


def regime_switch_targets(
    core_targets: pd.DataFrame,
    attack_targets: pd.DataFrame,
    close: pd.DataFrame,
    spec: RegimeSwitchSpec,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Use the convex sleeve only when the closed market regime supports it.

    The regime at close ``t`` is built solely from prices available at ``t``.
    The replay engine executes the resulting target no earlier than the next
    hourly open.  A seven-day shock can force the defensive state even while
    the slower trend has not yet rolled over.
    """

    if "BTCUSDT" not in close.columns:
        raise ValueError("BTCUSDT is required for the V16 market regime")
    aligned_close = close.reindex(core_targets.index)
    btc = aligned_close["BTCUSDT"]
    momentum = btc.div(btc.shift(spec.momentum_hours)).sub(1.0)
    shock = btc.div(btc.shift(spec.shock_hours)).sub(1.0)
    fast = btc.ewm(
        span=spec.fast_ema_hours,
        adjust=False,
        min_periods=spec.fast_ema_hours,
    ).mean()
    slow = btc.ewm(
        span=spec.slow_ema_hours,
        adjust=False,
        min_periods=spec.slow_ema_hours,
    ).mean()
    asset_return = aligned_close.div(
        aligned_close.shift(spec.breadth_hours)
    ).sub(1.0)
    breadth = (asset_return > 0.0).where(aligned_close.notna()).mean(axis=1)

    bull = (
        (momentum >= spec.bull_momentum)
        & (fast > slow)
        & (breadth >= spec.bull_breadth)
    )
    bear = (
        (momentum <= spec.bear_momentum)
        | ((fast < slow) & (breadth <= spec.bear_breadth))
        | (shock <= spec.shock_return)
    )
    regime = pd.Series("neutral", index=core_targets.index, dtype="object")
    regime.loc[bull] = "bull"
    regime.loc[bear] = "bear"

    attack_weight = pd.Series(spec.neutral_attack, index=regime.index)
    core_weight = pd.Series(spec.neutral_core, index=regime.index)
    attack_weight.loc[regime.eq("bull")] = spec.bull_attack
    core_weight.loc[regime.eq("bull")] = spec.bull_core
    attack_weight.loc[regime.eq("bear")] = spec.bear_attack
    core_weight.loc[regime.eq("bear")] = spec.bear_core

    event = pd.Series(
        np.arange(len(regime)) % spec.rebalance_hours == 0,
        index=regime.index,
    )
    attack_weight = attack_weight.where(event).ffill().fillna(spec.neutral_attack)
    core_weight = core_weight.where(event).ffill().fillna(spec.neutral_core)
    effective_regime = regime.where(event).ffill().fillna("neutral")
    core = core_targets.fillna(0.0).mul(core_weight, axis=0)
    attack = attack_targets.reindex_like(core_targets).fillna(0.0).mul(
        attack_weight, axis=0
    )
    targets = _cap_gross(core.add(attack, fill_value=0.0), spec.maximum_gross)
    diagnostics = pd.DataFrame(
        {
            "momentum": momentum,
            "shock_return": shock,
            "breadth": breadth,
            "regime": effective_regime,
            "attack_weight": attack_weight,
            "core_weight": core_weight,
            "gross": targets.abs().sum(axis=1),
        },
        index=targets.index,
    )
    return targets, diagnostics


def drawdown_regime_reentry_targets(
    targets: pd.DataFrame,
    proxy_equity: pd.Series,
    regime: pd.Series,
    *,
    drawdown_threshold: float,
    defensive_multiplier: float,
    reentry_return_hours: int,
    reentry_return: float,
    minimum_defensive_hours: int,
    rebalance_hours: int,
    maximum_gross: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Cut after a closed-equity loss and reattack on market confirmation.

    Unlike a fixed cooldown, the defensive state cannot expire merely because
    time passed.  Unlike equity-only recovery, it need not wait for a reduced
    sleeve to grind all the way back to its former peak.  Re-entry requires a
    confirmed bull regime and positive closed proxy performance, after which
    a new causal high-water cycle starts.
    """

    if not 0.0 < drawdown_threshold < 1.0:
        raise ValueError("drawdown_threshold must be a fraction")
    if not 0.0 <= defensive_multiplier <= 1.0:
        raise ValueError("defensive_multiplier must be between zero and one")
    if min(
        reentry_return_hours,
        minimum_defensive_hours,
        rebalance_hours,
    ) <= 0 or maximum_gross <= 0.0:
        raise ValueError("reentry, rebalance and gross parameters must be positive")

    equity = proxy_equity.reindex(targets.index).ffill()
    market_regime = regime.reindex(targets.index).ffill().fillna("neutral")
    recovery_return = equity.div(equity.shift(reentry_return_hours)).sub(1.0)
    factors = np.ones(len(targets), dtype=float)
    states: list[str] = []
    local_drawdowns = np.zeros(len(targets), dtype=float)
    defensive = False
    defensive_since = -1
    local_peak = np.nan
    factor = 1.0
    for row in range(len(targets)):
        value = float(equity.iloc[row]) if np.isfinite(equity.iloc[row]) else np.nan
        if np.isfinite(value):
            if not np.isfinite(local_peak):
                local_peak = value
            if not defensive:
                local_peak = max(local_peak, value)
            drawdown = value / local_peak - 1.0 if local_peak > 0.0 else 0.0
        else:
            drawdown = 0.0
        local_drawdowns[row] = drawdown
        if row % rebalance_hours == 0 and np.isfinite(value):
            if not defensive and drawdown <= -drawdown_threshold:
                defensive = True
                defensive_since = row
                factor = defensive_multiplier
            elif defensive:
                elapsed = row - defensive_since
                confirmed = (
                    market_regime.iloc[row] == "bull"
                    and np.isfinite(recovery_return.iloc[row])
                    and recovery_return.iloc[row] >= reentry_return
                )
                if elapsed >= minimum_defensive_hours and confirmed:
                    defensive = False
                    local_peak = value
                    factor = 1.0
        factors[row] = factor
        states.append("defensive" if defensive else "attack")

    factor_series = pd.Series(factors, index=targets.index)
    shielded = _cap_gross(targets.mul(factor_series, axis=0), maximum_gross)
    diagnostics = pd.DataFrame(
        {
            "proxy_drawdown": local_drawdowns,
            "recovery_return": recovery_return,
            "regime": market_regime,
            "risk_state": states,
            "risk_factor": factor_series,
            "gross": shielded.abs().sum(axis=1),
        },
        index=targets.index,
    )
    return shielded, diagnostics


def rolling_loss_limiter_targets(
    targets: pd.DataFrame,
    proxy_equity: pd.Series,
    *,
    short_hours: int,
    medium_hours: int,
    short_loss: float,
    medium_loss: float,
    short_multiplier: float,
    medium_multiplier: float,
    rebalance_hours: int,
    maximum_gross: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Reduce only while recent closed losses remain outside tolerance."""

    if min(short_hours, medium_hours, rebalance_hours) <= 0:
        raise ValueError("loss-limiter lookbacks must be positive")
    if not 0.0 < short_loss < medium_loss < 1.0:
        raise ValueError("loss thresholds must be ordered positive fractions")
    if not 0.0 <= short_multiplier <= medium_multiplier <= 1.0:
        raise ValueError("loss multipliers must be ordered within zero and one")
    if maximum_gross <= 0.0:
        raise ValueError("maximum_gross must be positive")

    equity = proxy_equity.reindex(targets.index).ffill()
    short_return = equity.div(equity.shift(short_hours)).sub(1.0)
    medium_return = equity.div(equity.shift(medium_hours)).sub(1.0)
    factor = pd.Series(1.0, index=targets.index)
    factor.loc[medium_return <= -medium_loss] = medium_multiplier
    factor.loc[short_return <= -short_loss] = short_multiplier
    event = pd.Series(
        np.arange(len(factor)) % rebalance_hours == 0,
        index=factor.index,
    )
    factor = factor.where(event).ffill().fillna(1.0)
    limited = _cap_gross(targets.mul(factor, axis=0), maximum_gross)
    diagnostics = pd.DataFrame(
        {
            "short_return": short_return,
            "medium_return": medium_return,
            "risk_factor": factor,
            "gross": limited.abs().sum(axis=1),
        },
        index=targets.index,
    )
    return limited, diagnostics


def regime_hedged_targets(
    targets: pd.DataFrame,
    regime: pd.Series,
    *,
    neutral_net_cap: float,
    bear_net_target: float,
    hedge_symbols: tuple[str, ...] = ("BTCUSDT", "ETHUSDT"),
    maximum_gross: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Add a liquid short hedge only when closed regime evidence requires it."""

    if neutral_net_cap < 0.0:
        raise ValueError("neutral_net_cap cannot be negative")
    if bear_net_target > 0.0:
        raise ValueError("bear_net_target must be zero or negative")
    if maximum_gross <= 0.0:
        raise ValueError("maximum_gross must be positive")
    missing = [symbol for symbol in hedge_symbols if symbol not in targets.columns]
    if missing:
        raise ValueError(f"missing hedge symbols: {missing}")

    market_regime = regime.reindex(targets.index).ffill().fillna("neutral")
    hedged = targets.fillna(0.0).copy()
    raw_net = hedged.sum(axis=1)
    desired_net = raw_net.copy()
    neutral = market_regime.eq("neutral")
    bear = market_regime.eq("bear")
    desired_net.loc[neutral] = np.minimum(
        desired_net.loc[neutral], neutral_net_cap
    )
    desired_net.loc[bear] = bear_net_target
    hedge_amount = (raw_net - desired_net).clip(lower=0.0)
    per_symbol = hedge_amount / len(hedge_symbols)
    for symbol in hedge_symbols:
        hedged[symbol] = hedged[symbol].sub(per_symbol, fill_value=0.0)
    hedged = _cap_gross(hedged, maximum_gross)
    diagnostics = pd.DataFrame(
        {
            "regime": market_regime,
            "raw_net": raw_net,
            "requested_net": desired_net,
            "hedge_gross": hedge_amount,
            "net": hedged.sum(axis=1),
            "gross": hedged.abs().sum(axis=1),
        },
        index=targets.index,
    )
    return hedged, diagnostics


def three_regime_sleeve_targets(
    core_targets: pd.DataFrame,
    attack_targets: pd.DataFrame,
    bear_short_targets: pd.DataFrame,
    regime: pd.Series,
    *,
    bull_attack: float,
    bull_core: float,
    neutral_attack: float,
    neutral_core: float,
    bear_short: float,
    bear_core: float,
    maximum_gross: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Select attack, defense or signal-confirmed shorts by closed regime."""

    weights = (
        bull_attack,
        bull_core,
        neutral_attack,
        neutral_core,
        bear_short,
        bear_core,
    )
    if min(weights) < 0.0 or maximum_gross <= 0.0:
        raise ValueError("sleeve weights and maximum_gross must be non-negative")
    market_regime = regime.reindex(core_targets.index).ffill().fillna("neutral")
    core = core_targets.fillna(0.0)
    attack = attack_targets.reindex_like(core).fillna(0.0)
    short_only = bear_short_targets.reindex_like(core).fillna(0.0).clip(upper=0.0)
    combined = pd.DataFrame(0.0, index=core.index, columns=core.columns)
    bull = market_regime.eq("bull")
    neutral = market_regime.eq("neutral")
    bear = market_regime.eq("bear")
    combined.loc[bull] = (
        attack.loc[bull] * bull_attack + core.loc[bull] * bull_core
    )
    combined.loc[neutral] = (
        attack.loc[neutral] * neutral_attack
        + core.loc[neutral] * neutral_core
    )
    combined.loc[bear] = (
        short_only.loc[bear] * bear_short + core.loc[bear] * bear_core
    )
    combined = _cap_gross(combined, maximum_gross)
    diagnostics = pd.DataFrame(
        {
            "regime": market_regime,
            "short_signal_gross": short_only.abs().sum(axis=1),
            "net": combined.sum(axis=1),
            "gross": combined.abs().sum(axis=1),
        },
        index=combined.index,
    )
    return combined, diagnostics


def _impulse_spec(spec: ConvexCaptureSpec, *, slow: bool) -> StrategySpec:
    return StrategySpec(
        family="impulse",
        lookback=spec.slow_lookback if slow else spec.fast_lookback,
        rebalance=spec.rebalance_hours,
        top_n=spec.top_n,
        fast=spec.volume_fast_hours,
        slow=spec.volume_baseline_hours,
        vol_lookback=spec.volatility_lookback_hours,
        vol_target=spec.signal_volatility_target,
        leverage_cap=spec.sleeve_leverage_cap,
        long_short_balance=0.5,
        threshold=spec.slow_threshold if slow else spec.fast_threshold,
        volume_multiple=(
            spec.slow_volume_multiple if slow else spec.fast_volume_multiple
        ),
        stop_loss=spec.stop_loss,
        trailing_stop=spec.trailing_stop,
        max_holding=(
            spec.slow_max_holding_hours if slow else spec.fast_max_holding_hours
        ),
        trend_filter_hours=spec.trend_slow_hours,
        cooldown_hours=spec.cooldown_hours,
    )


def adaptive_trend_targets(
    data: FuturesData,
    spec: AdaptiveTrendSpec,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build causal H6 trend targets with monthly trailing selection.

    Monthly membership uses only the prior rolling window observed at that
    month's first available close.  Position changes are decided on completed
    H6 bars and are therefore executed no earlier than the next H1 open by the
    replay engine.  Stops are close-confirmed; no ideal intrabar fill is used.
    """

    rule = f"{spec.bar_hours}h"
    # Label every aggregate at its *ending* timestamp.  A bar stamped 06:00
    # may use information through 06:00, never from 07:00-11:00.
    resample_args = {"label": "right", "closed": "right"}
    close = data.frames["close"].resample(rule, **resample_args).last()
    high = data.frames["high"].resample(rule, **resample_args).max()
    low = data.frames["low"].resample(rule, **resample_args).min()
    quote_volume = data.frames["quote_volume"].resample(
        rule, **resample_args
    ).sum(min_count=1)
    previous_close = close.shift(1)
    true_range = pd.DataFrame(
        np.maximum.reduce([
            high.sub(low).to_numpy(),
            high.sub(previous_close).abs().to_numpy(),
            low.sub(previous_close).abs().to_numpy(),
        ]),
        index=close.index,
        columns=close.columns,
    )
    atr = true_range.rolling(spec.atr_bars, min_periods=spec.atr_bars).mean()
    momentum = close.div(close.shift(spec.momentum_bars)).sub(1.0)
    returns = close.pct_change()
    selection_bars = max(4, spec.selection_days * 24 // spec.bar_hours)
    mean = returns.rolling(selection_bars, min_periods=selection_bars // 2).mean()
    volatility = returns.rolling(selection_bars, min_periods=selection_bars // 2).std()
    sharpe = mean.div(volatility.replace(0.0, np.nan)).mul(
        np.sqrt(365.25 * 24 / spec.bar_hours)
    )
    liquidity = quote_volume.rolling(
        selection_bars,
        min_periods=selection_bars // 2,
    ).mean()

    month = pd.Series(close.index.strftime("%Y-%m"), index=close.index)
    month_start = month.ne(month.shift(1))
    liquid_rank = liquidity.rank(axis=1, ascending=False, method="first")
    long_score = sharpe.where(liquid_rank <= spec.long_candidates)
    short_score = sharpe.where(liquid_rank <= spec.short_candidates)
    long_members = long_score.rank(axis=1, ascending=False, method="first") <= spec.long_candidates
    short_members = short_score.rank(axis=1, ascending=True, method="first") <= spec.short_candidates
    long_members = long_members.astype(float).where(month_start, np.nan).ffill().fillna(0.0).astype(bool)
    short_members = short_members.astype(float).where(month_start, np.nan).ffill().fillna(0.0).astype(bool)

    long_entry_score = momentum.where(
        long_members & (sharpe >= spec.long_sharpe_threshold)
        & (momentum >= spec.entry_threshold)
    )
    short_entry_score = momentum.where(
        short_members & (sharpe <= -spec.short_sharpe_threshold)
        & (momentum <= -spec.entry_threshold)
    )
    long_entry = long_entry_score.rank(axis=1, ascending=False, method="first") <= spec.long_count
    short_entry = short_entry_score.rank(axis=1, ascending=True, method="first") <= spec.short_count

    state = np.zeros(close.shape[1], dtype=np.int8)
    trail = np.full(close.shape[1], np.nan, dtype=float)
    raw = np.zeros(close.shape, dtype=float)
    close_values = close.to_numpy(dtype=float)
    atr_values = atr.to_numpy(dtype=float)
    long_values = long_entry.to_numpy(dtype=bool)
    short_values = short_entry.to_numpy(dtype=bool)
    long_member_values = long_members.to_numpy(dtype=bool)
    short_member_values = short_members.to_numpy(dtype=bool)
    for row in range(len(close)):
        prices = close_values[row]
        distances = atr_values[row] * spec.atr_multiplier
        valid = np.isfinite(prices) & np.isfinite(distances) & (distances > 0.0)
        for column in range(close.shape[1]):
            if not valid[column]:
                state[column] = 0
                trail[column] = np.nan
                continue
            price_now = prices[column]
            if state[column] > 0:
                if not long_member_values[row, column]:
                    state[column] = 0
                    trail[column] = np.nan
                else:
                    trail[column] = max(trail[column], price_now - distances[column])
                    if price_now <= trail[column]:
                        state[column] = 0
                        trail[column] = np.nan
            elif state[column] < 0:
                if not short_member_values[row, column]:
                    state[column] = 0
                    trail[column] = np.nan
                else:
                    trail[column] = min(trail[column], price_now + distances[column])
                    if price_now >= trail[column]:
                        state[column] = 0
                        trail[column] = np.nan
            if state[column] == 0:
                if long_values[row, column]:
                    state[column] = 1
                    trail[column] = price_now - distances[column]
                elif short_values[row, column]:
                    state[column] = -1
                    trail[column] = price_now + distances[column]
        long_active = state > 0
        short_active = state < 0
        if long_active.any():
            raw[row, long_active] = (
                spec.maximum_gross * spec.long_fraction / long_active.sum()
            )
        if short_active.any():
            raw[row, short_active] = -(
                spec.maximum_gross * (1.0 - spec.long_fraction) / short_active.sum()
            )

    h6_targets = pd.DataFrame(raw, index=close.index, columns=close.columns)
    targets = h6_targets.reindex(data.close.index).ffill().fillna(0.0)
    diagnostics = pd.DataFrame(
        {
            "gross": targets.abs().sum(axis=1),
            "net": targets.sum(axis=1),
            "long_positions": targets.gt(0.0).sum(axis=1),
            "short_positions": targets.lt(0.0).sum(axis=1),
        },
        index=targets.index,
    )
    return targets, diagnostics


def convex_capture_targets(
    data: FuturesData,
    spec: ConvexCaptureSpec,
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """Return V16 opportunity targets, regime labels and diagnostics."""

    fast = build_targets(data, _impulse_spec(spec, slow=False))
    slow = build_targets(data, _impulse_spec(spec, slow=True))
    trend = build_targets(
        data,
        StrategySpec(
            family="trend",
            lookback=spec.slow_lookback,
            rebalance=max(3, spec.rebalance_hours),
            fast=spec.trend_fast_hours,
            slow=spec.trend_slow_hours,
            vol_lookback=spec.volatility_lookback_hours,
            vol_target=spec.signal_volatility_target,
            leverage_cap=spec.sleeve_leverage_cap,
            threshold=spec.trend_threshold,
        ),
    )
    blended = (
        fast * spec.fast_weight
        + slow * spec.slow_weight
        + trend * spec.trend_weight
    )

    close = data.close
    btc = close["BTCUSDT"]
    btc_fast = btc.ewm(
        span=spec.trend_fast_hours,
        adjust=False,
        min_periods=spec.trend_fast_hours,
    ).mean()
    btc_slow = btc.ewm(
        span=spec.trend_slow_hours,
        adjust=False,
        min_periods=spec.trend_slow_hours,
    ).mean()
    asset_return = close.div(close.shift(spec.breadth_lookback_hours)).sub(1.0)
    breadth = (asset_return > 0.0).where(close.notna()).mean(axis=1)
    bull = (btc_fast > btc_slow) & (breadth >= spec.bull_breadth)
    bear = (btc_fast < btc_slow) & (breadth <= spec.bear_breadth)
    regime = pd.Series("neutral", index=close.index, dtype="object")
    regime.loc[bull] = "bull"
    regime.loc[bear] = "bear"

    long_factor = pd.Series(spec.neutral_multiplier, index=close.index)
    short_factor = pd.Series(spec.neutral_multiplier, index=close.index)
    long_factor.loc[bull] = spec.aligned_multiplier
    short_factor.loc[bull] = spec.countertrend_multiplier
    long_factor.loc[bear] = spec.countertrend_multiplier
    short_factor.loc[bear] = spec.aligned_multiplier

    market_strength = btc_fast.div(btc_slow).sub(1.0).abs()
    breadth_strength = breadth.sub(0.5).abs().mul(2.0)
    conviction = (
        0.55
        + market_strength.div(0.08).clip(0.0, 1.0) * 0.50
        + breadth_strength.clip(0.0, 1.0) * 0.40
    ).clip(spec.minimum_conviction, spec.maximum_conviction)
    directed = (
        blended.clip(lower=0.0).mul(long_factor, axis=0)
        + blended.clip(upper=0.0).mul(short_factor, axis=0)
    ).mul(conviction, axis=0)
    targets = _cap_gross(directed, spec.sleeve_leverage_cap)
    diagnostics = pd.DataFrame(
        {
            "breadth": breadth,
            "market_strength": market_strength,
            "conviction": conviction,
            "opportunity_gross": targets.abs().sum(axis=1),
        },
        index=close.index,
    )
    return targets, regime, diagnostics


def combine_convex_with_core(
    core_targets: pd.DataFrame,
    opportunity_targets: pd.DataFrame,
    *,
    core_fraction: float,
    maximum_portfolio_gross: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Allocate V16 without forcing the old core to dominate every regime."""

    if not 0.0 <= core_fraction <= 1.0:
        raise ValueError("core_fraction must be between zero and one")
    if maximum_portfolio_gross <= 0.0:
        raise ValueError("maximum_portfolio_gross must be positive")
    core = core_targets.mul(core_fraction).fillna(0.0)
    opportunity = opportunity_targets.reindex_like(core).fillna(0.0)
    core_gross = core.abs().sum(axis=1)
    if bool((core_gross > maximum_portfolio_gross + 1e-12).any()):
        raise ValueError("scaled core exceeds the V16 gross limit")
    spare = (maximum_portfolio_gross - core_gross).clip(lower=0.0)
    requested = opportunity.abs().sum(axis=1)
    scale = (spare / requested.replace(0.0, np.nan)).clip(upper=1.0).fillna(0.0)
    allocated = opportunity.mul(scale, axis=0)
    combined = core.add(allocated, fill_value=0.0)
    if bool((combined.abs().sum(axis=1) > maximum_portfolio_gross + 1e-10).any()):
        raise AssertionError("V16 exceeded maximum_portfolio_gross")
    return combined, allocated


def adaptive_equity_shield(
    targets: pd.DataFrame,
    proxy_equity: pd.Series,
    *,
    short_hours: int,
    long_hours: int,
    peak_hours: int,
    warning_drawdown: float,
    hard_drawdown: float,
    attack_multiplier: float,
    neutral_multiplier: float,
    weak_multiplier: float,
    hard_multiplier: float,
    shock_return: float,
    rebalance_hours: int,
    maximum_gross: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Scale a candidate from its own *closed* equity history.

    The shield is deliberately asymmetric: it permits convex exposure while
    both horizons are positive, but cuts quickly after a loss shock or a
    rolling drawdown.  Inputs observed at close ``t`` only affect a target
    that the replay can execute at the following open.
    """

    if not 0.0 < warning_drawdown < hard_drawdown < 1.0:
        raise ValueError("drawdown thresholds must be ordered fractions")
    if rebalance_hours <= 0 or maximum_gross <= 0.0:
        raise ValueError("rebalance_hours and maximum_gross must be positive")
    equity = proxy_equity.reindex(targets.index).ffill()
    short_return = equity.div(equity.shift(short_hours)).sub(1.0)
    long_return = equity.div(equity.shift(long_hours)).sub(1.0)
    one_day_return = equity.div(equity.shift(24)).sub(1.0)
    peak = equity.rolling(
        peak_hours,
        min_periods=max(24 * 7, peak_hours // 4),
    ).max()
    drawdown = equity.div(peak).sub(1.0)

    factor = pd.Series(neutral_multiplier, index=targets.index, dtype=float)
    strong = (short_return > 0.0) & (long_return > 0.0)
    weak = (short_return < 0.0) & (long_return < 0.0)
    factor.loc[strong] = attack_multiplier
    factor.loc[weak] = weak_multiplier
    factor.loc[drawdown <= -warning_drawdown] = np.minimum(
        factor.loc[drawdown <= -warning_drawdown], weak_multiplier
    )
    hard = (drawdown <= -hard_drawdown) | (one_day_return <= -abs(shock_return))
    factor.loc[hard] = hard_multiplier

    event = pd.Series(
        np.arange(len(factor)) % rebalance_hours == 0,
        index=factor.index,
    )
    factor = factor.where(event, np.nan).ffill().fillna(0.0)
    shielded = targets.mul(factor, axis=0)
    gross = shielded.abs().sum(axis=1)
    cap = (maximum_gross / gross.replace(0.0, np.nan)).clip(upper=1.0).fillna(0.0)
    shielded = shielded.mul(cap, axis=0).fillna(0.0)
    diagnostics = pd.DataFrame(
        {
            "short_return": short_return,
            "long_return": long_return,
            "one_day_return": one_day_return,
            "drawdown": drawdown,
            "risk_factor": factor,
            "gross": shielded.abs().sum(axis=1),
        },
        index=targets.index,
    )
    return shielded, diagnostics
