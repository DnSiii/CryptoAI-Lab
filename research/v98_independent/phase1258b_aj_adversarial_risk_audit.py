#!/usr/bin/env python3
"""V98 AJ1258b independent fixed-seed 5000 actual-open risk property audit."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import numpy as np
from phase1257_aj_open_viability_governor import aj_governor,FEES,ORDERS

def run():
    rng=np.random.default_rng(1258)
    errors=Counter()
    accepted=0
    rejected=0
    digest=hashlib.sha256()
    max_delta_residual=-float('inf')
    max_capacity_residual=-float('inf')
    max_survival_shortfall=-float('inf')
    for i in range(5000):
        p0=100*np.exp(rng.normal(0,.03,4))
        p=p0*np.exp(rng.normal(0,.03,4))
        old=rng.normal(0,5,4)
        target=rng.normal(0,5,4)
        q=rng.uniform(1e6,1e8,4)
        qmin=rng.uniform(1e6,q)
        d=rng.uniform(.45,.70,4)
        u=rng.uniform(.80,1.20,4)
        f=rng.uniform(.0005,.0015,4)
        mode=list(FEES)[i%3]
        order=ORDERS[i%2]
        kw=dict(cash_previous=10000.,old_units=old,
            prior_close=p0,opening=p,signed_target=target,
            prior_down=d,prior_up=u,funding_bound=f,
            prior_quote=q,min_quote=qmin,fee_mode=mode,
            funding_order=order)
        try:
            out=aj_governor(**kw)
        except ValueError as exc:
            rejected+=1
            errors[str(exc)]+=1
            continue
        again=aj_governor(**kw)
        n=out['units']
        if not np.array_equal(n,again['units']):
            raise AssertionError('AJ1258B_NONDETERMINISTIC_REPEAT_'+str(i))
        if not out['real_open_solvent'] or out['hidden_borrow']:
            raise AssertionError('AJ1258B_FALSE_SOLVENCY_'+str(i))
        cash_gap=float(10000+old@(p-p0))
        max_delta=.003*np.minimum(q,qmin)/p
        max_abs=.003*qmin/(2.2*p*(1+u))
        delta_res=float(np.max(np.abs(n-old)-max_delta))
        capacity_res=float(np.max(np.abs(n)-max_abs))
        max_delta_residual=max(max_delta_residual,delta_res)
        max_capacity_residual=max(max_capacity_residual,capacity_res)
        if delta_res>1e-10 or capacity_res>1e-10:
            raise AssertionError('AJ1258B_FAKE_FILL_'+str(i))
        fee,slip=FEES[mode]
        turnover=float(np.sum(np.abs(n-old)*p))
        payer=old if order=='carried_before_fill' else n
        funded_cash=cash_gap-(fee+slip)*turnover-float(
            np.sum(np.abs(payer*p)*f))
        notional=np.abs(n*p)
        loss=float(np.sum(np.where(n>=0,notional*d,notional*u)))
        stressed=float(np.sum(notional*(1+u)))
        reserve=24*float(np.sum(notional*f))
        remaining=funded_cash-loss-reserve-(fee+slip)*stressed
        required=max(.40*cash_gap,.40*10000.,.18*stressed)
        shortfall=float(required-remaining)
        max_survival_shortfall=max(max_survival_shortfall,shortfall)
        if shortfall>1e-8:
            raise AssertionError('AJ1258B_FALSE_FUTURE_SAFE_'+str(i))
        accepted+=1
        digest.update(np.asarray(n,dtype='<f8').tobytes())
    if accepted<1000 or accepted+rejected!=5000:
        raise AssertionError('AJ1258B_INADEQUATE_COVERAGE')
    return {'phase':1258,'audit':'AJ1258b','synthetic_only':True,
        'historical_system_pnl_computed':False,'cases':5000,
        'accepted':accepted,'explicit_rejections':rejected,
        'rejection_reasons':dict(errors),
        'max_order_delta_residual':max_delta_residual,
        'max_exit_capacity_residual':max_capacity_residual,
        'max_survival_shortfall':max_survival_shortfall,
        'accepted_units_raw_sha256':digest.hexdigest(),
        'decision':'PASS_AJ1258B_NO_FALSE_FEASIBLE_ORDERS'}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--output',default='aj1258b_risk_receipt.json')
    args=p.parse_args()
    receipt=run()
    with open(args.output,'w') as f:
        json.dump(receipt,f,sort_keys=True,indent=2,allow_nan=False)
    print('AJ1258B_RECEIPT',json.dumps(receipt,sort_keys=True))
