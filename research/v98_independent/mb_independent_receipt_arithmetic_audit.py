#!/usr/bin/env python3
"""Independent read-only V98 MB receipt audit. Does NOT replay hourly PnL."""
import argparse,json,math
from pathlib import Path
COSTS={'base':(.0004,.0002),'severe':(.001,.001),'supersevere':(.0015,.002)}
ORDERS=('carried_before_fill','new_after_fill')
BOOKS=('MB_full','MB_core_only','MB_minus_opportunity','MB_minus_RV','MB_minus_stress')
SLEEVES={'Opportunity':'MB_minus_opportunity','Relative_Value':'MB_minus_RV',
         'Stress_Recovery':'MB_minus_stress'}
def audit(path):
    d=json.loads(Path(path).read_text())
    if d.get('architecture')!='MB' or d.get('training_only') is not True or d.get('holdout_accessed') is not False:
        raise ValueError('MB_AUDIT_SCOPE')
    if d.get('eligible_for_promotion') is not False or d.get('independent_pnl_oracle') is not False:
        raise ValueError('MB_AUDIT_FALSE_PROMOTION')
    if d['source_gate']['decision']!='PASS_SOURCE_ONLY' or d['source_gate']['funding_events']!=9144:
        raise ValueError('MB_AUDIT_SOURCE')
    cells=d['cells']
    if len(cells)!=30 or d.get('native_30cell_executed') is not True:
        raise ValueError('MB_AUDIT_CELL_COUNT')
    seen=set();errors=[];failed=[]
    for x in cells:
        key=(x['tier'],x['order'],x['book'])
        if key in seen or key[0] not in COSTS or key[1] not in ORDERS or key[2] not in BOOKS:
            raise ValueError('MB_AUDIT_DUPLICATE_OR_UNKNOWN_CELL')
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
    if len(seen)!=30:raise ValueError('MB_AUDIT_INCOMPLETE_GRID')
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
                expected=group['MB_full']['log_growth']-group[book]['log_growth']
                actual=d['marginals'][k][name]
                if not math.isclose(actual,expected,rel_tol=1e-12,abs_tol=1e-10):
                    errors.append((k,name,'marginal_mismatch'))
    if errors:raise ValueError('MB_AUDIT_RECONCILIATION_'+str(errors[:10]))
    if failed and d['decision']!='REJECT_EARLY_TRAINING':
        raise ValueError('MB_AUDIT_PHYSICAL_FAILURE_MISCLASSIFIED')
    summary={}
    for tier in ('base','severe','supersevere'):
        full=next(x for x in cells if x['tier']==tier and x['order']=='carried_before_fill' and x['book']=='MB_full')
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
            'failure_examples':failed[:6],'arithmetic_mismatches':0,
            'training_only':True,'holdout_accessed':False,
            'independent_all_hour_pnl_oracle':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--receipt',required=True);a=p.parse_args()
    print(json.dumps(audit(a.receipt),indent=2,sort_keys=True))
