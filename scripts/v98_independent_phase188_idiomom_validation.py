from __future__ import annotations
# Phase188 untouched validation of Phase187 frozen h24_w90_low50. No tuning/rescue.
import hashlib,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,validate_data
import v98_independent_phase003_dispersion_neutral as p3
CFG=PROJECT/'config'/'v98_independent.json';OUT=PROJECT/'reports'/'v98_independent_phase188_idiomom_validation.json';PREREG=PROJECT/'research'/'v98_independent_phase188_idiomom_validation_preregister.md'
DATA_CFG='v98_independent_phase082_validation_data.json';ASSETS=['BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT'];TARGET=.30;CAP=.35;H=24;W=90;LOW=.50

def overlay(data):
 lag=data.close[ASSETS].shift(1);mom=lag.pct_change(H,fill_method=None);res=mom.sub(mom.mean(axis=1),axis=0);disp=res.std(axis=1);ref=disp.rolling(W*24,min_periods=max(24,W*12)).quantile(.5).shift(1);high=(disp>ref)&ref.notna();idx=data.close.index;t=pd.DataFrame(np.nan,index=idx,columns=data.close.columns);decision=idx.hour==0
 for ts in idx[decision]:
  mult=1.0 if bool(high.get(ts,False)) else LOW;t.loc[ts,ASSETS]=TARGET*mult/len(ASSETS)
 return t.where(pd.Series(decision,index=idx),np.nan).ffill().fillna(0.)
def ev(data,t,cfg,z):
 f=cfg['funding_stress'][z];return exact_fast(data,t,cost_per_side=cfg['costs'][f'{z}_per_side'],gross_guard_cap=CAP,funding_debit_multiplier=f['debit_multiplier'],funding_credit_multiplier=f['credit_multiplier'])
def tails(r,a,b):
 d=r.equity.loc[a:b].resample('1D').last().pct_change(fill_method=None).dropna();p=d[d>0];n=d[d<0]
 return {'top10_positive_share':float(p.nlargest(10).sum()/p.sum()) if p.sum()>0 else 0.,'bottom10_negative_share':float(abs(n.nsmallest(10).sum())/abs(n.sum())) if n.sum()<0 else 0.}
def contrib(data,t,a,b):
 x=(t.shift(1)*data.close.pct_change(fill_method=None)).loc[a:b,ASSETS].sum();den=float(x.abs().sum());return {k:(float(v/den) if den else 0.) for k,v in x.items()}
def main():
 cfg=json.loads(CFG.read_text());a=cfg['validation_start'];b=cfg['validation_end'];assert a.startswith('2026-01-01') and b.startswith('2026-07-31');assert cfg['final_holdout_start'].startswith('2026-08-01');assert cfg['research_rules']['holdout_used_for_selection'] is False;assert cfg['research_rules']['v99_used_for_selection'] is False
 data=load_data(PROJECT,DATA_CFG);v=validate_data(data);assert not v['errors'],v['errors'][:5];assert data.close.index.max()<pd.Timestamp('2026-08-01',tz='UTC'),'Phase188 final holdout boundary violated'
 t=overlay(data);rs={z:ev(data,t,cfg,z) for z in ('base','severe','supersevere')};base=rs['base'];m=p3.metrics(base,a,b);asset=contrib(data,t,a,b);ta=tails(base,a,b);reg=p3.regime_metrics(base,data,a,b,b);gross=float(base.open_positions.loc[a:b].abs().sum(axis=1).max())
 rep={'engine':'V98 Independent','phase':188,'candidate':'Phase187 frozen h24_w90_low50','parameters':{'momentum_hours':H,'reference_days':W,'low_dispersion_multiplier':LOW,'target_gross':TARGET,'gross_cap':CAP},'prereg_sha256':hashlib.sha256(PREREG.read_bytes()).hexdigest(),'window':[a,b],'parameters_frozen_from_phase187':True,'parameter_search':False,'rescue_allowed':False,'v16_used':False,'v99_used':False,'final_holdout':None,'final_holdout_untouched':True,'base':m,'severe':p3.metrics(rs['severe'],a,b),'supersevere':p3.metrics(rs['supersevere'],a,b),'regimes':reg,'concentration':p3.concentration_metrics(base,a,b),'asset_contribution_share':asset,'tails':ta,'max_open_gross':gross,'positions_sha256':hashlib.sha256(t.loc[a:b,ASSETS].to_csv().encode()).hexdigest()}
 fail=[]
 for z in ('base','severe','supersevere'):
  q=rep[z]
  if q['total_return']<=0:fail.append(f'{z}_return<=0')
  if q['profit_factor_daily']<=1:fail.append(f'{z}_pf<=1')
 if m.get('ruin') or gross>CAP+2e-5:fail.append('risk_invariant')
 if max(abs(x) for x in asset.values())>.60:fail.append('asset_concentration>0.60')
 if ta['top10_positive_share']>=.50:fail.append('positive_tail_concentration>=0.50')
 if ta['bottom10_negative_share']>=.50:fail.append('negative_tail_concentration>=0.50')
 nonneg=sum(1 for x in reg.values() if isinstance(x,dict) and x.get('n_hours',x.get('observations',1)) and x.get('approx_return',x.get('total_return',-1))>=0)
 if nonneg<2:fail.append('fewer_than_2_nonnegative_regimes')
 rep['validation_gate']={'passed':not fail,'decision':'PASS_VALIDATION_FREEZE_FOR_FINAL_HOLDOUT_DECISION' if not fail else 'REJECT_VALIDATION_NO_RESCUE','failures':fail,'nonnegative_regimes':nonneg}
 OUT.write_text(json.dumps(rep,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps(rep,indent=2,sort_keys=True,default=str))
if __name__=='__main__':main()
