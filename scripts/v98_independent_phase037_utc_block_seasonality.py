from __future__ import annotations
import json,sys
from pathlib import Path
import numpy as np,pandas as pd
PROJECT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(PROJECT/'src')); sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,point_in_time_liquid_view,validate_data
import v98_independent_phase003_dispersion_neutral as p3
CONFIG_PATH=PROJECT/'config'/'v98_independent.json'; STATE_PATH=PROJECT/'state'/'v98_independent_state.json'; REPORT_PATH=PROJECT/'reports'/'v98_independent_phase037_utc_block_seasonality.json'; POSITIONS_PATH=PROJECT/'reports'/'v98_independent_phase037_utc_block_seasonality_positions.csv'
PHASE={'id':'phase_037_utc_block_seasonality','liquidity_top_n':10,'liquidity_lookback_hours':720,'minimum_history_hours':2160,'beta_lookback_hours':720,'min_beta_obs':360,'block_hours':8,'same_block_observations':30,'minimum_same_block_observations':20,'rebalance_hours':8,'gross_target':0.75,'gross_cap':0.75}
def build_targets(data,membership):
    c=PHASE; close=data.close; lag=close.shift(1); eligible=(membership & close.notna()).copy(); eligible['BTCUSDT']=False
    hourly=lag.pct_change(fill_method=None); btc=hourly['BTCUSDT']; var=btc.rolling(c['beta_lookback_hours'],min_periods=c['min_beta_obs']).var(); beta=hourly.rolling(c['beta_lookback_hours'],min_periods=c['min_beta_obs']).cov(btc).div(var,axis=0)
    residual=hourly.sub(beta.mul(btc,axis=0)); block_return=residual.rolling(c['block_hours'],min_periods=c['block_hours']).sum()
    targets=pd.DataFrame(np.nan,index=close.index,columns=close.columns); events=targets.index.hour.isin([0,8,16]); event_idx=targets.index[events]
    for ts in event_idx:
        # A historical block with start-hour matching ts is observed at its end boundary.
        ends=event_idx[(event_idx<=ts) & (((event_idx.hour-c['block_hours'])%24)==ts.hour)]
        ends=ends[-c['same_block_observations']:]
        if len(ends)<c['minimum_same_block_observations']: continue
        exp=block_return.loc[ends].mean(axis=0); ok=eligible.loc[ts] & exp.notna() & beta.loc[ts].notna(); names=ok.index[ok]
        if len(names)<4: continue
        score=exp.loc[names].rank(pct=True).sub(0.5); y=score.to_numpy(float); b=beta.loc[ts,names].to_numpy(float); x=np.column_stack([np.ones(len(names)),b]); coef,*_=np.linalg.lstsq(x,y,rcond=None); neutral=y-x@coef; gross=float(np.abs(neutral).sum()); row=pd.Series(0.0,index=targets.columns)
        if np.isfinite(gross) and gross>1e-12: row.loc[names]=neutral*(c['gross_target']/gross)
        targets.loc[ts]=row
    targets=targets.ffill().fillna(0.0); gross=targets.abs().sum(axis=1); return targets.mul((c['gross_cap']/gross.replace(0,np.nan)).clip(upper=1).fillna(0),axis=0)
def ev(data,t,cfg,s):
    f=cfg['funding_stress'][s]; return exact_fast(data,t,cost_per_side=cfg['costs'][f'{s}_per_side'],gross_guard_cap=PHASE['gross_cap'],funding_debit_multiplier=f['debit_multiplier'],funding_credit_multiplier=f['credit_multiplier'])
def main():
    cfg=json.loads(CONFIG_PATH.read_text()); state=json.loads(STATE_PATH.read_text()); data=load_data(PROJECT,cfg['data_config']); v=validate_data(data)
    if v['errors']: raise RuntimeError(str(v['errors'][:5]))
    liquid,membership=point_in_time_liquid_view(data,top_n=PHASE['liquidity_top_n'],lookback_hours=PHASE['liquidity_lookback_hours'],minimum_history_hours=PHASE['minimum_history_hours']); t=build_targets(liquid,membership); r={s:ev(liquid,t,cfg,s) for s in ('base','severe','supersevere')}; a,b=cfg['research_start'],cfg['training_end']; train=p3.metrics(r['base'],a,b); folds={f['name']:p3.metrics(r['base'],f['start'],f['end']) for f in cfg['folds']}; sev=p3.metrics(r['severe'],a,b); sup=p3.metrics(r['supersevere'],a,b); conc=p3.concentration_metrics(r['base'],a,b); beta_n=p3.beta_neutrality_metrics(r['base'],liquid,a,b); regimes=p3.regime_metrics(r['base'],liquid,a,b,b); passed,failures=p3.training_gate(train,folds,sev,sup,conc)
    hyp='Causal same-UTC-8h-block residual history may capture recurring settlement and regional-flow seasonality cross-sectionally.'; report={'engine':'V98 Independent','phase':PHASE,'hypothesis':hyp,'preregistration':'reports/v98_independent_phase037_utc_block_seasonality_preregistration.md','selection_policy':'single frozen symmetric three-block causal specification; no block/sign/lookback/cadence/gross/threshold/regime search; validation only if training passes; final holdout untouched','training':train,'folds':folds,'stress_training':{'severe':sev,'supersevere':sup},'concentration_training':conc,'beta_neutrality_training':beta_n,'regimes_training':regimes,'training_gate':{'passed':passed,'failures':failures},'validation':None,'final_holdout':None}
    if passed:
        v0,v1=cfg['validation_start'],cfg['validation_end']; vb=p3.metrics(r['base'],v0,v1); vs=p3.metrics(r['severe'],v0,v1); vss=p3.metrics(r['supersevere'],v0,v1); vp,vf=p3.holdout_gate(vb,vs,vss); report['validation']={'base':vb,'severe':vs,'supersevere':vss,'gate':{'passed':vp,'failures':vf}}
    REPORT_PATH.parent.mkdir(parents=True,exist_ok=True); REPORT_PATH.write_text(json.dumps(report,indent=2,default=str)+'\n'); r['base'].positions.to_csv(POSITIONS_PATH); validation_pass=bool(passed and report['validation'] and report['validation']['gate']['passed']); state['phase']='phase_037_complete'; state['last_experiment']={'id':PHASE['id'],'hypothesis':hyp,'status':'frozen_pending_final_holdout' if validation_pass else ('training_passed_validation_rejected' if passed else 'training_rejected'),'parameters':'preregistered symmetric UTC 00/08/16 8h blocks; prior 30 same-block residual observations, min 20; 8h rebalance; 720h beta; 0.75 gross; beta/dollar neutral','report':str(REPORT_PATH.relative_to(PROJECT)),'training_summary':train,'folds':folds,'stress_training':report['stress_training'],'training_gate':report['training_gate'],'validation':report['validation'],'final_holdout_opened':False}; state['champion']=PHASE['id'] if validation_pass else state.get('champion'); state['final_holdout_untouched']=True; state['next_action']='If Phase037 passes training+validation, freeze before one-shot final holdout. If rejected, close UTC-block seasonality without block/sign/lookback rescue and move to another orthogonal alpha.'; STATE_PATH.write_text(json.dumps(state,indent=2,default=str)+'\n'); print(json.dumps({'phase':PHASE['id'],'training_gate':report['training_gate'],'training':train,'folds':folds,'stress':report['stress_training'],'validation':report['validation'],'final_holdout':'UNTOUCHED'},indent=2,default=str))
if __name__=='__main__': main()
