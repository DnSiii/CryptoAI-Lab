#!/usr/bin/env python3
"""V98 verified official mark OHLC envelope loader and side-aware worst funding settlement.
NOT exact native tick mark or validated trading PnL. 2022-24 training only.
"""
import argparse,csv,hashlib,json
import numpy as np
from v98_clean4_training_reader import load,ASSETS,START,HOURS
EXPECTED_SHA='acbd9c6f06da70bb5bc454c539f873c1a109d1fc31dc98111e88b24387d8bbf6'
ORDERS=('carried_before_fill','new_after_fill')

def read_envelope(path,d):
    raw=open(path,'rb').read();sha=hashlib.sha256(raw).hexdigest()
    if sha!=EXPECTED_SHA:raise ValueError('V98_ENVELOPE_PINNED_SHA_MISMATCH')
    lo=d['mark'].copy();hi=d['mark'].copy();seen=np.zeros((HOURS,4),bool)
    names={s:i for i,s in enumerate(ASSETS)}
    with open(path,newline='') as f:
        reader=csv.DictReader(f)
        for row in reader:
            symbol=row['symbol'];j=names.get(symbol)
            if j is None:raise ValueError('V98_ENVELOPE_UNKNOWN_ASSET')
            ms=int(row['funding_time_ms']);t=(ms-int(START.timestamp()*1000))//3600000
            if (ms-int(START.timestamp()*1000))%3600000 or not 0<=t<HOURS or not d['event'][t,j] or seen[t,j]:
                raise ValueError('V98_ENVELOPE_CALENDAR_DUPLICATE_OR_INVALID')
            a=float(row['mark_lower_bound']);b=float(row['mark_upper_bound']);m=float(row['original_conservative_mark'])
            if not np.isfinite([a,b,m]).all() or a<=0 or a>b or not a<=d['mark'][t,j]<=b or abs(m-d['mark'][t,j])>1e-8:
                raise ValueError('V98_ENVELOPE_MARK_INTEGRITY')
            lo[t,j]=a;hi[t,j]=b;seen[t,j]=True
    if not np.array_equal(seen,d['event']):raise ValueError('V98_ENVELOPE_INCOMPLETE_EVENT_COVERAGE')
    return lo,hi,sha

def worst_funding(old,new,rate,event,lo,hi,order):
    if order not in ORDERS:raise ValueError('V98_ENVELOPE_INVALID_ORDER')
    payer=np.asarray(old if order==ORDERS[0] else new,dtype=float)
    r=np.asarray(rate,dtype=float);e=np.asarray(event,dtype=bool)
    if any(np.asarray(x).shape!=(4,) for x in (payer,r,e,lo,hi)) or not all(np.isfinite(x).all() for x in (payer,r,lo,hi)):
        raise ValueError('V98_ENVELOPE_INVALID_VECTOR')
    obligation=payer*r*e
    return -float(np.dot(obligation,np.where(obligation>=0,hi,lo)))

def audit(d,path):
    lo,hi,sha=read_envelope(path,d)
    rng=np.random.default_rng(243)
    tested=0;worst_advantage=0.
    for t in np.flatnonzero(d['event'][:,0]):
        for order in ORDERS:
            old=rng.normal(size=4);new=rng.normal(size=4)
            worst=worst_funding(old,new,d['rate'][t],d['event'][t],lo[t],hi[t],order)
            payer=old if order==ORDERS[0] else new
            original=-float(np.dot(payer*d['rate'][t]*d['event'][t],d['mark'][t]))
            if worst>original+1e-8:raise ValueError('V98_ENVELOPE_NOT_CONSERVATIVE')
            worst_advantage=max(worst_advantage,original-worst);tested+=1
    return {'decision':'PASS_9144_EVENT_SIGNED_WORST_MARK_SETTLEMENT_CONTRACT_NOT_EXACT_TICK',
       'training_only':True,'holdout_read':False,'pnl_computed':False,'events_verified':int(d['event'].sum()),
       'signed_order_cases':tested,'orders':ORDERS,'max_single_case_extra_conservative_funding_cost':worst_advantage,
       'envelope_sha256':sha,'exact_funding_tick_mark_attested':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--envelope-csv',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    out=audit(load(a.root),a.envelope_csv);open(a.output,'w').write(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2))
