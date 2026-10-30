#!/usr/bin/env python3
"""V98 AE independent actual-open cash ledger with native funding and 81-corner audit."""
from __future__ import annotations
import numpy as np
from phase1208_ae_cash_anchor_governor import (
    CORNERS,ASSET_CAP,GROSS_CAP,NET_CAP,EQUITY_FLOOR,SLIPPAGE,vec,project)

FEES={'base':.0007,'severe':.0012,'supersevere':.002}
ORDERS=('carried_before_fill','new_after_fill')


def native_funding_cash(units,rate,event,mark_low,mark_high):
    u,r,e=map(vec,(units,rate,event))
    lo=np.asarray(mark_low,dtype=float)
    hi=np.asarray(mark_high,dtype=float)
    if (lo.shape!=(4,) or hi.shape!=(4,) or
            np.any((e!=0)&(e!=1)) or np.any(r[e==0]!=0) or
            not np.isfinite(lo[e==1]).all() or
            not np.isfinite(hi[e==1]).all() or
            np.any(lo[e==1]<=0) or np.any(hi[e==1]<lo[e==1])):
        raise ValueError('AE1210_NATIVE_FUNDING_MARK')
    mark=np.where(u*r>0,hi,lo)
    return -float(np.sum((u*r*mark)[e==1]))


def execute_hour(prior_close,opening,high,low,closing,cash,old_units,
                 desired_weights,down,up,funding_bound,prior_quote,min_quote,
                 fee,funding_rate,mark_low,mark_high,funding_event,order):
    pc,p,hi,lo,cl,old=map(vec,(prior_close,opening,high,low,closing,old_units))
    if (fee not in FEES or order not in ORDERS or not np.isfinite(cash) or
            np.any(pc<=0) or np.any(p<=0) or np.any(lo<=0) or
            np.any(hi<np.maximum(p,cl)) or np.any(lo>np.minimum(p,cl))):
        raise ValueError('AE1210_PRICE_OR_ORDER')
    prior_equity=float(cash+old@pc)
    open_equity=float(cash+old@p)
    if prior_equity<=0 or open_equity<=0:
        raise ValueError('AE1210_OPEN_GAP_INSOLVENCY')
    opening_gap_return=open_equity/prior_equity-1
    funding=0.
    if order=='carried_before_fill':
        funding=native_funding_cash(old,funding_rate,funding_event,mark_low,mark_high)
        cash+=funding
        open_equity+=funding
        if open_equity<=0:
            raise ValueError('AE1210_CARRIED_FUNDING_INSOLVENCY')
    projected=project(desired_weights,old,p,open_equity,down,up,funding_bound,
                      prior_quote,min_quote)
    new=projected['units']
    delta=new-old
    turnover=float(np.abs(delta)@p)
    execution=p*(1+np.sign(delta)*SLIPPAGE)
    fees=turnover*FEES[fee]
    slippage=turnover*SLIPPAGE
    cash=float(cash-delta@execution-fees)
    if order=='new_after_fill':
        funding=native_funding_cash(new,funding_rate,funding_event,mark_low,mark_high)
        cash+=funding
    prices=np.stack((lo,p,hi))[CORNERS,np.arange(4)]
    exposures=prices*new
    corner_equity=cash+exposures.sum(axis=1)
    if (np.any(corner_equity<EQUITY_FLOOR*open_equity-1e-9) or
            np.any(np.abs(exposures)>ASSET_CAP*corner_equity[:,None]+1e-9) or
            np.any(np.abs(exposures).sum(axis=1)>GROSS_CAP*corner_equity+1e-9) or
            np.any(np.abs(exposures.sum(axis=1))>NET_CAP*corner_equity+1e-9)):
        raise ValueError('AE1210_ACTUAL_INTRABAR_81_CORNER')
    nav=float(cash+new@cl)
    if nav<=0 or not np.isfinite(nav):
        raise ValueError('AE1210_CLOSE_INSOLVENCY')
    if not np.isclose(nav,cash+new@cl,atol=1e-8,rtol=0):
        raise ValueError('AE1210_NAV_RECONCILIATION')
    return {'cash':cash,'units':new,'equity':nav,
            'turnover':turnover,'fees':fees,'slippage':slippage,
            'funding_cash_delta':funding,
            'fraction':projected['fraction'],
            'opening_gap_return':opening_gap_return,
            'worst_actual_corner_equity':float(corner_equity.min()),
            'actual_execution_proven':True,
            'historical_system_pnl_computed':False}
