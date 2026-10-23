"""C148 structural independent TRAIN-only risk/fold/benchmark scorecard.

Consumes independently re-executed C146 journals. Model/synthetic only:
no exchange-authenticated backtest, ROI claim, orders or promotion.
"""
from __future__ import annotations
from collections import Counter
from datetime import timedelta
from decimal import Decimal
from research.tools.v99_r106_d1_full_train_guard import START, END, HOURS, FOLD_EDGES
from research.tools.v99_r106_d1_basis_carry_preregistered import Decision

ASSETS = ('BTC', 'ETH')
SCENARIOS = ('severe_model_only', 'supersevere_model_only')
REGIMES = frozenset(d+'__'+v for d in ('BULL','BEAR','SIDEWAYS')
                    for v in ('HIGH_VOLATILITY','LOW_VOLATILITY'))


def _d(v):
    try:
        x=Decimal(str(v))
    except Exception as exc:
        raise ValueError('C148_BAD_DECIMAL') from exc
    if not x.is_finite():
        raise ValueError('C148_NONFINITE_DECIMAL')
    return x


def _nav(frame):
    state=frame['after']; marks=frame['marks']
    return _d(state['cash_quote']) + sum(
        _d(state['spot_base'][a]) * _d(marks[a]['spot']) for a in ASSETS)


def _mdd(values):
    peak=values[0]; worst=Decimal('0')
    for x in values:
        if x > peak: peak=x
        if peak <= 0: raise ValueError('C148_NONPOSITIVE_NAV')
        worst=min(worst,x/peak-1)
    return worst


def _tail_concentration(values):
    changes=[b-a for a,b in zip(values,values[1:])]
    gains=sorted((x for x in changes if x>0),reverse=True)
    losses=sorted((-x for x in changes if x<0),reverse=True)
    k=max(1,(len(changes)+99)//100)
    return {'worst_1pct_hourly_loss_quote':str(sum(losses[:k],Decimal('0'))),
            'top_1pct_positive_pnl_share':str(sum(gains[:k],Decimal('0'))/
                  sum(gains,Decimal('0')) if gains else Decimal('0')),
            'top_tail_hours':k}


def score_full_train_model_only(journals, decisions_by_scenario):
    """Recompute risk from C146-verified frames; fail closed on partitions.

    Exogenous prices and funding MUST be identical across cost paths. Only
    exposures and cash accounting may differ, not underlying market history.
    """
    if type(journals) is not dict or set(journals)!=set(SCENARIOS) or (
            type(decisions_by_scenario) is not dict or
            set(decisions_by_scenario)!=set(SCENARIOS)):
        raise ValueError('C148_BOTH_SCENARIOS_REQUIRED')
    ref=journals[SCENARIOS[0]]['frames']
    if len(ref)!=HOURS or ref[0]['time']!=START or ref[-1]['time']!=END-timedelta(hours=1):
        raise ValueError('C148_INCOMPLETE_TRAIN')
    for i,frame in enumerate(ref):
        if frame['time']!=START+timedelta(hours=i):
            raise ValueError('C148_HOURLY_GAP')
    common_decision_times=tuple(sorted(decisions_by_scenario[SCENARIOS[0]]))
    expected=tuple(START+timedelta(hours=i) for i in range(168,HOURS,24))
    if common_decision_times!=expected or len(expected)!=654:
        raise ValueError('C148_654_CAUSAL_DAILY_DECISIONS_REQUIRED')
    first=decisions_by_scenario[SCENARIOS[0]]
    for s in SCENARIOS:
        journal=journals[s]
        frames=journal['frames']
        if (len(frames)!=HOURS or journal.get('c146_full_feature_funding_proof',{}).get(
                'decision_hours_checked')!=654 or journal.get('account_proof',{}).get(
                'hours_replayed')!=HOURS):
            raise ValueError('C148_INDEPENDENT_REPLAY_PROOF_REQUIRED')
        decisions=decisions_by_scenario[s]
        if tuple(sorted(decisions))!=common_decision_times:
            raise ValueError('C148_COST_SCENARIO_DECISION_GRID_DIVERGENCE')
        for t in common_decision_times:
            a,b=first[t],decisions[t]
            if (not isinstance(a,Decision) or not isinstance(b,Decision) or
                    a.regime not in REGIMES or b.regime!=a.regime or
                    a.time!=t or b.time!=t or
                    a.feature_max_time>t-timedelta(hours=1) or
                    b.feature_max_time>t-timedelta(hours=1)):
                raise ValueError('C148_COST_SCENARIO_REGIME_OR_CAUSALITY_MISMATCH')
        for i,(base,fr) in enumerate(zip(ref,frames)):
            if (fr['time']!=base['time'] or fr['marks']!=base['marks'] or
                    fr['funding']!=base['funding']):
                raise ValueError('C148_EXOGENOUS_PRICE_OR_FUNDING_DIVERGENCE')
    initial_nav=_d(ref[0]['before']['cash_quote'])+sum(
        _d(ref[0]['before']['spot_base'][a])*_d(ref[0]['marks'][a]['spot'])
        for a in ASSETS)
    if initial_nav<=0:
        raise ValueError('C148_BAD_INITIAL_CAPITAL')
    fold_bounds=[int((edge-START)/timedelta(hours=1)) for edge in FOLD_EDGES]
    if fold_bounds!=[0,3172,6345,9518,12691,HOURS]:
        raise ValueError('C148_FOLD_PARTITION_CHANGED')
    first_marks=ref[0]['marks']; last_marks=ref[-1]['marks']
    gross_passive={a:last_marks[a]['spot'] for a in ASSETS}
    benchmarks={'cash':Decimal('1')}
    for a in ASSETS:
        benchmarks[a+'_spot_gross'] = _d(gross_passive[a])/_d(first_marks[a]['spot'])
    benchmarks['equal_spot_gross']=(benchmarks['BTC_spot_gross']+
                                     benchmarks['ETH_spot_gross'])/2
    result={'status':'C148_STRUCTURAL_MODEL_ONLY_NO_ECONOMIC_CLAIMS',
            'hours':HOURS,'daily_decisions':654,'fold_hours':[3172,3173,3173,3173,3173],
            'regime_counts':{k:Counter(first[t].regime for t in common_decision_times).get(k,0) for k in sorted(REGIMES)},
            'all_six_regimes_observed':len(set(first[t].regime for t in common_decision_times))==6,
            'passive_gross_only_multipliers':{k:str(v) for k,v in benchmarks.items()},
            'scenarios':{},'exchange_authenticated':False,'historical_roi_authorized':False,
            'validation_opened':False,'holdout_opened':False,'promotion_authorized':False,
            'orders_enabled':False}
    for s in SCENARIOS:
        values=[initial_nav]+[_nav(fr) for fr in journals[s]['frames']]
        if any(x<=0 for x in values):
            raise ValueError('C148_NONPOSITIVE_NAV')
        folds=[]
        for lo,hi in zip(fold_bounds,fold_bounds[1:]):
            part=values[lo:hi+1]
            folds.append({'hours':hi-lo,'model_only_return':str(part[-1]/part[0]-1),
                          'model_only_mdd':str(_mdd(part))})
        result['scenarios'][s]={
            'model_only_final_nav':str(values[-1]),
            'model_only_return':str(values[-1]/values[0]-1),
            'model_only_max_drawdown':str(_mdd(values)),
            'model_only_positive_folds':sum(_d(x['model_only_return'])>0 for x in folds),
            'folds':folds,'tail_diagnostics':_tail_concentration(values)}
    result['both_cost_paths_have_five_positive_model_folds'] = all(
        result['scenarios'][s]['model_only_positive_folds']==5 for s in SCENARIOS)
    result['structural_fixture_not_economic_gate'] = True
    return result
