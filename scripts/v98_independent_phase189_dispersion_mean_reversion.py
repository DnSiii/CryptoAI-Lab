from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,validate_data
import v98_independent_phase003_dispersion_neutral as p3
CFG=PROJECT/'config'/'v98_independent.json';OUT=PROJECT/'reports'/'v98_independent_phase189_dispersion_mean_reversion.json';PREREG=PROJECT/'reports'/'v98_independent_phase189_preregister.json'
ASSETS=['BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT'];A='2023-01-01';B='2025-12-31';TARGET=.30;CAP=.35
GRID=[(h,w,q) for h in (6,12) for w in (60,120) for q in (.80,.90)]
def overlay(data,horizon,window_hours,quantile):
 lag=data.close[ASSETS].shift(1);ret=lag.pct_change(horizon,fill_method=None);med=ret.median(axis=1);dev=ret.sub(med,axis=0);disp=dev.abs().median(axis=1);ref=disp.rolling(window_hours,min_periods=max(24,window_hours//2)).quantile(quantile).shift(1);active=(disp>ref)&ref.notna();idx=data.close.index;t=pd.DataFrame(np.nan,index=idx,columns=data.close.columns);decision=idx.hour==0
 for ts in idx[decision]:
  w=pd.Series(0.,index=ASSETS)
  if bool(active.get(ts,False)):
   d=dev.loc[ts].dropna().sort_values();w[d.index[0]]=TARGET/2;w[d.index[-1]]=-TARGET/2
  t.loc[ts,ASSETS]=w
 return t.where(pd.Series(decision,index=idx),np.nan).ffill().fillna(0.)
def ev(data,t,cfg,z):
 f=cfg['funding_stress'][z];return exact_fast(data,t,cost_per_side=cfg['costs'][f'{z}_per_side'],gross_guard_cap=CAP,funding_debit_multiplier=f['debit_multiplier'],funding_credit_multiplier=f['credit_multiplier'])
def audit(r,data,t):
 m=p3.metrics(r,A,B);d=r.equity.loc[A:B].resample('1D').last().pct_change(fill_method=None).dropna();pos=d[d>0];neg=d[d<0];x=(t.shift(1)*data.close.pct_change(fill_method=None)).loc[A:B,ASSETS].sum();den=float(x.abs().sum());return {'metrics':m,'regimes':p3.regime_metrics(r,data,f'{A}T00:00:00+00:00',f'{B}T00:00:00+00:00',f'{B}T00:00:00+00:00'),'concentration':p3.concentration_metrics(r,A,B),'asset_contribution_share':{k:(float(v/den) if den else 0.) for k,v in x.items()},'tails':{'top10_positive_share':float(pos.nlargest(10).sum()/pos.sum()) if pos.sum()>0 else 0.,'bottom10_negative_share':float(abs(neg.nsmallest(10).sum())/abs(neg.sum())) if neg.sum()<0 else 0.}}
def main():
 cfg=json.loads(CFG.read_text());pre=json.loads(PREREG.read_text());assert pre['phase']==189 and pre['status']=='PREREGISTERED_TRAINING_ONLY';data=load_data(PROJECT,cfg['data_config']);v=validate_data(data);assert not v['errors'],v['errors'][:5];assert data.close.loc['2026-01-01':].empty,'Phase189 must not load 2026 data'
 specs={}
 for h,w,q in GRID:
  key=f'h{h}_w{w}_q{int(q*100)}';t=overlay(data,h,w,q);rs={z:ev(data,t,cfg,z) for z in ('base','severe','supersevere')};specs[key]={'params':{'return_lookback_hours':h,'dispersion_window_hours':w,'trigger_quantile':q},'base':audit(rs['base'],data,t),'severe':p3.metrics(rs['severe'],A,B),'supersevere':p3.metrics(rs['supersevere'],A,B),'folds':{y:p3.metrics(rs['base'],f'{y}-01-01',f'{y}-12-31') for y in ('2023','2024','2025')},'max_open_gross':float(rs['base'].open_positions.loc[A:B].abs().sum(axis=1).max())}
 eligible=[]
 for k,s in specs.items():
  m=s['base']['metrics'];folds=s['folds'];fail=[]
  if any(folds[y]['total_return']<=0 or folds[y]['profit_factor_daily']<=1 for y in ('2023','2024','2025')):fail.append('fold_inconsistency')
  if s['severe']['total_return']<=0 or s['supersevere']['total_return']<=0:fail.append('stress_nonpositive')
  if s['severe']['profit_factor_daily']<=1 or s['supersevere']['profit_factor_daily']<=1:fail.append('stress_pf_not_robust')
  if s['base']['tails']['top10_positive_share']>.50 or s['base']['tails']['bottom10_negative_share']>.50:fail.append('tail_concentration')
  if max(abs(x) for x in s['base']['asset_contribution_share'].values())>.50:fail.append('asset_concentration')
  if s['max_open_gross']>CAP+2e-5 or m['ruin']:fail.append('risk_invariant')
  s['failures']=fail
  if not fail:eligible.append(k)
 winner=max(eligible,key=lambda k:(min(specs[k]['folds'][y]['profit_factor_daily'] for y in ('2023','2024','2025')),specs[k]['supersevere']['profit_factor_daily'])) if eligible else None
 report={'engine':'V98 Independent','phase':189,'training_only':True,'window':[A,B],'validation':None,'final_holdout':None,'v16_used':False,'v99_used':False,'prereg_sha256':hashlib.sha256(PREREG.read_bytes()).hexdigest(),'grid_size':len(GRID),'selection_rule':'eligible then maximize worst-fold PF, tie-break supersevere PF','specs':specs,'gate':{'passed':winner is not None,'winner':winner,'decision':'PASS_TRAINING_FREEZE_FOR_SEPARATE_VALIDATION_PREREG' if winner else 'REJECT_FAMILY_NO_RESCUE'}}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True))
if __name__=='__main__':main()
