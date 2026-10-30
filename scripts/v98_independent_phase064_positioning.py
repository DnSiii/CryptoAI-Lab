from __future__ import annotations
import csv,io,json,math,sys,urllib.request,zipfile
from pathlib import Path
import numpy as np,pandas as pd
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,validate_data
import v98_independent_phase003_dispersion_neutral as p3
CFG=PROJECT/'config'/'v98_independent.json';OUT=PROJECT/'reports'/'v98_independent_phase064_positioning.json';POS=PROJECT/'reports'/'v98_independent_phase064_positioning_positions.csv'
PREREG='reports/v98_independent_phase064_positioning_preregistration.md'
SYMBOLS=('BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT');LOOKBACK=7;GROSS=.75
URL='https://data.binance.vision/data/futures/um/daily/metrics/{symbol}/{symbol}-metrics-{day}.zip'

def archive(symbol,day):
 u=URL.format(symbol=symbol,day=day);req=urllib.request.Request(u,headers={'User-Agent':'CryptoAI-Lab-V98-Independent/1.0'})
 with urllib.request.urlopen(req,timeout=60) as r: payload=r.read()
 with zipfile.ZipFile(io.BytesIO(payload)) as z:
  names=[n for n in z.namelist() if n.lower().endswith('.csv')]
  if len(names)!=1: raise RuntimeError(f'bad archive {symbol} {day}')
  rows=list(csv.DictReader(io.StringIO(z.read(names[0]).decode('utf-8-sig'))))
 vals=[]
 for row in rows:
  try: oi=float(row['sum_open_interest_value']);ls=float(row['count_long_short_ratio'])
  except (KeyError,TypeError,ValueError): continue
  if math.isfinite(oi) and oi>0 and math.isfinite(ls): vals.append((oi,ls))
 if not vals: raise RuntimeError(f'no finite metrics {symbol} {day}')
 return vals[-1]

def signal_series(start,end):
 days=pd.date_range(pd.Timestamp(start)-pd.Timedelta(days=LOOKBACK+1),pd.Timestamp(end),freq='D')
 raw={s:{} for s in SYMBOLS}
 for s in SYMBOLS:
  for d in days:
   day=d.strftime('%Y-%m-%d');raw[s][day]=archive(s,day)
 votes={}
 for d in pd.date_range(pd.Timestamp(start),pd.Timestamp(end),freq='D'):
  a=(d-pd.Timedelta(days=1)).strftime('%Y-%m-%d');b=(d-pd.Timedelta(days=LOOKBACK+1)).strftime('%Y-%m-%d');sv=[]
  for s in SYMBOLS:
   oi1,ls1=raw[s][a];oi0,_=raw[s][b];g=oi1/oi0-1
   sv.append(1 if g>0 and ls1>1 else (-1 if g<0 and ls1<1 else 0))
  votes[d]=float(np.sign(sum(sv)))
 return pd.Series(votes,dtype=float),{'archives_requested':len(SYMBOLS)*len(days),'days':len(days),'symbols':list(SYMBOLS)}

def targets(data,sig):
 idx=data.close.index;days=idx.floor('D');x=sig.reindex(days).set_axis(idx).fillna(0.);t=pd.DataFrame(0.,index=idx,columns=data.close.columns);events=idx.hour==0
 for s in SYMBOLS:
  if s not in t.columns: raise RuntimeError(f'{s} unavailable')
  t.loc[events,s]=(GROSS/len(SYMBOLS))*x.loc[events].to_numpy()
 return t.where(pd.Series(events,index=idx),np.nan).ffill().fillna(0.)

def ev(data,t,cfg,stress):
 f=cfg['funding_stress'][stress];return exact_fast(data,t,cost_per_side=cfg['costs'][f'{stress}_per_side'],gross_guard_cap=GROSS,funding_debit_multiplier=f['debit_multiplier'],funding_credit_multiplier=f['credit_multiplier'])

def main():
 cfg=json.loads(CFG.read_text());data=load_data(PROJECT,cfg['data_config']);v=validate_data(data)
 if v['errors']: raise RuntimeError(str(v['errors'][:5]))
 # Phase064 preregistration explicitly freezes training to the chronological 2023/2024/2025 folds.
 # Do not inherit the broader V98 research_start here: that would request pre-training metrics outside the frozen contract.
 a=cfg['folds'][0]['start'];b=cfg['training_end'];sig,diag=signal_series(a,b);t=targets(data,sig);r={s:ev(data,t,cfg,s) for s in ('base','severe','supersevere')}
 train=p3.metrics(r['base'],a,b);folds={f['name']:p3.metrics(r['base'],f['start'],f['end']) for f in cfg['folds']};sev=p3.metrics(r['severe'],a,b);sup=p3.metrics(r['supersevere'],a,b);conc=p3.concentration_metrics(r['base'],a,b);reg=p3.regime_metrics(r['base'],data,a,b,b)
 failures=[]
 if train['total_return']<=0: failures.append('aggregate_return<=0')
 if train['profit_factor_daily']<=1.05: failures.append('aggregate_pf<=1.05')
 if train['max_drawdown']<=-0.35: failures.append('max_drawdown<=-35%')
 for name,m in folds.items():
  if m['total_return']<=0: failures.append(f'{name}_return<=0')
  if m['profit_factor_daily']<=1.02: failures.append(f'{name}_pf<=1.02')
 rep={'engine':'V98 Independent','phase':'064','hypothesis':'7-day OI-value growth confirmed by account long/short direction; equal-weight five-asset cross-sectional vote.','preregistration':PREREG,'selection_policy':'single frozen mechanism; no search/inversion/rescue','source_diagnostics':diag,'signal_diagnostics':{'positive_days':int((sig>0).sum()),'negative_days':int((sig<0).sum()),'flat_days':int((sig==0).sum())},'training':train,'folds':folds,'stress_training':{'severe':sev,'supersevere':sup},'concentration_training':conc,'regimes_training':reg,'training_gate':{'passed':not failures,'failures':failures},'validation':None,'final_holdout':None,'final_holdout_untouched':True,'v99_used':False,'v16_used':False,'parameter_search':False}
 OUT.write_text(json.dumps(rep,indent=2,default=str)+'\n');r['base'].positions.to_csv(POS);print(json.dumps({'phase':'064','training_gate':rep['training_gate'],'training':train,'folds':folds,'stress':rep['stress_training'],'final_holdout':'UNTOUCHED'},indent=2,default=str))
if __name__=='__main__': main()
