#!/usr/bin/env python3
"""V98 Independent Phase053 — preregistered spot/perp basis convergence.
Training only (2023-2025). Validation/holdout are never requested.
Frozen before returns: 5 assets, 24h lagged mean log(perp/spot), convergence sign,
8h rebalance, cross-sectional demean/L1 gross 0.75. No parameter search/rescue.
"""
from __future__ import annotations
import io,json,urllib.request,zipfile
from pathlib import Path
import numpy as np,pandas as pd
SYMS=['BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT']; YEARS=[2023,2024,2025]
OUT=Path('reports/v98_independent_phase053_spot_perp_basis.json')
GROSS=.75; LOOKBACK=24; REBAL=8
COSTS={'base':.0007,'severe':.0012,'supersevere':.0020} # per side fee+slippage

def getzip(url):
 req=urllib.request.Request(url,headers={'User-Agent':'CryptoAI-V98-Independent/1.0'})
 with urllib.request.urlopen(req,timeout=30) as r:b=r.read()
 with zipfile.ZipFile(io.BytesIO(b)) as z:return z.read(z.namelist()[0])
def klines(mkt,s,y,m):
 root='spot' if mkt=='spot' else 'futures/um'; u=f'https://data.binance.vision/data/{root}/monthly/klines/{s}/1h/{s}-1h-{y}-{m:02d}.zip'
 try:
  a=pd.read_csv(io.BytesIO(getzip(u)),header=None); t=pd.to_numeric(a[0],errors='coerce'); c=pd.to_numeric(a[4],errors='coerce'); ok=t.notna()&c.notna(); t=t[ok]; c=c[ok]
  # archives may encode microseconds in newer files; training dates are ms, guard anyway
  unit='us' if float(t.iloc[0])>1e14 else 'ms'; return pd.Series(c.values,index=pd.to_datetime(t.values,unit=unit,utc=True),name=s)
 except Exception:return pd.Series(dtype=float,name=s)
def funding(s,y,m):
 u=f'https://data.binance.vision/data/futures/um/monthly/fundingRate/{s}/{s}-fundingRate-{y}-{m:02d}.zip'
 try:
  a=pd.read_csv(io.BytesIO(getzip(u))); cols={x.lower():x for x in a.columns}; tc=next(v for k,v in cols.items() if 'time' in k); rc=next(v for k,v in cols.items() if 'funding' in k and 'rate' in k)
  t=pd.to_numeric(a[tc],errors='coerce'); r=pd.to_numeric(a[rc],errors='coerce'); ok=t.notna()&r.notna(); unit='us' if float(t[ok].iloc[0])>1e14 else 'ms'; return pd.Series(r[ok].values,index=pd.to_datetime(t[ok].values,unit=unit,utc=True),name=s)
 except Exception:return pd.Series(dtype=float,name=s)
def metrics(r):
 r=r.dropna(); eq=(1+r).cumprod(); dd=eq/eq.cummax()-1; pos=r[r>0].sum(); neg=-r[r<0].sum(); days=r.resample('1D').sum(); wins=days[days>0]; losses=-days[days<0]
 return {'return':float(eq.iloc[-1]-1) if len(eq) else None,'max_drawdown':float(dd.min()) if len(dd) else None,'profit_factor_daily':float(wins.sum()/losses.sum()) if losses.sum()>0 else None,'payoff_daily':float(wins.mean()/losses.mean()) if len(wins) and len(losses) else None,'win_rate_daily':float((days>0).mean()) if len(days) else None,'positive_days':int((days>0).sum()),'days':int(len(days))}
def main():
 spot={}; perp={}; fund={}
 for s in SYMS:
  ss=[];pp=[];ff=[]
  for y in YEARS:
   for m in range(1,13): ss.append(klines('spot',s,y,m)); pp.append(klines('perp',s,y,m)); ff.append(funding(s,y,m))
  spot[s]=pd.concat(ss).sort_index(); perp[s]=pd.concat(pp).sort_index(); fund[s]=pd.concat(ff).sort_index() if any(len(x) for x in ff) else pd.Series(dtype=float)
 S=pd.concat(spot,axis=1).sort_index(); P=pd.concat(perp,axis=1).reindex(S.index); basis=np.log(P/S).replace([np.inf,-np.inf],np.nan)
 # only information through t-1 enters signal at t
 score=-basis.shift(1).rolling(LOOKBACK,min_periods=LOOKBACK).mean()
 ranks=score.rank(axis=1,pct=True)-.5; raw=ranks.sub(ranks.mean(axis=1),axis=0); w=raw.div(raw.abs().sum(axis=1),axis=0).fillna(0)*GROSS
 event=pd.Series(np.arange(len(w))%REBAL==0,index=w.index); w=w.where(event, np.nan).ffill().fillna(0)
 ret=P.pct_change(fill_method=None).fillna(0); gross=(w.shift(1).fillna(0)*ret).sum(axis=1)
 # funding: long pays positive rate, aligned at published timestamps
 F=pd.DataFrame(0.,index=w.index,columns=SYMS)
 for s in SYMS:
  x=fund[s]; common=F.index.intersection(x.index); F.loc[common,s]=x.reindex(common).values
 funding_pnl=-(w.shift(1).fillna(0)*F).sum(axis=1); turnover=w.diff().abs().sum(axis=1).fillna(w.abs().sum(axis=1))
 scenarios={}
 for name,c in COSTS.items(): scenarios[name]=metrics(gross+funding_pnl-turnover*c)
 folds={str(y):metrics((gross+funding_pnl-turnover*COSTS['base']).loc[f'{y}-01-01':f'{y}-12-31 23:59']) for y in YEARS}
 base=gross+funding_pnl-turnover*COSTS['base']; btc=P['BTCUSDT'].pct_change(24); reg=pd.Series(np.where(btc>.02,'bull',np.where(btc<-.02,'bear','sideways')),index=P.index)
 regimes={k:metrics(base[reg==k]) for k in ['bull','bear','sideways']}
 absw=w.abs(); conc={'mean_top1_weight_share':float((absw.max(axis=1)/absw.sum(axis=1).replace(0,np.nan)).mean()),'p95_top1_weight_share':float((absw.max(axis=1)/absw.sum(axis=1).replace(0,np.nan)).quantile(.95)),'mean_active_assets':float((absw>0).sum(axis=1).mean()),'turnover_total':float(turnover.sum())}
 gate=bool(scenarios['base']['profit_factor_daily'] is not None and scenarios['base']['profit_factor_daily']>=1.15 and scenarios['base']['return']>0 and scenarios['severe']['return']>0 and scenarios['supersevere']['profit_factor_daily'] is not None and scenarios['supersevere']['profit_factor_daily']>=1.0 and sum(v['return']>0 for v in folds.values())>=2)
 report={'engine':'V98 Independent','phase':'053','mechanism':'spot-perpetual basis convergence','preregistered':{'symbols':SYMS,'training':'2023-01-01..2025-12-31','lookback_hours':LOOKBACK,'rebalance_hours':REBAL,'gross':GROSS,'signal':'negative lagged 24h mean log(perp/spot), cross-sectional demeaned','cost_per_side':COSTS},'guardrails':{'validation_accessed':False,'final_holdout_accessed':False,'v99_used':False,'parameter_search':False,'sign_search':False},'coverage':{'spot_hours':{s:int(spot[s].notna().sum()) for s in SYMS},'perp_hours':{s:int(perp[s].notna().sum()) for s in SYMS},'funding_events':{s:int(fund[s].notna().sum()) for s in SYMS}},'scenarios':scenarios,'folds':folds,'regimes':regimes,'concentration':conc,'training_gate_pass':gate,'decision':'PROMOTE_TO_VALIDATION_GATE' if gate else 'REJECT_NO_RESCUE'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'phase':'053','gate':gate,'base':scenarios['base'],'severe':scenarios['severe'],'supersevere':scenarios['supersevere'],'folds':folds},indent=2))
if __name__=='__main__':main()
