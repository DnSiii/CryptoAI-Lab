#!/usr/bin/env python3
import hashlib,json,math
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

OUT=Path('reports/v98_independent_phase110_bridge_flow_feasibility.json')
BASE='https://bridges.llama.fi/bridgevolume/'
CHAINS=('Ethereum','BSC');START='2023-01-01';END='2025-12-31';EXPECTED=1096

def norm_date(x):
    if isinstance(x,(int,float)):
        return datetime.fromtimestamp(float(x),tz=timezone.utc).date().isoformat()
    s=str(x)
    if s.isdigit():
        return datetime.fromtimestamp(float(s),tz=timezone.utc).date().isoformat()
    return s[:10]

def fetch(chain):
    url=BASE+chain; req=Request(url,headers={'User-Agent':'CryptoAI-Lab-V98-Independent/phase110'})
    try:
        with urlopen(req,timeout=60) as r: raw=r.read();status=getattr(r,'status',200)
    except HTTPError as e:
        raw=e.read();return {'chain':chain,'url':url,'http_status':e.code,'error':f'HTTP {e.code}','raw_sha256':hashlib.sha256(raw).hexdigest(),'body_preview':raw[:300].decode('utf-8','replace'),'passed':False}
    except (URLError,TimeoutError,Exception) as e:
        return {'chain':chain,'url':url,'error':type(e).__name__+': '+str(e),'passed':False}
    sha=hashlib.sha256(raw).hexdigest()
    try: payload=json.loads(raw)
    except Exception as e: return {'chain':chain,'url':url,'http_status':status,'error':'JSON '+str(e),'raw_sha256':sha,'passed':False}
    if isinstance(payload,dict): rows=payload.get('data',payload.get('chart',payload.get('totalDataChart',[])))
    else: rows=payload
    if not isinstance(rows,list):
        return {'chain':chain,'url':url,'http_status':status,'error':'unexpected_payload_shape','raw_sha256':sha,'passed':False}
    dates=[];invalid=0;filtered=0
    for x in rows:
        if not isinstance(x,dict): continue
        try:
            d=norm_date(x['date'])
            if d<START or d>END: continue
            dep=float(x['depositUSD']);wd=float(x['withdrawUSD']);filtered+=1;dates.append(d)
            if not math.isfinite(dep) or dep<0 or not math.isfinite(wd) or wd<0: invalid+=1
        except Exception: invalid+=1
    unique=len(set(dates));duplicates=max(0,len(dates)-unique);canonical=sorted(set(dates));coverage=unique/EXPECTED
    passed=(status==200 and unique>=math.ceil(.95*EXPECTED) and bool(canonical) and canonical[0]<='2023-01-07' and canonical[-1]>='2025-12-24' and invalid==0 and duplicates==0)
    return {'chain':chain,'url':url,'http_status':status,'raw_rows':len(rows),'filtered_rows':filtered,'unique_dates':unique,'coverage':coverage,'first_date':canonical[0] if canonical else None,'last_date':canonical[-1] if canonical else None,'duplicates':duplicates,'invalid_values':invalid,'canonical_strict_order':all(canonical[i]<canonical[i+1] for i in range(len(canonical)-1)),'raw_sha256':sha,'passed':passed}

def main():
    checks=[fetch(c) for c in CHAINS];gate='PASS_DATA_ONLY' if all(x.get('passed') is True for x in checks) else 'FAIL_DATA_NO_ALPHA'
    rep={'engine':'V98 Independent','phase':'110','mode':'DATA_ONLY_NO_ALPHA_NO_PNL','source':'bridges.llama.fi public bridgevolume endpoint','chains':list(CHAINS),'window':[START,END],'expected_days_per_chain':EXPECTED,'checks':checks,'gate':gate,'validation':None,'final_holdout':None,'future_holdout_required':True,'v16_used':False,'v99_used':False,'phase083_selection_use':False,'alpha_or_pnl_computed':False,'parameter_search':False,'rescue_allowed':False,'generated_at':datetime.now(timezone.utc).isoformat()}
    OUT.write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n');print(json.dumps(rep,indent=2,sort_keys=True))
if __name__=='__main__':main()
