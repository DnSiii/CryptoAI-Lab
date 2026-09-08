"""V16 relative-value portfolio construction; research-only, no exchange I/O.

Cross-sectional predictions rank assets, rather than justify an outright
directional position. Match the two sides in dollars or estimated BTC beta.
Beta neutrality is an estimate at a rebalance, not a guarantee during gaps.
"""
from dataclasses import asdict, dataclass
import numpy as np
import pandas as pd
from .data import FuturesData
from .v16_rebuild import GrowthSpec, eligibility


@dataclass(frozen=True)
class RelativeSpec:
    balance: str = "beta"
    retain_rank_buffer: bool = False
    rebalance_hours: int = 12
    positions_per_side: int = 4
    maximum_asset_weight: float = .20
    maximum_gross: float = 1.6
    minimum_pair_edge: float = .004
    beta_hours: int = 720
    annual_volatility_target: float = .35
    basket_loss_limit: float = .04
    cooldown_hours: int = 24
    # Require forecast improvement to exceed stressed round-trip turnover costs.
    # Zero preserves the prior, fully recorded experiment for reproduction.
    trading_cost_hurdle: float = 0.
    assumed_cost_per_side: float = .0012
    maximum_beta_drift: float = .10

    def __post_init__(self):
        if self.balance not in {"dollar", "beta"}:
            raise ValueError("invalid balance method")
        if min(self.rebalance_hours,self.positions_per_side,self.beta_hours,self.cooldown_hours)<=0:
            raise ValueError("positive clock and sample sizes required")
        if not 0<self.maximum_asset_weight<=self.maximum_gross<=2:
            raise ValueError("invalid exposure bounds")
        if self.minimum_pair_edge<.0014 or not 0<self.basket_loss_limit<1:
            raise ValueError("invalid costs/exit limit")
        if not 0<self.annual_volatility_target<=1:
            raise ValueError("invalid volatility budget")
        if self.trading_cost_hurdle<0 or self.assumed_cost_per_side<0 or self.maximum_beta_drift<=0:
            raise ValueError("invalid execution hurdle")

    def to_dict(self): return asdict(self)


def balance_sides(long,short,beta,spec):
    """Positive long/short allocations become signed, bounded target weights."""
    long=np.asarray(long,float); short=np.asarray(short,float)
    if long.sum()<=0 or short.sum()<=0:
        return np.zeros_like(long)
    long=long/long.sum(); short=short/short.sum()
    if spec.balance=="beta":
        lb=float(long@beta); sb=float(short@beta)
        if not np.isfinite(lb+sb) or min(lb,sb)<=0:
            return np.zeros_like(long)
        weight=long*sb/(lb+sb)-short*lb/(lb+sb)
    else:
        weight=(long-short)/2
    weight*=spec.maximum_gross
    largest=float(np.max(np.abs(weight)))
    if largest>spec.maximum_asset_weight:
        weight*=spec.maximum_asset_weight/largest
    return weight


def worthwhile_rebalance(current,proposal,forecasts,spec):
    """Expected improvement, not total portfolio forecast, must pay turnover."""
    delta=np.asarray(proposal)-np.asarray(current)
    improvement=float(delta@np.asarray(forecasts))
    hurdle=float(np.abs(delta).sum()*2*spec.assumed_cost_per_side*spec.trading_cost_hurdle)
    return bool(np.isfinite(improvement) and improvement>hurdle)


def relative_targets(data:FuturesData,forecasts:pd.DataFrame,spec:RelativeSpec):
    if not forecasts.index.equals(data.close.index) or not forecasts.columns.equals(data.close.columns):
        raise ValueError("forecasts must align exactly with market data")
    if "BTCUSDT" not in data.symbols:
        raise ValueError("BTC market factor unavailable")
    ret=data.close.pct_change(fill_method=None)
    eligible=eligibility(data,GrowthSpec())
    vol=ret.rolling(168,min_periods=168).std().replace(0,np.nan)
    market=ret.BTCUSDT
    var=market.rolling(spec.beta_hours,min_periods=spec.beta_hours).var().replace(0,np.nan)
    beta=ret.rolling(spec.beta_hours,min_periods=spec.beta_hours).cov(market).div(var,axis=0)
    # Reject unidentifiable/negative-beta assets rather than invent hedge ratios.
    usable=eligible & beta.gt(.05) & beta.lt(5) & vol.gt(0)
    x=forecasts.where(usable).to_numpy()
    bv=beta.to_numpy(); vv=vol.to_numpy(); cv=data.close.to_numpy()
    av=usable.to_numpy(); r=ret.to_numpy()
    n,m=x.shape; output=np.zeros((n,m)); current=np.zeros(m)
    starts=np.ones(m); until=-1
    raw_beta=np.zeros(n); events=np.zeros(n,dtype=bool); skipped=np.zeros(n,dtype=bool)
    clock=(data.close.index.asi8//(3600*10**9))%spec.rebalance_hours==0
    for i in range(n):
        # Exit the whole relative basket if one held leg becomes unavailable.
        # Missing execution prices remain a separate rejection in the evaluator.
        held=np.abs(current)>1e-12
        valid_held=np.all(av[i,held])
        basket_mark=float(np.sum(current[held]*(cv[i,held]/starts[held]-1))) if valid_held else -np.inf
        if np.any(held) and (not valid_held or basket_mark<=-spec.basket_loss_limit):
            current[:]=0
            until=i+spec.cooldown_hours
        if clock[i] and i>=until:
            events[i]=True
            finite=np.flatnonzero(np.isfinite(x[i]))
            proposal=np.zeros(m)
            k=spec.positions_per_side
            if len(finite)>=2*k:
                ordered=finite[np.argsort(x[i,finite],kind="stable")]
                high=ordered[::-1]; low=ordered
                def choose(order,old):
                    if not spec.retain_rank_buffer:
                        return list(order[:k])
                    retained=[j for j in order[:2*k] if old[j]]
                    return (retained+[j for j in order if j not in retained])[:k]
                longs=choose(high,current>0); shorts=choose(low,current<0)
                # No self-crossing even when rank buffers overlap.
                if not set(longs).intersection(shorts):
                    edge=float(np.mean(x[i,longs])-np.mean(x[i,shorts]))
                    if edge>=spec.minimum_pair_edge:
                        lp=np.zeros(m); sp=np.zeros(m)
                        lp[longs]=1/vv[i,longs]; sp[shorts]=1/vv[i,shorts]
                        proposal=balance_sides(lp,sp,np.nan_to_num(bv[i]),spec)
                        # Covariance of today's basket measured on PAST returns.
                        hist=r[max(0,i-spec.beta_hours+1):i+1]
                        portfolio=np.nan_to_num(hist)@proposal
                        risk=float(np.std(portfolio,ddof=1)*np.sqrt(365*24))
                        if risk>spec.annual_volatility_target:
                            proposal*=spec.annual_volatility_target/risk
            # The held quantities drift while the requested target remains fixed.
            # This mark uses only observed closes; the native executor separately
            # accounts for actual fees/funding and next-open fill prices.
            change=True
            if spec.trading_cost_hurdle>0 and np.any(held) and np.any(proposal):
                ratio=np.where(held,cv[i]/starts,1.)
                marked=current*ratio/max(1+float(np.nansum(current*(ratio-1))),.01)
                beta_risk=abs(float(marked@np.nan_to_num(bv[i])))
                forced=(beta_risk>spec.maximum_beta_drift or
                        np.abs(marked).max()>spec.maximum_asset_weight*1.25 or
                        np.abs(marked).sum()>spec.maximum_gross*1.10 or
                        not np.isfinite(x[i,held]).all())
                if not forced and not worthwhile_rebalance(marked,proposal,np.nan_to_num(x[i]),spec):
                    change=False; skipped[i]=True
            if change:
                current=proposal
                starts=np.where(np.isfinite(cv[i])&(cv[i]>0),cv[i],1)
        output[i]=current
        raw_beta[i]=float(current@np.nan_to_num(bv[i]))
    target=pd.DataFrame(output,index=data.close.index,columns=data.close.columns)
    diag=pd.DataFrame({"net_dollars":target.sum(axis=1),"estimated_beta":raw_beta,
        "gross":target.abs().sum(axis=1),"rebalance":events,"cost_gate_skipped":skipped},index=target.index)
    return target,diag
