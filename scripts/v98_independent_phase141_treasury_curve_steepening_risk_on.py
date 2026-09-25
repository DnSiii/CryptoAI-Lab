from __future__ import annotations
import csv,hashlib,io,json,math,sys,time,urllib.request
from pathlib import Path
import numpy as np,pandas as pd
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,validate_data
import v98_independent_phase003_dispersion_neutral as p3
CFG=PROJECT/'config'/'v98_independent.json';OUT=PROJECT/'reports'/'v98_independent_phase141_treasury_curve_steepening_risk_on.json'
PREREG='reports/v98_independent_phase141_treasury_curve_steepening_risk_on_prereg.md'
PIT=PROJECT/'reports'/'v98_independent_phase140_t10y2y_pit_audit.json'
ASSETS=['BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT'];TARGET_GROSS=.45;HARD_GROSS=.50;LOOKBACK=20
URL='https://fred.stlouisfed.org/graph/fredgraph.csv?id=T10Y2Y&cosd=2022-10-01&coed=2025-12-31'

def fetch_macro():
 last=None
 for attempt,timeout in enumerate((45,75,105,135),start=1):
  try:
   req=urllib.request.Request(URL,headers={'User-Agent':'CryptoAI-Lab-V98-Independent-Phase141/1.0','Accept':'text/csv','Connection':'close'})
   with urllib.request.urlopen(req,timeout=timeout) as r:payload=r.read()
   rd=csv.DictReader(io.StringIO(payload.decode('utf-8-sig')));vals=[]
   for row in rd:
    try:
     ds=row.get('observation_date') or row.get('DATE');d=pd.Timestamp(ds,tz='UTC');v=float(row['T10Y2Y'])
    except Exception:continue
    if math.isfinite(v):vals.append((d,v))
   s=pd.Series(dict(vals),dtype=float).sort_index();assert s.index.is_unique and len(s)>700
   return s,payload
  except Exception as exc:
   last=exc
   if attempt<4:time.sleep(2*attempt)
 raise RuntimeError(f'Phase141 macro transport failed: {type(last).__name__}') from last

def build_targets(data,macro):
 delta=macro-macro.shift(LOOKBACK);sig=(delta>0).astype(float);activation=sig.copy();activation.index=activation.index+pd.Timedelta(days=1)
 t=pd.DataFrame(np.nan,index=data.close.index,columns=data.close.columns);decision=t.index.hour==0
 state=activation.reindex(t.index[decision],method='ffill').fillna(0.)
 for ts,v in state.items():t.loc[ts,ASSETS]=float(v)*TARGET_GROSS/len(ASSETS)
 return t.where(pd.Series(decision,index=t.index),np.nan).ffill().fillna(0.),activation

def ev(data,t,cfg,s):
 f=cfg['funding_stress'][s]
 return exact_fast(data,t,cost_per_side=cfg['costs'][f'{s}_per_side'],gross_guard_cap=HARD_GROSS+1e-8,funding_debit_multiplier=f['debit_multiplier'],funding_credit_multiplier=f['credit_multiplier'])

def daily(r,a,b):return r.equity.loc[a:b].resample('1D').last().pct_change(fill_method=None).dropna()

def asset_contrib(data,t,a,b):
 x=(t.shift(1)*data.close.pct_change(fill_method=None)).loc[a:b,ASSETS].sum().fillna(0.);pos=x.clip(lower=0);den=float(pos.sum())
 return {k:(float(v/den) if den else 0.) for k,v in pos.items()}

def main():
 pit=json.loads(PIT.read_text());assert pit['decision']=='PASS_PIT_SHORTCUT' and pit['values_exposed'] is False and pit['crypto_returns_accessed'] is False and pit['pnl_computed'] is False
 prereg=PROJECT/PREREG;assert prereg.exists();txt=prereg.read_text();assert '20 available observations' in txt and 'steepening => long' in txt and '0.45' in txt
 cfg=json.loads(CFG.read_text());data=load_data(PROJECT,cfg['data_config']);v=validate_data(data);assert not v['errors'],v['errors'][:5]
 macro,payload=fetch_macro();t,activation=build_targets(data,macro);a=cfg['folds'][0]['start'];b=cfg['training_end']
 rr={z:ev(data,t,cfg,z) for z in ('base','severe','supersevere')};base=rr['base'];train=p3.metrics(base,a,b)
 folds={f['name']:p3.metrics(base,f['start'],f['end']) for f in cfg['folds']};stress={z:p3.metrics(rr[z],a,b) for z in ('severe','supersevere')}
 d=daily(base,a,b);positive=d[d>0];top10=float(positive.nlargest(10).sum()/positive.sum()) if positive.sum()>0 else 0.;shares=asset_contrib(data,t,a,b)
 op=base.open_positions.loc[a:b].abs().sum(axis=1);maxopen=float(op.max());fail=[]
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
 if maxopen>HARD_GROSS:fail.append('hard_gross_cap>0.50')
 rep={'engine':'V98 Independent','phase':'141','hypothesis':'20-observation T10Y2Y steepening is a causal risk-on permission state for equal-weight crypto','preregistration':PREREG,
 'pit_dependency':{'report':'reports/v98_independent_phase140_t10y2y_pit_audit.json','decision':pit['decision'],'sample_vintages':pit['counts']['successful_vintages'],'mismatches':pit['counts']['mismatches']},
 'signal_contract':{'series':'T10Y2Y','lookback_available_observations':LOOKBACK,'direction':'delta>0 => long; else flat','publication_lag':'next calendar day 00:00 UTC','target_gross':TARGET_GROSS,'hard_gross_cap':HARD_GROSS},
 'training':train,'folds':folds,'stress_training':stress,'regimes_training':p3.regime_metrics(base,data,a,b,b),'concentration_training':p3.concentration_metrics(base,a,b),
 'asset_positive_contribution_share':shares,'tails_training':{'top10_positive_day_share':top10,'worst10_sum':float(d.nsmallest(10).sum()),'best10_sum':float(d.nlargest(10).sum()),'worst_day':float(d.min()),'best_day':float(d.max())},
 'signal_observations_training':int(activation.loc[pd.Timestamp(a):pd.Timestamp(b)].notna().sum()),'active_signal_observations_training':int(activation.loc[pd.Timestamp(a):pd.Timestamp(b)].sum()),
 'execution_guard_audit':{'max_open_gross':maxopen,'target_gross':TARGET_GROSS,'hard_cap':HARD_GROSS},
 'reproducibility':{'macro_payload_sha256':hashlib.sha256(payload).hexdigest(),'activation_sha256':hashlib.sha256(activation.to_csv().encode()).hexdigest(),'targets_sha256':hashlib.sha256(t.loc[a:b,ASSETS].to_csv().encode()).hexdigest(),'prereg_sha256':hashlib.sha256(prereg.read_bytes()).hexdigest()},
 'training_gate':{'passed':not fail,'decision':'PASS_TRAINING' if not fail else 'REJECT_NO_RESCUE','failures':fail},'validation':None,'final_holdout':None,'phase083_selection_use':False,'v99_used':False,'v16_used':False,'parameter_search':False,'rescue_allowed':False}
 OUT.write_text(json.dumps(rep,indent=2,default=str)+'\n');print(json.dumps({'gate':rep['training_gate'],'training':train,'folds':folds,'stress':stress,'max_open_gross':maxopen},indent=2,default=str))
if __name__=='__main__':main()
