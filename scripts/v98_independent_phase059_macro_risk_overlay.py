from __future__ import annotations
import csv,io,json,math,sys,urllib.request
from pathlib import Path
import numpy as np,pandas as pd
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,validate_data
import v98_independent_phase003_dispersion_neutral as p3
CFG=PROJECT/'config'/'v98_independent.json';OUT=PROJECT/'reports'/'v98_independent_phase059_macro_risk_overlay.json';POS=PROJECT/'reports'/'v98_independent_phase059_macro_risk_overlay_positions.csv'
SERIES=('VIXCLS','DGS10','DFF');SYMBOLS=('BTCUSDT','ETHUSDT','SOLUSDT','XRPUSDT','BNBUSDT');GROSS=.75

def fetch(s,start,end):
 u=f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={s}&cosd={start[:10]}&coed={end[:10]}'
 q=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 CryptoAI-Lab-V98-Independent/1.0','Accept':'text/csv,*/*'})
 with urllib.request.urlopen(q,timeout=120) as r:text=r.read().decode('utf-8')
 rows=list(csv.DictReader(io.StringIO(text))); x=[]
 for z in rows:
  try:v=float(z[s]);d=pd.Timestamp(z['observation_date'],tz='UTC')
  except (ValueError,TypeError,KeyError):continue
  if math.isfinite(v):x.append((d,v))
 return pd.Series(dict(x),dtype=float).sort_index()

def macro(start,end,idx):
 raw={s:fetch(s,start,end) for s in SERIES};daily=pd.DataFrame(raw).sort_index()
 # Conservative one-calendar-day publication lag; no same-date macro observation can affect trading.
 daily.index=daily.index+pd.Timedelta(days=1); daily=daily.reindex(pd.date_range(daily.index.min(),pd.Timestamp(end).ceil('D'),freq='D',tz='UTC')).ffill()
 v=daily.VIXCLS; y=daily.DGS10; f=daily.DFF
 vm=v.rolling(252,min_periods=126).median();ym=y.rolling(252,min_periods=126).median()
 on=(v<=vm)&(y<=ym)&(f<=f.shift(21))&vm.notna()&ym.notna()&f.shift(21).notna()
 return on.reindex(idx.floor('D')).set_axis(idx).fillna(False),{'rows':int(len(daily)),'start':str(daily.index.min()),'end':str(daily.index.max()),'risk_on_days':int(on.sum())}

def targets(data,on):
 idx=data.close.index;t=pd.DataFrame(0.,index=idx,columns=data.close.columns);events=idx.hour==0
 for k,ts in enumerate(idx):
  if not events[k]:continue
  names=[s for s in SYMBOLS if s in t.columns and pd.notna(data.close.at[ts,s])]
  if bool(on.iloc[k]) and names:t.loc[ts,names]=GROSS/len(names)
 return t.where(pd.Series(events,index=idx),np.nan).ffill().fillna(0.)

def ev(data,t,cfg,s):
 f=cfg['funding_stress'][s];return exact_fast(data,t,cost_per_side=cfg['costs'][f'{s}_per_side'],gross_guard_cap=GROSS,funding_debit_multiplier=f['debit_multiplier'],funding_credit_multiplier=f['credit_multiplier'])

def main():
 cfg=json.loads(CFG.read_text());data=load_data(PROJECT,cfg['data_config']);v=validate_data(data)
 if v['errors']:raise RuntimeError(str(v['errors'][:5]))
 on,md=macro(cfg['research_start'],cfg['training_end'],data.close.index);t=targets(data,on);r={s:ev(data,t,cfg,s) for s in ('base','severe','supersevere')};a,b=cfg['research_start'],cfg['training_end']
 train=p3.metrics(r['base'],a,b);folds={f['name']:p3.metrics(r['base'],f['start'],f['end']) for f in cfg['folds']};sev=p3.metrics(r['severe'],a,b);sup=p3.metrics(r['supersevere'],a,b);conc=p3.concentration_metrics(r['base'],a,b);reg=p3.regime_metrics(r['base'],data,a,b,b);passed,fail=p3.training_gate(train,folds,sev,sup,conc)
 rep={'engine':'V98 Independent','phase':'059','hypothesis':'Lagged benign VIX/10Y/Fed-Funds state permits broad crypto long exposure; otherwise flat.','preregistration':'reports/v98_independent_phase059_macro_risk_preregistration.md','selection_policy':'single frozen conjunction; one-day macro lag; 252-observation medians; 21-observation DFF direction; equal-weight five-symbol long; no search/inversion/rescue','macro_diagnostics':md,'training':train,'folds':folds,'stress_training':{'severe':sev,'supersevere':sup},'concentration_training':conc,'regimes_training':reg,'training_gate':{'passed':passed,'failures':fail},'validation':None,'final_holdout':None,'final_holdout_untouched':True,'v99_used':False}
 # Validation is deliberately opened only after frozen training gate passes; final holdout never loaded here.
 if passed:
  von,vmd=macro(cfg['research_start'],cfg['validation_end'],data.close.index);vt=targets(data,von);vr={s:ev(data,vt,cfg,s) for s in ('base','severe','supersevere')};x,y=cfg['validation_start'],cfg['validation_end'];vb=p3.metrics(vr['base'],x,y);vs=p3.metrics(vr['severe'],x,y);vss=p3.metrics(vr['supersevere'],x,y);vp,vf=p3.holdout_gate(vb,vs,vss);rep['validation']={'macro_diagnostics':vmd,'base':vb,'severe':vs,'supersevere':vss,'gate':{'passed':vp,'failures':vf}}
 OUT.write_text(json.dumps(rep,indent=2,default=str)+'\n');r['base'].positions.to_csv(POS);print(json.dumps({'phase':'059','training_gate':rep['training_gate'],'training':train,'folds':folds,'stress':rep['stress_training'],'validation':rep['validation'],'final_holdout':'UNTOUCHED'},indent=2,default=str))
if __name__=='__main__':main()
