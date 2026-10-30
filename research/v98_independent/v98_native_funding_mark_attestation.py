#!/usr/bin/env python3
"""V98 Clean4 training-only Binance USD-M funding rate/markPrice attestation.
Read-only; never changes signed source, candidate signals, frozen engines, holdout or PnL.
"""
import argparse,hashlib,json,time,urllib.parse,urllib.request
import numpy as np
from v98_clean4_training_reader import load,ASSETS,START,END,FUNDING_SHA
END_MS=int(END.timestamp()*1000)
BASES=('https://fapi.binance.com','https://fapi1.binance.com')

def query(symbol,start_ms,end_ms,fetch=None):
    if fetch is not None:return fetch(symbol,start_ms,end_ms)
    params=urllib.parse.urlencode({'symbol':symbol,'startTime':start_ms,'endTime':end_ms,'limit':1000})
    errors=[]
    for base in BASES:
        for attempt in range(3):
            try:
                req=urllib.request.Request(base+'/fapi/v1/fundingRate?'+params,headers={'User-Agent':'V98-Independent-Source-Audit/1.0'})
                with urllib.request.urlopen(req,timeout=18) as resp:
                    obj=json.load(resp)
                if not isinstance(obj,list):raise ValueError('NON_LIST_API_RESPONSE')
                return obj
            except Exception as exc:
                errors.append(type(exc).__name__+':'+str(exc)[:150]);time.sleep(.5*(attempt+1))
    raise RuntimeError('V98_BINANCE_OFFICIAL_MARK_UNAVAILABLE: '+' | '.join(errors[-4:]))

def collect(symbol,first_ms,last_ms,fetch=None):
    cursor=first_ms;rows=[];pages=0
    while cursor<=last_ms:
        batch=query(symbol,cursor,last_ms,fetch)
        pages+=1
        if pages>10:raise ValueError('V98_PAGINATION_OVERFLOW')
        if not batch:break
        last=-1
        for row in batch:
            ts=int(row['fundingTime']);rate=float(row['fundingRate']);mark=float(row['markPrice'])
            if ts<cursor or ts>last_ms or ts<=last or not np.isfinite(rate) or not np.isfinite(mark) or mark<=0:
                raise ValueError('V98_NATIVE_MARK_INVALID_OR_UNSORTED_'+symbol)
            rows.append((ts,rate,mark));last=ts
        cursor=last+1
        if len(batch)<1000:break
    return rows,pages

def attest(d,fetch=None):
    # Source reader independently verifies original SHA256 before external requests.
    allrows=[];summary={}
    for j,symbol in enumerate(ASSETS):
        ts=np.flatnonzero(d['event'][:,j]);assert len(ts)==2286
        first=int((START+ts[0]*np.timedelta64(1,'h')).timestamp()*1000)
        last=int((START+ts[-1]*np.timedelta64(1,'h')).timestamp()*1000)
        rows,pages=collect(symbol,first,last,fetch)
        expected_ms=np.array([int((START+t*np.timedelta64(1,'h')).timestamp()*1000) for t in ts],dtype=np.int64)
        actual_ms=np.array([r[0] for r in rows],dtype=np.int64)
        if not np.array_equal(expected_ms,actual_ms):raise ValueError('V98_NATIVE_MARK_CALENDAR_MISMATCH_'+symbol+':'+str((len(expected_ms),len(actual_ms))))
        original=d['rate'][ts,j];official=np.array([r[1] for r in rows])
        diff=float(np.max(np.abs(original-official)))
        if diff>1e-10:raise ValueError('V98_NATIVE_FUNDING_RATE_MISMATCH_'+symbol+':'+str(diff))
        conservative=d['mark'][ts,j];native=np.array([r[2] for r in rows])
        rel=np.abs(native/conservative-1)
        summary[symbol]={'events':len(rows),'pages':pages,'rate_max_abs_difference':diff,'mark_max_relative_difference':float(np.max(rel)),'mark_median_relative_difference':float(np.median(rel)),'native_mark_min':float(np.min(native)),'native_mark_max':float(np.max(native))}
        allrows.extend((symbol,*row) for row in rows)
    encoded='\n'.join(f'{s},{t},{r:.12f},{m:.12f}' for s,t,r,m in allrows).encode()
    return {'decision':'PASS_NATIVE_FUNDING_AND_MARK_SOURCE_ATTESTATION_NOT_PNL','training_only':True,'holdout_read':False,'native_mark_attested':True,'source_funding_sha256':FUNDING_SHA,'official_response_canonical_sha256':hashlib.sha256(encoded).hexdigest(),'summary':summary,'events':len(allrows),'pnl_computed':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    out=attest(load(a.root));open(a.output,'w').write(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n');print(json.dumps(out,indent=2))
