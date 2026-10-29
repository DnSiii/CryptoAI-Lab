#!/usr/bin/env python3
"""Independent LI *receipt arithmetic* only, NOT independent physical settlement."""
from __future__ import annotations
import argparse,json,math
from pathlib import Path

def run(full_path,abl_path,core_path):
    full=json.loads(Path(full_path).read_text())['cells']
    abl=json.loads(Path(abl_path).read_text())['cells']
    core=json.loads(Path(core_path).read_text())['cells']
    errors=[]
    for x in full+abl+core:
        if not x['passed']:errors.append('PHYSICAL_'+x['path'])
        if not math.isclose((x['final_nav']/x['initial_nav'])**(365.25/731)-1,x['cagr'],abs_tol=1e-10):errors.append('CAGR_'+x['path'])
        if not math.isclose(math.log(x['final_nav']/x['initial_nav']),x['log_growth'],abs_tol=1e-10):errors.append('LOG_'+x['path'])
        a=x['annual']
        if not math.isclose((1+a['2023']['net_return'])*(1+a['2024']['net_return']),x['final_nav']/x['initial_nav'],rel_tol=1e-10):errors.append('ANNUAL_'+x['path'])
        fee,slip={'base':(.0005,.0005),'severe':(.002,.003)}[x['fee']]
        if not math.isclose(x['fees'],x['turnover']*fee,rel_tol=1e-10):errors.append('FEES_'+x['path'])
        if not math.isclose(x['slippage'],x['turnover']*slip,rel_tol=1e-10):errors.append('SLIP_'+x['path'])
        if x['max_gross_to_nav']>1+1e-8:errors.append('GROSS_'+x['path'])
    for fee in ('base','severe'):
        pair=[x for x in full if x['fee']==fee]
        if len(pair)!=2 or not math.isclose(pair[0]['final_nav'],pair[1]['final_nav'],abs_tol=1e-7):errors.append('FUNDING_ORDER_'+fee)
    marg={}
    for fee in ('base','severe'):
        f=next(x for x in full if x['fee']==fee)
        marg[fee]={}
        for name in ('opportunity','RV','stress'):
            a=next(x for x in abl if x['fee']==fee and x['path']=='LI_minus_'+name)
            marg[fee][name]=f['log_growth']-a['log_growth']
    return {'decision':'PASS_ARITHMETIC_ONLY' if not errors else 'FAIL_ARITHMETIC',
            'economic_decision':'REJECT_LI','source_gate':'PASS_SOURCE_ONLY',
            'original_30cell_run':False,'independent_settlement_replay':False,
            'cells_arithmetic_checked':len(full+abl+core),'errors':errors,
            'base_turnover':next(x['turnover'] for x in full if x['fee']=='base'),
            'turnover_gate_usd':600000,'marginal_log_growth':marg}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--full',required=True);p.add_argument('--ablations',required=True)
    p.add_argument('--core',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();r=run(a.full,a.ablations,a.core)
    Path(a.output).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    print(r['decision'],r['economic_decision'],r['errors'])
    raise SystemExit(0 if not r['errors'] else 2)
