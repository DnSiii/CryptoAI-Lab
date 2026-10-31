#!/usr/bin/env python3
"""Independent read-only V98 OB receipt audit. Does NOT replay hourly PnL."""
import argparse,json,math
from pathlib import Path
COSTS={'base':(.0004,.0002),'severe':(.001,.001),'supersevere':(.0015,.002)}
ORDERS=('carried_before_fill','new_after_fill')
BOOKS=('OB_full','OB_core_only','OB_minus_opportunity','OB_minus_RV','OB_minus_stress')
SLEEVES={'Opportunity':'OB_minus_opportunity','Relative_Value':'OB_minus_RV',
         'Stress_Recovery':'OB_minus_stress'}
def audit(path):
    d=json.loads(Path(path).read_text())
    if d.get('architecture')!='OB' or d.get('training_only') is not True or d.get('holdout_accessed') is not False:
        raise ValueError('OB_AUDIT_SCOPE')
    if d.get('eligible_for_promotion') is not False or d.get('independent_pnt_oracle') is not False or d.get('one_way_netting') is not True:
        raise ValueError('OB_AUDIT_FALSE_PROMOTION')
    if d['source_gate']['decision']!='PASS_SOURCE_ONLY' or d['source_gate']['funding_events']!=9144:
        raise ValueError('OB_AUDIT_SOURCE')
    cells=d['cells']
    if len(cells)!=30 or d.get('native_30cell_executed') is not True:
        raise ValueError('OB_AUDIT_CELL_COUNT')
    seen=set();errors=[];failed=[]
    for x in cells:
        key=(x['tier'],x['order'],x['book'])
        if key in seen or key[0] not in COSTS or key[1] not in ORDERS or key[2] not in BOOKS:
            raise ValueError('OB_AUDIT_DUPLICATE_OR_UNLNOWN_CELL')
        seen.add(key)
        if not x['passed']:
            failed.append({'tier':key[0],'order':key[1],'book':key[2],'failure':x['failure'],'t':x['t']})
            continue
        f,s=COSTS[key[0]]
        for name,actual,expected in (
            ('fees',x['fees'],x['turnover']*f),
            ('slippage',x['slippage'],x['turnover']*s),
            ('log_growth',x['log_growth'],math.log(x['final_equity']/10000.)),
            ('cagr',x['cagr'],(x['final_equity']/10000.)**(365.25/731)-1)):
            if not math.isclose(actual,expected,rel_tol=1e-10,abs_tol=1e-8):
                errors.append((key,name,actual,expected))
        if x['max_intermediate_gross_fraction']>1+1e-9 or x['max_pretrade_or_post_gross_fraction']>1+1e-9:
            errors.append((key,'gross_violation'))
        if x['min_intrabar_equity']<=0 or not 0<=x['max_single_asset_gross_concentration']<=1+1e-9:
            errors.append((key,'survival_violation'))
    if len(seen)!=30:raise ValueError('OB_AUDIT_INCOMPLETE_GRID')
    for tier in COSTS:
        for order in ORDERS:
            group={x['book']:x for x in cells if x['tier']==tier and x['order']==order}
            k=tier+'/'+order
            if not all(x['passed'] for x in group.values()):
                if k in d['marginals']:errors.append((k,'invalid_marginal_for_failed_cell'))
                if not any(k+':physical_invariant'==x for x in d['gate_failures']):
                    errors.append((k,'missing_physical_failure'))
                continue
            if k not in d['marginals']:errors.append((k,'missing_marginals'));continue
            for name,book in SLEEVES.items():
                expected=group['OB_full']['log_growth']-group[book]['log_growth']
                actual=d['marginals'][k][name]
                if not math.isclose(actual,expected,rel_tol=1e-12,abs_tol=1e-10):
                    errors.append((k,name,'marginal_mismatch'))
    if errors:raise ValueError('OB_AUDIT_RECONCILIATION_'+str(errors[:10]))
    if failed and d['decision']!='REJECT_EARLY_TRAINING':
        raise ValueError('OB_AUDIT_PHYSICAL_FAILURE_MISCLASSIFIED')
    independent_failures=[]
    for tier in COSTS:
        for order in ORDERS:
            key=tier+'/'+order
            group={z['book']:z for z in cells if z['tier']==tier and z['order']==order}
            if not all(z['passed'] for z in group.values()):
                independent_failures.append(key+':physical_invariant')
                continue
            full=group['OB_full']
            if tier not in ('base','severe'):continue
            if full['cagr']<=(.80 if tier=='base' else .60):
                independent_failures.append(key+':cagr')
            if full['turnover']>600000:
                independent_failures.append(key+':turnover')
            if tier=='severe':
                if full['max_dd']<=-.45:independent_failures.append(key+':max_dd')
                if any(x<=0 for x in full['year_returns'].values()):
                    independent_failures.append(key+':annual_return')
            for sleeve,ablation in SLEEVES.items():
                ab=group[ablation]
                marginal=full['log_growth']-ab['log_growth']
                if marginal<=.02:
                    independent_failures.append(key+':'+sleeve+':marginal')
                for year in ('2023','2024'):
                    annual=math.log1p(full['year_returns'][year])-math.log1p(ab['year_returns'][year])
                    if annual<-.03:
                        independent_failures.append(key+':'+sleeve+':'+year+':annual_marginal')
    if sorted(independent_failures)!=sorted(d['gate_failures']):
        raise ValueError('OB_AUDIT_INDEPENDENT_ECONOMIC_GATE_MISMATCH_'+str(
            sorted(set(independent_failures)^set(d['gate_failures']))[:12]))
    if d['decision']!=('REJECT_EARLY_TRAINING' if independent_failures else
                      'PASS_PROVISIONAL_TRAINING_NOT_VALIDATED'):
        raise ValueError('OB_AUDIT_INDEPENDENT_DECISION_MISMATCH')
    summary={}
    for tier in ('base','severe','supersevere'):
        full=next(x for x in cells if x['tier']==tier and x['order']=='carried_before_fill' and x['book']=='OB_full')
        group={x['book']:x for x in cells if x['tier']==tier and x['order']=='carried_before_fill'}
        attribution={}
        if all(x['passed'] for x in group.values()):
            for name,book in SLEEVES.items():
                ab=group[book]
                attribution[name]={
                    'marginal_turnover_usd':round(full['turnover']-ab['turnover'],2),
                    'marginal_funding_usd':round(full['funding']-ab['funding'],2),
                    'marginal_fees_slippage_usd':round(
                        (full['fees']+full['slippage'])-(ab['fees']+ab['slippage']),2),
                    'annual_marginal_log_growth':{
                        year:round(math.log1p(full['year_returns'][year])-math.log1p(ab['year_returns'][year]),6)
                        for year in ('2023','2024')}}
        summary[tier]={'sleeve_attribution':attribution,
                       'full_cagr_pct':round(full['cagr']*100,4) if full['passed'] else None,
                       'full_turnover_usd':round(full['turnover'],2) if full['passed'] else None,
                       'full_max_dd_pct':round(full['max_dd']*100,4) if full['passed'] else None,
                       'full_annual_returns':full.get('year_returns'),
                       'marginal_log_growth':d['marginals'].get(tier+'/carried_before_fill')}
    return {'summary':summary,'original_decision':d['decision'],
            'original_gate_failures':d['gate_failures'],
            'decision':'PASS_READ_ONLY_ARITHMETIC_NOT_INDEPENDENT_HOURLY_ORACLE',
            'cells_verified':len(seen),'physical_failed_cells':len(failed),
            'failure_examples':failed[:6],'arithmetic_mismatches':0,'economic_gate_recomputed':True,
            'training_only':True,'holdout_accessed':False,
            'independent_all_hour_pnt_oracle':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--receipt',required=True);a=p.parse_args()
    print(json.dumps(audit(a.receipt),indent=2,sort_keys=True))
