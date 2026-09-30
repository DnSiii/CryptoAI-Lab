from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,validate_data
import v98_independent_phase003_dispersion_neutral as p3
CFG=PROJECT/'config'/'v98_independent.json';OUT=PROJECT/'reports'/'v98_independent_phase199_funding_pressure_reversion.json';PREREG=PROJECT/'reports'/'v98_independent_phase199_prereg.md'
ASSETS=['BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT'];A='2023-01-01';B='2025-12-31';CAP=1.0
GRID=[(w,q,h) for w in (24,72) for q in (.20,.30) for h in (8,24)]
def overlay(data,w,q,h):
 f=data.funding[ASSETS].shift(1).rolling(w,min_periods=w).mean();raw=pd.DataFrame(0.,index=f.index,columns=ASSETS)
 n=max(1,int(np.floor(len(ASSETS)*q)))
 for ts,row in f.iterrows():
  valid=row.dropna().sort_values(kind='mergesort')
  if len(valid)<2*n: continue
  lo=list(valid.index[:n]);hi=list(valid.index[-n:]);raw.loc[ts,lo]=.5/n;raw.loc[ts,hi]=-.5/n
 decision=pd.Series((np.arange(len(f.index))%h)==0,index=f.index);t=pd.DataFrame(np.nan,index=f.index,columns=data.close.columns);t.loc[decision,ASSETS]=raw.loc[decision,ASSETS];return t.ffill().fillna(0.)
def ev(data,t,cfg,z):
 f=cfg['funding_stress'][z];return exact_fast(data,t,cost_per_side=cfg['costs'][f'{z}_per_side'],gross_guard_cap=CAP,funding_debit_multiplier=f['debit_multiplier'],funding_credit_multiplier=f['credit_multiplier'])
def audit(r,data,t):
 m=p3.metrics(r,A,B);d=r.equity.loc[A:B].resample('1D').last().pct_change(fill_method=None).dropna();pos=d[d>0];neg=d[d<0];conc=t.loc[A:B,ASSETS].abs();gross=conc.sum(axis=1).replace(0,np.nan);top=conc.max(axis=1)/gross;net=t.loc[A:B,ASSETS].sum(axis=1).abs()
 return {'metrics':m,'regimes':p3.regime_metrics(r,data,f'{A}T00:00:00+00:00',f'{B}T00:00:00+00:00',f'{B}T00:00:00+00:00'),'concentration':{'mean_top1_share':float(top.mean()) if top.notna().any() else 0.,'p95_top1_share':float(top.quantile(.95)) if top.notna().any() else 0.},'tails':{'top10_positive_share':float(pos.nlargest(10).sum()/pos.sum()) if pos.sum()>0 else 0.,'bottom10_negative_share':float(abs(neg.nsmallest(10).sum())/abs(neg.sum())) if neg.sum()<0 else 0.},'exposure':{'max_abs_net':float(net.max()),'max_gross':float(gross.fillna(0).max()),'active_hours':int(gross.notna().sum())}}
def main():
 cfg=json.loads(CFG.read_text());pre=PREREG.read_text();assert 'FROZEN BEFORE IMPLEMENTATION/RESULTS' in pre and 'Phase199' in pre;data=load_data(PROJECT,cfg['data_config']);v=validate_data(data);assert not v['errors'],v['errors'][:5];assert data.close.loc['2026-01-01':].empty and data.funding.loc['2026-01-01':].empty
 specs={}
 for w,q,h in GRID:
  key=f'f{w}_q{int(q*100)}_h{h}';t=overlay(data,w,q,h);rs={z:ev(data,t,cfg,z) for z in ('base','severe','supersevere')};base=audit(rs['base'],data,t);specs[key]={'params':{'funding_lookback_hours':w,'tail':q,'rebalance_hours':h},'base':base,'severe':p3.metrics(rs['severe'],A,B),'supersevere':p3.metrics(rs['supersevere'],A,B),'folds':{y:p3.metrics(rs['base'],f'{y}-01-01',f'{y}-12-31') for y in ('2023','2024','2025')}}
 eligible=[]
 for k,x in specs.items():
  fail=[];m=x['base']['metrics'];folds=x['folds'];reg=x['base']['regimes'];nonneg=sum(1 for r in reg.values() if r.get('return_sum_approx',r.get('return_sum',r.get('total_return',-1)))>=0)
  if x['base']['exposure']['active_hours']==0:fail.append('zero_activity')
  if m['total_return']<=0 or m['profit_factor_daily']<=1:fail.append('base_edge')
  if m['max_drawdown']<-.35:fail.append('base_drawdown')
  if any(folds[y]['total_return']<=0 or folds[y]['profit_factor_daily']<=1 for y in ('2023','2024','2025')):fail.append('fold_inconsistency')
  for z,dd in (('severe',-.40),('supersevere',-.45)):
   if x[z]['total_return']<=0 or x[z]['profit_factor_daily']<=1:fail.append(f'{z}_edge')
   if x[z]['max_drawdown']<dd:fail.append(f'{z}_drawdown')
  if nonneg<2:fail.append('regime_breadth')
  if x['base']['concentration']['mean_top1_share']>.60:fail.append('concentration')
  if x['base']['tails']['top10_positive_share']>=.50 or x['base']['tails']['bottom10_negative_share']>=.50:fail.append('tails')
  if x['base']['exposure']['max_gross']>CAP+2e-5 or x['base']['exposure']['max_abs_net']>2e-5 or m['ruin']:fail.append('risk_invariant')
  x['failures']=sorted(set(fail));
  if not x['failures']:eligible.append(k)
 def rank(k):
  x=specs[k];return (min(x['folds'][y]['profit_factor_daily'] for y in ('2023','2024','2025')),x['supersevere']['profit_factor_daily'],-abs(x['base']['metrics']['max_drawdown']),-x['base']['metrics'].get('turnover_sum',0))
 winner=max(eligible,key=rank) if eligible else None
 report={'engine':'V98 Independent','phase':199,'training_only':True,'window':[A,B],'validation':None,'final_holdout':None,'v16_used':False,'v99_used':False,'prereg_sha256':hashlib.sha256(PREREG.read_bytes()).hexdigest(),'grid_size':len(GRID),'specs':specs,'gate':{'passed':winner is not None,'winner':winner,'decision':'PASS_TRAINING_FREEZE_FOR_SEPARATE_VALIDATION_PREREG' if winner else 'REJECT_FAMILY_NO_RESCUE'}};OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True))
if __name__=='__main__':main()
