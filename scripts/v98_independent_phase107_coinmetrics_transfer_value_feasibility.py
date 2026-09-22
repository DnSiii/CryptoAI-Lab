#!/usr/bin/env python3
import hashlib,json,math
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

OUT=Path('reports/v98_independent_phase107_coinmetrics_transfer_value_feasibility.json')
BASE='https://community-api.coinmetrics.io/v4/timeseries/asset-metrics'
ASSETS=('btc','eth');METRIC='TxTfrValAdjUSD';START='2023-01-01';END='2025-12-31';EXPECTED=1096

def fetch(asset):
    params={'assets':asset,'metrics':METRIC,'frequency':'1d','start_time':START,'end_time':END,'page_size':10000}
    url=BASE+'?'+urlencode(params);req=Request(url,headers={'User-Agent':'CryptoAI-Lab-V98-Independent/phase107'})
    try:
        with urlopen(req,timeout=45) as r: raw=r.read();status=getattr(r,'status',200)
    except HTTPError as e:
        raw=e.read();return {'asset':asset,'url':url,'http_status':e.code,'error':f'HTTP {e.code}','raw_sha256':hashlib.sha256(raw).hexdigest(),'body_preview':raw[:300].decode('utf-8','replace'),'passed':False}
    except (URLError,TimeoutError,Exception) as e:
        return {'asset':asset,'url':url,'error':type(e).__name__+': '+str(e),'passed':False}
    sha=hashlib.sha256(raw).hexdigest()
    try: payload=json.loads(raw)
    except Exception as e: return {'asset':asset,'url':url,'http_status':status,'error':'JSON '+str(e),'raw_sha256':sha,'passed':False}
    rows=payload.get('data',[]) if isinstance(payload,dict) else [];dates=[];invalid=0
    for x in rows:
        try:
            d=str(x['time'])[:10];v=float(x[METRIC]);dates.append(d)
            if not math.isfinite(v) or v<0: invalid+=1
        except Exception: invalid+=1
    unique=len(set(dates));duplicates=max(0,len(dates)-unique);ordered=all(dates[i]<dates[i+1] for i in range(len(dates)-1));coverage=unique/EXPECTED
    passed=(status==200 and unique>=math.ceil(.95*EXPECTED) and bool(dates) and min(dates)<='2023-01-07' and max(dates)>='2025-12-24' and invalid==0 and duplicates==0 and ordered)
    return {'asset':asset,'url':url,'http_status':status,'rows':len(rows),'unique_dates':unique,'coverage':coverage,'first_date':min(dates) if dates else None,'last_date':max(dates) if dates else None,'duplicates':duplicates,'invalid_values':invalid,'strict_order':ordered,'raw_sha256':sha,'passed':passed}

def main():
    assets=[fetch(a) for a in ASSETS];gate='PASS_DATA_ONLY' if all(x.get('passed') is True for x in assets) else 'FAIL_DATA_NO_ALPHA'
    report={'engine':'V98 Independent','phase':'107','mode':'DATA_ONLY_NO_ALPHA_NO_PNL','source':'Coin Metrics Community API','metric':METRIC,'frequency':'1d','window':[START,END],'expected_days_per_asset':EXPECTED,'assets':assets,'gate':gate,'validation':None,'final_holdout':None,'future_holdout_required':True,'v16_used':False,'v99_used':False,'phase083_selection_use':False,'alpha_or_pnl_computed':False,'parameter_search':False,'rescue_allowed':False,'generated_at':datetime.now(timezone.utc).isoformat()}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True))
if __name__=='__main__':main()
