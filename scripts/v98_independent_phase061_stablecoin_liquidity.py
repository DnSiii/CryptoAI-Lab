from __future__ import annotations
import json,math,sys,urllib.request
from datetime import datetime,timezone
from pathlib import Path
import numpy as np,pandas as pd
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,validate_data
import v98_independent_phase003_dispersion_neutral as p3
CFG=PROJECT/'config'/'v98_independent.json';OUT=PROJECT/'reports'/'v98_independent_phase061_stablecoin_liquidity.json';POS=PROJECT/'reports'/'v98_independent_phase061_stablecoin_liquidity_positions.csv'
URL='https://stablecoins.llama.fi/stablecoincharts/all';SYMBOL='BTCUSDT';GROSS=.75;LOOKBACK=30

def get_total(row):
 for key in ('totalCirculatingUSD','totalCirculating'):
  v=row.get(key);v=v.get('peggedUSD') if isinstance(v,dict) else v
  try:
   x=float(v)
   if math.isfinite(x) and x>0:return x
  except (TypeError,ValueError):pass
 return None

def supply():
 req=urllib.request.Request(URL,headers={'User-Agent':'CryptoAI-Lab-V98-Independent/1.0'})
 with urllib.request.urlopen(req,timeout=120) as r:rows=json.load(r)
 x={}
 for row in rows:
  try:d=pd.Timestamp(datetime.fromtimestamp(int(row['date']),tz=timezone.utc).date(),tz='UTC');v=get_total(row)
  except Exception:continue
  if v is not None:x[d]=v
 return pd.Series(x,dtype=float).sort_index()

def targets(data,s):
 idx=data.close.index;days=idx.floor('D');daily=s.reindex(pd.date_range(s.index.min(),days.max(),freq='D',tz='UTC')).ffill()
 # Frozen causal rule: at day t use only t-1 and t-31 observations.
 growth=daily.shift(1)/daily.shift(LOOKBACK+1)-1;sig=np.sign(growth).reindex(days).set_axis(idx).fillna(0.)
 t=pd.DataFrame(0.,index=idx,columns=data.close.columns);events=idx.hour==0
 if SYMBOL not in t.columns:raise RuntimeError('BTCUSDT unavailable')
 t.loc[events,SYMBOL]=GROSS*sig.loc[events].to_numpy();return t.where(pd.Series(events,index=idx),np.nan).ffill().fillna(0.),{'source_rows':int(len(s)),'source_start':str(s.index.min()),'source_end':str(s.index.max()),'positive_signal_hours':int((sig>0).sum()),'negative_signal_hours':int((sig<0).sum())}

def ev(data,t,cfg,s):
 f=cfg['funding_stress'][s];return exact_fast(data,t,cost_per_side=cfg['costs'][f'{s}_per_side'],gross_guard_cap=GROSS,funding_debit_multiplier=f['debit_multiplier'],funding_credit_multiplier=f['credit_multiplier'])

def main():
 cfg=json.loads(CFG.read_text());data=load_data(PROJECT,cfg['data_config']);v=validate_data(data)
 if v['errors']:raise RuntimeError(str(v['errors'][:5]))
 t,diag=targets(data,supply());r={s:ev(data,t,cfg,s) for s in ('base','severe','supersevere')};a,b=cfg['research_start'],cfg['training_end']
 train=p3.metrics(r['base'],a,b);folds={f['name']:p3.metrics(r['base'],f['start'],f['end']) for f in cfg['folds']};sev=p3.metrics(r['severe'],a,b);sup=p3.metrics(r['supersevere'],a,b);conc=p3.concentration_metrics(r['base'],a,b);reg=p3.regime_metrics(r['base'],data,a,b,b)
 failures=[]
 if train['total_return']<=0:failures.append('aggregate_return<=0')
 if train['profit_factor_daily']<=1.05:failures.append('aggregate_pf<=1.05')
 if train['max_drawdown']<=-0.35:failures.append('max_drawdown<=-35%')
 for name,m in folds.items():
  if m['total_return']<=0:failures.append(f'{name}_return<=0')
  if m['profit_factor_daily']<=1.02:failures.append(f'{name}_pf<=1.02')
 passed=not failures
 rep={'engine':'V98 Independent','phase':'061','hypothesis':'Lagged 30-calendar-day aggregate stablecoin supply growth direction predicts BTC liquidity direction.','preregistration':'reports/v98_independent_phase061_stablecoin_liquidity_preregistration.md','selection_policy':'single frozen 30-day sign; BTCUSDT perpetual gross 0.75; daily 00:00 UTC rebalance; no search/inversion/rescue','source_diagnostics':diag,'training':train,'folds':folds,'stress_training':{'severe':sev,'supersevere':sup},'concentration_training':conc,'regimes_training':reg,'training_gate':{'passed':passed,'failures':failures},'validation':None,'final_holdout':None,'final_holdout_untouched':True,'v99_used':False}
 # Validation is intentionally NOT executed in the same training script. A PASS freezes evidence first, then a separate validation-only gate may be created without changing signal construction.
 OUT.write_text(json.dumps(rep,indent=2,default=str)+'\n');r['base'].positions.to_csv(POS);print(json.dumps({'phase':'061','training_gate':rep['training_gate'],'training':train,'folds':folds,'stress':rep['stress_training'],'final_holdout':'UNTOUCHED'},indent=2,default=str))
if __name__=='__main__':main()
