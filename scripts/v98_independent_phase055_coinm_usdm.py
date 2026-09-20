#!/usr/bin/env python3
"""V98 Independent Phase055 — preregistered COIN-M/USD-M convergence, training only."""
from __future__ import annotations
import io,json,urllib.request,zipfile
from pathlib import Path
import numpy as np,pandas as pd
ASSETS={'BTC':('BTCUSD_PERP','BTCUSDT'),'ETH':('ETHUSD_PERP','ETHUSDT'),'BNB':('BNBUSD_PERP','BNBUSDT'),'XRP':('XRPUSD_PERP','XRPUSDT'),'SOL':('SOLUSD_PERP','SOLUSDT')}
YEARS=[2023,2024,2025]; LOOKBACK=24; REBAL=8; TOTAL_GROSS=.75; SPREAD_GROSS=TOTAL_GROSS/2
COSTS={'base':.0007,'severe':.0012,'supersevere':.0020}; OUT=Path('reports/v98_independent_phase055_coinm_usdm.json')
def getzip(url):
 req=urllib.request.Request(url,headers={'User-Agent':'CryptoAI-V98-Independent/1.0'}); raw=urllib.request.urlopen(req,timeout=30).read()
 with zipfile.ZipFile(io.BytesIO(raw)) as z:return z.read(z.namelist()[0])
def kline(kind,s,y,m):
 root='cm' if kind=='cm' else 'um'; u=f'https://data.binance.vision/data/futures/{root}/monthly/klines/{s}/1h/{s}-1h-{y}-{m:02d}.zip'
 try:
  a=pd.read_csv(io.BytesIO(getzip(u)),header=None); t=pd.to_numeric(a[0],errors='coerce'); c=pd.to_numeric(a[4],errors='coerce'); ok=t.notna()&c.notna(); t=t[ok]; c=c[ok]; unit='us' if float(t.iloc[0])>1e14 else 'ms'; return pd.Series(c.values,index=pd.to_datetime(t.values,unit=unit,utc=True))
 except Exception:return pd.Series(dtype=float)
def funding(kind,s,y,m):
 root='cm' if kind=='cm' else 'um'; u=f'https://data.binance.vision/data/futures/{root}/monthly/fundingRate/{s}/{s}-fundingRate-{y}-{m:02d}.zip'
 try:
  a=pd.read_csv(io.BytesIO(getzip(u))); cols={x.lower():x for x in a.columns}; tc=next(v for k,v in cols.items() if 'time' in k); rc=next(v for k,v in cols.items() if 'funding' in k and 'rate' in k); t=pd.to_numeric(a[tc],errors='coerce'); r=pd.to_numeric(a[rc],errors='coerce'); ok=t.notna()&r.notna(); unit='us' if float(t[ok].iloc[0])>1e14 else 'ms'; return pd.Series(r[ok].values,index=pd.to_datetime(t[ok].values,unit=unit,utc=True))
 except Exception:return pd.Series(dtype=float)
def metrics(r):
 r=r.dropna(); eq=(1+r).cumprod(); dd=eq/eq.cummax()-1; d=r.resample('1D').sum(); w=d[d>0]; l=-d[d<0]
 return {'return':float(eq.iloc[-1]-1) if len(eq) else None,'max_drawdown':float(dd.min()) if len(dd) else None,'profit_factor_daily':float(w.sum()/l.sum()) if l.sum()>0 else None,'payoff_daily':float(w.mean()/l.mean()) if len(w) and len(l) else None,'win_rate_daily':float((d>0).mean()) if len(d) else None,'positive_days':int((d>0).sum()),'days':int(len(d))}
def main():
 C={};U={};FC={};FU={}
 for a,(cm,um) in ASSETS.items():
  cc=[];uu=[];fc=[];fu=[]
  for y in YEARS:
   for m in range(1,13): cc.append(kline('cm',cm,y,m)); uu.append(kline('um',um,y,m)); fc.append(funding('cm',cm,y,m)); fu.append(funding('um',um,y,m))
  C[a]=pd.concat(cc).sort_index(); U[a]=pd.concat(uu).sort_index(); FC[a]=pd.concat(fc).sort_index() if any(len(x) for x in fc) else pd.Series(dtype=float); FU[a]=pd.concat(fu).sort_index() if any(len(x) for x in fu) else pd.Series(dtype=float)
 cm=pd.concat(C,axis=1).sort_index(); um=pd.concat(U,axis=1).reindex(cm.index); basis=np.log(cm/um).replace([np.inf,-np.inf],np.nan)
 score=-basis.shift(1).rolling(LOOKBACK,min_periods=LOOKBACK).mean(); ranks=score.rank(axis=1,pct=True)-.5; raw=ranks.sub(ranks.mean(axis=1),axis=0); w=raw.div(raw.abs().sum(axis=1),axis=0).fillna(0)*SPREAD_GROSS
 event=pd.Series(np.arange(len(w))%REBAL==0,index=w.index); w=w.where(event,np.nan).ffill().fillna(0)
 spread_ret=cm.pct_change(fill_method=None)-um.pct_change(fill_method=None); gross=(w.shift(1).fillna(0)*spread_ret.fillna(0)).sum(axis=1)
 fcm=pd.DataFrame(0.,index=w.index,columns=ASSETS); fum=fcm.copy()
 for a in ASSETS:
  ix=fcm.index.intersection(FC[a].index); fcm.loc[ix,a]=FC[a].reindex(ix).values; ix=fum.index.intersection(FU[a].index); fum.loc[ix,a]=FU[a].reindex(ix).values
 # long COIN-M weight w pays cm funding; opposite USD-M leg (-w) pays/receives its funding
 funding_pnl=(-(w.shift(1)*fcm).sum(axis=1)+(w.shift(1)*fum).sum(axis=1)).fillna(0)
 turnover=2*w.diff().abs().sum(axis=1).fillna(2*w.abs().sum(axis=1)); pre=gross+funding_pnl
 scenarios={n:metrics(pre-turnover*c) for n,c in COSTS.items()}; base=pre-turnover*COSTS['base']; folds={str(y):metrics(base.loc[f'{y}-01-01':f'{y}-12-31 23:59']) for y in YEARS}
 btc=um['BTC'].pct_change(24); reg=pd.Series(np.where(btc>.02,'bull',np.where(btc<-.02,'bear','sideways')),index=um.index); regimes={k:metrics(base[reg==k]) for k in ['bull','bear','sideways']}
 absw=w.abs(); share=absw.max(axis=1)/absw.sum(axis=1).replace(0,np.nan); daily=base.resample('1D').sum(); tails={'best_day':float(daily.max()),'worst_day':float(daily.min()),'p01_day':float(daily.quantile(.01)),'p99_day':float(daily.quantile(.99))}
 conc={'mean_top1_spread_share':float(share.mean()),'p95_top1_spread_share':float(share.quantile(.95)),'mean_active_spreads':float((absw>0).sum(axis=1).mean()),'turnover_total_both_legs':float(turnover.sum())}
 b=scenarios['base']; ss=scenarios['supersevere']; gate=bool(b['return']>0 and b['profit_factor_daily'] is not None and b['profit_factor_daily']>=1.15 and scenarios['severe']['return']>0 and ss['profit_factor_daily'] is not None and ss['profit_factor_daily']>=1.0 and sum(v['return']>0 for v in folds.values())>=2)
 report={'engine':'V98 Independent','phase':'055','mechanism':'COIN-M/USD-M collateral dislocation convergence','preregistered':{'assets':list(ASSETS),'training':'2023-01-01..2025-12-31','lookback_hours':LOOKBACK,'rebalance_hours':REBAL,'total_leg_gross':TOTAL_GROSS,'cost_per_traded_leg':COSTS},'guardrails':{'validation_accessed':False,'final_holdout_accessed':False,'v99_used':False,'parameter_search':False,'sign_search':False},'coverage':{'coinm_hours':{a:int(C[a].notna().sum()) for a in ASSETS},'usdm_hours':{a:int(U[a].notna().sum()) for a in ASSETS},'coinm_funding_events':{a:int(FC[a].notna().sum()) for a in ASSETS},'usdm_funding_events':{a:int(FU[a].notna().sum()) for a in ASSETS}},'scenarios':scenarios,'folds':folds,'regimes':regimes,'concentration':conc,'tails':tails,'training_gate_pass':gate,'decision':'PROMOTE_TO_VALIDATION_GATE' if gate else 'REJECT_NO_RESCUE'}
 OUT.write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps({'phase':'055','gate':gate,'scenarios':scenarios,'folds':folds,'regimes':regimes,'concentration':conc,'tails':tails},indent=2))
if __name__=='__main__':main()
