from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,validate_data
import v98_independent_phase003_dispersion_neutral as p3
CFG=PROJECT/'config'/'v98_independent.json';OUT=PROJECT/'reports'/'v98_independent_phase196_idiovol_reversion.json';PREREG=PROJECT/'research'/'v98_independent'/'phase196_prereg.md'
ASSETS=['BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT'];A='2023-01-01';B='2025-12-31';CAP=1.0
GRID=[(d,s,h) for d in (6,24) for s in (1.5,2.0) for h in (6,12)]
def overlay(data,d,s,hold):
 c=data.close[ASSETS];r=np.log(c/c.shift(1));mkt=r.mean(axis=1)
 # Every decision-t feature ends at t-1. Rolling beta is estimated only from completed returns.
 cov=r.rolling(168,min_periods=168).cov(mkt);var=mkt.rolling(168,min_periods=168).var().replace(0,np.nan);beta=cov.div(var,axis=0)
 resid=r-beta.mul(mkt,axis=0)
 disp=resid.shift(1).rolling(d,min_periods=d).sum()
 rv=resid.shift(1).rolling(24,min_periods=24).std()
 rvmed=rv.shift(1).rolling(168,min_periods=168).median().replace(0,np.nan)
 ratio=rv/rvmed
 score=disp.where(ratio>s)
 out=pd.DataFrame(0.,index=c.index,columns=c.columns);remaining=0;pos={}
 for t in c.index:
  if remaining>0:
   for a,w in pos.items():out.at[t,a]=w
   remaining-=1;continue
  z=score.loc[t].dropna()
  if len(z)<2:continue
  lo=z.idxmin();hi=z.idxmax()
  if lo==hi:continue
  # post-shock relative reversion: long negative residual displacement, short positive.
  pos={lo:.5,hi:-.5};remaining=hold
  for a,w in pos.items():out.at[t,a]=w
  remaining-=1
 return out
def ev(data,t,cfg,z):
 f=cfg['funding_stress'][z];return exact_fast(data,t,cost_per_side=cfg['costs'][f'{z}_per_side'],gross_guard_cap=CAP,funding_debit_multiplier=f['debit_multiplier'],funding_credit_multiplier=f['credit_multiplier'])
def audit(r,data,t):
 m=p3.metrics(r,A,B);daily=r.equity.loc[A:B].resample('1D').last().pct_change(fill_method=None).dropna();pos=daily[daily>0];neg=daily[daily<0]
 w=t.loc[A:B,ASSETS].abs();gross=w.sum(axis=1).replace(0,np.nan);top=w.max(axis=1)/gross;net=t.loc[A:B,ASSETS].sum(axis=1).abs();active=gross.fillna(0)>0
 return {'metrics':m,'regimes':p3.regime_metrics(r,data,f'{A}T00:00:00+00:00',f'{B}T00:00:00+00:00',f'{B}T00:00:00+00:00'),'concentration':{'mean_top1_share':float(top.mean()) if top.notna().any() else 0.,'p95_top1_share':float(top.quantile(.95)) if top.notna().any() else 0.},'tails':{'top10_positive_share':float(pos.nlargest(10).sum()/pos.sum()) if pos.sum()>0 else 0.,'bottom10_negative_share':float(abs(neg.nsmallest(10).sum())/abs(neg.sum())) if neg.sum()<0 else 0.},'exposure':{'max_abs_net':float(net.max()),'max_gross':float(gross.fillna(0).max())},'activity':{'active_hours':int(active.sum()),'episodes':int((active&~active.shift(1,fill_value=False)).sum())}}
def main():
 cfg=json.loads(CFG.read_text());pre=PREREG.read_text();assert 'FROZEN BEFORE EXECUTION' in pre and 'Phase196' in pre
 data=load_data(PROJECT,cfg['data_config']);v=validate_data(data);assert not v['errors'],v['errors'][:5]
 assert data.close.loc['2026-01-01':].empty and data.funding.loc['2026-01-01':].empty
 specs={}
 for d,s,h in GRID:
  key=f'd{d}_s{s:g}_h{h}';t=overlay(data,d,s,h);rs={z:ev(data,t,cfg,z) for z in ('base','severe','supersevere')};base=audit(rs['base'],data,t)
  specs[key]={'params':{'displacement_hours':d,'shock_ratio':s,'hold_hours':h},'base':base,'severe':p3.metrics(rs['severe'],A,B),'supersevere':p3.metrics(rs['supersevere'],A,B),'folds':{y:p3.metrics(rs['base'],f'{y}-01-01',f'{y}-12-31') for y in ('2023','2024','2025')}}
 eligible=[]
 for k,x in specs.items():
  fail=[];m=x['base']['metrics'];folds=x['folds'];reg=x['base']['regimes'];nonneg=sum(1 for q in reg.values() if q.get('return_sum_approx',q.get('return_sum',q.get('total_return',-1)))>=0)
  if m['total_return']<=0 or m['profit_factor_daily']<=1:fail.append('base_edge')
  if m['max_drawdown']<-.35:fail.append('base_drawdown')
  if any(folds[y]['total_return']<=0 or folds[y]['profit_factor_daily']<=1 for y in ('2023','2024','2025')):fail.append('fold_inconsistency')
  for z,dd in (('severe',-.40),('supersevere',-.45)):
   if x[z]['total_return']<=0 or x[z]['profit_factor_daily']<=1:fail.append(f'{z}_edge')
   if x[z]['max_drawdown']<dd:fail.append(f'{z}_drawdown')
  if nonneg<2:fail.append('regime_breadth')
  if x['base']['concentration']['mean_top1_share']>.60:fail.append('concentration')
  if x['base']['tails']['top10_positive_share']>=.50 or x['base']['tails']['bottom10_negative_share']>=.50:fail.append('tails')
  if x['base']['activity']['episodes']<60:fail.append('insufficient_activity')
  if x['base']['exposure']['max_gross']>CAP+2e-5 or x['base']['exposure']['max_abs_net']>2e-5 or m['ruin']:fail.append('risk_invariant')
  x['failures']=sorted(set(fail))
  if not x['failures']:eligible.append(k)
 def rank(k):
  x=specs[k];return (min(x['folds'][y]['profit_factor_daily'] for y in ('2023','2024','2025')),x['supersevere']['profit_factor_daily'],-abs(x['base']['metrics']['max_drawdown']),-x['base']['metrics'].get('turnover_sum',0))
 winner=max(eligible,key=rank) if eligible else None
 report={'engine':'V98 Independent','phase':196,'training_only':True,'window':[A,B],'validation':None,'final_holdout':None,'v16_used':False,'v99_used':False,'prereg_sha256':hashlib.sha256(PREREG.read_bytes()).hexdigest(),'grid_size':len(GRID),'specs':specs,'gate':{'passed':winner is not None,'winner':winner,'decision':'PASS_TRAINING_FREEZE_FOR_SEPARATE_VALIDATION_PREREG' if winner else 'REJECT_FAMILY_NO_RESCUE'}}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True))
if __name__=='__main__':main()
