from __future__ import annotations
import json,sys
from pathlib import Path
import numpy as np
import pandas as pd
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,validate_data
import v98_independent_phase003_dispersion_neutral as p3
import v98_independent_phase171_t10y2y_data_only as p171
CFG=PROJECT/'config'/'v98_independent.json';PRE=PROJECT/'reports'/'v98_independent_phase172_t10y2y_steepening_long_preregistration.json';AUD=PROJECT/'reports'/'v98_independent_phase172_causality_audit.json';P171=PROJECT/'reports'/'v98_independent_phase171_t10y2y_data_only.json';OUT=PROJECT/'reports'/'v98_independent_phase172_t10y2y_steepening_long.json'
ASSETS=['BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT'];LAG_DAYS=1;TARGET=.30;CAP=.35

def load_macro():
 rows,qa=p171.parse(p171.acquire());g=json.loads(P171.read_text());assert g['status']=='PASS_DATA_ONLY'
 h=p171.hashlib.sha256(p171.canonical(rows)).hexdigest();assert h==g['sha256'][0]
 s=pd.Series({pd.Timestamp(d,tz='UTC'):float(v) for d,v in rows}).sort_index();assert s.index.is_unique and s.index.is_monotonic_increasing
 return s,h

def targets(data,s):
 state=(s.diff()>0).astype(float);state.iloc[0]=0.;state.index=state.index+pd.Timedelta(days=LAG_DAYS)
 t=pd.DataFrame(np.nan,index=data.close.index,columns=data.close.columns);decision=t.index.hour==0
 st=state.reindex(t.index[decision]).ffill().fillna(0.)
 for ts,v in st.items():t.loc[ts,ASSETS]=float(v)*TARGET/len(ASSETS)
 return t.where(pd.Series(decision,index=t.index),np.nan).ffill().fillna(0.)

def ev(data,t,cfg,stress):
 f=cfg['funding_stress'][stress];return exact_fast(data,t,cost_per_side=cfg['costs'][f'{stress}_per_side'],gross_guard_cap=CAP,funding_debit_multiplier=f['debit_multiplier'],funding_credit_multiplier=f['credit_multiplier'])
def daily(result,a,b):return result.equity.loc[a:b].resample('1D').last().pct_change(fill_method=None).dropna()
def asset_share(data,t,a,b):
 x=(t.shift(1)*data.close.pct_change(fill_method=None)).loc[a:b,ASSETS].sum().fillna(0.);den=float(x.abs().sum());return {k:(float(v/den) if den else 0.) for k,v in x.items()}
def utc_boundary(d):return f'{d}T00:00:00+00:00'

def main():
 pre=json.loads(PRE.read_text());aud=json.loads(AUD.read_text());assert pre['phase']=='172' and pre['signal_contract']['economic_use_lag_days']==LAG_DAYS;assert aud['decision']=='PASS_CAUSAL_CONTRACT_FOR_TRAINING_ONLY' and aud['causal_contract']['minimum_calendar_lag_days']==LAG_DAYS
 ao=pre['anti_overfit'];assert not any(ao[k] for k in ('parameter_search','threshold_search','lookback_search','rescue_allowed','v16_used','v99_used','validation_used_for_selection','holdout_used_for_selection'))
 s,h=load_macro();assert h==pre['dependency']['sha256_required'];cfg=json.loads(CFG.read_text());data=load_data(PROJECT,cfg['data_config']);v=validate_data(data);assert not v['errors'],v['errors'][:5]
 t=targets(data,s);a=pre['training_window'][0];b=pre['training_window'][1];rs={z:ev(data,t,cfg,z) for z in ('base','severe','supersevere')};base=rs['base']
 train=p3.metrics(base,a,b);folds={y:p3.metrics(base,f'{y}-01-01',f'{y}-12-31') for y in pre['chronological_folds']};stress={z:p3.metrics(rs[z],a,b) for z in ('severe','supersevere')}
 d=daily(base,a,b);pos=d[d>0];neg=d[d<0];top10=float(pos.nlargest(10).sum()/pos.sum()) if float(pos.sum())>0 else 0.;bottom10=float(abs(neg.nsmallest(10).sum())/abs(neg.sum())) if float(neg.sum())<0 else 0.;shares=asset_share(data,t,a,b);max_open=float(base.open_positions.loc[a:b].abs().sum(axis=1).max());max_close=float(base.positions.loc[a:b].abs().sum(axis=1).max())
 obs=s.loc[(s.index>=pd.Timestamp(a,tz='UTC'))&(s.index<=pd.Timestamp(b,tz='UTC'))];chg=obs.diff().dropna();activation={'observations':int(len(obs)),'changes':int(len(chg)),'active_steepening':int((chg>0).sum()),'active_change_rate':float((chg>0).mean()) if len(chg) else 0.}
 fail=[]
 if train['total_return']<=0:fail.append('aggregate_return<=0')
 if train['profit_factor_daily']<=1:fail.append('aggregate_pf<=1')
 for n,m in folds.items():
  if m['total_return']<=0:fail.append(f'{n}_return<=0')
  if m['profit_factor_daily']<=1:fail.append(f'{n}_pf<=1')
 for z in ('severe','supersevere'):
  if stress[z]['total_return']<=0:fail.append(f'{z}_return<=0')
 if max_open>CAP+1e-12:fail.append('max_open_gross>0.35')
 regimes=p3.regime_metrics(base,data,utc_boundary(a),utc_boundary(b),utc_boundary(b))
 report={'engine':'V98 Independent','phase':'172','hypothesis':'T10Y2Y steepening long crypto basket after conservative 1d lag','phase171_dependency':{'status':'PASS_DATA_ONLY','hash':h,'reacquisition_hash_verified':True},'causality_audit':'PASS_CAUSAL_CONTRACT_FOR_TRAINING_ONLY','signal_contract':{'direction':'delta(T10Y2Y)>0 => long; else flat','threshold':0.0,'economic_use_lag_days':LAG_DAYS,'target_gross':TARGET,'hard_gross_cap':CAP,'assets':ASSETS},'activation_training':activation,'training':train,'folds':folds,'stress_training':stress,'regimes_training':regimes,'concentration_training':p3.concentration_metrics(base,a,b),'asset_contribution_share':shares,'tails_training':{'top10_positive_day_share':top10,'bottom10_negative_day_share':bottom10,'p01_day':train['p01_day'],'p05_day':train['p05_day'],'cvar05_day':train['cvar05_day'],'worst_day':train['worst_day'],'best_day':train['best_day']},'max_open_gross':max_open,'max_close_gross':max_close,'validation':None,'final_holdout':None,'parameter_search':False,'threshold_search':False,'lookback_search':False,'rescue_allowed':False,'v16_used':False,'v99_used':False,'gate':{'passed':not fail,'decision':'PASS_TRAINING' if not fail else 'REJECT_NO_RESCUE','failures':fail}}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True))
if __name__=='__main__':main()
