from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
import numpy as np,pandas as pd
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,validate_data
import v98_independent_phase003_dispersion_neutral as p3
CFG=PROJECT/'config'/'v98_independent.json';OUT=PROJECT/'reports'/'v98_independent_phase130_realized_volatility_regime.json';POS=PROJECT/'reports'/'v98_independent_phase130_realized_volatility_regime_positions.csv'
PREREG='reports/v98_independent_phase130_realized_volatility_regime_prereg.md';GROSS=.75;ASSETS=['BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT'];LOOKBACK=28

def daily_rv(data):
 c=data.close['BTCUSDT'].loc['2023-01-01':'2025-12-31 23:00:00'].astype(float)
 lr=np.log(c).diff();g=lr.groupby(lr.index.normalize());n=g.count();rv=np.sqrt(g.apply(lambda x: float(np.square(x.dropna()).sum())));return rv[n>=23].sort_index()

def build_targets(data,rv):
 med=rv.rolling(LOOKBACK,min_periods=LOOKBACK).median();state=(rv<=med).where(med.notna(),False);activation=(state.index+pd.Timedelta(days=1)).normalize();sig=pd.Series(state.astype(float).values,index=activation).sort_index();t=pd.DataFrame(np.nan,index=data.close.index,columns=data.close.columns);events=t.index.hour==0;states=[]
 for ts in t.index[events]:
  prior=sig.loc[:ts.normalize()];side=float(prior.iloc[-1]) if len(prior) else 0.;t.loc[ts,ASSETS]=side*GROSS/len(ASSETS);states.append((ts.normalize(),'low_normal' if side>0 else 'elevated'))
 t=t.where(pd.Series(events,index=t.index),np.nan).ffill().fillna(0.);return t,pd.DataFrame(states,columns=['date','state'])

def always_long(data):
 t=pd.DataFrame(0.,index=data.close.index,columns=data.close.columns);events=t.index.hour==0;t.loc[events,ASSETS]=GROSS/len(ASSETS);return t.where(pd.Series(events,index=t.index),np.nan).ffill().fillna(0.)

def ev(data,t,cfg,s):
 f=cfg['funding_stress'][s];return exact_fast(data,t,cost_per_side=cfg['costs'][f'{s}_per_side'],gross_guard_cap=GROSS,funding_debit_multiplier=f['debit_multiplier'],funding_credit_multiplier=f['credit_multiplier'])

def tails(r,a,b):
 d=r.equity.loc[a:b].resample('1D').last().pct_change(fill_method=None).dropna();den=float(d.abs().sum());ad=d.abs().sort_values(ascending=False);return {'top10_absolute_day_share':float(ad.head(10).sum()/den) if den else 0.,'worst10_sum':float(d.nsmallest(10).sum()),'best10_sum':float(d.nlargest(10).sum())}

def contribution(data,t,a,b):
 x=(t.shift(1)*data.close.pct_change(fill_method=None)).loc[a:b,ASSETS].sum().fillna(0.);den=float(x.abs().sum());return {'pre_cost_position_return_sum':{k:float(v) for k,v in x.items()},'absolute_contribution_share':{k:(float(abs(v)/den) if den else 0.) for k,v in x.items()}}

def main():
 gate=json.loads((PROJECT/'reports'/'v98_independent_phase129_realized_volatility_data_only.json').read_text());assert gate.get('decision')=='PASS_DATA_ONLY' and gate.get('alpha_or_pnl_inspected') is False
 cfg=json.loads(CFG.read_text());data=load_data(PROJECT,cfg['data_config']);v=validate_data(data)
 if v['errors']: raise RuntimeError(str(v['errors'][:5]))
 rv=daily_rv(data);t,states=build_targets(data,rv);a=cfg['folds'][0]['start'];b=cfg['training_end'];rr={z:ev(data,t,cfg,z) for z in ('base','severe','supersevere')};base=rr['base'];train=p3.metrics(base,a,b);folds={f['name']:p3.metrics(base,f['start'],f['end']) for f in cfg['folds']};stress={z:p3.metrics(rr[z],a,b) for z in ('severe','supersevere')};con=contribution(data,t,a,b);tail=tails(base,a,b);st=states[(states.date>=pd.Timestamp(a,tz='UTC'))&(states.date<=pd.Timestamp(b,tz='UTC'))].state.value_counts().to_dict();op=base.open_positions.loc[a:b].abs().sum(axis=1) if base.open_positions is not None else pd.Series(dtype=float);maxopen=float(op.max()) if len(op) else 0.;benchmark=p3.metrics(ev(data,always_long(data),cfg,'base'),a,b)
 fail=[]
 if train['total_return']<=0: fail.append('aggregate_return<=0')
 if train['profit_factor_daily']<=1.10: fail.append('aggregate_pf<=1.10')
 if train['max_drawdown']<-.35: fail.append('max_drawdown<-35%')
 if train['worst_day']<-.12: fail.append('worst_day<-12%')
 for n,m in folds.items():
  if m['total_return']<=0: fail.append(f'{n}_return<=0')
  if m['profit_factor_daily']<=1.02: fail.append(f'{n}_pf<=1.02')
 for z in ('severe','supersevere'):
  if stress[z]['total_return']<=0 or stress[z]['profit_factor_daily']<=1.: fail.append(f'{z}_gate')
 if max(con['absolute_contribution_share'].values(),default=0)>0.45: fail.append('single_asset_contribution>45%')
 if tail['top10_absolute_day_share']>0.60: fail.append('top10_absolute_day_share>60%')
 if maxopen>GROSS+1e-9: fail.append('max_open_gross>0.75')
 if any(st.get(x,0)==0 for x in ('low_normal','elevated')): fail.append('both_states_not_identified')
 rep={'engine':'V98 Independent','phase':'130','hypothesis':'BTC realized-volatility risk-permission regime','preregistration':PREREG,'parameters':{'gross':GROSS,'assets':ASSETS,'rv':'sqrt(sum hourly log-return squared), >=23 returns/day','lookback_days':LOOKBACK,'activation_lag':'completed UTC day +1 day at 00:00 UTC','low_normal':'long','elevated':'flat'},'training':train,'folds':folds,'stress_training':stress,'state_observation_counts':st,'regimes_training':p3.regime_metrics(base,data,a,b,b),'concentration_training':p3.concentration_metrics(base,a,b),'asset_contribution_proxy':con,'tails_training':tail,'execution_guard_audit':{'max_open_gross':maxopen,'cap':GROSS},'always_long_context_benchmark':benchmark,'reproducibility':{'rv_date_manifest_sha256':hashlib.sha256('\n'.join(x.isoformat() for x in rv.index).encode()).hexdigest(),'targets_sha256':hashlib.sha256(t.loc[a:b,ASSETS].to_csv().encode()).hexdigest(),'prereg_sha256':hashlib.sha256((PROJECT/PREREG).read_bytes()).hexdigest()},'training_gate':{'passed':not fail,'decision':'PASS_TRAINING' if not fail else 'REJECT_NO_RESCUE','failures':fail},'validation':None,'final_holdout':None,'phase083_selection_use':False,'future_holdout_required':True,'v99_used':False,'v16_used':False,'parameter_search':False,'rescue_allowed':False}
 OUT.write_text(json.dumps(rep,indent=2,default=str)+'\n');base.positions.to_csv(POS);print(json.dumps(rep,indent=2,default=str))
if __name__=='__main__':main()
