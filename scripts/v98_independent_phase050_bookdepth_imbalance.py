from __future__ import annotations
import concurrent.futures as cf,io,json,sys,urllib.request,zipfile
from pathlib import Path
import numpy as np,pandas as pd
PROJECT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(PROJECT/'src')); sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,point_in_time_liquid_view,validate_data
import v98_independent_phase003_dispersion_neutral as p3
CONFIG_PATH=PROJECT/'config'/'v98_independent.json'; STATE_PATH=PROJECT/'state'/'v98_independent_state.json'; AUDIT_PATH=PROJECT/'reports'/'v98_independent_phase050_bookdepth_audit.json'; REPORT_PATH=PROJECT/'reports'/'v98_independent_phase050_bookdepth_imbalance.json'; POSITIONS_PATH=PROJECT/'reports'/'v98_independent_phase050_bookdepth_imbalance_positions.csv'
PHASE={'id':'phase_050_bookdepth_imbalance','liquidity_top_n':5,'liquidity_lookback_hours':720,'minimum_history_hours':2160,'beta_lookback_hours':720,'min_beta_obs':360,'rebalance_hours':24,'gross_target':0.75,'gross_cap':0.75}
SYMBOLS=('BTCUSDT','ETHUSDT','SOLUSDT','XRPUSDT','BNBUSDT'); BASE='https://data.binance.vision/data/futures/um/daily/bookDepth/{symbol}/{symbol}-bookDepth-{date}.zip'
def fetch_day(symbol,date):
 try:
  with urllib.request.urlopen(BASE.format(symbol=symbol,date=date),timeout=20) as r: payload=r.read()
  with zipfile.ZipFile(io.BytesIO(payload)) as z:
   names=[n for n in z.namelist() if n.lower().endswith('.csv')]
   if len(names)!=1:return symbol,date,np.nan,'csv_members'
   with z.open(names[0]) as f: df=pd.read_csv(f,usecols=['timestamp','percentage','notional'])
  df['timestamp']=pd.to_datetime(df.timestamp,utc=True,errors='coerce'); df['percentage']=pd.to_numeric(df.percentage,errors='coerce'); df['notional']=pd.to_numeric(df.notional,errors='coerce'); df=df.dropna()
  if df.empty:return symbol,date,np.nan,'empty'
  g=df.groupby('timestamp'); bid=g.apply(lambda x:x.loc[x.percentage<0,'notional'].sum(),include_groups=False); ask=g.apply(lambda x:x.loc[x.percentage>0,'notional'].sum(),include_groups=False); den=bid+ask; imb=((bid-ask)/den.replace(0,np.nan)).replace([np.inf,-np.inf],np.nan).dropna()
  return symbol,date,float(imb.median()) if len(imb) else np.nan,None
 except Exception as e:return symbol,date,np.nan,f'{type(e).__name__}:{e}'
def acquire(start,end):
 days=pd.date_range(pd.Timestamp(start).floor('D'),pd.Timestamp(end).floor('D'),freq='D',tz='UTC'); tasks=[(s,d.strftime('%Y-%m-%d')) for s in SYMBOLS for d in days]; vals=[]; failures=[]
 with cf.ThreadPoolExecutor(max_workers=32) as ex:
  for fut in cf.as_completed([ex.submit(fetch_day,*x) for x in tasks]):
   s,d,v,e=fut.result(); failures.append((s,d,e)) if e or not np.isfinite(v) else vals.append((pd.Timestamp(d,tz='UTC'),s,v))
 x=pd.DataFrame(vals,columns=['day','symbol','imbalance']).pivot(index='day',columns='symbol',values='imbalance').sort_index() if vals else pd.DataFrame(); cov={s:float(x[s].notna().sum()/len(days)) if s in x else 0.0 for s in SYMBOLS}; return x,{'requested_days':len(days),'requested_files':len(tasks),'failed_files':len(failures),'failure_examples':failures[:25],'daily_coverage':cov,'min_symbol_coverage':min(cov.values()) if cov else 0.0}
def build_targets(data,membership,signal):
 c=PHASE; idx=data.close.index; daily=signal.copy(); daily.index=daily.index+pd.Timedelta(days=1); lag=daily.reindex(idx,method='ffill'); ret=data.close.shift(1).pct_change(fill_method=None); btc=ret['BTCUSDT']; var=btc.rolling(c['beta_lookback_hours'],min_periods=c['min_beta_obs']).var(); beta=ret.rolling(c['beta_lookback_hours'],min_periods=c['min_beta_obs']).cov(btc).div(var,axis=0); eligible=(membership & data.close.notna()); targets=pd.DataFrame(0.0,index=idx,columns=data.close.columns); events=(idx.hour==0)
 for k,ts in enumerate(idx):
  if not events[k]:continue
  names=[s for s in SYMBOLS if s in targets.columns and s in lag.columns and bool(eligible.at[ts,s]) and pd.notna(lag.at[ts,s]) and pd.notna(beta.at[ts,s])]
  if len(names)<4:continue
  raw=lag.loc[ts,names].rank(pct=True)-0.5; b=beta.loc[ts,names].to_numpy(float); y=raw.to_numpy(float); X=np.column_stack([np.ones(len(names)),b]); coef,*_=np.linalg.lstsq(X,y,rcond=None); neutral=y-X@coef; gross=float(np.abs(neutral).sum())
  if np.isfinite(gross) and gross>1e-12:targets.loc[ts,names]=neutral*(c['gross_target']/gross)
 targets=targets.where(pd.Series(events,index=idx),np.nan).ffill().fillna(0.0); gross=targets.abs().sum(axis=1); return targets.mul((c['gross_cap']/gross.replace(0,np.nan)).clip(upper=1).fillna(0),axis=0)
def ev(data,t,cfg,s):
 f=cfg['funding_stress'][s]; return exact_fast(data,t,cost_per_side=cfg['costs'][f'{s}_per_side'],gross_guard_cap=PHASE['gross_cap'],funding_debit_multiplier=f['debit_multiplier'],funding_credit_multiplier=f['credit_multiplier'])
def main():
 cfg=json.loads(CONFIG_PATH.read_text()); state=json.loads(STATE_PATH.read_text()); audit=json.loads(AUDIT_PATH.read_text());
 if audit.get('decision')!='integrity_gate_pass':raise RuntimeError('Phase050 blocked: book-depth integrity gate has not passed')
 data=load_data(PROJECT,cfg['data_config']); v=validate_data(data)
 if v['errors']:raise RuntimeError(str(v['errors'][:5]))
 liquid,membership=point_in_time_liquid_view(data,top_n=PHASE['liquidity_top_n'],lookback_hours=PHASE['liquidity_lookback_hours'],minimum_history_hours=PHASE['minimum_history_hours']); signal,cov=acquire(cfg['research_start'],cfg['training_end']); t=build_targets(liquid,membership,signal); r={s:ev(liquid,t,cfg,s) for s in ('base','severe','supersevere')}; a,b=cfg['research_start'],cfg['training_end']; train=p3.metrics(r['base'],a,b); folds={f['name']:p3.metrics(r['base'],f['start'],f['end']) for f in cfg['folds']}; sev=p3.metrics(r['severe'],a,b); sup=p3.metrics(r['supersevere'],a,b); conc=p3.concentration_metrics(r['base'],a,b); beta_n=p3.beta_neutrality_metrics(r['base'],liquid,a,b); regimes=p3.regime_metrics(r['base'],liquid,a,b,b); passed,failures=p3.training_gate(train,folds,sev,sup,conc)
 hyp='Contracts with stronger prior-completed-day bid-vs-ask quoted notional imbalance subsequently outperform peers after dollar/BTC-beta neutralization.'; report={'engine':'V98 Independent','phase':PHASE,'hypothesis':hyp,'preregistration':'reports/v98_independent_phase050_bookdepth_preregistration.md','acquisition_training':cov,'selection_policy':'single frozen positive previous-completed-UTC-day median all-level book-depth imbalance; no sign/level/window/cadence/gross/threshold/regime/subset search','training':train,'folds':folds,'stress_training':{'severe':sev,'supersevere':sup},'concentration_training':conc,'beta_neutrality_training':beta_n,'regimes_training':regimes,'training_gate':{'passed':passed,'failures':failures},'validation':None,'final_holdout':None}
 if passed:
  vr0,vcov=acquire(cfg['validation_start'],cfg['validation_end']); alls=pd.concat([signal,vr0]).sort_index(); vt=build_targets(liquid,membership,alls); vr={s:ev(liquid,vt,cfg,s) for s in ('base','severe','supersevere')}; v0,v1=cfg['validation_start'],cfg['validation_end']; vb=p3.metrics(vr['base'],v0,v1); vs=p3.metrics(vr['severe'],v0,v1); vss=p3.metrics(vr['supersevere'],v0,v1); vp,vf=p3.holdout_gate(vb,vs,vss); report['validation']={'acquisition':vcov,'base':vb,'severe':vs,'supersevere':vss,'gate':{'passed':vp,'failures':vf}}
 REPORT_PATH.write_text(json.dumps(report,indent=2,default=str)+'\n'); r['base'].positions.to_csv(POSITIONS_PATH); validation_pass=bool(passed and report['validation'] and report['validation']['gate']['passed']); state['phase']='phase_050_complete'; state['last_experiment']={'id':PHASE['id'],'hypothesis':hyp,'status':'frozen_pending_final_holdout' if validation_pass else ('training_passed_validation_rejected' if passed else 'training_rejected'),'parameters':'preregistered positive lagged daily book-depth imbalance; daily rebalance; 720h beta; 0.75 gross; beta/dollar neutral','report':str(REPORT_PATH.relative_to(PROJECT)),'training_summary':train,'folds':folds,'stress_training':report['stress_training'],'training_gate':report['training_gate'],'validation':report['validation'],'final_holdout_opened':False}; state['champion']=PHASE['id'] if validation_pass else state.get('champion'); state['final_holdout_untouched']=True; state['next_action']='If Phase050 passes training+validation, freeze before one-shot final holdout. If rejected, close exact book-depth imbalance without rescue tuning.'; STATE_PATH.write_text(json.dumps(state,indent=2,default=str)+'\n'); print(json.dumps({'phase':PHASE['id'],'coverage':cov,'training_gate':report['training_gate'],'training':train,'folds':folds,'stress':report['stress_training'],'validation':report['validation'],'final_holdout':'UNTOUCHED'},indent=2,default=str))
if __name__=='__main__':main()
