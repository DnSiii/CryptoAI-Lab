#!/usr/bin/env python3
"""Read-only independent arithmetic check of immutable MA 30-cell receipt; NOT a PnL oracle."""
import argparse,json,math
from pathlib import Path
BOOKS=('MA_full','MA_core_only','MA_minus_opportunity','MA_minus_RV','MA_minus_stress')
FEES={'base':.0004,'severe':.001,'supersevere':.0015}
SLEEVES={'Opportunity':'MA_minus_opportunity','Relative_Value':'MA_minus_RV','Stress_Recovery':'MA_minus_stress'}
ORDERS=('carried_before_fill','new_after_fill')

def audit(receipt):
    d=json.loads(Path(receipt).read_text())
    cells=d['cells']
    if len(cells)!=30 or d['architecture']!='MA' or d['decision']!='REJECT_EARLY_TRAINING_ECONOMIC':
        raise ValueError('MA_RECEIPT_UNEXPECTED_SHAPE_OR_DECISION')
    count=0
    for tier,fee in FEES.items():
        for order in ORDERS:
            sub={x['book']:x for x in cells if x['tier']==tier and x['order']==order}
            if set(sub)!=set(BOOKS):raise ValueError('MA_MISSING_OR_DUPLICATE_BOOK')
            for x in sub.values():
                if not x['passed'] or x['gross_breaches'] or x['min_intrabar_equity']<=0:
                    raise ValueError('MA_PHYSICAL_INVARIANT')
                if not math.isclose(x['log_growth'],math.log(x['final_equity']/10000),abs_tol=1e-12):
                    raise ValueError('MA_LOG_GROWTH')
                if not math.isclose(x['cagr'],(x['final_equity']/10000)**(365.25/731)-1,abs_tol=1e-12):
                    raise ValueError('MA_CAGR')
                if not math.isclose(x['turnover']*fee,x['fees'],rel_tol=1e-9,abs_tol=1e-8):
                    raise ValueError('MA_FEE')
                count+=1
            for sleeve,ab in SLEEVES.items():
                m=sub['MA_full']['log_growth']-sub[ab]['log_growth']
                if not math.isclose(m,d['marginals'][tier+'/'+order][sleeve],abs_tol=1e-12):
                    raise ValueError('MA_MARGINAL')
            other={x['book']:x for x in cells if x['tier']==tier and x['order']!=order}
            if any(not math.isclose(sub[b]['final_equity'],other[b]['final_equity'],abs_tol=1e-8) for b in BOOKS):
                raise ValueError('MA_ORDER_DIVERGENCE')
    fails=d['gate_failures']
    if len(fails)!=12 or not all(f.split(':')[1] in ('turnover','Opportunity','Relative_Value') for f in fails):
        raise ValueError('MA_GATE_FAILURES')
    return {'decision':'PASS_INDEPENDENT_RECEIPT_ARITHMETIC_ONLY_MA_REJECTED',
            'cells_checked':count,'hard_failures':len(fails),'holdout_accessed':False,
            'independent_all_hour_ledger':False,'eligible_for_promotion':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--receipt',required=True);a=p.parse_args()
    print(json.dumps(audit(a.receipt),indent=2))
