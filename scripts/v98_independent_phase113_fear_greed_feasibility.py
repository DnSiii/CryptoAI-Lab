#!/usr/bin/env python3
import hashlib,json,math
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
import pandas as pd

OUT=Path('reports/v98_independent_phase113_fear_greed_feasibility.json')
URL='https://api.alternative.me/fng/?limit=0&format=json'
START='2023-01-01'; END='2025-12-31'; EXPECTED=1096

def get(url):
    req=Request(url,headers={'User-Agent':'CryptoAI-Lab-V98-Independent/phase113'})
    try:
        with urlopen(req,timeout=120) as r:
            raw=r.read(); status=getattr(r,'status',200)
        return status,raw,None
    except HTTPError as e:
        return e.code,e.read(),f'HTTP {e.code}'
    except (URLError,TimeoutError,Exception) as e:
        return None,b'',type(e).__name__+': '+str(e)

def main():
    status,raw,err=get(URL)
    integrity={'http_status':status,'error':err,'payload_sha256':hashlib.sha256(raw).hexdigest() if raw else None,
               'schema_contract':'object with data list; records require timestamp and integer value [0,100]'}
    gate='FAIL_DATA_NO_ALPHA'; check={}
    if status==200:
        try:
            obj=json.loads(raw); data=obj.get('data') if isinstance(obj,dict) else None
            schema_ok=isinstance(data,list); rows=[]; invalid=0
            if schema_ok:
                for x in data:
                    try:
                        ts=pd.to_datetime(int(x['timestamp']),unit='s',utc=True)
                        val=int(x['value'])
                        if not 0<=val<=100: invalid+=1; continue
                        rows.append((ts,ts.strftime('%Y-%m-%d'),val))
                    except Exception:
                        invalid+=1
            df=pd.DataFrame(rows,columns=['timestamp','date_norm','value'])
            if len(df):
                df=df[(df.date_norm>=START)&(df.date_norm<=END)].sort_values('timestamp')
                before=len(df); df=df.drop_duplicates('date_norm',keep='last').sort_values('date_norm')
                collapsed=before-len(df); unique=int(df.date_norm.nunique()); cov=unique/EXPECTED
                first=df.date_norm.iloc[0] if unique else None; last=df.date_norm.iloc[-1] if unique else None
                dup=int(df.date_norm.duplicated().sum())
            else:
                collapsed=unique=dup=0; cov=0.0; first=last=None
            passed=bool(schema_ok and invalid==0 and unique>=math.ceil(.95*EXPECTED) and first is not None and first<='2023-01-07' and last>='2025-12-24' and dup==0)
            check={'schema_ok':schema_ok,'usable_daily_dates':unique,'coverage':cov,'first_date':first,'last_date':last,
                   'invalid_records':invalid,'collapsed_duplicate_days':collapsed,'post_canonical_duplicate_days':dup,
                   'canonicalization':'timestamp ascending; keep last observation per UTC day','passed':passed}
            gate='PASS_DATA_ONLY' if passed else 'FAIL_DATA_NO_ALPHA'
        except Exception as e:
            integrity['parse_error']=type(e).__name__+': '+str(e)
    rep={'engine':'V98 Independent','phase':'113','mode':'DATA_ONLY_NO_ALPHA_NO_PNL','source':'alternative.me/fng',
         'window':[START,END],'expected_days':EXPECTED,'integrity':integrity,'check':check,'gate':gate,
         'value_descriptives_exposed':False,'alpha_or_pnl_computed':False,'validation':None,'final_holdout':None,
         'future_holdout_required':True,'v16_used':False,'v99_used':False,'phase083_selection_use':False,
         'parameter_search':False,'rescue_allowed':False,'generated_at':datetime.now(timezone.utc).isoformat()}
    OUT.write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n'); print(json.dumps(rep,indent=2,sort_keys=True))

if __name__=='__main__': main()
