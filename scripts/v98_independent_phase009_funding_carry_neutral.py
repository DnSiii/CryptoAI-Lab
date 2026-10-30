from __future__ import annotations

import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'src')); sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data, point_in_time_liquid_view, validate_data
import v98_independent_phase003_dispersion_neutral as p3
import v98_independent_phase005_dual_sleeve as p5

CONFIG_PATH=PROJECT/'config'/'v98_independent.json'; STATE_PATH=PROJECT/'state'/'v98_independent_state.json'
REPORT_PATH=PROJECT/'reports'/'v98_independent_phase009_funding_carry_neutral.json'
POSITIONS_PATH=PROJECT/'reports'/'v98_independent_phase009_funding_carry_neutral_positions.csv'
PHASE={'id':'phase_009_funding_carry_neutral','liquidity_top_n':10,'liquidity_lookback_hours':720,'minimum_history_hours':2160,'funding_lookback_hours':168,'funding_min_observations':5,'volatility_lookback_hours':720,'rebalance_hours':24,'long_count':3,'short_count':3,'gross_cap':0.75}

def build_targets(data,membership):
    """Cross-sectional funding carry, beta-neutral and causal.

    Phase008 proved the residual-dispersion signal can satisfy all training gates after
    risk budgeting but failed its one-shot holdout. We therefore do not tune that
    signal. Phase009 changes alpha family: persistent funding pressure is a futures
    carry premium. Long relatively low/negative funding and short relatively high
    funding, using only funding observations known at t-1. One architecture, no grid.
    """
    hourly,beta,_,eligible=p5.residual_components(data,membership)
    known_funding=data.funding.shift(1)
    carry=known_funding.rolling(PHASE['funding_lookback_hours'],min_periods=PHASE['funding_min_observations']).mean()
    score=(-carry).rank(axis=1,pct=True,method='average').where(eligible)
    vol=hourly.rolling(PHASE['volatility_lookback_hours'],min_periods=360).std()
    inv=(1/vol.replace(0,np.nan)).clip(upper=50).where(eligible)
    targets=pd.DataFrame(0.0,index=data.close.index,columns=data.close.columns)
    events=np.arange(len(targets))%PHASE['rebalance_hours']==0
    old=(p5.PHASE['sleeve_gross'],p5.PHASE['long_count'],p5.PHASE['short_count'])
    try:
        p5.PHASE['sleeve_gross']=PHASE['gross_cap']; p5.PHASE['long_count']=PHASE['long_count']; p5.PHASE['short_count']=PHASE['short_count']
        for ts in targets.index[events]:
            w=p5._neutral_event_weights(score,inv,beta,eligible,ts)
            if len(w): targets.loc[ts,w.index]=w
    finally:
        p5.PHASE['sleeve_gross'],p5.PHASE['long_count'],p5.PHASE['short_count']=old
    targets=targets.where(pd.Series(events,index=targets.index),np.nan).ffill().fillna(0)
    gross=targets.abs().sum(axis=1); scale=(PHASE['gross_cap']/gross.replace(0,np.nan)).clip(upper=1).fillna(0)
    return targets.mul(scale,axis=0)

def evaluate(data,targets,cfg,scenario):
    s=cfg['funding_stress'][scenario]
    return exact_fast(data,targets,cost_per_side=cfg['costs'][f'{scenario}_per_side'],gross_guard_cap=PHASE['gross_cap'],funding_debit_multiplier=s['debit_multiplier'],funding_credit_multiplier=s['credit_multiplier'])

def main():
    cfg=json.loads(CONFIG_PATH.read_text()); state=json.loads(STATE_PATH.read_text())
    data=load_data(PROJECT,cfg['data_config']); v=validate_data(data)
    if v['errors']: raise RuntimeError(f"data validation failed: {v['errors'][:5]}")
    liquid,membership=point_in_time_liquid_view(data,top_n=PHASE['liquidity_top_n'],lookback_hours=PHASE['liquidity_lookback_hours'],minimum_history_hours=PHASE['minimum_history_hours'])
    targets=build_targets(liquid,membership); results={x:evaluate(liquid,targets,cfg,x) for x in ('base','severe','supersevere')}
    start,end=cfg['research_start'],cfg['training_end']; train=p3.metrics(results['base'],start,end)
    folds={f['name']:p3.metrics(results['base'],f['start'],f['end']) for f in cfg['folds']}
    severe=p3.metrics(results['severe'],start,end); supersevere=p3.metrics(results['supersevere'],start,end)
    conc=p3.concentration_metrics(results['base'],start,end); beta=p3.beta_neutrality_metrics(results['base'],liquid,start,end); regimes=p3.regime_metrics(results['base'],liquid,start,end,end)
    passed,failures=p3.training_gate(train,folds,severe,supersevere,conc)
    hypothesis='Persistent cross-sectional funding pressure contains an economically distinct carry premium: low/negative-funding contracts outperform high-funding contracts after dollar/BTC-beta neutralization.'
    report={'engine':'V98 Independent','phase':PHASE,'hypothesis':hypothesis,'selection_policy':'orthogonal funding-carry family selected after Phase008 holdout rejection; one predeclared architecture; t-1 funding only; no grid; no holdout selection','training':train,'folds':folds,'stress_training':{'severe':severe,'supersevere':supersevere},'concentration_training':conc,'beta_neutrality_training':beta,'regimes_training':regimes,'training_gate':{'passed':passed,'failures':failures},'holdout':None}
    if passed:
        h0,h1=cfg['holdout_start'],cfg['holdout_end']; hb=p3.metrics(results['base'],h0,h1); hs=p3.metrics(results['severe'],h0,h1); hss=p3.metrics(results['supersevere'],h0,h1); hp,hf=p3.holdout_gate(hb,hs,hss)
        report['holdout']={'base':hb,'severe':hs,'supersevere':hss,'gate':{'passed':hp,'failures':hf}}
    REPORT_PATH.parent.mkdir(parents=True,exist_ok=True); REPORT_PATH.write_text(json.dumps(report,indent=2,default=str)+'\n'); results['base'].positions.to_csv(POSITIONS_PATH)
    final=bool(passed and report['holdout'] and report['holdout']['gate']['passed']); state['phase']='phase_009_complete'; state['champion']=PHASE['id'] if final else state.get('champion')
    state['last_experiment']={'id':PHASE['id'],'hypothesis':hypothesis,'status':'validated_candidate' if final else ('training_passed_holdout_rejected' if passed else 'training_rejected'),'parameters':'single predeclared 7d funding-carry architecture; 24h rebalance; 0.75 gross; no grid','report':str(REPORT_PATH.relative_to(PROJECT)),'training_summary':train,'folds':folds,'stress_training':report['stress_training'],'training_gate':report['training_gate'],'holdout_validation_recorded_but_not_for_selection':report['holdout']}
    state['holdout_evaluated_for_validation']=bool(passed); state['next_action']='Diagnose Phase009 training/fold/stress evidence. If rejected, change alpha family rather than tuning funding horizon. If validated, freeze and run robustness gate.'; STATE_PATH.write_text(json.dumps(state,indent=2,default=str)+'\n')
    print(json.dumps({'phase':PHASE['id'],'training_gate':report['training_gate'],'training':train,'folds':folds,'stress':report['stress_training'],'holdout':report['holdout']},indent=2,default=str))
if __name__=='__main__': main()
