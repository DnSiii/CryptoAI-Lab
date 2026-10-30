#!/usr/bin/env python3
"""AD self-financing signed USD-M open executor, synthetic until full freeze."""
from __future__ import annotations
import numpy as np
from phase1196_ad_81corner_governor import (
    CORNERS,propose,ASSET_CAP,GROSS_CAP,NET_CAP,EQUITY_FLOOR,SLIPPAGE,vector)

FEES={'base':.0007,'severe':.0012,'supersevere':.002}
ORDERS=('carried_before_fill','new_after_fill')


def funding_cash(units,rate,event,mark_low,mark_high):
    u,r,e=map(vector,(units,rate,event))
    low=np.asarray(mark_low,dtype=float)
    high=np.asarray(mark_high,dtype=float)
    if (low.shape!=(4,) or high.shape!=(4,) or np.any((e!=0)&(e!=1)) or
            np.any(r[e==0]!=0) or not np.isfinite(r).all() or
            np.any(~np.isfinite(low[e==1])) or np.any(~np.isfinite(high[e==1])) or
            np.any(low[e==1]<=0) or np.any(high[e==1]<low[e==1])):
        raise ValueError('AD1197_NATIVE_MARK')
    mark=np.where(u*r>0,high,low)
    return -float(np.sum((u*r*mark)[e==1]))


def execute_hour(prior_close,opening,high,low,closing,cash,old_units,
                 desired_weights,down,up,funding_bound,prior_quote,min_quote,
                 fee,funding_rate,mark_low,mark_high,funding_event,order):
    old,p,pc,hi,lo,cl=map(vector,(old_units,opening,prior_close,high,low,closing))
    if (fee not in FEES or order not in ORDERS or not np.isfinite(cash) or
            np.any(p<=0) or np.any(pc<=0) or np.any(lo<=0) or
            np.any(hi<np.maximum(p,cl)) or np.any(lo>np.minimum(p,cl))):
        raise ValueError('AD1197_INPUT')
    prior_equity=float(cash+old@pc)
    open_equity=float(cash+old@p)
    if prior_equity<=0 or open_equity<=0:
        raise ValueError('AD1197_OPEN_GAP_INSOLVENCY')
    raw_gap_return=open_equity/prior_equity-1
    funding=0.
    if order=='carried_before_fill':
        funding=funding_cash(old,funding_rate,funding_event,mark_low,mark_high)
        cash+=funding
        open_equity+=funding
        if open_equity<=0:raise ValueError('AD1197_FUNDING_INSOLVENCY')
    new,alpha=propose(desired_weights,old,p,open_equity,down,up,funding_bound,
                      prior_quote,min_quote)
    delta=new-old
    execution=p*(1+np.sign(delta)*SLIPPAGE)
    turnover=float(np.sum(np.abs(delta)*p))
    fees=turnover*FEES[fee]
    cash=float(cash-delta@execution-fees)
    if order=='new_after_fill':
        funding=funding_cash(new,funding_rate,funding_event,mark_low,mark_high)
        cash+=funding
    prices=p*np.stack((lo/p,np.ones(4),hi/p))[CORNERS,np.arange(4)]
    exposure=prices*new
    corner_equity=cash+exposure.sum(axis=1)
    if (np.any(corner_equity<EQUITY_FLOOR*open_equity-1e-9) or
            np.any(np.abs(exposure)>ASSET_CAP*corner_equity[:,None]+1e-9) or
            np.any(np.abs(exposure).sum(axis=1)>GROSS_CAP*corner_equity+1e-9) or
            np.any(np.abs(exposure.sum(axis=1))>NET_CAP*corner_equity+1e-9)):
        raise ValueError('AD1197_INTRABAR_81_CORNER')
    nav=float(cash+new@cl)
    if nav<=0 or not np.isfinite(nav):
        raise ValueError('AD1197_CLOSE_INSOLVENCY')
    return {'cash':cash,'units':new,'equity':nav,'turnover':turnover,
            'fees':fees,'funding_cash_delta':funding,'alpha':alpha,
            'opening_gap_return':raw_gap_return,
            'min_intrabar_equity':float(corner_equity.min()),
            'actual_execution_proven':True}
