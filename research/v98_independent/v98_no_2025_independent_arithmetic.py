#!/usr/bin/env python3
"""V98 NO 2025 independent read-only 30-cell arithmetic/economic decision replay."""
import argparse,json,math
from pathlib import Path
COSTS={'base':(.0004,.0002),'severe':(.001,.001),'supersevere':(.0015,.002)}
ORDERS=('carried_before_fill','new_after_fill')
BOOKS=('NO_full','NO_core_only','NO_minus_opportunity','NO_minus_RV','NO_minus_stress')
SLEEVES={'Opportunity':'NO_minus_opportunity','Relative_Value':'NO_minus_RV',
         'Stress_Recovery':'NO_minus_stress'}
def audit(path):
    d=json.loads(Path(path).read_text())
    if d.get('architecture')!='NO' or d.get('validation_year')!=2025 or d.get('2026_future_holdout_accessed') is not False:
        raise ValueError('NO_2025_ARITH_SCOPE')
    if d.get('eligible_for_promotion') is not False or d.get('source_frozen_prefix_reproduced') is not True:
        raise ValueError('NO_2025_ARITH_FROZEN_PREFIX')
    cells=d['cells']
    if len(cells)!=30 or not d.get('native_30cell_executed'):
        raise ValueError('NO_2025_ARITH_CELL_COUNT')
    seen=set();errors=[];failures=[]
    for x in cells:
        key=(x['tier'],x['order'],x['book'])
        if key in seen or key[0] not in COSTS or key[1] not in ORDERS or key[2] not in BOOKS:
            raise ValueError('NO_2025_ARITH_UNKNOWN_OR_DUPLICATE_CELL')
        seen.add(key)
        if not x['passed']:continue
        fee,slip=COSTS[key[0]]
        for name,actual,expected in (
            ('fees',x['fees'],x['turnover']*fee),
            ('slippage',x['slippage'],x['turnover']*slip),
            ('log_growth',x['log_growth'],math.log(x['final_equity']/10000.)),
            ('cagr_2025',x['cagr_2025'],x['final_equity']/10000.-1)):
            if not math.isclose(actual,expected,rel_tol=1e-10,abs_tol=1e-8):
                errors.append((key,name,actual,expected))
        if x['max_intermediate_gross_fraction']>1+1e-9 or x['max_pretrade_or_post_gross_fraction']>1+1e-9:
            errors.append((key,'gross'))
        if x['min_intrabar_equity']<=0 or x['daily_count']!=365:
            errors.append((key,'survival_or_daily'))
    if len(seen)!=30:raise ValueError('NO_2025_ARITH_INCOMPLETE_GRID')
    for tier in COSTS:
        for order in ORDERS:
            key=tier+'/'+order
            group={x['book']:x for x in cells if x['tier']==tier and x['order']==order}
            if not all(x['passed'] for x in group.values()):
                failures.append(key+':physical_invariant')
                if key in d['marginals']:errors.append((key,'invalid_marginal'))
                continue
            full=group['NO_full']
            for sleeve,book in SLEEVES.items():
                expected=full['log_growth']-group[book]['log_growth']
                actual=d['marginals'][key][sleeve]
                if not math.isclose(actual,expected,rel_tol=1e-12,abs_tol=1e-10):
                    errors.append((key,sleeve,'marginal'))
            if tier not in ('base','severe'):continue
            if full['log_growth']<=0:failures.append(key+':nonpositive_growth')
            if full['turnover']>350000:failures.append(key+':turnover')
            if tier=='severe' and full['max_dd']<=-.45:failures.append(key+':max_dd')
            for sleeve,book in SLEEVES.items():
                if full['log_growth']-group[book]['log_growth']<=0:
                    failures.append(key+':'+sleeve+':marginal')
    if errors:raise ValueError('NO_2025_ARITH_MISMATCH_'+str(errors[:8]))
    if sorted(failures)!=sorted(d['gate_failures']):
        raise ValueError('NO_2025_ARITH_GATE_MISMATCH_'+str(sorted(set(failures)^set(d['gate_failures']))))
    expected_decision='REJECT_SEALED_2025_VALIDATION' if failures else 'PASS_PROVISIONAL_2025_PHYSICAL_AWAIT_INDEPENDENT_ORACLES'
    if d['decision']!=expected_decision:raise ValueError('NO_2025_ARITH_DECISION_MISMATCH')
    return {'decision':'PASS_NO_2025_INDEPENDENT_30CELL_ARITHMETIC_NOT_FINAL_VALIDATION',
        'original_physical_decision':d['decision'],'cells_verified':30,
        'arithmetic_mismatches':0,'economic_gate_recomputed':True,
        'gate_failures':failures,'2025_validation_only':True,
        '2026_future_holdout_accessed':False,'live_authorized':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--receipt',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();out=audit(a.receipt)
    Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True))
