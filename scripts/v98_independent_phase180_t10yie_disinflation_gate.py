from __future__ import annotations
import csv,io,json,sys,urllib.request,urllib.error,time
from pathlib import Path
import numpy as np
import pandas as pd
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,validate_data
import v98_independent_phase003_dispersion_neutral as p3
CFG=PROJECT/'config'/'v98_independent.json';OUT=PROJECT/'reports'/'v98_independent_phase180_t10yie_disinflation_gate.json'
ASSETS=['BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT'];A='2023-01-01';B='2025-12-31';TARGET=.30;CAP=.35
URL='https://fred.stlouisfed.org/graph/fredgraph.csv?id=T10YIE&cosd=2022-01-01&coed=2025-12-31'

def acquire():
 req=urllib.request.Request(URL,headers={'User-Agent':'CryptoAI-Lab-V98-Independent/1.0','Accept':'text/csv'});errs=[]
 for attempt in range(4):
  try:
   with urllib.request.urlopen(req,timeout=90) as r: raw=r.read()
   if len(raw)<100: raise RuntimeError(f'implausibly short response: {len(raw)} bytes')
   return raw.decode('utf-8-sig')
  except (TimeoutError,urllib.error.URLError,RuntimeError) as e:
   errs.append(f'{type(e).__name__}: {e}')
   if attempt<3: time.sleep(2**attempt)
 raise RuntimeError('FRED acquisition failed after 4 attempts: '+' | '.join(errs))

def macro():
 r=csv.DictReader(io.StringIO(acquire()));fields=r.fieldnames or [];dc='DATE' if 'DATE' in fields else 'observation_date' if 'observation_date' in fields else None
 if dc is None or 'T10YIE' not in fields: raise RuntimeError(f'unexpected FRED schema: {fields}')
 x=[]
 for z in r:
  if z['T10YIE'] not in ('','.'):
   x.append((pd.Timestamp(z[dc],tz='UTC'),float(z['T10YIE'])))
 s=pd.Series(dict(x)).sort_index();assert s.index.is_unique and s.index.max()<pd.Timestamp('2026-01-01',tz='UTC')
 # Conservative causal floor frozen by prereg: next US business day, never same-day.
 s.index=s.index+pd.offsets.BDay(1)
 return s

def targets(data,s,mult):
 stress=s.diff(63)<0
 t=pd.DataFrame(np.nan,index=data.close.index,columns=data.close.columns);decision=t.index.hour==0
 state=stress.reindex(t.index[decision],method='ffill').fillna(False)
 for ts,v in state.items():
  gross=TARGET*(mult if bool(v) else 1.0);t.loc[ts,ASSETS]=gross/len(ASSETS)
 return t.where(pd.Series(decision,index=t.index),np.nan).ffill().fillna(0.)

def ev(data,t,cfg,z):
 f=cfg['funding_stress'][z]
 return exact_fast(data,t,cost_per_side=cfg['costs'][f'{z}_per_side'],gross_guard_cap=CAP,funding_debit_multiplier=f['debit_multiplier'],funding_credit_multiplier=f['credit_multiplier'])
def daily(r):return r.equity.loc[A:B].resample('1D').last().pct_change(fill_method=None).dropna()
def audit(r,data,t):
 m=p3.metrics(r,A,B);d=daily(r);pos=d[d>0];neg=d[d<0]
 x=(t.shift(1)*data.close.pct_change(fill_method=None)).loc[A:B,ASSETS].sum();den=float(x.abs().sum());shares={k:(float(v/den) if den else 0.) for k,v in x.items()}
 return {'metrics':m,'regimes':p3.regime_metrics(r,data,f'{A}T00:00:00+00:00',f'{B}T00:00:00+00:00',f'{B}T00:00:00+00:00'),'concentration':p3.concentration_metrics(r,A,B),'asset_contribution_share':shares,'tails':{'top10_positive_share':float(pos.nlargest(10).sum()/pos.sum()) if pos.sum()>0 else 0.,'bottom10_negative_share':float(abs(neg.nsmallest(10).sum())/abs(neg.sum())) if neg.sum()<0 else 0.}}
def main():
 cfg=json.loads(CFG.read_text());assert cfg['final_holdout_start'].startswith('2026-08-01')
 data=load_data(PROJECT,cfg['data_config']);v=validate_data(data);assert not v['errors'],v['errors'][:5];s=macro();variants={}
 for name,mult in [('CONTROL',1.0),('DISINFLATION_GATE',.5)]:
  t=targets(data,s,mult);rs={z:ev(data,t,cfg,z) for z in ('base','severe','supersevere')}
  variants[name]={'base':audit(rs['base'],data,t),'severe':p3.metrics(rs['severe'],A,B),'supersevere':p3.metrics(rs['supersevere'],A,B),'folds':{y:p3.metrics(rs['base'],f'{y}-01-01',f'{y}-12-31') for y in ('2023','2024','2025')},'max_open_gross':float(rs['base'].open_positions.loc[A:B].abs().sum(axis=1).max())}
 c=variants['CONTROL']['base']['metrics'];g=variants['DISINFLATION_GATE']['base']['metrics'];fail=[]
 if g['total_return']<=c['total_return']:fail.append('no_return_improvement_vs_control')
 if g['profit_factor_daily']<=c['profit_factor_daily']:fail.append('no_pf_improvement_vs_control')
 if any(variants['DISINFLATION_GATE']['folds'][y]['total_return']<=0 for y in ('2023','2024','2025')):fail.append('nonpositive_year')
 for z in ('severe','supersevere'):
  if variants['DISINFLATION_GATE'][z]['total_return']<=0:fail.append(f'{z}_return<=0')
 if variants['DISINFLATION_GATE']['max_open_gross']>CAP+2e-5:fail.append('gross_cap')
 report={'engine':'V98 Independent','phase':180,'hypothesis':'fixed T10YIE 63-observation disinflation-stress 0.50 gross gate','window':[A,B],'causal_availability':'next_US_business_day','same_day_use':False,'parameter_search':False,'threshold_search':False,'lookback_search':False,'rescue_allowed':False,'v16_used':False,'v99_used':False,'validation':None,'final_holdout':None,'variants':variants,'gate':{'passed':not fail,'decision':'PASS_TRAINING_FREEZE_FOR_VALIDATION' if not fail else 'REJECT_NO_RESCUE','failures':fail}}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True))
if __name__=='__main__':main()
