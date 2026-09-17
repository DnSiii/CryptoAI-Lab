from __future__ import annotations

import json, sys
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'src')); sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data, point_in_time_liquid_view, validate_data
import v98_independent_phase003_dispersion_neutral as p3

CONFIG_PATH=PROJECT/'config'/'v98_independent.json'
STATE_PATH=PROJECT/'state'/'v98_independent_state.json'
REPORT_PATH=PROJECT/'reports'/'v98_independent_phase008_tail_budgeted_dispersion.json'
POSITIONS_PATH=PROJECT/'reports'/'v98_independent_phase008_tail_budgeted_dispersion_positions.csv'
PHASE={
    'id':'phase_008_tail_budgeted_dispersion',
    'source_alpha':'phase_003_dispersion_neutral_frozen_signal',
    'gross_target':0.75,
    'gross_cap':0.75,
    'rationale':'Phase003 failed training only on tail budget (worst day -13.10% vs -12% gate). Test one predeclared lower gross risk budget without changing signal, horizons, ranks, regime gate, or using holdout.'
}

def build_targets(data,membership):
    old_target,old_cap=p3.PHASE['gross_target'],p3.PHASE['gross_cap']
    try:
        p3.PHASE['gross_target']=PHASE['gross_target']; p3.PHASE['gross_cap']=PHASE['gross_cap']
        return p3.build_targets(data,membership)
    finally:
        p3.PHASE['gross_target'],p3.PHASE['gross_cap']=old_target,old_cap

def evaluate(data,targets,cfg,scenario):
    s=cfg['funding_stress'][scenario]
    return exact_fast(data,targets,cost_per_side=cfg['costs'][f'{scenario}_per_side'],gross_guard_cap=PHASE['gross_cap'],funding_debit_multiplier=s['debit_multiplier'],funding_credit_multiplier=s['credit_multiplier'])

def main():
    cfg=json.loads(CONFIG_PATH.read_text()); state=json.loads(STATE_PATH.read_text())
    data=load_data(PROJECT,cfg['data_config']); v=validate_data(data)
    if v['errors']: raise RuntimeError(f"data validation failed: {v['errors'][:5]}")
    liquid,membership=point_in_time_liquid_view(data,top_n=p3.PHASE['liquidity_top_n'],lookback_hours=p3.PHASE['liquidity_lookback_hours'],minimum_history_hours=p3.PHASE['minimum_history_hours'])
    targets=build_targets(liquid,membership)
    results={x:evaluate(liquid,targets,cfg,x) for x in ('base','severe','supersevere')}
    start,end=cfg['research_start'],cfg['training_end']
    train=p3.metrics(results['base'],start,end)
    folds={f['name']:p3.metrics(results['base'],f['start'],f['end']) for f in cfg['folds']}
    severe=p3.metrics(results['severe'],start,end); supersevere=p3.metrics(results['supersevere'],start,end)
    conc=p3.concentration_metrics(results['base'],start,end); beta=p3.beta_neutrality_metrics(results['base'],liquid,start,end); regimes=p3.regime_metrics(results['base'],liquid,start,end,end)
    passed,failures=p3.training_gate(train,folds,severe,supersevere,conc)
    hypothesis='The Phase003 residual-dispersion alpha is economically useful but its fixed 1.0 gross budget breaches the predeclared daily tail gate; a single 0.75 gross budget should preserve alpha quality while bringing tail and drawdown risk inside launch constraints.'
    report={'engine':'V98 Independent','phase':PHASE,'hypothesis':hypothesis,'selection_policy':'single predeclared risk-budget test derived only from Phase003 training failure; signal frozen; no grid; no holdout selection','training':train,'folds':folds,'stress_training':{'severe':severe,'supersevere':supersevere},'concentration_training':conc,'beta_neutrality_training':beta,'regimes_training':regimes,'training_gate':{'passed':passed,'failures':failures},'holdout':None}
    if passed:
        h0,h1=cfg['holdout_start'],cfg['holdout_end']; hb=p3.metrics(results['base'],h0,h1); hs=p3.metrics(results['severe'],h0,h1); hss=p3.metrics(results['supersevere'],h0,h1); hp,hf=p3.holdout_gate(hb,hs,hss)
        report['holdout']={'base':hb,'severe':hs,'supersevere':hss,'gate':{'passed':hp,'failures':hf}}
    REPORT_PATH.parent.mkdir(parents=True,exist_ok=True); REPORT_PATH.write_text(json.dumps(report,indent=2,default=str)+'\n'); results['base'].positions.to_csv(POSITIONS_PATH)
    final=bool(passed and report['holdout'] and report['holdout']['gate']['passed'])
    state['phase']='phase_008_complete'; state['champion']=PHASE['id'] if final else state.get('champion')
    state['last_experiment']={'id':PHASE['id'],'hypothesis':hypothesis,'status':'validated_candidate' if final else ('training_passed_holdout_rejected' if passed else 'training_rejected'),'parameters':'frozen Phase003 signal; single 0.75 gross risk budget; no grid','report':str(REPORT_PATH.relative_to(PROJECT)),'training_summary':train,'folds':folds,'stress_training':report['stress_training'],'training_gate':report['training_gate'],'holdout_validation_recorded_but_not_for_selection':report['holdout']}
    state['holdout_evaluated_for_validation']=bool(passed); state['next_action']='Diagnose Phase008 evidence. If rejected, do not tune gross from holdout; move to an orthogonal alpha/portfolio hypothesis. If validated, freeze candidate and run robustness gate.'
    STATE_PATH.write_text(json.dumps(state,indent=2,default=str)+'\n')
    print(json.dumps({'phase':PHASE['id'],'training_gate':report['training_gate'],'training':train,'folds':folds,'stress':report['stress_training'],'holdout':report['holdout']},indent=2,default=str))

if __name__=='__main__': main()
