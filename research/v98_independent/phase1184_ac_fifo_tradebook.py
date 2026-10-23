#!/usr/bin/env python3
"""V98 AC independent FIFO trade-level net PnL observer, no strategy imports."""
from __future__ import annotations
import math
from collections import deque
import numpy as np


class FIFOTradebook:
    def __init__(self, initial_capital):
        if not math.isfinite(initial_capital) or initial_capital <= 0:
            raise ValueError('AC1184_CAPITAL')
        self.initial_capital = float(initial_capital)
        self.lots = [deque() for _ in range(4)]
        self.closed = []
        self.fees = 0.
        self.funding = 0.

    def trade(self, asset, delta, fill_price, fee):
        if (not isinstance(asset,int) or not 0<=asset<4 or
                not all(math.isfinite(float(x)) for x in (delta,fill_price,fee)) or
                fill_price<=0 or fee<0 or (abs(delta)<1e-12 and fee>1e-12)):
            raise ValueError('AC1184_INVALID_TRADE')
        delta=float(delta);price=float(fill_price);fee=float(fee)
        if abs(delta)<1e-12:return
        self.fees+=fee
        remaining=delta
        fee_per_unit=fee/abs(delta)
        queue=self.lots[asset]
        while queue and abs(remaining)>1e-12 and queue[0]['qty']*remaining<0:
            lot=queue[0]
            old_abs=abs(lot['qty'])
            matched=min(abs(remaining),old_abs)
            sign=1 if lot['qty']>0 else -1
            fraction=matched/old_abs
            entry_fee=lot['fee']*fraction
            attributed_funding=lot['funding']*fraction
            exit_fee=fee_per_unit*matched
            net=sign*matched*(price-lot['entry'])-entry_fee-exit_fee+attributed_funding
            self.closed.append({'asset':asset,'side':'long' if sign>0 else 'short',
                                'quantity':matched,'entry':lot['entry'],'exit':price,
                                'gross_pnl':sign*matched*(price-lot['entry']),
                                'entry_fee':entry_fee,'exit_fee':exit_fee,
                                'funding_cash':attributed_funding,'net_pnl':net})
            lot['qty']-=sign*matched
            lot['fee']-=entry_fee
            lot['funding']-=attributed_funding
            remaining+=sign*matched
            if abs(lot['qty'])<1e-12:queue.popleft()
        if abs(remaining)>1e-12:
            queue.append({'qty':remaining,'entry':price,
                          'fee':fee_per_unit*abs(remaining),'funding':0.})

    def apply_funding(self, asset, cash_flow):
        if not isinstance(asset,int) or not 0<=asset<4 or not math.isfinite(cash_flow):
            raise ValueError('AC1184_INVALID_FUNDING')
        flow=float(cash_flow)
        size=sum(abs(lot['qty']) for lot in self.lots[asset])
        if size<1e-12:
            if abs(flow)>1e-9:raise ValueError('AC1184_FUNDING_WITHOUT_INVENTORY')
            return
        self.funding+=flow
        for lot in self.lots[asset]:
            lot['funding']+=flow*abs(lot['qty'])/size

    def positions(self):
        return np.array([sum(lot['qty'] for lot in q) for q in self.lots],float)

    def unrealized(self,marks):
        p=np.asarray(marks,float)
        if p.shape!=(4,) or not np.isfinite(p).all() or np.any(p<=0):
            raise ValueError('AC1184_MARK')
        return float(sum(lot['qty']*(p[j]-lot['entry'])-lot['fee']+lot['funding']
                         for j,q in enumerate(self.lots) for lot in q))

    def realized(self):
        return float(sum(x['net_pnl'] for x in self.closed))

    def reconcile(self,cash,units,marks):
        u=np.asarray(units,float);p=np.asarray(marks,float)
        if u.shape!=(4,) or p.shape!=(4,) or not np.isfinite(u).all() or not math.isfinite(cash):
            raise ValueError('AC1184_LEDGER_INPUT')
        tol=1e-6*self.initial_capital/10000.
        if not np.allclose(self.positions(),u,rtol=0,atol=tol):
            raise ValueError('AC1184_POSITION_RECONCILIATION')
        observed=float(cash+np.dot(u,p)-self.initial_capital)
        accounted=self.realized()+self.unrealized(p)
        if abs(observed-accounted)>tol:
            raise ValueError('AC1184_NAV_RECONCILIATION')
        return {'passed':True,'observed_pnl':observed,'accounted_pnl':accounted,
                'realized':self.realized(),'unrealized':self.unrealized(p),
                'closed_trades':len(self.closed)}

    def trade_metrics(self):
        pnl=np.array([x['net_pnl'] for x in self.closed],float)
        win=pnl[pnl>0];loss=pnl[pnl<0]
        return {'closed_trades':len(pnl),
                'profit_factor':float(win.sum()/-loss.sum()) if len(loss) else None,
                'payoff':float(win.mean()/-loss.mean()) if len(win) and len(loss) else None,
                'win_rate':float(len(win)/len(pnl)) if len(pnl) else None,
                'net_closed_pnl':float(pnl.sum())}
