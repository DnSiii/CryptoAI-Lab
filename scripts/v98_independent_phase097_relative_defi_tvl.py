from __future__ import annotations
import hashlib,json,math,sys,urllib.request
from pathlib import Path
import numpy as np,pandas as pd
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,validate_data
import v98_independent_phase003_dispersion_neutral as p3
CFG=PROJECT/'config'/'v98_independent.json';OUT=PROJECT/'reports'/'v98_independent_phase097_relative_defi_tvl.json';POS=PROJECT/'reports'/'v98_independent_phase097_relative_defi_tvl_positions.csv'
PREREG='reports/v98_independent_phase097_relative_defi_tvl_prereg.md';BASE='https://api.llama.fi/v2/historicalChainTvl/{}';CHAINS=('Ethereum','BSC');SYMBOLS=('ETHUSDT','BNBUSDT');GROSS=.75

def chain_tvl(chain):
 url=BASE.format(chain);req=urllib.request.Request(url,headers={'Accept':'application/json','User-Agent':'CryptoAI-Lab-V98-Phase097/1.0'});raw=urllib.request.urlopen(req,timeout=60).read();obj=json.loads(raw);rows=[]
 for x in obj if isinstance(obj,list) else []:
  try:
   ts=pd.to_datetime(float(x['date']),unit='s',utc=True).normalize();v=float(x['tvl'])
   if math.isfinite(v) and v>=0:rows.append((ts,v))
  except Exception:pass
 s=pd.Series(dict(rows),dtype=float).sort_index();return s,raw,url

def targets(data,eth,bsc):
 t=pd.DataFrame(0.,index=data.close.index,columns=data.close.columns);events=t.index.hour==0
 cal=pd.date_range('2022-12-20','2025-12-31',freq='1D',tz='UTC')
 # Strict causality: shift(1) makes the newest TVL input prior calendar day.
 e=eth.reindex(cal).ffill(limit=3).shift(1);b=bsc.reindex(cal).ffill(limit=3).shift(1)
 er=e/e.shift(7)-1.;br=b/b.shift(7)-1.
 for ts in t.index[events]:
  d=ts.normalize();x=er.get(d,np.nan);y=br.get(d,np.nan)
  if pd.isna(x) or pd.isna(y) or x==y:continue
  if x>y:t.loc[ts,'ETHUSDT']=.375;t.loc[ts,'BNBUSDT']=-.375
  else:t.loc[ts,'ETHUSDT']=-.375;t.loc[ts,'BNBUSDT']=.375
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
 eth,eraw,eurl=chain_tvl('Ethereum');bsc,braw,burl=chain_tvl('BSC');a=cfg['folds'][0]['start'];b=cfg['training_end'];t=targets(data,eth,bsc);rs={x:ev(data,t,cfg,x) for x in ('base','severe','supersevere')};base=rs['base'];train=p3.metrics(base,a,b);folds={f['name']:p3.metrics(base,f['start'],f['end']) for f in cfg['folds']};stress={x:p3.metrics(rs[x],a,b) for x in ('severe','supersevere')};conc=p3.concentration_metrics(base,a,b);con=contribution(data,t,a,b);tail=tails(base,a,b);fail=[]
 if train['total_return']<=0:fail.append('aggregate_return<=0')
 if train['profit_factor_daily']<=1.10:fail.append('aggregate_pf<=1.10')
 if train['max_drawdown']<-.35:fail.append('max_drawdown<-35%')
 for n,m in folds.items():
  if m['total_return']<=0:fail.append(f'{n}_return<=0')
 for x in ('severe','supersevere'):
  if stress[x]['total_return']<=0 or stress[x]['profit_factor_daily']<=1.0:fail.append(f'{x}_gate')
 if max(con['absolute_contribution_share'].values(),default=0)>0.60:fail.append('single_asset_contribution>60%')
 if tail['top10_absolute_day_share']>0.60:fail.append('top10_absolute_day_share>60%')
 rep={'engine':'V98 Independent','phase':'097','hypothesis':'relative 7d DeFi TVL momentum, ETH vs BNB market-neutral','preregistration':PREREG,'parameters':{'lookback_calendar_days':7,'gross':GROSS,'weights':[.375,-.375],'chains':CHAINS,'symbols':SYMBOLS,'lag':'strict prior UTC day','rebalance':'daily 00:00 UTC','direction':'long stronger relative TVL momentum / short weaker'},'source':{'Ethereum':{'url':eurl,'raw_sha256':hashlib.sha256(eraw).hexdigest()},'BSC':{'url':burl,'raw_sha256':hashlib.sha256(braw).hexdigest()}},'phase083_selection_use':False,'future_holdout_required':True,'training':train,'folds':folds,'stress_training':stress,'regimes_training':p3.regime_metrics(base,data,a,b,b),'concentration_training':conc,'asset_contribution_proxy':con,'tails_training':tail,'reproducibility':{'targets_sha256':hashlib.sha256(t.loc[a:b,list(SYMBOLS)].to_csv().encode()).hexdigest(),'prereg_sha256':hashlib.sha256((PROJECT/PREREG).read_bytes()).hexdigest()},'training_gate':{'passed':not fail,'decision':'PASS_TRAINING' if not fail else 'REJECT_NO_RESCUE','failures':fail},'validation':None,'final_holdout':None,'v99_used':False,'v16_used':False,'parameter_search':False,'rescue_allowed':False};OUT.write_text(json.dumps(rep,indent=2,default=str)+'\n');base.positions.to_csv(POS);print(json.dumps({'phase':'097','training_gate':rep['training_gate'],'training':train,'folds':folds,'stress':stress},indent=2,default=str))
if __name__=='__main__':main()
