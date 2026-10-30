#!/usr/bin/env python3
"""Z independent signed FIFO realized-trade observer; never controls orders."""
from __future__ import annotations
import numpy as np
import pandas as pd

class TradeBook:
    def __init__(self,initial):
        if not np.isfinite(initial) or initial<=0:raise ValueError('Z1151_CAPITAL')
        self.initial=float(initial);self.lots=[[] for _ in range(4)];self.closed=[]
    def units(self):
        return np.array([sum(l['units'] for l in lots) for lots in self.lots])
    def fill(self,asset,delta,price,fee,timestamp):
        if (asset not in range(4) or not all(np.isfinite(v) for v in (delta,price,fee))
            or price<=0 or fee<0):raise ValueError('Z1151_FILL')
        if abs(delta)<1e-12:return
        t=pd.Timestamp(timestamp)
        if t.tzinfo is None:raise ValueError('Z1151_TIMESTAMP')
        fee_unit=fee/abs(delta);remaining=float(delta);lots=self.lots[asset]
        while abs(remaining)>1e-12 and lots and remaining*lots[0]['units']<0:
            lot=lots[0];qty=min(abs(remaining),abs(lot['units']))
            side=np.sign(lot['units'])
            pnl=qty*(side*(price-lot['price'])-lot['fee_unit']-fee_unit+lot['funding_unit'])
            self.closed.append({'timestamp':t.isoformat(),'asset':asset,
                'pnl_usd':float(pnl),'closed_units':float(qty)})
            lot['units']-=side*qty;remaining+=side*qty
            if abs(lot['units'])<1e-12:lots.pop(0)
        if abs(remaining)>1e-12:
            lots.append({'units':remaining,'price':float(price),
                'fee_unit':float(fee_unit),'funding_unit':0.})
    def funding(self,asset,cash_delta,timestamp):
        if asset not in range(4) or not np.isfinite(cash_delta):
            raise ValueError('Z1151_FUNDING')
        if abs(cash_delta)<1e-12:return
        lots=self.lots[asset];size=sum(abs(l['units']) for l in lots)
        if size>1e-12:
            for lot in lots:lot['funding_unit']+=float(cash_delta/size)
        else:
            t=pd.Timestamp(timestamp).isoformat()
            closed=[x for x in self.closed if x['asset']==asset and x['timestamp']==t]
            total=sum(x['closed_units'] for x in closed)
            if total<=1e-12:raise ValueError('Z1151_UNATTRIBUTABLE_FUNDING')
            for x in closed:x['pnl_usd']+=float(cash_delta*x['closed_units']/total)
    def apply_hour(self,events,funding_by_asset,timestamp,order):
        if order not in ('carried_before_fill','new_after_fill'):
            raise ValueError('Z1151_ORDER')
        f=np.asarray(funding_by_asset,float)
        if f.shape!=(4,) or not np.isfinite(f).all():raise ValueError('Z1151_FUNDING_VECTOR')
        if order=='carried_before_fill':
            for j,v in enumerate(f):self.funding(j,float(v),timestamp)
        for e in events:
            if set(e)!={'asset','action','delta_units','fill_price','fee_usd','notional'}:
                raise ValueError('Z1151_EVENT_SCHEMA')
            self.fill(e['asset'],e['delta_units'],e['fill_price'],e['fee_usd'],timestamp)
        if order=='new_after_fill':
            for j,v in enumerate(f):self.funding(j,float(v),timestamp)
    def total_pnl(self,mark):
        p=np.asarray(mark,float)
        if p.shape!=(4,) or not np.isfinite(p).all() or (p<=0).any():
            raise ValueError('Z1151_MARK')
        unrealized=0.
        for j,lots in enumerate(self.lots):
            for l in lots:
                unrealized+=abs(l['units'])*(np.sign(l['units'])*(p[j]-l['price'])
                    -l['fee_unit']+l['funding_unit'])
        return float(sum(x['pnl_usd'] for x in self.closed)+unrealized)
