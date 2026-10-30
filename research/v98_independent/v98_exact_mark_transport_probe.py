#!/usr/bin/env python3
"""V98-only 2023 historical exact funding markPrice transport probe; NO PnL, no holdout."""
import hashlib,json,urllib.request,urllib.error,socket
from pathlib import Path
HOSTS=(
 'https://fapi.binance.com',
 'https://fapi1.binance.com',
 'https://api-dev.pipai.org',
)
PATH='/fapi/v1/fundingRate?symbol=BTCUSDT&startTime=1672531200000&endTime=1672617600000&limit=10'
out={'scope':'V98_CLEAN4_2023_ONLY_SOURCE_PROBE','pnl_computed':False,
     '2025_accessed':False,'2026_plus_accessed':False,'transport':[]}
for host in HOSTS:
    url=host+PATH
    record={'host':host,'source_claim':'OFFICIAL' if 'binance.com' in host else 'UNVERIFIED_THIRD_PARTY_MIRROR'}
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'V98-Independent-Source-Integrity/1.0','Accept':'application/json'})
        with urllib.request.urlopen(req,timeout=12) as res:
            body=res.read(250000)
            record['http_status']=res.status
            record['body_sha256']=hashlib.sha256(body).hexdigest()
            rows=json.loads(body)
            if not isinstance(rows,list):raise ValueError('NOT_LIST')
            record['row_count']=len(rows)
            record['all_have_markPrice']=bool(rows) and all(
                isinstance(x,dict) and all(k in x for k in ('symbol','fundingTime','fundingRate','markPrice'))
                for x in rows)
            record['timestamps_2023_only']=all(1672531200000<=int(x['fundingTime'])<=1672617600000 for x in rows)
            record['schema_usable']=record['all_have_markPrice'] and record['timestamps_2023_only']
    except urllib.error.HTTPError as e:
        record['http_status']=e.code
        record['error']='HTTP_'+str(e.code)
    except (urllib.error.URLError,TimeoutError,socket.timeout,ValueError,json.JSONDecodeError) as e:
        record['error']=type(e).__name__+':'+str(e)[:220]
    out['transport'].append(record)
Path('v98_mark_transport_probe_receipt.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
print('V98_MARK_TRANSPORT_PROBE_ONLY_NO_EXACT_PROVENANCE_NO_PNL')
