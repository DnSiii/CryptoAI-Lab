from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
import pandas as pd
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.data import load_data,validate_data
import v98_independent_phase003_dispersion_neutral as p3
import v98_independent_phase075_downside_asymmetry as p75
CFG=PROJECT/'config'/'v98_independent.json';OUT=PROJECT/'reports'/'v98_independent_phase076_validation.json';POS=PROJECT/'reports'/'v98_independent_phase076_validation_positions.csv'
PREREG='reports/v98_independent_phase076_validation_preregistration.md';DATA_CFG='v98_independent_phase076_validation_data.json'

def main():
 cfg=json.loads(CFG.read_text());data=load_data(PROJECT,DATA_CFG);v=validate_data(data)
 if v['errors']: raise RuntimeError(str(v['errors'][:5]))
 a=cfg['validation_start'];b=cfg['validation_end'];t=p75.targets(data,a,b);rs={s:p75.ev(data,t,cfg,s) for s in ('base','severe','supersevere')};base=rs['base'];m=p3.metrics(base,a,b);stress={s:p3.metrics(rs[s],a,b) for s in ('severe','supersevere')};fail=[]
 if m['total_return']<=0: fail.append('validation_return<=0')
 if m['profit_factor_daily']<=1.02: fail.append('validation_pf<=1.02')
 if m['max_drawdown']<-.35: fail.append('validation_max_drawdown<-35%')
 if m.get('ruin'): fail.append('validation_ruin')
 if stress['severe']['total_return']<=0: fail.append('severe_return<=0')
 if stress['supersevere']['total_return']<=0: fail.append('supersevere_return<=0')
 months={}
 for x in pd.period_range('2026-01','2026-07',freq='M'):
  s=max(pd.Timestamp(a),x.start_time.tz_localize('UTC'));e=min(pd.Timestamp(b),x.end_time.tz_localize('UTC'));months[str(x)]=p3.metrics(base,s,e)
 active=(t.loc[a:b,list(p75.SYMBOLS)].abs().sum(axis=1)>0);poshash=hashlib.sha256(t.loc[a:b,list(p75.SYMBOLS)].to_csv().encode()).hexdigest()
 rep={'engine':'V98 Independent','phase':'076','candidate':'Phase075 frozen 21-day cross-sectional downside-risk asymmetry','preregistration':PREREG,'validation':m,'validation_months':months,'stress_validation':stress,'regimes_validation':p3.regime_metrics(base,data,a,b,b),'concentration_validation':p3.concentration_metrics(base,a,b),'asset_contribution_proxy':p75.contribution(data,t,a,b),'tails_validation':p75.tails(base,a,b),'activation':{'active_hour_ratio':float(active.mean()),'active_hours':int(active.sum()),'hours':int(len(active))},'reproducibility':{'positions_sha256':poshash,'training_positions_sha256':'33286707f5ae63d13b8758ee1a93b2fc786ce434fb4d3e8884df0ad3d84d0880','training_prereg_sha256':'dfa7300edf9631e979db01eabb103a17383f3c7c75f7453857d7926d6cbbfbb7'},'validation_gate':{'passed':not fail,'failures':fail},'parameters_frozen_from_phase075':True,'parameter_search':False,'rescue_allowed':False,'final_holdout':None,'final_holdout_untouched':True,'v99_used':False,'v16_used':False}
 OUT.write_text(json.dumps(rep,indent=2,default=str)+'\n');base.positions.loc[a:b].to_csv(POS);print(json.dumps({'phase':'076','validation_gate':rep['validation_gate'],'validation':m,'months':months,'stress':stress,'final_holdout':'UNTOUCHED'},indent=2,default=str))
if __name__=='__main__':main()
