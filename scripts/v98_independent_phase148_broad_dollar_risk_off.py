from __future__ import annotations
import csv,io,json,sys
from decimal import Decimal,InvalidOperation
from pathlib import Path
import numpy as np
import pandas as pd
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,validate_data
import v98_independent_phase003_dispersion_neutral as p3
import v98_independent_phase147_broad_dollar_data_only as p147
CFG=PROJECT/'config'/'v98_independent.json';PRE=PROJECT/'reports'/'v98_independent_phase148_broad_dollar_risk_off_preregistration.json';P147=PROJECT/'reports'/'v98_independent_phase147_broad_dollar_data_only.json';OUT=PROJECT/'reports'/'v98_independent_phase148_broad_dollar_risk_off.json'
ASSETS=['BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT'];LOOKBACK=20;LAG_DAYS=1;TARGET=.30;CAP=.35

def load_macro():
 raw=p147.acquire(); a=p147.audit(raw); governing=json.loads(P147.read_text()); assert governing['decision']=='PASS_DATA_ONLY'; assert a['normalized_observations_sha256']==governing['normalized_observations_sha256']
 r=csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))); obs=[]
 for row in r:
  v=(row.get('DTWEXBGS') or '').strip()
  if v in ('','.','NA','NaN'):continue
  try:x=Decimal(v); assert x.is_finite()
  except (InvalidOperation,ValueError,AssertionError):continue
  d=pd.Timestamp(row['observation_date'],tz='UTC'); obs.append((d,float(x)))
 s=pd.Series(dict(obs)).sort_index(); assert s.index.is_unique and s.index.is_monotonic_increasing
 return s,a['normalized_observations_sha256']

def targets(data,s):
 state=(s>s.shift(LOOKBACK)).astype(float); state.index=state.index+pd.Timedelta(days=LAG_DAYS)
 t=pd.DataFrame(np.nan,index=data.close.index,columns=data.close.columns); decision=t.index.hour==0; st=state.reindex(t.index[decision],method='ffill').fillna(0.)
 for ts,v in st.items(): t.loc[ts,ASSETS]=-float(v)*TARGET/len(ASSETS)
 return t.where(pd.Series(decision,index=t.index),np.nan).ffill().fillna(0.)

def ev(data,t,cfg,stress):
 f=cfg['funding_stress'][stress];return exact_fast(data,t,cost_per_side=cfg['costs'][f'{stress}_per_side'],gross_guard_cap=CAP,funding_debit_multiplier=f['debit_multiplier'],funding_credit_multiplier=f['credit_multiplier'])
def daily(result,a,b):return result.equity.loc[a:b].resample('1D').last().pct_change(fill_method=None).dropna()
def asset_share(data,t,a,b):
 x=(t.shift(1)*data.close.pct_change(fill_method=None)).loc[a:b,ASSETS].sum().fillna(0.).clip(lower=0);den=float(x.sum());return {k:(float(v/den) if den else 0.) for k,v in x.items()}

def main():
 pre=json.loads(PRE.read_text()); assert pre['phase']=='148' and pre['anti_overfit']['parameter_search'] is False and pre['anti_overfit']['rescue_allowed'] is False
 s,h=load_macro(); assert h==pre['dependency']['phase147_observations_sha256']
 cfg=json.loads(CFG.read_text());data=load_data(PROJECT,cfg['data_config']);v=validate_data(data);assert not v['errors'],v['errors'][:5]
 t=targets(data,s);a=cfg['folds'][0]['start'];b=cfg['training_end'];rs={z:ev(data,t,cfg,z) for z in ('base','severe','supersevere')};base=rs['base']
 train=p3.metrics(base,a,b);folds={f['name']:p3.metrics(base,f['start'],f['end']) for f in cfg['folds']};stress={z:p3.metrics(rs[z],a,b) for z in ('severe','supersevere')}
 d=daily(base,a,b);pos=d[d>0];top10=float(pos.nlargest(10).sum()/pos.sum()) if float(pos.sum())>0 else 0.;shares=asset_share(data,t,a,b);max_open=float(base.open_positions.loc[a:b].abs().sum(axis=1).max());max_close=float(base.positions.loc[a:b].abs().sum(axis=1).max())
 fail=[]
 if train['total_return']<=0:fail.append('aggregate_return<=0')
 if train['profit_factor_daily']<1.05:fail.append('aggregate_pf<1.05')
 for n,m in folds.items():
  if m['total_return']<=0:fail.append(f'{n}_return<=0')
  if m['profit_factor_daily']<1.02:fail.append(f'{n}_pf<1.02')
 if stress['severe']['total_return']<=0:fail.append('severe_return<=0')
 if stress['supersevere']['total_return']<=0:fail.append('supersevere_return<=0')
 if max_open>CAP+1e-12:fail.append('max_open_gross>0.35')
 report={'engine':'V98 Independent','phase':'148','hypothesis':'20-observation rising broad-dollar risk-off short crypto basket','preregistration':'reports/v98_independent_phase148_broad_dollar_risk_off_preregistration.json','phase147_dependency':{'decision':'PASS_DATA_ONLY','hash':h,'reacquisition_hash_verified':True},'signal_contract':{'lookback_accepted_observations':LOOKBACK,'direction':'DTWEXBGS_t > DTWEXBGS_t_minus_20 => short; else flat','economic_use_lag_days':LAG_DAYS,'target_gross':TARGET,'hard_gross_cap':CAP,'assets':ASSETS},'training':train,'folds':folds,'stress_training':stress,'regimes_training':p3.regime_metrics(base,data,a,b,b),'concentration_training':p3.concentration_metrics(base,a,b),'asset_positive_contribution_share':shares,'tails_training':{'top10_positive_day_share':top10,'p01_day':train['p01_day'],'p05_day':train['p05_day'],'cvar05_day':train['cvar05_day'],'worst_day':train['worst_day'],'best_day':train['best_day']},'max_open_gross':max_open,'max_close_gross':max_close,'validation':None,'final_holdout':None,'parameter_search':False,'rescue_allowed':False,'v16_used':False,'v99_used':False,'gate':{'passed':not fail,'decision':'PASS_TRAINING' if not fail else 'REJECT_NO_RESCUE','failures':fail}}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
