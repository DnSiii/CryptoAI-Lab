from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
import numpy as np,pandas as pd
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,validate_data
import v98_independent_phase003_dispersion_neutral as p3
CFG=PROJECT/'config'/'v98_independent.json';OUT=PROJECT/'reports'/'v98_independent_phase089_session_gap.json';POS=PROJECT/'reports'/'v98_independent_phase089_session_gap_positions.csv';PREREG='reports/v98_independent_phase089_prereg.md';SYMBOLS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT','XRPUSDT');GROSS=.75;LOOKBACK=7

def daily_gap(data):
 o=data.frames['open'].loc[:,list(SYMBOLS)].resample('1D').first();c=data.close.loc[:,list(SYMBOLS)].resample('1D').last();return o.div(c.shift(1))-1.
def targets(data,a,b):
 g=daily_gap(data);sig=g.rolling(LOOKBACK,min_periods=LOOKBACK).mean();t=pd.DataFrame(0.,index=data.close.index,columns=data.close.columns);events=(t.index.hour==0)&(t.index>=pd.Timestamp(a))&(t.index<=pd.Timestamp(b))
 for ts in t.index[events]:
  prior=ts.normalize()-pd.Timedelta(days=1)
  if prior not in sig.index:continue
  s=sig.loc[prior,list(SYMBOLS)].dropna();s=s-float(s.mean());o=sorted(((float(s[k]),k) for k in s.index),key=lambda x:(x[0],x[1]));q=max(1,len(o)//4)
  if len(o)<4 or not o[-1][0]>o[0][0]:continue
  for _,k in o[:q]:t.loc[ts,k]=-GROSS/(2*q)
  for _,k in o[-q:]:t.loc[ts,k]=GROSS/(2*q)
 return t.where(pd.Series(events,index=t.index),np.nan).ffill().fillna(0.)
def ev(data,t,cfg,s):
 f=cfg['funding_stress'][s];return exact_fast(data,t,cost_per_side=cfg['costs'][f'{s}_per_side'],gross_guard_cap=GROSS,funding_debit_multiplier=f['debit_multiplier'],funding_credit_multiplier=f['credit_multiplier'])
def tails(r,a,b):
 d=r.equity.loc[a:b].resample('1D').last().pct_change(fill_method=None).dropna().sort_values();n=max(1,int(np.ceil(.05*len(d))));ad=d.abs().sort_values(ascending=False);den=float(d.abs().sum());return {'bottom_5pct_sum':float(d.iloc[:n].sum()),'top_5pct_sum':float(d.iloc[-n:].sum()),'bottom_5_days':{str(k):float(v) for k,v in d.head().items()},'top_5_days':{str(k):float(v) for k,v in d.tail().items()},'top10_absolute_day_share':float(ad.head(10).sum()/den) if den else 0.}
def contribution(data,t,a,b):
 x=(t.shift(1)*data.close.pct_change(fill_method=None)).loc[a:b,list(SYMBOLS)].sum().fillna(0.);d=float(x.abs().sum());return {'pre_cost_position_return_sum':{k:float(v) for k,v in x.items()},'absolute_contribution_share':{k:(float(abs(v)/d) if d else 0.) for k,v in x.items()}}
def main():
 cfg=json.loads(CFG.read_text());data=load_data(PROJECT,cfg['data_config']);v=validate_data(data)
 if v['errors']:raise RuntimeError(str(v['errors'][:5]))
 a=cfg['folds'][0]['start'];b=cfg['training_end'];t=targets(data,a,b);rs={s:ev(data,t,cfg,s) for s in ('base','severe','supersevere')};base=rs['base'];train=p3.metrics(base,a,b);folds={f['name']:p3.metrics(base,f['start'],f['end']) for f in cfg['folds']};stress={s:p3.metrics(rs[s],a,b) for s in ('severe','supersevere')};conc=p3.concentration_metrics(base,a,b);fail=[]
 if train['total_return']<=0:fail.append('aggregate_return<=0')
 if train['profit_factor_daily']<1.15:fail.append('aggregate_pf<1.15')
 if train['max_drawdown']<-.35:fail.append('max_drawdown<-35%')
 if train.get('ruin'):fail.append('ruin')
 for n,m in folds.items():
  if m['total_return']<=0:fail.append(f'{n}_return<=0')
  if m['profit_factor_daily']<1.05:fail.append(f'{n}_pf<1.05')
 if stress['severe']['total_return']<=0 or stress['severe']['profit_factor_daily']<1.10:fail.append('severe_gate')
 if stress['supersevere']['total_return']<=0 or stress['supersevere']['profit_factor_daily']<1.03 or stress['supersevere']['max_drawdown']<-.55:fail.append('supersevere_gate')
 if conc.get('p95_top1_weight_share',0)>0.45:fail.append('p95_top1>45%')
 rep={'engine':'V98 Independent','phase':'089','hypothesis':'lagged 7-day UTC session-boundary gap continuation','preregistration':PREREG,'parameters':{'symbols':SYMBOLS,'lookback_completed_days':LOOKBACK,'gross':GROSS,'rebalance':'00:00 UTC daily'},'phase083_selection_use':False,'future_holdout_required':True,'training':train,'folds':folds,'stress_training':stress,'regimes_training':p3.regime_metrics(base,data,a,b,b),'concentration_training':conc,'asset_contribution_proxy':contribution(data,t,a,b),'tails_training':tails(base,a,b),'reproducibility':{'targets_sha256':hashlib.sha256(t.loc[a:b,list(SYMBOLS)].to_csv().encode()).hexdigest(),'prereg_sha256':hashlib.sha256((PROJECT/PREREG).read_bytes()).hexdigest()},'training_gate':{'passed':not fail,'failures':fail},'validation':None,'final_holdout':None,'v99_used':False,'v16_used':False,'parameter_search':False,'rescue_allowed':False};OUT.write_text(json.dumps(rep,indent=2,default=str)+'\n');base.positions.to_csv(POS);print(json.dumps({'phase':'089','training_gate':rep['training_gate'],'training':train,'folds':folds,'stress':stress},indent=2,default=str))
if __name__=='__main__':main()
