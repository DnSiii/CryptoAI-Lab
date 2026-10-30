from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
import numpy as np,pandas as pd
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,validate_data
import v98_independent_phase003_dispersion_neutral as p3
CFG=PROJECT/'config'/'v98_independent.json';OUT=PROJECT/'reports'/'v98_independent_phase136_post_jump_rebound.json'
PREREG='reports/v98_independent_phase136_post_jump_rebound_prereg.md';ASSETS=['BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT'];GROSS=.50;LOOKBACK_DAYS=28;MULT=3.;BREADTH=3

def build_targets(data):
 close=data.close[ASSETS].loc['2022-12-01':'2025-12-31 23:00:00'].astype(float);lr=np.log(close).diff();days=lr.index.normalize();shock=pd.DataFrame(False,index=lr.index,columns=ASSETS)
 for a in ASSETS:
  daily_abs=lr[a].abs().groupby(days).apply(lambda x:float(x.median()) if x.notna().sum()>=23 else np.nan);scale=daily_abs.rolling(LOOKBACK_DAYS,min_periods=LOOKBACK_DAYS).median().shift(1);mapped=pd.Series(days,index=lr.index).map(scale);shock[a]=lr[a]<=(-MULT*mapped.values)
 signal=(shock.groupby(days).any().sum(axis=1)>=BREADTH).astype(float);activation=signal.copy();activation.index+=pd.Timedelta(days=1)
 t=pd.DataFrame(np.nan,index=data.close.index,columns=data.close.columns);decision=t.index.hour==0
 for ts in t.index[decision]: t.loc[ts,ASSETS]=float(activation.get(ts.normalize(),0.))*GROSS/len(ASSETS)
 return t.where(pd.Series(decision,index=t.index),np.nan).ffill().fillna(0.),activation

def ev(data,t,cfg,s):
 f=cfg['funding_stress'][s];return exact_fast(data,t,cost_per_side=cfg['costs'][f'{s}_per_side'],gross_guard_cap=GROSS+1e-8,funding_debit_multiplier=f['debit_multiplier'],funding_credit_multiplier=f['credit_multiplier'])
def daily(r,a,b):return r.equity.loc[a:b].resample('1D').last().pct_change(fill_method=None).dropna()
def asset_contrib(data,t,a,b):
 x=(t.shift(1)*data.close.pct_change(fill_method=None)).loc[a:b,ASSETS].sum().fillna(0.);pos=x.clip(lower=0);den=float(pos.sum());return {k:(float(v/den) if den else 0.) for k,v in pos.items()}
def main():
 gate=json.loads((PROJECT/'reports'/'v98_independent_phase135_post_jump_directional_asymmetry_data_only.json').read_text());assert gate['decision']=='PASS_DATA_ONLY' and gate['alpha_or_pnl_inspected'] is False and gate['next_day_return_values_exposed'] is False
 cfg=json.loads(CFG.read_text());data=load_data(PROJECT,cfg['data_config']);v=validate_data(data);assert not v['errors'],v['errors'][:5]
 t,activation=build_targets(data);a=cfg['folds'][0]['start'];b=cfg['training_end'];rr={z:ev(data,t,cfg,z) for z in ('base','severe','supersevere')};base=rr['base'];train=p3.metrics(base,a,b);folds={f['name']:p3.metrics(base,f['start'],f['end']) for f in cfg['folds']};stress={z:p3.metrics(rr[z],a,b) for z in ('severe','supersevere')};d=daily(base,a,b);positive=d[d>0];top10=float(positive.nlargest(10).sum()/positive.sum()) if positive.sum()>0 else 0.;shares=asset_contrib(data,t,a,b);op=base.open_positions.loc[a:b].abs().sum(axis=1);maxopen=float(op.max());fail=[]
 if train['total_return']<=0:fail.append('aggregate_return<=0')
 if train['profit_factor_daily']<1.05:fail.append('aggregate_pf<1.05')
 if train['max_drawdown']<-.35:fail.append('max_drawdown<-35%')
 for n,m in folds.items():
  if m['total_return']<=0:fail.append(f'{n}_return<=0')
  if m['profit_factor_daily']<1.02:fail.append(f'{n}_pf<1.02')
 if stress['severe']['total_return']<=0 or stress['severe']['profit_factor_daily']<1.02:fail.append('severe_gate')
 if stress['supersevere']['total_return']<=0 or stress['supersevere']['profit_factor_daily']<1.00:fail.append('supersevere_gate')
 if max(shares.values(),default=0)>0.45:fail.append('single_asset_positive_contribution>45%')
 if top10>=.35:fail.append('top10_positive_day_share>=35%')
 if maxopen>GROSS+1e-6:fail.append('gross_cap')
 rep={'engine':'V98 Independent','phase':'136','hypothesis':'frozen broad downside-jump event has stable next-day rebound expectancy','preregistration':PREREG,'training':train,'folds':folds,'stress_training':stress,'regimes_training':p3.regime_metrics(base,data,a,b,b),'concentration_training':p3.concentration_metrics(base,a,b),'asset_positive_contribution_share':shares,'tails_training':{'top10_positive_day_share':top10,'worst10_sum':float(d.nsmallest(10).sum()),'best10_sum':float(d.nlargest(10).sum()),'worst_day':float(d.min()),'best_day':float(d.max())},'event_days':int(activation.loc[pd.Timestamp(a,tz='UTC'):pd.Timestamp(b,tz='UTC')].sum()),'execution_guard_audit':{'max_open_gross':maxopen,'cap':GROSS},'reproducibility':{'activation_sha256':hashlib.sha256(activation.to_csv().encode()).hexdigest(),'targets_sha256':hashlib.sha256(t.loc[a:b,ASSETS].to_csv().encode()).hexdigest(),'prereg_sha256':hashlib.sha256((PROJECT/PREREG).read_bytes()).hexdigest()},'training_gate':{'passed':not fail,'decision':'PASS_TRAINING' if not fail else 'REJECT_NO_RESCUE','failures':fail},'validation':None,'final_holdout':None,'phase083_selection_use':False,'v99_used':False,'v16_used':False,'parameter_search':False,'rescue_allowed':False}
 OUT.write_text(json.dumps(rep,indent=2,default=str)+'\n');print(json.dumps(rep,indent=2,default=str))
if __name__=='__main__':main()
