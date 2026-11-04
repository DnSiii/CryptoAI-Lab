#!/usr/bin/env python3
"""V98 source-only alternative Binance USD-M historical markPrice transports; 2023 only."""
import hashlib,json,math,socket,time,urllib.parse,urllib.request,urllib.error
from pathlib import Path
HOSTS=('https://fapi2.binance.com','https://fapi3.binance.com','https://fapi4.binance.com')
PATH='/fapi/v1/fundingRate?symbol=BTCUSDT&startTime=1672531200000&endTime=1672617600000&limit=10'
class StrictSameOriginRedirect(urllib.request.HTTPRedirectHandler):
    """Allow one transparent canonical redirect only when origin, path and query are identical."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        old=urllib.parse.urlsplit(req.full_url)
        new=urllib.parse.urlsplit(newurl)
        hops=int(req.headers.get('X-v98-redirect-hops','0'))
        if (code not in (301,302,307,308) or hops >= 1 or
            new.scheme != 'https' or old.scheme != 'https' or
            new.hostname != old.hostname or new.port != old.port or
            new.path != old.path or new.query != old.query or new.username or new.password):
            return None
        next_req=super().redirect_request(req,fp,code,msg,headers,newurl)
        if next_req is not None:
            next_req.add_header('X-v98-redirect-hops','1')
        return next_req

OPENER=urllib.request.build_opener(StrictSameOriginRedirect)
out={'scope':'V98_2023_ONLY_NO_PNL','2025_accessed':False,'2026_plus_accessed':False,
     'candidate_transport_hosts_not_yet_attested':list(HOSTS),'results':[]}
for host in HOSTS:
    rec={'host':host,'status':'UNVERIFIED_TRANSPORT'}
    try:
        req=urllib.request.Request(host+PATH,headers={'User-Agent':'V98-Independent-Mark-Probe/1.0','Accept':'application/json'})
        started=time.monotonic()
        with OPENER.open(req,timeout=8) as res:
            final=urllib.parse.urlsplit(res.geturl())
            expected=urllib.parse.urlsplit(host)
            rec['final_host']=final.hostname
            rec['elapsed_ms']=round((time.monotonic()-started)*1000)
            if final.scheme!='https' or final.hostname!=expected.hostname:
                raise ValueError('UNTRUSTED_REDIRECT_ORIGIN')
            body=res.read(100001)
            if len(body)>100000:raise ValueError('OVERSIZE_RESPONSE')
            rec['http_status']=res.status
            rec['content_type']=res.headers.get('Content-Type','')
            if 'json' not in rec['content_type'].lower():
                raise ValueError('NON_JSON_CONTENT_TYPE')
            rec['sha256']=hashlib.sha256(body).hexdigest()
            rows=json.loads(body)
            if not isinstance(rows,list):raise ValueError('RESPONSE_NOT_LIST')
            rec['row_count']=len(rows)
            valid=bool(rows)
            times=[]
            for row in rows:
                if not isinstance(row,dict) or row.get('symbol')!='BTCUSDT':
                    valid=False;break
                if not all(k in row for k in ('fundingTime','fundingRate','markPrice')):
                    valid=False;break
                t=int(row['fundingTime']);r=float(row['fundingRate']);m=float(row['markPrice'])
                if not (1672531200000<=t<=1672617600000 and math.isfinite(r) and math.isfinite(m) and m>0):
                    valid=False;break
                times.append(t)
            if len(times)!=len(set(times)) or times!=sorted(times):valid=False
            rec['status']='SAMPLE_SCHEMA_PASS_NOT_FULL_PROVENANCE' if valid else 'UNUSABLE_SAMPLE'
    except (urllib.error.HTTPError,urllib.error.URLError,socket.timeout,TimeoutError,ValueError,TypeError,KeyError,OverflowError) as e:
        rec['error']=type(e).__name__+':'+str(e)[:160]
        if isinstance(e,urllib.error.HTTPError):
            rec['http_status']=e.code
            if 300 <= e.code < 400:
                location=e.headers.get('Location','')
                parsed=urllib.parse.urlsplit(urllib.parse.urljoin(host+PATH,location))
                rec['redirect_status']=e.code
                rec['redirect_scheme']=parsed.scheme
                rec['redirect_host']=parsed.hostname
                rec['redirect_path']=parsed.path
                rec['redirect_query_keys']=sorted(urllib.parse.parse_qs(parsed.query))
                rec['redirect_is_official_same_host']=parsed.scheme=='https' and parsed.hostname==urllib.parse.urlsplit(host).hostname
                rec['redirect_followed']=False
                rec['http_error_class']='REDIRECT_NOT_FOLLOWED'
            rec['http_error_class']=rec.get('http_error_class') or ('REGION_RESTRICTED' if e.code==451 else ('ACCESS_DENIED' if e.code in (403,418) else 'OTHER_HTTP_ERROR'))
            rec['retry_after']=e.headers.get('Retry-After')
            rec['error_body_sha256']=hashlib.sha256(e.read(4096)).hexdigest()
    out['results'].append(rec)
Path('v98_exact_mark_alternate_probe_receipt.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
print('V98_ALTERNATE_OFFICIAL_HOST_SAMPLE_PROBE_ONLY_NO_PNL')
if not any(x['status']=='SAMPLE_SCHEMA_PASS_NOT_FULL_PROVENANCE' for x in out['results']):
    raise SystemExit('V98_EXACT_MARK_SOURCE_TRANSPORT_BLOCKED_NO_USABLE_SAMPLE')
