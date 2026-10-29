#!/usr/bin/env python3
"""V98 Independent read-only pre-governor no-hidden-leverage survival gate.
This does NOT reclassify previously frozen candidate decisions.
"""
import argparse,json,math
from pathlib import Path

def audit(path,limit=1.0):
    d=json.loads(Path(path).read_text())
    cells=d.get('cells',[])
    if not cells:raise ValueError('V98_NO_PHYSICAL_CELLS')
    offenders=[]
    for x in cells:
        gross=x.get('max_pre_governor_gross_fraction')
        if not isinstance(gross,(float,int)) or not math.isfinite(gross):
            raise ValueError('V98_PRETRIM_GROSS_NOT_RECORDED')
        if gross>limit+1e-12:
            offenders.append({'book':x['book'],'tier':x['tier'],'order':x['order'],
                              'max_pre_governor_gross_fraction':gross})
    return {'decision':'FAIL_PRE_GOVERNOR_NO_HIDDEN_LEVERAGE' if offenders else 'PASS_PRE_GOVERNOR_NO_HIDDEN_LEVERAGE',
            'pre_governor_gross_limit':limit,'cells_checked':len(cells),
            'offending_cells':offenders,'training_only':True,
            'not_independent_pnl_validation':True,'retroactive_reclassification':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--receipt',required=True);a=p.parse_args()
    result=audit(a.receipt);print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['decision'].startswith('PASS_') else 2)
