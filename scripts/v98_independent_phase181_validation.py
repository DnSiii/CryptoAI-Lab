from __future__ import annotations
# Phase181 confirmatory validation of Phase180 frozen candidate. No tuning/rescue.
import csv,hashlib,io,json,sys,time,urllib.error,urllib.request
from pathlib import Path
import numpy as np
import pandas as pd
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,validate_data
import v98_independent_phase003_dispersion_neutral as p3
CFG=PROJECT/'config'/'v98_independent.json';OUT=PROJECT/'reports'/'v98_independent_phase181_validation.json'
DATA_CFG='v98_independent_phase082_validation_data.json';ASSETS=['BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT'];TARGET=.30;CAP=.35
URL='https://fred.stlouisfed.org/graph/fredgraph.csv?id=T10YIE&cosd=2022-01-01&coed=2026-07-31'

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
 x=[(pd.Timestamp(z[dc],tz='UTC'),float(z['T10YIE'])) for z in r if z['T10YIE'] not in ('','.')]
 s=pd.Series(dict(x)).sort_index();assert s.index.is_unique and s.index.max()<pd.Timestamp('2026-08-01',tz='UTC')
 s.index=s.index+pd.offsets.BDay(1);return s

def targets(data,s,mult):
 stress=s.diff(63)<0;t=pd.DataFrame(np.nan,index=data.close.index,columns=data.close.columns);decision=t.index.hour==0
 state=stress.reindex(t.index[decision],method='ffill').fillna(False)
 for ts,v in state.items():
  gross=TARGET*(mult if bool(v) else 1.0);t.loc[ts,ASSETS]=gross/len(ASSETS)
 return t.where(pd.Series(decision,index=t.index),np.nan).ffill().fillna(0.)

def ev(data,t,cfg,z):
 f=cfg['funding_stress'][z];return exact_fast(data,t,cost_per_side=cfg['costs'][f'{z}_per_side'],gross_guard_cap=CAP,funding_debit_multiplier=f['debit_multiplier'],funding_credit_multiplier=f['credit_multiplier'])
def tails(r,a,b):
 d=r.equity.loc[a:b].resample('1D').last().pct_change(fill_method=None).dropna();p=d[d>0];n=d[d<0]
 return {'top10_positive_share':float(p.nlargest(10).sum()/p.sum()) if p.sum()>0 else 0.,'bottom10_negative_share':float(abs(n.nsmallest(10).sum())/abs(n.sum())) if n.sum()<0 else 0.}
def contrib(data,t,a,b):
 x=(t.shift(1)*data.close.pct_change(fill_method=None)).loc[a:b,ASSETS].sum();den=float(x.abs().sum());return {k:(float(v/den) if den else 0.) for k,v in x.items()}
def main():
 cfg=json.loads(CFG.read_text());a=cfg['validation_start'];b=cfg['validation_end'];assert b<'2026-08-01'
 data=load_data(PROJECT,DATA_CFG);v=validate_data(data);assert not v['errors'],v['errors'][:5];s=macro();variants={}
 for name,mult in [('CONTROL',1.0),('DISINFLATION_GATE',.5)]:
  t=targets(data,s,mult);rs={z:ev(data,t,cfg,z) for z in ('base','severe','supersevere')};base=rs['base'];m=p3.metrics(base,a,b)
  months={}
  for x in pd.period_range('2026-01','2026-07',freq='M'):
   aa=max(pd.Timestamp(a),x.start_time.tz_localize('UTC'));bb=min(pd.Timestamp(b),x.end_time.tz_localize('UTC'));months[str(x)]=p3.metrics(base,aa,bb)
  variants[name]={'base':m,'severe':p3.metrics(rs['severe'],a,b),'supersevere':p3.metrics(rs['supersevere'],a,b),'months':months,'regimes':p3.regime_metrics(base,data,a,b,b),'concentration':p3.concentration_metrics(base,a,b),'asset_contribution_share':contrib(data,t,a,b),'tails':tails(base,a,b),'max_open_gross':float(base.open_positions.loc[a:b].abs().sum(axis=1).max()),'positions_sha256':hashlib.sha256(t.loc[a:b,ASSETS].to_csv().encode()).hexdigest()}
 g=variants['DISINFLATION_GATE'];m=g['base'];fail=[]
 if m['total_return']<=0:fail.append('validation_return<=0')
 if m['profit_factor_daily']<=1.02:fail.append('validation_pf<=1.02')
 if m['max_drawdown']<-.35:fail.append('validation_max_drawdown<-35%')
 if m.get('ruin'):fail.append('validation_ruin')
 if g['severe']['total_return']<=0:fail.append('severe_return<=0')
 if g['supersevere']['total_return']<=0:fail.append('supersevere_return<=0')
 if g['max_open_gross']>CAP+2e-5:fail.append('gross_cap')
 rep={'engine':'V98 Independent','phase':181,'candidate':'Phase180 frozen T10YIE 63-observation disinflation-stress 0.50 gate','window':[a,b],'parameters_frozen_from_phase180':True,'same_day_use':False,'parameter_search':False,'threshold_search':False,'lookback_search':False,'rescue_allowed':False,'v16_used':False,'v99_used':False,'final_holdout':None,'final_holdout_untouched':True,'variants':variants,'validation_gate':{'passed':not fail,'decision':'PASS_VALIDATION_FREEZE_FOR_FINAL_HOLDOUT' if not fail else 'REJECT_VALIDATION_NO_RESCUE','failures':fail}}
 OUT.write_text(json.dumps(rep,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps(rep,indent=2,sort_keys=True,default=str))
if __name__=='__main__':main()
