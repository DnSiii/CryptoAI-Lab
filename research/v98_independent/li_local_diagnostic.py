#!/usr/bin/env python3
"""V98 LI local early-rejection diagnostic only; NOT original 30-cell CI or independent oracle.

Reuses generic KO physical signed-collateral simulator but NOT KO strategy signals.
Run only with original pinned Clean-4 artifact extracted into --root.
Never use this output for promotion, live trading or future-holdout selection.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import ko_physical as simulator
from li_sources import bundle,static_check

simulator.bundle=bundle
simulator.static_check=static_check
NAMES={
    'LI_core_only':'KO_core_only',
    'LI_full':'KO_full',
    'LI_minus_opportunity':'KO_minus_opportunity',
    'LI_minus_RV':'KO_minus_RV',
    'LI_minus_stress':'KO_minus_stress'
}
def run(root,paths,fees,orders):
    out=simulator.run(root,tuple(NAMES[p] for p in paths),tuple(fees),tuple(orders))
    out['architecture']='LI'
    out['local_diagnostic_only']=True
    out['original_github_30cell_run']=False
    out['independent_settlement_oracle_completed']=False
    out['eligible_for_promotion']=False
    out['holdout_2025_read']=False
    out['external_benchmarks_used']=False
    for rec in out['cells']:
        rec['path']=rec['path'].replace('KO_','LI_')
        rec['local_diagnostic_only']=True
    out['decision']='LI_LOCAL_DIAGNOSTIC_NOT_VALIDATION'
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True)
    p.add_argument('--output',required=True)
    p.add_argument('--paths',nargs='+',choices=tuple(NAMES),default=['LI_full'])
    p.add_argument('--fees',nargs='+',choices=('base','severe','supersevere'),default=['base','severe'])
    p.add_argument('--orders',nargs='+',choices=('carried_before_fill','new_after_fill'),default=['carried_before_fill','new_after_fill'])
    a=p.parse_args()
    r=run(a.root,a.paths,a.fees,a.orders)
    Path(a.output).write_text(json.dumps(r,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print('LI_LOCAL_DIAGNOSTIC',r['passed'],'/',r['total'],'NO_PROMOTION')
    raise SystemExit(0 if r['passed']==r['total'] else 2)
