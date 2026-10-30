#!/usr/bin/env python3
"""V98 training-only third-party funding mark mirror; not official provenance."""
import argparse,csv,hashlib,json,math,time,urllib.parse,urllib.request
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,ASSETS,START
from v98_mark_envelope_settlement import read_envelope
from v98_native_funding_mark_attestation import attest
HOST='https://api-dev.pipai.org'
def probe(root,envelope,mirror_csv):
    d=load(root);lo,hi,env_sha=read_envelope(envelope,d)
    allrows=[]
    def fetch(symbol,start_ms,end_ms):
        params=urllib.parse.urlencode({'symbol':symbol,'startTime':start_ms,'endTime':end_ms,'limit':1000})
        url=HOST+'/fapi/v1/fundingRate?'+params
        last_error=None
        for retry in range(2):
            try:
                req=urllib.request.Request(url,headers={'Accept':'application/json','User-Agent':'V98-Independent-Untrusted-Mirror/1.0'})
                with urllib.request.urlopen(req,timeout=12) as r:
                    if r.status!=200:raise ValueError('HTTP_'+str(r.status))
                    batch=json.loads(r.read(1200000))
                if not isinstance(batch,list):raise ValueError('MIRROR_NOT_LIST')
                j=ASSETS.index(symbol)
                for row in batch:
                    ms=int(row['fundingTime']);mark=float(row['markPrice'])
                    t=(ms-int(START.timestamp()*1000))//3600000
                    if row.get('symbol',symbol)!=symbol or not 0<=t<len(d['c']) or not d['event'][t,j]:
                        raise ValueError('MIRROR_BAD_SYMBOL_OR_TIMESTAMP')
                    if not math.isfinite(mark) or not float(lo[t,j])-1e-8<=mark<=float(hi[t,j])+1e-8:
                        raise ValueError('MIRROR_MARK_OUTSIDE_OFFICIAL_OHLC_'+symbol+'_'+str(t))
                    allrows.append((symbol,ms,str(row['fundingRate']),str(row['markPrice'])))
                return batch
            except Exception as e:
                last_error=type(e).__name__+':'+str(e)[:200]
                if retry==0:time.sleep(.4)
        raise RuntimeError('MIRROR_UNAVAILABLE_'+symbol+'_'+str(start_ms)+'_'+last_error)
    r=attest(d,fetch=fetch)
    if len(allrows)!=9144:raise ValueError('MIRROR_INCOMPLETE_9144_'+str(len(allrows)))
    with open(mirror_csv,'w',newline='') as f:
        w=csv.writer(f);w.writerow(('symbol','fundingTime','fundingRate','markPrice'))
        w.writerows(allrows)
    return {'decision':'PASS_THIRD_PARTY_MIRROR_CORROBORATED_NOT_OFFICIAL_ORIGIN',
            'events':len(allrows),'summary':r['summary'],
            'mirror_csv_sha256':hashlib.sha256(Path(mirror_csv).read_bytes()).hexdigest(),
            'official_mark_envelope_sha256':env_sha,'source_funding_sha256':r['source_funding_sha256'],
            'mirror_host':HOST,'mirror_origin_unverified':True,'exact_official_tick_mark_attested':False,
            'eligible_for_pnl':False,'training_only':True,'2025_or_later_accessed':False,
            'holdout_accessed':False,'strategy_pnl_computed':False}
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True);p.add_argument('--envelope-csv',required=True)
    p.add_argument('--output',required=True);p.add_argument('--mirror-csv',required=True)
    a=p.parse_args()
    try:out=probe(a.root,a.envelope_csv,a.mirror_csv);status=0
    except Exception as e:
        out={'decision':'FAIL_THIRD_PARTY_MIRROR_NOT_ELIGIBLE',
             'error':type(e).__name__+':'+str(e)[:350],
             'mirror_host':HOST,'mirror_origin_unverified':True,
             'exact_official_tick_mark_attested':False,'eligible_for_pnl':False,
             'training_only':True,'2025_or_later_accessed':False,
             'holdout_accessed':False,'strategy_pnl_computed':False}
        status=2
    Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True,allow_nan=False),flush=True)
    raise SystemExit(status)
