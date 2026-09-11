"""V17 causal pooled forecasting research. No production/order integration.

Monthly rolling fits use only labels whose ENTIRE holding period has elapsed.
Scalers are fit to the training fold, never to the full panel. Every forecast
is recorded before the result of its own trade is observed.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd
from .data import FuturesData
from .v17_rebuild import GrowthSpec, eligibility, hold_on_clock


@dataclass(frozen=True)
class ForecastSpec:
    model: str = "ridge"
    horizon_hours: int = 24
    train_days: int = 180
    min_train_days: int = 60
    decision_every_hours: int = 12
    objective: str = "absolute"
    minimum_edge: float = 0.003
    maximum_asset_weight: float = 0.20
    maximum_gross: float = 1.6
    max_positions_per_side: int = 4
    stop_fraction: float = 0.05
    trailing_fraction: float = 0.10
    annual_volatility_target: float = 0.45

    def __post_init__(self):
        if self.model not in {"ridge","boosting"} or self.objective not in {"absolute","relative"}:
            raise ValueError("invalid forecast model/objective")
        if min(self.horizon_hours,self.train_days,self.min_train_days,self.decision_every_hours,
               self.max_positions_per_side)<=0 or self.min_train_days>self.train_days:
            raise ValueError("invalid chronological training config")
        if not 0<self.maximum_asset_weight<=self.maximum_gross<=2 or self.minimum_edge<.0014:
            raise ValueError("invalid exposure or below modeled round-trip costs")
        if not 0<self.stop_fraction<self.trailing_fraction<1:
            raise ValueError("invalid exit distances")

    def to_dict(self): return asdict(self)


def feature_panel(data: FuturesData):
    close=data.close
    r=close.pct_change(fill_method=None)
    vol=r.rolling(168,min_periods=168).std().replace(0,np.nan)
    eligible=eligibility(data,GrowthSpec())
    def broadcast(series):
        return pd.DataFrame(np.broadcast_to(series.to_numpy()[:,None],close.shape),index=close.index,columns=close.columns)
    features={}
    for horizon in (1,6,24,72,168,720):
        ret=close.pct_change(horizon,fill_method=None)
        features[f"return_{horizon}"]=ret
        features[f"relative_{horizon}"]=ret.sub(ret.where(eligible).median(axis=1),axis=0)
        features[f"risk_return_{horizon}"]=ret/(vol*np.sqrt(horizon))
    features["vol_week"]=vol
    features["vol_day_week"]=r.rolling(24,min_periods=24).std()/vol
    features["vol_week_month"]=vol/r.rolling(720,min_periods=720).std().replace(0,np.nan)
    features["range"]=data.frames["high"].sub(data.frames["low"])/close
    features["close_location"]=close.sub(data.frames["low"])/data.frames["high"].sub(data.frames["low"]).replace(0,np.nan)
    volume=data.frames["quote_volume"]
    features["volume_surge"]=volume.rolling(24,min_periods=24).mean()/volume.shift(24).rolling(168,min_periods=168).mean()
    features["liquidity_rank"]=volume.rolling(720,min_periods=720).mean().where(eligible).rank(axis=1,pct=True)
    for horizon in (24,168,720):
        features[f"funding_{horizon}"]=data.funding.rolling(horizon,min_periods=horizon).sum()
        features[f"market_{horizon}"]=broadcast(close.pct_change(horizon,fill_method=None).where(eligible).median(axis=1))
        features[f"breadth_{horizon}"]=broadcast(close.pct_change(horizon,fill_method=None).where(eligible).gt(0).sum(axis=1)/eligible.sum(axis=1).replace(0,np.nan))
    x=np.stack([v.to_numpy(dtype=float) for v in features.values()],axis=2)
    # Undefined ratios are unavailable observations, never extreme convictions.
    x=np.where(np.isfinite(x),np.clip(x,-100,100),np.nan)
    return x,list(features),eligible


def forward_labels(data: FuturesData, hours: int):
    # Signal at close t, enter open t+1, leave open t+h+1.
    price=data.frames["open"].shift(-hours-1)/data.frames["open"].shift(-1)-1
    cumulative=data.funding.cumsum()
    funding=cumulative.shift(-hours-1)-cumulative.shift(-1)
    label=price-funding
    # Refuse labels spanning a missing candle. No synthetic delisting fill.
    valid=data.close.notna().rolling(hours+2,min_periods=hours+2).sum().shift(-hours-1).eq(hours+2)
    return label.where(valid)


def purged_train_rows(index: pd.DatetimeIndex, asof: pd.Timestamp, spec: ForecastSpec):
    # Label outcome at t+h+1 open is known strictly before this fitting time.
    mature=index+pd.Timedelta(hours=spec.horizon_hours+1)<asof
    start=index>=asof-pd.Timedelta(days=spec.train_days)
    clock=(index.asi8//(3600*10**9))%spec.decision_every_hours==0
    return mature&start&clock


def walkforward_forecasts(data: FuturesData,spec: ForecastSpec,first_fit="2025-04-01",progress=None):
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.linear_model import Ridge
    from sklearn.preprocessing import StandardScaler
    from threadpoolctl import threadpool_limits
    x,names,eligible=feature_panel(data)
    labels=forward_labels(data,spec.horizon_hours)
    if spec.objective=="relative":
        labels=labels.sub(labels.where(eligible).median(axis=1),axis=0)
    y=labels.to_numpy()
    valid=np.isfinite(x).all(axis=2)&eligible.to_numpy()
    output=np.full(data.close.shape,np.nan)
    first=pd.Timestamp(first_fit)
    first=first.tz_localize("UTC") if first.tzinfo is None else first.tz_convert("UTC")
    months=pd.date_range(first,data.close.index[-1],freq="MS",tz="UTC")
    audit=[]
    for asof in months:
        train_rows=purged_train_rows(data.close.index,asof,spec)
        train=valid&train_rows[:,None]&np.isfinite(y)
        infer_rows=(data.close.index>=asof)&(data.close.index<asof+pd.DateOffset(months=1))
        infer=valid&infer_rows[:,None]
        time_rows=np.flatnonzero(train.any(axis=1))
        if len(time_rows)==0 or train.sum()<2000 or (asof-data.close.index[time_rows[0]]).days<spec.min_train_days:
            continue
        train_x=x[train]; train_y=np.clip(y[train],-.20,.20)
        test_x=x[infer]
        if not len(test_x): continue
        with threadpool_limits(limits=2):
            if spec.model=="ridge":
                scaler=StandardScaler().fit(train_x)
                model=Ridge(alpha=100.)
                model.fit(scaler.transform(train_x),train_y)
                predicted=model.predict(scaler.transform(test_x))
            else:
                model=HistGradientBoostingRegressor(learning_rate=.05,max_iter=100,
                    max_leaf_nodes=15,min_samples_leaf=200,l2_regularization=10.,
                    max_bins=63,early_stopping=False,random_state=1605)
                model.fit(train_x,train_y)
                predicted=model.predict(test_x)
        output[infer]=predicted
        last_label=data.close.index[time_rows[-1]]+pd.Timedelta(hours=spec.horizon_hours+1)
        assert last_label<asof
        record={"fit_at":asof.isoformat(),"first_training_observation":data.close.index[time_rows[0]].isoformat(),
            "last_training_observation":data.close.index[time_rows[-1]].isoformat(),
            "last_training_label_matured_at":last_label.isoformat(),"training_rows":int(train.sum()),
            "forecast_rows":int(infer.sum()),"n_features":len(names)}
        audit.append(record)
        if progress: progress(record)
    return pd.DataFrame(output,index=data.close.index,columns=data.close.columns),audit


def forecasts_to_targets(data: FuturesData,forecasts: pd.DataFrame,spec: ForecastSpec):
    eligible=eligibility(data,GrowthSpec())
    known=forecasts.where(eligible)
    long=known.gt(spec.minimum_edge)&known.rank(axis=1,ascending=False,method="first").le(spec.max_positions_per_side)
    short=known.lt(-spec.minimum_edge)&known.rank(axis=1,ascending=True,method="first").le(spec.max_positions_per_side)
    vol=data.close.pct_change(fill_method=None).rolling(168,min_periods=168).std()*np.sqrt(365*24)
    risk_weight=(spec.annual_volatility_target/np.sqrt(2*spec.max_positions_per_side)/vol).clip(upper=spec.maximum_asset_weight).fillna(0)
    raw=(long.astype(float)-short.astype(float))*risk_weight
    factor=(spec.maximum_gross/raw.abs().sum(axis=1).replace(0,np.nan)).clip(upper=1).fillna(0)
    raw=raw.mul(factor,axis=0)
    target=hold_on_clock(raw,spec.decision_every_hours).where(eligible,0)
    # Close-confirmed stops fill next open, including any adverse gap.
    c=data.close.to_numpy(); t=target.to_numpy(copy=True)
    state=np.zeros(len(data.symbols)); entry=np.zeros(len(data.symbols)); peak=np.zeros(len(data.symbols))
    blocked=np.zeros(len(data.symbols),dtype=int)
    for i in range(len(c)):
        sign=np.sign(t[i]); different=(sign!=state)
        active=sign!=0
        entry=np.where(different,c[i],entry)
        peak=np.where(different,c[i],peak)
        peak=np.where(sign>0,np.maximum(peak,c[i]),np.minimum(peak,c[i]))
        loss=np.where(sign>0,c[i]/np.where(entry>0,entry,1)-1,1-c[i]/np.where(entry>0,entry,1))
        pullback=np.where(sign>0,c[i]/np.where(peak>0,peak,1)-1,1-c[i]/np.where(peak>0,peak,1))
        stopped=active&((loss<=-spec.stop_fraction)|(pullback<=-spec.trailing_fraction))
        blocked=np.where(stopped,i+spec.decision_every_hours,blocked)
        disabled=(i<blocked)|~np.isfinite(c[i])
        t[i]=np.where(disabled,0,t[i])
        state=np.where(disabled,0,sign)
    return pd.DataFrame(t,index=target.index,columns=target.columns)


def forecast_menu():
    return {f"{model}_{h}_{objective}":ForecastSpec(model=model,horizon_hours=h,
        decision_every_hours=h,objective=objective)
        for model in ("ridge","boosting") for h in (12,24) for objective in ("absolute","relative")}

