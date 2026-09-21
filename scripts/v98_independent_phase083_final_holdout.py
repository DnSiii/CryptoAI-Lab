from __future__ import annotations
# Phase083: single pre-registered final-holdout opening for the frozen Phase081 candidate.
import hashlib,json,sys
from pathlib import Path
import pandas as pd
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.data import load_data,validate_data
import v98_independent_phase003_dispersion_neutral as p3
import v98_independent_phase081_channel_location as p81
CFG=PROJECT/'config'/'v98_independent.json';OUT=PROJECT/'reports'/'v98_independent_phase083_final_holdout.json';POS=PROJECT/'reports'/'v98_independent_phase083_final_holdout_positions.csv'
PREREG='reports/v98_independent_phase083_final_holdout_preregistration.md';DATA_CFG='v98_independent_phase083_final_holdout_data.json'

def main():
 cfg=json.loads(CFG.read_text());data=load_data(PROJECT,DATA_CFG);v=validate_data(data)
 if v['errors']: raise RuntimeError(str(v['errors'][:5]))
 a=cfg['final_holdout_start'];b=cfg['final_holdout_end']
 # Never silently shorten the pre-registered one-shot holdout if current-month archives are incomplete.
 idx=data.close.index
 if idx.min()>pd.Timestamp(a) or idx.max()<pd.Timestamp(b):
  raise RuntimeError(f'Phase083 holdout coverage incomplete: {idx.min()}..{idx.max()} required {a}..{b}; scoring aborted before PnL evaluation')
 t=p81.targets(data,a,b);rs={s:p81.ev(data,t,cfg,s) for s in ('base','severe','supersevere')};base=rs['base'];m=p3.metrics(base,a,b);stress={s:p3.metrics(rs[s],a,b) for s in ('severe','supersevere')};fail=[]
 if m['total_return']<=0: fail.append('final_return<=0')
 if m['profit_factor_daily']<=1.02: fail.append('final_pf<=1.02')
 if m['max_drawdown']<-.35: fail.append('final_max_drawdown<-35%')
 if m.get('ruin'): fail.append('final_ruin')
 if stress['severe']['total_return']<=0: fail.append('severe_return<=0')
 if stress['supersevere']['total_return']<=0: fail.append('supersevere_return<=0')
 months={}
 for x in pd.period_range('2026-08','2026-09',freq='M'):
  s=max(pd.Timestamp(a),x.start_time.tz_localize('UTC'));e=min(pd.Timestamp(b),x.end_time.tz_localize('UTC'));months[str(x)]=p3.metrics(base,s,e)
 active=(t.loc[a:b,list(p81.SYMBOLS)].abs().sum(axis=1)>0);poshash=hashlib.sha256(t.loc[a:b,list(p81.SYMBOLS)].to_csv().encode()).hexdigest();passed=not fail
 rep={'engine':'V98 Independent','phase':'083','candidate':'Phase081 frozen 28-day cross-sectional lagged channel-location spread','preregistration':PREREG,'holdout_boundary':{'start':a,'end':b},'final_holdout':m,'final_holdout_months':months,'stress_final_holdout':stress,'regimes_final_holdout':p3.regime_metrics(base,data,a,b,b),'concentration_final_holdout':p3.concentration_metrics(base,a,b),'asset_contribution_proxy':p81.contribution(data,t,a,b),'tails_final_holdout':p81.tails(base,a,b),'activation':{'active_hour_ratio':float(active.mean()),'active_hours':int(active.sum()),'hours':int(len(active))},'reproducibility':{'positions_sha256':poshash,'training_positions_sha256':'eac49cb65271d67640a4e856c96eb9398bc25681b7d336228736228fce4a2357','validation_positions_sha256':'4271a9d78363b04a8e97f55bbb54cac7f9c06fa0035f0eea341e57b34cea49dd'},'final_gate':{'passed':passed,'failures':fail,'decision':'PROMOTE_V98_INDEPENDENT_FINAL' if passed else 'REJECT_FINAL_HOLDOUT'},'parameters_frozen_from_phase081':True,'parameter_search':False,'rescue_allowed':False,'single_open':True,'v99_used':False,'v16_used':False}
 OUT.write_text(json.dumps(rep,indent=2,default=str)+'\n');base.positions.loc[a:b].to_csv(POS);print(json.dumps({'phase':'083','final_gate':rep['final_gate'],'final_holdout':m,'months':months,'stress':stress},indent=2,default=str))
if __name__=='__main__':main()
