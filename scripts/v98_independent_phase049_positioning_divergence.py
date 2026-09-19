from __future__ import annotations
import concurrent.futures as cf,io,json,sys,urllib.request,zipfile
from pathlib import Path
import numpy as np,pandas as pd
PROJECT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(PROJECT/'src')); sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,point_in_time_liquid_view,validate_data
import v98_independent_phase003_dispersion_neutral as p3
import v98_independent_phase047_acquire as acq
CONFIG_PATH=PROJECT/'config'/'v98_independent.json'; STATE_PATH=PROJECT/'state'/'v98_independent_state.json'; AUDIT_PATH=PROJECT/'reports'/'v98_independent_phase047_oi_acquisition_audit.json'; REPORT_PATH=PROJECT/'reports'/'v98_independent_phase049_positioning_divergence.json'; POSITIONS_PATH=PROJECT/'reports'/'v98_independent_phase049_positioning_divergence_positions.csv'
PHASE={'id':'phase_049_positioning_divergence','liquidity_top_n':10,'liquidity_lookback_hours':720,'minimum_history_hours':2160,'beta_lookback_hours':720,'min_beta_obs':360,'rebalance_hours':24,'gross_target':0.75,'gross_cap':0.75}
SYMBOLS=acq.SYMBOLS; BASE=acq.BASE

def canonical_positioning(df):
 x=pd.DataFrame({'timestamp':pd.to_datetime(df['create_time'],utc=True,errors='coerce'),'top':pd.to_numeric(df['sum_toptrader_long_short_ratio'],errors='coerce'),'broad':pd.to_numeric(df['count_long_short_ratio'],errors='coerce')})
 x=x[x.timestamp.notna() & x.top.notna() & x.broad.notna() & (x.top>0) & (x.broad>0)].copy().sort_values('timestamp',kind='stable'); x['hour']=x.timestamp.dt.floor('h'); x['divergence']=np.log(x.top)-np.log(x.broad)
 return x.groupby('hour',sort=True,as_index=False).tail(1).reset_index(drop=True)

def fetch_day(symbol,date):
 url=BASE.format(symbol=symbol,date=date)
 try:
  with urllib.request.urlopen(url,timeout=20) as r: payload=r.read()
  with zipfile.ZipFile(io.BytesIO(payload)) as z:
   names=[n for n in z.namelist() if n.lower().endswith('.csv')]
   if len(names)!=1:return symbol,date,None,'csv_members'
   with z.open(names[0]) as f: df=pd.read_csv(f,usecols=['create_time','sum_toptrader_long_short_ratio','count_long_short_ratio'])
  h=canonical_positioning(df)
  if h.empty:return symbol,date,None,'no_valid_hourly_positioning'
  return symbol,date,h[['hour','divergence']],None
 except Exception as e:return symbol,date,None,f'{type(e).__name__}:{e}'

def acquire(start,end):
 days=pd.date_range(pd.Timestamp(start).floor('D'),pd.Timestamp(end).floor('D'),freq='D',tz='UTC'); tasks=[(s,d.strftime('%Y-%m-%d')) for s in SYMBOLS for d in days]; frames={s:[] for s in SYMBOLS}; failures=[]
 with cf.ThreadPoolExecutor(max_workers=32) as ex:
  futs=[ex.submit(fetch_day,*x) for x in tasks]
  for fut in cf.as_completed(futs):
   s,d,h,e=fut.result(); failures.append((s,d,e)) if e else frames[s].append(h)
 out={}
 for s,parts in frames.items():
  if parts: out[s]=pd.concat(parts,ignore_index=True).drop_duplicates('hour',keep='last').sort_values('hour').set_index('hour')['divergence']
 x=pd.DataFrame(out).sort_index(); expected=len(days)*24; cov={s:float(x[s].notna().sum()/expected) if s in x else 0.0 for s in SYMBOLS}
 return x,{'requested_days':len(days),'requested_files':len(tasks),'failed_files':len(failures),'failure_examples':failures[:25],'hourly_coverage':cov,'min_symbol_coverage':min(cov.values()) if cov else 0.0}

def build_targets(data,membership,signal):
 c=PHASE; idx=data.close.index; lag=signal.reindex(idx).shift(1); ret=data.close.shift(1).pct_change(fill_method=None); btc=ret['BTCUSDT']; var=btc.rolling(c['beta_lookback_hours'],min_periods=c['min_beta_obs']).var(); beta=ret.rolling(c['beta_lookback_hours'],min_periods=c['min_beta_obs']).cov(btc).div(var,axis=0)
 eligible=(membership & data.close.notna()); eligible['BTCUSDT']=False; targets=pd.DataFrame(0.0,index=idx,columns=data.close.columns); events=np.arange(len(idx))%c['rebalance_hours']==0
 for k,ts in enumerate(idx):
  if not events[k]:continue
  names=[s for s in targets.columns if s in lag.columns and bool(eligible.at[ts,s]) and pd.notna(lag.at[ts,s]) and pd.notna(beta.at[ts,s])]
  if len(names)<4:continue
  y=(lag.loc[ts,names].rank(pct=True)-0.5).to_numpy(float); b=beta.loc[ts,names].to_numpy(float); X=np.column_stack([np.ones(len(names)),b]); coef,*_=np.linalg.lstsq(X,y,rcond=None); neutral=y-X@coef; gross=float(np.abs(neutral).sum())
  if np.isfinite(gross) and gross>1e-12:targets.loc[ts,names]=neutral*(c['gross_target']/gross)
 targets=targets.where(pd.Series(events,index=idx),np.nan).ffill().fillna(0.0); gross=targets.abs().sum(axis=1); return targets.mul((c['gross_cap']/gross.replace(0,np.nan)).clip(upper=1).fillna(0),axis=0)

def ev(data,t,cfg,s):
 f=cfg['funding_stress'][s]; return exact_fast(data,t,cost_per_side=cfg['costs'][f'{s}_per_side'],gross_guard_cap=PHASE['gross_cap'],funding_debit_multiplier=f['debit_multiplier'],funding_credit_multiplier=f['credit_multiplier'])

def main():
 cfg=json.loads(CONFIG_PATH.read_text()); state=json.loads(STATE_PATH.read_text()); audit=json.loads(AUDIT_PATH.read_text())
 if audit.get('decision')!='integrity_sample_pass':raise RuntimeError('Phase049 blocked: shared metrics archive integrity sample has not passed')
 data=load_data(PROJECT,cfg['data_config']); v=validate_data(data)
 if v['errors']:raise RuntimeError(str(v['errors'][:5]))
 liquid,membership=point_in_time_liquid_view(data,top_n=PHASE['liquidity_top_n'],lookback_hours=PHASE['liquidity_lookback_hours'],minimum_history_hours=PHASE['minimum_history_hours'])
 signal,cov=acquire(cfg['research_start'],cfg['training_end']); t=build_targets(liquid,membership,signal); r={s:ev(liquid,t,cfg,s) for s in ('base','severe','supersevere')}; a,b=cfg['research_start'],cfg['training_end']; train=p3.metrics(r['base'],a,b); folds={f['name']:p3.metrics(r['base'],f['start'],f['end']) for f in cfg['folds']}; sev=p3.metrics(r['severe'],a,b); sup=p3.metrics(r['supersevere'],a,b); conc=p3.concentration_metrics(r['base'],a,b); beta_n=p3.beta_neutrality_metrics(r['base'],liquid,a,b); regimes=p3.regime_metrics(r['base'],liquid,a,b,b); passed,failures=p3.training_gate(train,folds,sev,sup,conc)
 hyp='Contracts where top-trader long/short positioning is stronger relative to broad-account positioning subsequently outperform peers after dollar/BTC-beta neutralization.'; report={'engine':'V98 Independent','phase':PHASE,'hypothesis':hyp,'preregistration':'reports/v98_independent_phase049_positioning_divergence_preregistration.md','acquisition_training':cov,'selection_policy':'single frozen positive strictly lagged log(top-trader position ratio)-log(broad-account ratio); no sign/field/window/cadence/gross/threshold/regime/subset search','training':train,'folds':folds,'stress_training':{'severe':sev,'supersevere':sup},'concentration_training':conc,'beta_neutrality_training':beta_n,'regimes_training':regimes,'training_gate':{'passed':passed,'failures':failures},'validation':None,'final_holdout':None}
 if passed:
  vr0,vcov=acquire(cfg['validation_start'],cfg['validation_end']); alls=pd.concat([signal,vr0]).sort_index(); vt=build_targets(liquid,membership,alls); vr={s:ev(liquid,vt,cfg,s) for s in ('base','severe','supersevere')}; v0,v1=cfg['validation_start'],cfg['validation_end']; vb=p3.metrics(vr['base'],v0,v1); vs=p3.metrics(vr['severe'],v0,v1); vss=p3.metrics(vr['supersevere'],v0,v1); vp,vf=p3.holdout_gate(vb,vs,vss); report['validation']={'acquisition':vcov,'base':vb,'severe':vs,'supersevere':vss,'gate':{'passed':vp,'failures':vf}}
 REPORT_PATH.write_text(json.dumps(report,indent=2,default=str)+'\n'); r['base'].positions.to_csv(POSITIONS_PATH); validation_pass=bool(passed and report['validation'] and report['validation']['gate']['passed']); state['phase']='phase_049_complete'; state['last_experiment']={'id':PHASE['id'],'hypothesis':hyp,'status':'frozen_pending_final_holdout' if validation_pass else ('training_passed_validation_rejected' if passed else 'training_rejected'),'parameters':'preregistered positive lagged top-vs-broad positioning divergence; daily rebalance; 720h beta; 0.75 gross; beta/dollar neutral','report':str(REPORT_PATH.relative_to(PROJECT)),'training_summary':train,'folds':folds,'stress_training':report['stress_training'],'training_gate':report['training_gate'],'validation':report['validation'],'final_holdout_opened':False}; state['champion']=PHASE['id'] if validation_pass else state.get('champion'); state['final_holdout_untouched']=True; state['next_action']='If Phase049 passes training+validation, freeze before one-shot final holdout. If rejected, close participant-positioning divergence without rescue tuning.'; STATE_PATH.write_text(json.dumps(state,indent=2,default=str)+'\n'); print(json.dumps({'phase':PHASE['id'],'coverage':cov,'training_gate':report['training_gate'],'training':train,'folds':folds,'stress':report['stress_training'],'validation':report['validation'],'final_holdout':'UNTOUCHED'},indent=2,default=str))
if __name__=='__main__':main()
