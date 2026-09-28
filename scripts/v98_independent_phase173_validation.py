from __future__ import annotations
import json,sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.data import load_data,validate_data
import v98_independent_phase003_dispersion_neutral as p3
import v98_independent_phase172_t10y2y_steepening_long as p172
CFG=PROJECT/'config'/'v98_independent.json';PRE=PROJECT/'reports'/'v98_independent_phase173_validation_preregistration.json';P172=PROJECT/'reports'/'v98_independent_phase172_t10y2y_steepening_long.json';OUT=PROJECT/'reports'/'v98_independent_phase173_validation.json'
ASSETS=['BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT'];A='2026-01-01';B='2026-07-31';CAP=.35

def main():
 pre=json.loads(PRE.read_text());tr=json.loads(P172.read_text());assert pre['status']=='PREREGISTERED_NOT_RUN' and tr['gate']['decision']=='PASS_TRAINING'
 c=pre['frozen_contract'];assert c['economic_use_lag_days']==1 and c['threshold']==0.0 and c['target_gross']==.30 and c['hard_gross_cap']==CAP and c['assets']==ASSETS
 ao=pre['anti_overfit'];assert not any(ao.values())
 s,h=p172.load_macro();assert h==pre['training_evidence_required']['phase171_data_sha256'];cfg=json.loads(CFG.read_text());data=load_data(PROJECT,cfg['data_config']);v=validate_data(data);assert not v['errors'],v['errors'][:5]
 # Validation must be present through July 2026, while final holdout (2026-08+) remains inaccessible to this evaluator.
 for asset in ASSETS:
  last=data.close[asset].dropna().index.max()
  assert last >= p172.utc_boundary(B),f'validation_data_incomplete:{asset}:{last}'
 t=p172.targets(data,s);rs={z:p172.ev(data,t,cfg,z) for z in ('base','severe','supersevere')};base=rs['base'];m=p3.metrics(base,A,B);stress={z:p3.metrics(rs[z],A,B) for z in ('severe','supersevere')}
 assert 'error' not in m,f'validation_metrics_unavailable:{m}'
 for z in stress: assert 'error' not in stress[z],f'{z}_metrics_unavailable:{stress[z]}'
 d=p172.daily(base,A,B);pos=d[d>0];neg=d[d<0];top10=float(pos.nlargest(10).sum()/pos.sum()) if float(pos.sum())>0 else 0.;bottom10=float(abs(neg.nsmallest(10).sum())/abs(neg.sum())) if float(neg.sum())<0 else 0.;shares=p172.asset_share(data,t,A,B);max_open=float(base.open_positions.loc[A:B].abs().sum(axis=1).max());max_close=float(base.positions.loc[A:B].abs().sum(axis=1).max())
 fail=[]
 if m['total_return']<=0:fail.append('validation_return<=0')
 if m['profit_factor_daily']<=1:fail.append('validation_pf<=1')
 for z in ('severe','supersevere'):
  if stress[z]['total_return']<=0:fail.append(f'{z}_return<=0')
 if m['ruin']:fail.append('ruin_true')
 if max_open>CAP+1e-12:fail.append('max_open_gross>0.35')
 report={'engine':'V98 Independent','phase':'173','candidate':'phase172_t10y2y_steepening_long','window':[A,B],'frozen_contract':c,'training_evidence_blob_sha_required':pre['training_evidence_required']['phase172_blob_sha'],'validation':m,'stress_validation':stress,'regimes_validation':p3.regime_metrics(base,data,p172.utc_boundary(A),p172.utc_boundary(B),p172.utc_boundary(B)),'concentration_validation':p3.concentration_metrics(base,A,B),'asset_contribution_share':shares,'tails_validation':{'top10_positive_day_share':top10,'bottom10_negative_day_share':bottom10,'p01_day':m['p01_day'],'p05_day':m['p05_day'],'cvar05_day':m['cvar05_day'],'worst_day':m['worst_day'],'best_day':m['best_day']},'max_open_gross':max_open,'max_close_gross':max_close,'reproducibility_contract':'deterministic_double_run_required','causality':'frozen_1d_lag','parameter_search':False,'threshold_search':False,'lookback_search':False,'rescue_allowed':False,'training_retune_after_validation':False,'v16_used':False,'v99_used':False,'final_holdout':None,'gate':{'passed':not fail,'decision':'PASS_VALIDATION_FREEZE_FOR_FINAL_HOLDOUT' if not fail else 'REJECT_VALIDATION_NO_RESCUE','failures':fail}}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True))
if __name__=='__main__':main()
