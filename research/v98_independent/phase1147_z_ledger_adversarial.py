#!/usr/bin/env python3
"""Synthetic-only Z execution/accounting adversarial test; no market history."""
import json
import numpy as np
from phase1146_z_inventory_ledger import execute_hour,risk_corners,FEE_TIERS,ORDERS

def run(cases=1000,seed=1147):
    rng=np.random.default_rng(seed)
    survived=blocked=0;violations=[];failure_counts={}
    for i in range(cases):
        prior=np.full(4,100.)
        gap=rng.uniform(-.03,.03,4)
        op=prior*(1+gap)
        close=op*(1+rng.uniform(-.025,.025,4))
        high=np.maximum(op,close)*(1+rng.uniform(.001,.025,4))
        low=np.minimum(op,close)*(1-rng.uniform(.001,.025,4))
        w=rng.uniform(-.12,.12,4)
        cap=float(rng.choice([1e4,1e6,1e7]))
        fee=float(rng.choice(list(FEE_TIERS.values())))
        rate=np.zeros(4);event=np.zeros(4,bool)
        if i%4==0:
            event[:]=True;rate=rng.uniform(-.0005,.0005,4)
        marks=np.stack((close*.999,close*1.001),axis=1)
        kw=dict(prior=prior,opening=op,high=high,low=low,closing=close,
            carried_units=np.zeros(4),desired_weights=w,cash=cap,
            prior_down=np.full(4,.15),prior_up=np.full(4,.15),
            prior_funding_bound=np.full(4,.001),
            prior_quote=np.full(4,cap*500),fee=fee,
            order=ORDERS[i%2],funding_rate=rate,
            funding_mark_bounds=marks,funding_event=event,rebalance=True)
        try:x=execute_hour(**kw)
        except Exception as e:
            violations.append({'case':i,'exception':type(e).__name__+':'+str(e)})
            continue
        if not x['ok']:
            blocked+=1;reason=x.get('reason','UNKNOWN')
            failure_counts[reason]=failure_counts.get(reason,0)+1
            if not reason.startswith('Z1146_'):
                violations.append({'case':i,'reason':reason})
            continue
        survived+=1
        balance=cap;units=np.zeros(4)
        for event in x['events']:
            j=event['asset'];d=event['delta_units'];p=event['fill_price']
            balance-=d*p+event['fee_usd'];units[j]+=d
        balance+=x['funding_cash_delta']
        if (not np.allclose(units,x['units'],atol=1e-8,rtol=0)
            or not np.isclose(balance,x['cash'],atol=1e-6,rtol=0)
            or not np.isclose(balance+np.dot(units,close),x['equity'],atol=1e-6,rtol=0)
            or not risk_corners(balance,units,np.stack((low,op,high)),cap)['ok']):
            violations.append({'case':i,'reason':'SELF_FINANCING_OR_CORNER'})
    out={'phase':1147,'cases':cases,'survived':survived,'blocked':blocked,
        'failure_counts':failure_counts,'violations':violations[:10],
        'decision':'PASS_Z_LEDGER_SYNTHETIC_ONLY' if not violations and survived+blocked==cases
        else 'BLOCKED_Z_LEDGER_SYNTHETIC',
        'historical_pnl_computed':False,'validation_2025_read':False}
    print(json.dumps(out,sort_keys=True))
    return 0 if not violations else 2

def run_extreme(cases=1000,seed=1148):
    rng=np.random.default_rng(seed);blocked=survived=0;violations=[];reasons={}
    for i in range(cases):
        prior=np.full(4,100.)
        op=prior*(1+rng.uniform(-.45,.45,4))
        close=op*(1+rng.uniform(-.35,.35,4))
        high=np.maximum(op,close)*(1+rng.uniform(.01,.35,4))
        low=np.minimum(op,close)*(1-rng.uniform(.01,.35,4))
        capital=float(rng.choice([1e4,1e6,1e7]))
        quote=capital*10**rng.uniform(-3,3,4)
        w=rng.uniform(-.45,.45,4)
        rate=rng.uniform(-.02,.02,4)
        marks=np.stack((close*.9,close*1.1),axis=1)
        try:
            x=execute_hour(prior,op,high,low,close,np.zeros(4),w,capital,
                np.full(4,.15),np.full(4,.15),np.full(4,.02),quote,
                fee=float(rng.choice(list(FEE_TIERS.values()))),order=ORDERS[i%2],
                funding_rate=rate,funding_mark_bounds=marks,
                funding_event=np.ones(4,bool),rebalance=True)
            if not x['ok']:
                blocked+=1;reason=x.get('reason','UNKNOWN');reasons[reason]=reasons.get(reason,0)+1
                if not reason.startswith('Z1146_'):violations.append({'case':i,'reason':reason})
            else:
                survived+=1
                if not risk_corners(x['cash'],x['units'],np.stack((low,op,high)),capital)['ok']:
                    violations.append({'case':i,'reason':'UNSAFE_SURVIVAL'})
        except Exception as exc:
            violations.append({'case':i,'exception':type(exc).__name__+':'+str(exc)})
    out={'phase':1147,'scenario':'extreme','cases':cases,'survived':survived,
        'blocked':blocked,'reasons':reasons,'violations':violations[:10],
        'decision':'PASS_Z_EXTREME_FAIL_CLOSED_SYNTHETIC_ONLY' if not violations and
            survived+blocked==cases else 'BLOCKED_Z_EXTREME_SYNTHETIC',
        'historical_pnl_computed':False,'validation_2025_read':False}
    print(json.dumps(out,sort_keys=True))
    return 0 if not violations else 2

if __name__=='__main__':
    a=run();b=run_extreme()
    raise SystemExit(max(a,b))
