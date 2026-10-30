from __future__ import annotations
import json,sys
from pathlib import Path
import numpy as np,pandas as pd
PROJECT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(PROJECT/'src')); sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,point_in_time_liquid_view,validate_data
import v98_independent_phase003_dispersion_neutral as p3
import v98_independent_phase005_dual_sleeve as p5
CONFIG_PATH=PROJECT/'config'/'v98_independent.json'; STATE_PATH=PROJECT/'state'/'v98_independent_state.json'; REPORT_PATH=PROJECT/'reports'/'v98_independent_phase011_volume_attention.json'; POSITIONS_PATH=PROJECT/'reports'/'v98_independent_phase011_volume_attention_positions.csv'
PHASE={'id':'phase_011_volume_attention','liquidity_top_n':10,'liquidity_lookback_hours':720,'minimum_history_hours':2160,'volume_fast_hours':24,'volume_reference_hours':720,'rebalance_hours':24,'long_count':3,'short_count':3,'gross_cap':0.75}
def build_targets(data,membership):
    """Independent attention/flow factor using only lagged quote volume.
    Phase010 low-vol risk premium failed broadly, so its sign/lookback are not tuned.
    Hypothesis: persistent abnormal trading attention carries cross-sectional information.
    Long high relative quote-volume attention and short low attention, with dollar/BTC-beta
    neutralization. Signal uses quote volume shifted one hour; one predeclared architecture.
    """
    hourly,beta,_,eligible=p5.residual_components(data,membership); qv=data.frames['quote_volume'].shift(1)
    fast=qv.rolling(PHASE['volume_fast_hours'],min_periods=12).mean(); ref=qv.rolling(PHASE['volume_reference_hours'],min_periods=360).median(); attention=np.log((fast/ref.replace(0,np.nan)).clip(lower=1e-6)); score=attention.rank(axis=1,pct=True,method='average').where(eligible)
    inv=(1/hourly.rolling(720,min_periods=360).std().replace(0,np.nan)).clip(upper=50).where(eligible); targets=pd.DataFrame(0.0,index=data.close.index,columns=data.close.columns); events=np.arange(len(targets))%PHASE['rebalance_hours']==0; old=(p5.PHASE['sleeve_gross'],p5.PHASE['long_count'],p5.PHASE['short_count'])
    try:
        p5.PHASE['sleeve_gross']=PHASE['gross_cap']; p5.PHASE['long_count']=PHASE['long_count']; p5.PHASE['short_count']=PHASE['short_count']
        for ts in targets.index[events]:
            w=p5._neutral_event_weights(score,inv,beta,eligible,ts)
            if len(w): targets.loc[ts,w.index]=w
    finally: p5.PHASE['sleeve_gross'],p5.PHASE['long_count'],p5.PHASE['short_count']=old
    targets=targets.where(pd.Series(events,index=targets.index),np.nan).ffill().fillna(0); gross=targets.abs().sum(axis=1); return targets.mul((PHASE['gross_cap']/gross.replace(0,np.nan)).clip(upper=1).fillna(0),axis=0)
def evaluate(data,t,cfg,s):
    f=cfg['funding_stress'][s]; return exact_fast(data,t,cost_per_side=cfg['costs'][f'{s}_per_side'],gross_guard_cap=PHASE['gross_cap'],funding_debit_multiplier=f['debit_multiplier'],funding_credit_multiplier=f['credit_multiplier'])
def main():
    cfg=json.loads(CONFIG_PATH.read_text()); state=json.loads(STATE_PATH.read_text()); data=load_data(PROJECT,cfg['data_config']); v=validate_data(data)
    if v['errors']: raise RuntimeError(str(v['errors'][:5]))
    liquid,membership=point_in_time_liquid_view(data,top_n=PHASE['liquidity_top_n'],lookback_hours=PHASE['liquidity_lookback_hours'],minimum_history_hours=PHASE['minimum_history_hours']); t=build_targets(liquid,membership); r={s:evaluate(liquid,t,cfg,s) for s in ('base','severe','supersevere')}; start,end=cfg['research_start'],cfg['training_end']; train=p3.metrics(r['base'],start,end); folds={f['name']:p3.metrics(r['base'],f['start'],f['end']) for f in cfg['folds']}; sev=p3.metrics(r['severe'],start,end); sup=p3.metrics(r['supersevere'],start,end); conc=p3.concentration_metrics(r['base'],start,end); beta=p3.beta_neutrality_metrics(r['base'],liquid,start,end); regimes=p3.regime_metrics(r['base'],liquid,start,end,end); passed,failures=p3.training_gate(train,folds,sev,sup,conc); hypothesis='Cross-sectional abnormal trading attention measured by lagged quote-volume expansion predicts relative returns after market-beta neutralization.'; report={'engine':'V98 Independent','phase':PHASE,'hypothesis':hypothesis,'selection_policy':'independent volume/attention family after Phase010 rejection; one predeclared architecture; t-1 quote volume; no grid; no holdout selection','training':train,'folds':folds,'stress_training':{'severe':sev,'supersevere':sup},'concentration_training':conc,'beta_neutrality_training':beta,'regimes_training':regimes,'training_gate':{'passed':passed,'failures':failures},'holdout':None}
    if passed:
        h0,h1=cfg['holdout_start'],cfg['holdout_end']; hb=p3.metrics(r['base'],h0,h1); hs=p3.metrics(r['severe'],h0,h1); hss=p3.metrics(r['supersevere'],h0,h1); hp,hf=p3.holdout_gate(hb,hs,hss); report['holdout']={'base':hb,'severe':hs,'supersevere':hss,'gate':{'passed':hp,'failures':hf}}
    REPORT_PATH.parent.mkdir(parents=True,exist_ok=True); REPORT_PATH.write_text(json.dumps(report,indent=2,default=str)+'\n'); r['base'].positions.to_csv(POSITIONS_PATH); final=bool(passed and report['holdout'] and report['holdout']['gate']['passed']); state['phase']='phase_011_complete'; state['champion']=PHASE['id'] if final else state.get('champion'); state['last_experiment']={'id':PHASE['id'],'hypothesis':hypothesis,'status':'validated_candidate' if final else ('training_passed_holdout_rejected' if passed else 'training_rejected'),'parameters':'24h lagged quote-volume attention vs 30d reference; daily rebalance; 0.75 gross; no grid','report':str(REPORT_PATH.relative_to(PROJECT)),'training_summary':train,'folds':folds,'stress_training':report['stress_training'],'training_gate':report['training_gate'],'holdout_validation_recorded_but_not_for_selection':report['holdout']}; state['holdout_evaluated_for_validation']=bool(passed); state['next_action']='Diagnose Phase011. If rejected, move to another independent family rather than tuning volume windows. If validated, freeze and run robustness gate.'; STATE_PATH.write_text(json.dumps(state,indent=2,default=str)+'\n'); print(json.dumps({'phase':PHASE['id'],'training_gate':report['training_gate'],'training':train,'folds':folds,'stress':report['stress_training'],'holdout':report['holdout']},indent=2,default=str))
if __name__=='__main__': main()
