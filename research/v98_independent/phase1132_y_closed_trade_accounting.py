#!/usr/bin/env python3
"""Y per-asset FIFO closed-trade PnL including entry/exit fees and funding.

Pure observer: never changes execution decisions, units, cash or risk caps.
Both preregistered native funding orderings are explicit. No PnL data loaded.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

class TradeBook:
    def __init__(self,initial_capital):
        if not np.isfinite(initial_capital) or initial_capital<=0:
            raise ValueError('Y1132_BAD_INITIAL_CAPITAL')
        self.initial=float(initial_capital)
        self.lots=[[] for _ in range(4)]
        self.closed=[]
    def units(self):
        return np.array([sum(l['units'] for l in lots) for lots in self.lots])
    def fill(self,asset,delta,price,fee,timestamp):
        if (asset not in range(4) or not all(np.isfinite(x) for x in (delta,price,fee))
            or price<=0 or fee<0):raise ValueError('Y1132_BAD_FILL')
        if abs(delta)<1e-12:return
        t=pd.Timestamp(timestamp)
        if t.tzinfo is None:raise ValueError('Y1132_NAIVE_TIMESTAMP')
        fee_per_unit=fee/abs(delta)
        remaining=float(delta)
        lots=self.lots[asset]
        while abs(remaining)>1e-12 and lots and remaining*lots[0]['units']<0:
            lot=lots[0]
            qty=min(abs(remaining),abs(lot['units']))
            side=np.sign(lot['units'])
            realized=float(qty*side*(price-lot['price'])
                -qty*(lot['fee_per_unit']+fee_per_unit)
                +qty*lot['funding_per_unit'])
            self.closed.append({'timestamp':t.isoformat(),'asset':asset,
                                'pnl_usd':realized,'closed_units':float(qty)})
            lot['units']-=side*qty
            remaining+=side*qty
            if abs(lot['units'])<1e-12:lots.pop(0)
        if abs(remaining)>1e-12:
            lots.append({'units':remaining,'price':float(price),
                         'fee_per_unit':float(fee_per_unit),
                         'funding_per_unit':0.,'opened':t.isoformat()})
    def fund(self,asset,cash_delta,timestamp):
        if asset not in range(4) or not np.isfinite(cash_delta):
            raise ValueError('Y1132_BAD_FUNDING')
        if abs(cash_delta)<1e-12:return
        lots=self.lots[asset];qty=sum(abs(l['units']) for l in lots)
        if qty>1e-12:
            for lot in lots:lot['funding_per_unit']+=float(cash_delta/qty)
        else:
            t=pd.Timestamp(timestamp).isoformat()
            recent=[x for x in self.closed if x['asset']==asset and x['timestamp']==t]
            total=sum(x['closed_units'] for x in recent)
            if total<=1e-12:raise ValueError('Y1132_UNATTRIBUTABLE_FUNDING')
            for x in recent:x['pnl_usd']+=float(cash_delta*x['closed_units']/total)
    def apply_hour(self,events,funding_by_asset,timestamp,*,funding_order):
        if funding_order not in ('carried_before_fill','new_after_fill'):
            raise ValueError('Y1132_BAD_FUNDING_ORDER')
        f=np.asarray(funding_by_asset,float)
        if f.shape!=(4,) or not np.isfinite(f).all():
            raise ValueError('Y1132_BAD_FUNDING_VECTOR')
        if funding_order=='carried_before_fill':
            for j,v in enumerate(f):self.fund(j,float(v),timestamp)
        for e in events:
            if set(e)!={'asset','action','delta_units','fill_price','fee_usd','notional'}:
                raise ValueError('Y1132_EVENT_SCHEMA')
            self.fill(e['asset'],e['delta_units'],e['fill_price'],e['fee_usd'],timestamp)
        if funding_order=='new_after_fill':
            for j,v in enumerate(f):self.fund(j,float(v),timestamp)
    def total_pnl(self,mark):
        p=np.asarray(mark,float)
        if p.shape!=(4,) or not np.isfinite(p).all() or (p<=0).any():
            raise ValueError('Y1132_BAD_MARK')
        unrealized=0.
        for j,lots in enumerate(self.lots):
            for l in lots:
                q=abs(l['units']);side=np.sign(l['units'])
                unrealized+=q*(side*(p[j]-l['price'])-l['fee_per_unit']+l['funding_per_unit'])
        return float(sum(x['pnl_usd'] for x in self.closed)+unrealized)
