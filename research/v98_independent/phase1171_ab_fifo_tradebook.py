#!/usr/bin/env python3
"""AB independent FIFO closed-trade accounting with fee/funding attribution."""
from __future__ import annotations
import numpy as np

class Tradebook:
    def __init__(self,assets=4):
        self.lots=[[] for _ in range(assets)]
        self.closed=[]
    def position(self,asset):
        return sum(x['qty'] for x in self.lots[asset])
    def funding(self,asset,cash_delta):
        if not np.isfinite(cash_delta):raise ValueError('AB1171_FUNDING')
        lots=self.lots[asset];gross=sum(abs(x['qty']) for x in lots)
        if gross<1e-12:
            if abs(cash_delta)>1e-9:raise ValueError('AB1171_FUNDING_WITHOUT_INVENTORY')
            return
        for lot in lots:lot['funding']+=cash_delta*abs(lot['qty'])/gross
    def trade(self,asset,delta,price,fee):
        if not all(np.isfinite(v) for v in (delta,price,fee)) or price<=0 or fee<0:
            raise ValueError('AB1171_INVALID_TRADE')
        if abs(delta)<1e-12:
            if fee>1e-12:raise ValueError('AB1171_FEE_WITHOUT_TRADE')
            return []
        size=abs(delta);direction=np.sign(delta);remaining=size;closed=[]
        lots=self.lots[asset]
        while remaining>1e-12 and lots and np.sign(lots[0]['qty'])!=direction:
            lot=lots[0];prior_abs=abs(lot['qty']);matched=min(remaining,prior_abs)
            entry_fee=lot['fee']*matched/prior_abs
            funding=lot['funding']*matched/prior_abs
            exit_fee=fee*matched/size
            pnl=(price-lot['entry'])*matched*np.sign(lot['qty'])
            record={'asset':asset,'quantity':matched,
                'direction':'LONG' if lot['qty']>0 else 'SHORT',
                'entry_price':lot['entry'],'exit_price':price,'gross_pnl':pnl,
                'entry_fee':entry_fee,'exit_fee':exit_fee,'funding_cash':funding,
                'net_pnl':pnl-entry_fee-exit_fee+funding}
            closed.append(record);self.closed.append(record)
            lot['qty']-=np.sign(lot['qty'])*matched
            lot['fee']-=entry_fee;lot['funding']-=funding
            remaining-=matched
            if abs(lot['qty'])<1e-12:lots.pop(0)
        if remaining>1e-12:
            open_fee=fee*remaining/size
            lots.append({'qty':direction*remaining,'entry':price,'fee':open_fee,'funding':0.})
        return closed
    def metrics(self):
        pnl=np.array([x['net_pnl'] for x in self.closed],float)
        wins=pnl[pnl>0];losses=pnl[pnl<0]
        return {'closed_trades':int(len(pnl)),
            'net_realized_pnl':float(pnl.sum()),
            'profit_factor':float(wins.sum()/(-losses.sum())) if len(losses) else None,
            'payoff':float(wins.mean()/(-losses.mean())) if len(wins) and len(losses) else None,
            'win_rate':float(len(wins)/len(pnl)) if len(pnl) else None,
            'open_lots':int(sum(map(len,self.lots)))}
