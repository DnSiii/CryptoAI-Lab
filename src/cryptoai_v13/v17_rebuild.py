"""V17 bounded-concentration research families, never a production approval.

All decisions use closes up to t and execute at t+1 or later. Membership is
applied BEFORE ranks and budgets. No historical target is recomputed using
future universe eligibility. The functions contain no external I/O.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from .data import FuturesData


@dataclass(frozen=True)
class GrowthSpec:
    family: str = "trend"
    fast_hours: int = 168
    slow_hours: int = 672
    rebalance_hours: int = 12
    volatility_hours: int = 720
    minimum_history_hours: int = 720
    liquidity_hours: int = 720
    liquid_top_n: int = 20
    max_positions_per_side: int = 6
    maximum_gross: float = 1.8
    maximum_asset_weight: float = 0.20
    annual_volatility_target: float = 0.45
    score_threshold: float = 0.20
    hourly_shock_limit: float = 0.12
    shock_cooldown_hours: int = 24

    def __post_init__(self):
        if self.family not in {"trend", "relative_momentum", "relative_reversal", "carry", "breakout"}:
            raise ValueError("unknown V17 family")
        if min(self.fast_hours,self.slow_hours,self.rebalance_hours,self.volatility_hours,
               self.minimum_history_hours,self.liquidity_hours,self.liquid_top_n,
               self.max_positions_per_side,self.shock_cooldown_hours) <= 0:
            raise ValueError("lookbacks/counts must be positive")
        if self.fast_hours >= self.slow_hours:
            raise ValueError("fast horizon must be shorter than slow horizon")
        if not 0 < self.maximum_asset_weight <= self.maximum_gross <= 2:
            raise ValueError("invalid bounded exposure")
        if not 0 < self.annual_volatility_target <= 1 or self.score_threshold < 0:
            raise ValueError("invalid risk or conviction")
        if not 0 < self.hourly_shock_limit < 1:
            raise ValueError("invalid shock filter")

    def to_dict(self):
        return asdict(self)


def hold_on_clock(raw: pd.DataFrame, hours: int) -> pd.DataFrame:
    # UTC anchoring survives prefix truncation and changing source start dates.
    utc_hours = raw.index.asi8 // (3_600 * 10**9)
    event = pd.Series(utc_hours % hours == 0, index=raw.index)
    return raw.where(event, np.nan).ffill().fillna(0)


def eligibility(data: FuturesData, spec: GrowthSpec,
                eligible_after: dict[str, str] | None = None) -> pd.DataFrame:
    valid = data.close.notna()
    for field in ("open", "high", "low", "close"):
        valid &= data.frames[field].gt(0) & np.isfinite(data.frames[field])
    qualified = valid.rolling(spec.minimum_history_hours,
                              min_periods=spec.minimum_history_hours).sum().eq(spec.minimum_history_hours)
    # Discovery boundaries are enforced BEFORE cross-sectional selection.
    if eligible_after is not None:
        for symbol in data.symbols:
            boundary = eligible_after.get(symbol)
            if boundary is None:
                qualified[symbol] = False
            else:
                stamp = pd.Timestamp(boundary)
                if stamp.tzinfo is None:
                    raise ValueError("eligibility boundary must have timezone")
                qualified[symbol] &= data.close.index >= stamp
    volume = data.frames["quote_volume"].shift(1).rolling(
        spec.liquidity_hours, min_periods=spec.liquidity_hours).mean().where(qualified)
    rank = volume.rank(axis=1, ascending=False, method="first")
    shocked = data.close.pct_change(fill_method=None).abs().gt(spec.hourly_shock_limit)
    quarantined = shocked.rolling(spec.shock_cooldown_hours, min_periods=1).max().astype(bool)
    return qualified & rank.le(spec.liquid_top_n) & ~quarantined & valid


def growth_targets(data: FuturesData, spec: GrowthSpec,
                   eligible_after: dict[str, str] | None = None):
    close = data.close
    available = eligibility(data,spec,eligible_after)
    returns = close.pct_change(fill_method=None)
    vol = returns.rolling(spec.volatility_hours, min_periods=spec.volatility_hours).std()
    volatility = vol.replace(0, np.nan)
    fast = close.ewm(span=spec.fast_hours,adjust=False,min_periods=spec.fast_hours).mean()
    slow = close.ewm(span=spec.slow_hours,adjust=False,min_periods=spec.slow_hours).mean()
    if spec.family == "trend":
        score = np.log(fast/slow).div(volatility*np.sqrt(spec.slow_hours-spec.fast_hours))
    elif spec.family in {"relative_momentum","relative_reversal"}:
        move = np.log(close/close.shift(spec.fast_hours)).where(available)
        score = move.sub(move.median(axis=1), axis=0).div(volatility*np.sqrt(spec.fast_hours))
        if spec.family == "relative_reversal":
            score = -score
    elif spec.family == "carry":
        # Settled past funding only. Positive funding -> a SHORT, not a free yield.
        funding = data.funding.rolling(spec.fast_hours,min_periods=spec.fast_hours).sum()
        score = -funding.div(volatility*np.sqrt(spec.fast_hours))*100
        # Refuse to oppose a very strong, already observed directional trend.
        trend = np.log(fast/slow).div(volatility*np.sqrt(spec.slow_hours))
        score = score.where((np.sign(score)==np.sign(trend)) | trend.abs().lt(0.5))
    else:
        upper = data.frames["high"].shift(1).rolling(spec.slow_hours,min_periods=spec.slow_hours).max()
        lower = data.frames["low"].shift(1).rolling(spec.slow_hours,min_periods=spec.slow_hours).min()
        exits_low = data.frames["low"].shift(1).rolling(spec.fast_hours,min_periods=spec.fast_hours).min()
        exits_high = data.frames["high"].shift(1).rolling(spec.fast_hours,min_periods=spec.fast_hours).max()
        state = np.zeros(len(close.columns))
        values = np.zeros(close.shape)
        cv,uv,lv,el,eh,av=(x.to_numpy() for x in (close,upper,lower,exits_low,exits_high,available))
        for i in range(len(close)):
            state=np.where((state>0)&(cv[i]<el[i]) | (state<0)&(cv[i]>eh[i]),0,state)
            state=np.where((state==0)&(cv[i]>uv[i]),1,state)
            state=np.where((state==0)&(cv[i]<lv[i]),-1,state)
            state=np.where(av[i],state,0)
            values[i]=state
        score=pd.DataFrame(values,index=close.index,columns=close.columns)
    score = score.where(available).replace([np.inf,-np.inf],np.nan)
    longs = score.gt(spec.score_threshold) & score.rank(axis=1,ascending=False,method="first").le(spec.max_positions_per_side)
    shorts = score.lt(-spec.score_threshold) & score.rank(axis=1,ascending=True,method="first").le(spec.max_positions_per_side)
    raw = np.tanh(score).where(longs|shorts,0).div(volatility).fillna(0)
    if spec.family in {"relative_momentum","relative_reversal","carry"}:
        long=raw.clip(lower=0)
        short=raw.clip(upper=0)
        long=long.div(long.sum(axis=1).replace(0,np.nan),axis=0).fillna(0)*0.5
        short=short.div(short.abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)*0.5
        both=long.sum(axis=1).gt(0)&short.sum(axis=1).lt(0)
        unit=(long+short).where(both,0)
    else:
        unit=raw.div(raw.abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
    # Actual historical portfolio covariance is reflected by a causal unit proxy.
    proxy = (unit.shift(1).fillna(0)*returns.fillna(0)).sum(axis=1)
    risk = proxy.rolling(spec.volatility_hours,min_periods=spec.volatility_hours).std()*np.sqrt(365*24)
    scale=(spec.annual_volatility_target/risk.replace(0,np.nan)).clip(upper=spec.maximum_gross).fillna(0)
    desired=unit.mul(scale,axis=0)
    # A global shrink preserves neutrality while respecting every position cap.
    per_asset_scale=(spec.maximum_asset_weight/desired.abs().max(axis=1).replace(0,np.nan)).clip(upper=1).fillna(0)
    desired=desired.mul(per_asset_scale,axis=0)
    targets=hold_on_clock(desired,spec.rebalance_hours).where(available,0)
    diagnostics=pd.DataFrame({"gross":targets.abs().sum(axis=1),"net":targets.sum(axis=1),
        "max_asset":targets.abs().max(axis=1),"eligible_count":available.sum(axis=1),
        "long_count":targets.gt(0).sum(axis=1),"short_count":targets.lt(0).sum(axis=1)},index=close.index)
    return targets,diagnostics


def online_mix(targets: dict[str,pd.DataFrame], net_returns: pd.DataFrame,
               windows_days=(30,90,180), max_sleeve=0.35, score_floor=0.0):
    """Performance allocation using ONLY already closed, net sleeve outcomes.

    No retrospective winner choice. Unallocated capacity stays cash. The
    candidate hyperparameters and sleeve menu are fixed before validation.
    """
    if not targets or not 0 < max_sleeve <= 1 or not windows_days or min(windows_days)<=0:
        raise ValueError("invalid online allocator")
    scores=[]
    for days in windows_days:
        n=days*24
        mean=net_returns.rolling(n,min_periods=n).mean()
        std=net_returns.rolling(n,min_periods=n).std().replace(0,np.nan)
        scores.append(mean/std*np.sqrt(365*24))
    score=sum(scores)/len(scores)
    # Continuous, bounded confidence; no exponential winner-takes-all chasing.
    confidence=(score-score_floor).clip(lower=0,upper=3).fillna(0)
    weights=confidence.div(confidence.sum(axis=1).clip(lower=1),axis=0).clip(upper=max_sleeve)
    weights=hold_on_clock(weights,24)
    mixed=sum(t.mul(weights[name],axis=0) for name,t in targets.items())
    return mixed,weights


def research_menu() -> dict[str,GrowthSpec]:
    """Small prespecified family menu, not an unbounded parameter search."""
    result={}
    for fast,slow in ((48,192),(168,672),(336,1344)):
        result[f"trend_{fast}_{slow}"]=GrowthSpec(fast_hours=fast,slow_hours=slow)
    for family in ("relative_momentum","relative_reversal"):
        for fast,slow in ((24,168),(168,672)):
            result[f"{family}_{fast}"]=GrowthSpec(family=family,fast_hours=fast,slow_hours=slow)
    for fast,slow in ((168,672),(720,1440)):
        result[f"carry_{fast}"]=GrowthSpec(family="carry",fast_hours=fast,slow_hours=slow)
    for fast,slow in ((24,168),(168,672)):
        result[f"breakout_{fast}_{slow}"]=GrowthSpec(family="breakout",fast_hours=fast,slow_hours=slow)
    return result

