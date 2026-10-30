from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
import numpy as np,pandas as pd
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,validate_data
import v98_independent_phase003_dispersion_neutral as p3
CFG=PROJECT/'config'/'v98_independent.json';OUT=PROJECT/'reports'/'v98_independent_phase065_residual_momentum.json';POS=PROJECT/'reports'/'v98_independent_phase065_residual_momentum_positions.csv'
PREREG='reports/v98_independent_phase065_preregistration.md';SYMBOLS=('BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT');ALT=SYMBOLS[1:];GROSS=.75;LOOKBACK_H=30*24

def targets(data,start,end):
 close=data.close.loc[:end,SYMBOLS];lag=close.shift(1);score=np.log(lag/lag.shift(LOOKBACK_H));res=score.sub(score['BTCUSDT'],axis=0)
 t=pd.DataFrame(0.,index=data.close.index,columns=data.close.columns);events=(t.index.hour==0)&(t.index>=pd.Timestamp(start))&(t.index<=pd.Timestamp(end))
 for ts in t.index[events]:
  s=res.loc[ts,list(ALT)].dropna()
  if len(s)!=len(ALT): continue
  lo=s.idxmin();hi=s.idxmax();t.loc[ts,hi]=GROSS/2;t.loc[ts,lo]=-GROSS/2
 t=t.where(pd.Series(events,index=t.index),np.nan).ffill().fillna(0.);return t

def ev(data,t,cfg,scenario):
 f=cfg['funding_stress'][scenario];return exact_fast(data,t,cost_per_side=cfg['costs'][f'{scenario}_per_side'],gross_guard_cap=GROSS,funding_debit_multiplier=f['debit_multiplier'],funding_credit_multiplier=f['credit_multiplier'])

def contribution_proxy(data,t,a,b):
 r=data.close.pct_change(fill_method=None);x=(t.shift(1)*r).loc[a:b,list(SYMBOLS)].sum().fillna(0.);den=float(x.abs().sum())
 return {'pre_cost_position_return_sum':{k:float(v) for k,v in x.items()},'absolute_contribution_share':{k:(float(abs(v)/den) if den else 0.) for k,v in x.items()}}

def tails(result,a,b):
 d=result.equity.loc[a:b].resample('1D').last().pct_change(fill_method=None).dropna().sort_values();n=max(1,int(np.ceil(.05*len(d))))
 return {'bottom_5pct_sum':float(d.iloc[:n].sum()),'top_5pct_sum':float(d.iloc[-n:].sum()),'bottom_5_days':{str(k):float(v) for k,v in d.head(5).items()},'top_5_days':{str(k):float(v) for k,v in d.tail(5).items()}}

def main():
 cfg=json.loads(CFG.read_text());data=load_data(PROJECT,cfg['data_config']);v=validate_data(data)
 if v['errors']: raise RuntimeError(str(v['errors'][:5]))
 a=cfg['folds'][0]['start'];b=cfg['training_end'];t=targets(data,a,b);rs={s:ev(data,t,cfg,s) for s in ('base','severe','supersevere')};base=rs['base']
 train=p3.metrics(base,a,b);folds={f['name']:p3.metrics(base,f['start'],f['end']) for f in cfg['folds']};fail=[]
 if train['total_return']<=0: fail.append('aggregate_return<=0')
 if train['profit_factor_daily']<=1.05: fail.append('aggregate_pf<=1.05')
 if train['max_drawdown']<=-.35: fail.append('max_drawdown<=-35%')
 if train.get('ruin'): fail.append('ruin')
 for n,m in folds.items():
  if m['total_return']<=0: fail.append(f'{n}_return<=0')
  if m['profit_factor_daily']<=1.02: fail.append(f'{n}_pf<=1.02')
 poshash=hashlib.sha256(t.loc[a:b,SYMBOLS].to_csv().encode()).hexdigest()
 rep={'engine':'V98 Independent','phase':'065','hypothesis':'frozen 30-calendar-day BTC-residual cross-sectional momentum','preregistration':PREREG,'parameters':{'symbols':SYMBOLS,'lookback_hours':LOOKBACK_H,'gross':GROSS,'rebalance':'00:00 UTC daily'},'training':train,'folds':folds,'stress_training':{s:p3.metrics(rs[s],a,b) for s in ('severe','supersevere')},'regimes_training':p3.regime_metrics(base,data,a,b,b),'concentration_training':p3.concentration_metrics(base,a,b),'asset_contribution_proxy':contribution_proxy(data,t,a,b),'tails_training':tails(base,a,b),'reproducibility':{'positions_sha256':poshash},'training_gate':{'passed':not fail,'failures':fail},'validation':None,'final_holdout':None,'final_holdout_untouched':True,'v99_used':False,'v16_used':False,'parameter_search':False,'rescue_allowed':False}
 OUT.write_text(json.dumps(rep,indent=2,default=str)+'\n');base.positions.to_csv(POS);print(json.dumps({'phase':'065','training_gate':rep['training_gate'],'training':train,'folds':folds,'stress':rep['stress_training'],'final_holdout':'UNTOUCHED'},indent=2,default=str))
if __name__=='__main__':main()
