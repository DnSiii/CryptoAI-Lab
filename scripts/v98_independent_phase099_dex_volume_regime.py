from __future__ import annotations
import hashlib,json,math,sys,urllib.request
from pathlib import Path
import numpy as np,pandas as pd
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,validate_data
import v98_independent_phase003_dispersion_neutral as p3
CFG=PROJECT/'config'/'v98_independent.json';OUT=PROJECT/'reports'/'v98_independent_phase099_dex_volume_regime.json';POS=PROJECT/'reports'/'v98_independent_phase099_dex_volume_regime_positions.csv';PREREG='reports/v98_independent_phase099_dex_volume_regime_prereg.md'
URL='https://api.llama.fi/overview/dexs?excludeTotalDataChartBreakdown=true&excludeTotalDataChart=false';SYMBOLS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT','XRPUSDT');GROSS=.75

def volume():
 req=urllib.request.Request(URL,headers={'Accept':'application/json','User-Agent':'CryptoAI-Lab-V98-Phase099/1.0'});raw=urllib.request.urlopen(req,timeout=60).read();obj=json.loads(raw);rows=[]
 for x in obj.get('totalDataChart',[]):
  try:
   ts=pd.to_datetime(float(x[0]),unit='s',utc=True).normalize();v=float(x[1])
   if math.isfinite(v) and v>=0:rows.append((ts,v))
  except Exception:pass
 return pd.Series(dict(rows),dtype=float).sort_index(),raw

def targets(data,s):
 t=pd.DataFrame(0.,index=data.close.index,columns=data.close.columns);events=t.index.hour==0;cal=pd.date_range('2022-12-10','2025-12-31',freq='1D',tz='UTC');lag=s.reindex(cal).ffill(limit=3).shift(1);recent=lag.rolling(7,min_periods=7).sum();prior=recent.shift(7)
 for ts in t.index[events]:
  d=ts.normalize();x=recent.get(d,np.nan);y=prior.get(d,np.nan)
  if pd.isna(x) or pd.isna(y) or x==y:continue
  side=1. if x>y else -1.
  for k in SYMBOLS:t.loc[ts,k]=side*GROSS/len(SYMBOLS)
 return t.where(pd.Series(events,index=t.index),np.nan).ffill().fillna(0.)
def ev(data,t,cfg,s):
 f=cfg['funding_stress'][s];return exact_fast(data,t,cost_per_side=cfg['costs'][f'{s}_per_side'],gross_guard_cap=GROSS,funding_debit_multiplier=f['debit_multiplier'],funding_credit_multiplier=f['credit_multiplier'])
def tails(r,a,b):
 d=r.equity.loc[a:b].resample('1D').last().pct_change(fill_method=None).dropna().sort_values();n=max(1,int(np.ceil(.05*len(d))));ad=d.abs().sort_values(ascending=False);den=float(d.abs().sum());return {'bottom_5pct_sum':float(d.iloc[:n].sum()),'top_5pct_sum':float(d.iloc[-n:].sum()),'top10_absolute_day_share':float(ad.head(10).sum()/den) if den else 0.}
def contribution(data,t,a,b):
 x=(t.shift(1)*data.close.pct_change(fill_method=None)).loc[a:b,list(SYMBOLS)].sum().fillna(0.);d=float(x.abs().sum());return {'pre_cost_position_return_sum':{k:float(v) for k,v in x.items()},'absolute_contribution_share':{k:(float(abs(v)/d) if d else 0.) for k,v in x.items()}}
def main():
 cfg=json.loads(CFG.read_text());data=load_data(PROJECT,cfg['data_config']);v=validate_data(data)
 if v['errors']:raise RuntimeError(str(v['errors'][:5]))
 s,raw=volume();a=cfg['folds'][0]['start'];b=cfg['training_end'];t=targets(data,s);rs={x:ev(data,t,cfg,x) for x in ('base','severe','supersevere')};base=rs['base'];train=p3.metrics(base,a,b);folds={f['name']:p3.metrics(base,f['start'],f['end']) for f in cfg['folds']};stress={x:p3.metrics(rs[x],a,b) for x in ('severe','supersevere')};conc=p3.concentration_metrics(base,a,b);con=contribution(data,t,a,b);tail=tails(base,a,b);fail=[]
 if train['total_return']<=0:fail.append('aggregate_return<=0')
 if train['profit_factor_daily']<=1.10:fail.append('aggregate_pf<=1.10')
 if train['max_drawdown']<-.35:fail.append('max_drawdown<-35%')
 for n,m in folds.items():
  if m['total_return']<=0:fail.append(f'{n}_return<=0')
 for x in ('severe','supersevere'):
  if stress[x]['total_return']<=0 or stress[x]['profit_factor_daily']<=1.0:fail.append(f'{x}_gate')
 if max(con['absolute_contribution_share'].values(),default=0)>0.60:fail.append('single_asset_contribution>60%')
 if tail['top10_absolute_day_share']>0.60:fail.append('top10_absolute_day_share>60%')
 rep={'engine':'V98 Independent','phase':'099','hypothesis':'aggregate DEX volume 7d-vs-prior-7d directional regime','preregistration':PREREG,'parameters':{'window_days':7,'comparison':'non-overlapping prior 7d','gross':GROSS,'symbols':SYMBOLS,'lag':'strict prior UTC day','rebalance':'daily 00:00 UTC','direction':'long if recent volume sum rises, short if falls'},'source':{'url':URL,'raw_sha256':hashlib.sha256(raw).hexdigest()},'phase083_selection_use':False,'future_holdout_required':True,'training':train,'folds':folds,'stress_training':stress,'regimes_training':p3.regime_metrics(base,data,a,b,b),'concentration_training':conc,'asset_contribution_proxy':con,'tails_training':tail,'reproducibility':{'targets_sha256':hashlib.sha256(t.loc[a:b,list(SYMBOLS)].to_csv().encode()).hexdigest(),'prereg_sha256':hashlib.sha256((PROJECT/PREREG).read_bytes()).hexdigest()},'training_gate':{'passed':not fail,'decision':'PASS_TRAINING' if not fail else 'REJECT_NO_RESCUE','failures':fail},'validation':None,'final_holdout':None,'v99_used':False,'v16_used':False,'parameter_search':False,'rescue_allowed':False};OUT.write_text(json.dumps(rep,indent=2,default=str)+'\n');base.positions.to_csv(POS);print(json.dumps({'phase':'099','training_gate':rep['training_gate'],'training':train,'folds':folds,'stress':stress},indent=2,default=str))
if __name__=='__main__':main()
