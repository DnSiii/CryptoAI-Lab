from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,validate_data
import v98_independent_phase003_dispersion_neutral as p3
CFG=PROJECT/'config'/'v98_independent.json';OUT=PROJECT/'reports'/'v98_independent_phase195_liquidity_adjusted_trend.json';PREREG=PROJECT/'research'/'v98_independent'/'phase195_prereg.md'
ASSETS=['BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT'];A='2023-01-01';B='2025-12-31';CAP=1.0
GRID=[(tr,liq,h) for tr in (24,72) for liq in (24,168) for h in (6,12)]
def overlay(data,tr,liq,hold):
 c=data.close[ASSETS];q=data.frames['quote_volume'][ASSETS]
 # Decision t uses completed observations through t-1 only.
 ret=np.log(c.shift(1)/c.shift(1+tr));qtrail=q.shift(1).rolling(liq,min_periods=liq).sum()
 med=qtrail.median(axis=1);eligible=qtrail.ge(med,axis=0)
 # denominator is contemporaneous trailing quote volume of eligible assets only.
 denom=qtrail.where(eligible).sum(axis=1).replace(0,np.nan);share=qtrail.div(denom,axis=0)
 score=ret/np.sqrt(share.clip(lower=1e-12));score=score.where(eligible)
 out=pd.DataFrame(0.,index=c.index,columns=c.columns);remaining=0;pos={}
 for t in c.index:
  if remaining>0:
   for a,w in pos.items():out.at[t,a]=w
   remaining-=1;continue
  s=score.loc[t].dropna()
  if len(s)<2:continue
  lo=s.idxmin();hi=s.idxmax()
  if lo==hi:continue
  pos={hi:.5,lo:-.5};remaining=hold
  for a,w in pos.items():out.at[t,a]=w
  remaining-=1
 return out
def ev(data,t,cfg,z):
 f=cfg['funding_stress'][z];return exact_fast(data,t,cost_per_side=cfg['costs'][f'{z}_per_side'],gross_guard_cap=CAP,funding_debit_multiplier=f['debit_multiplier'],funding_credit_multiplier=f['credit_multiplier'])
def audit(r,data,t):
 m=p3.metrics(r,A,B);d=r.equity.loc[A:B].resample('1D').last().pct_change(fill_method=None).dropna();pos=d[d>0];neg=d[d<0];w=t.loc[A:B,ASSETS].abs();gross=w.sum(axis=1).replace(0,np.nan);top=w.max(axis=1)/gross;net=t.loc[A:B,ASSETS].sum(axis=1).abs();active=gross.fillna(0)>0
 return {'metrics':m,'regimes':p3.regime_metrics(r,data,f'{A}T00:00:00+00:00',f'{B}T00:00:00+00:00',f'{B}T00:00:00+00:00'),'concentration':{'mean_top1_share':float(top.mean()) if top.notna().any() else 0.,'p95_top1_share':float(top.quantile(.95)) if top.notna().any() else 0.},'tails':{'top10_positive_share':float(pos.nlargest(10).sum()/pos.sum()) if pos.sum()>0 else 0.,'bottom10_negative_share':float(abs(neg.nsmallest(10).sum())/abs(neg.sum())) if neg.sum()<0 else 0.},'exposure':{'max_abs_net':float(net.max()),'max_gross':float(gross.fillna(0).max())},'activity':{'active_hours':int(active.sum()),'episodes':int((active&~active.shift(1,fill_value=False)).sum())}}
def main():
 cfg=json.loads(CFG.read_text());pre=PREREG.read_text();assert 'FROZEN BEFORE EXECUTION' in pre and 'Phase195' in pre
 data=load_data(PROJECT,cfg['data_config']);v=validate_data(data);assert not v['errors'],v['errors'][:5]
 assert data.close.loc['2026-01-01':].empty and data.frames['quote_volume'].loc['2026-01-01':].empty and data.funding.loc['2026-01-01':].empty
 specs={}
 for tr,liq,h in GRID:
  key=f't{tr}_q{liq}_h{h}';t=overlay(data,tr,liq,h);rs={z:ev(data,t,cfg,z) for z in ('base','severe','supersevere')};base=audit(rs['base'],data,t)
  specs[key]={'params':{'trend_hours':tr,'liquidity_hours':liq,'hold_hours':h},'base':base,'severe':p3.metrics(rs['severe'],A,B),'supersevere':p3.metrics(rs['supersevere'],A,B),'folds':{y:p3.metrics(rs['base'],f'{y}-01-01',f'{y}-12-31') for y in ('2023','2024','2025')}}
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
 report={'engine':'V98 Independent','phase':195,'training_only':True,'window':[A,B],'validation':None,'final_holdout':None,'v16_used':False,'v99_used':False,'prereg_sha256':hashlib.sha256(PREREG.read_bytes()).hexdigest(),'grid_size':len(GRID),'specs':specs,'gate':{'passed':winner is not None,'winner':winner,'decision':'PASS_TRAINING_FREEZE_FOR_SEPARATE_VALIDATION_PREREG' if winner else 'REJECT_FAMILY_NO_RESCUE'}}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True))
if __name__=='__main__':main()
