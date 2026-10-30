#!/usr/bin/env python3
"""V98 source-only alternative Binance USD-M historical markPrice transports; 2023 only."""
import hashlib,json,math,socket,urllib.request,urllib.error
from pathlib import Path
HOSTS=('https://fapi2.binance.com','https://fapi3.binance.com','https://fapi4.binance.com')
PATH='/fapi/v1/fundingRate?symbol=BTCUSDT&startTime=1672531200000&endTime=1672617600000&limit=10'
out={'scope':'V98_2023_ONLY_NO_PNL','2025_accessed':False,'2026_plus_accessed':False,
     'candidate_transport_hosts_not_yet_attested':list(HOSTS),'results':[]}
for host in HOSTS:
    rec={'host':host,'status':'UNVERIFIED_TRANSPORT'}
    try:
        req=urllib.request.Request(host+PATH,headers={'User-Agent':'V98-Independent-Mark-Probe/1.0','Accept':'application/json'})
        with urllib.request.urlopen(req,timeout=8) as res:
            body=res.read(100000)
            rec['http_status']=res.status
            rec['sha256']=hashlib.sha256(body).hexdigest()
            rows=json.loads(body)
            if not isinstance(rows,list):raise ValueError('RESPONSE_NOT_LIST')
            rec['row_count']=len(rows)
            valid=bool(rows)
            for row in rows:
                if not isinstance(row,dict) or row.get('symbol')!='BTCUSDT':
                    valid=False;break
                if not all(k in row for k in ('fundingTime','fundingRate','markPrice')):
                    valid=False;break
                t=int(row['fundingTime']);r=float(row['fundingRate']);m=float(row['markPrice'])
                if not (1672531200000<=t<=1672617600000 and math.isfinite(r) and math.isfinite(m) and m>0):
                    valid=False;break
            rec['status']='SAMPLE_SCHEMA_PASS_NOT_FULL_PROVENANCE' if valid else 'UNUSABLE_SAMPLE'
    except (urllib.error.HTTPError,urllib.error.URLError,socket.timeout,TimeoutError,ValueError) as e:
        rec['error']=type(e).__name__+':'+str(e)[:160]
        if isinstance(e,urllib.error.HTTPError):rec['http_status']=e.code
    out['results'].append(rec)
Path('v98_exact_mark_alternate_probe_receipt.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
print('V98_ALTERNATE_OFFICIAL_HOST_SAMPLE_PROBE_ONLY_NO_PNL')
