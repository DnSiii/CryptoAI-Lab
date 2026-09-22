#!/usr/bin/env python3
import hashlib,json,math
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
import pandas as pd

OUT=Path('reports/v98_independent_phase111_stablecoin_peg_feasibility.json')
META='https://stablecoins.llama.fi/stablecoins?includePrices=true'
HIST='https://stablecoins.llama.fi/stablecoinprices'
SYMS=('USDT','USDC');START='2023-01-01';END='2025-12-31';EXPECTED=1096

def get(url):
    req=Request(url,headers={'User-Agent':'CryptoAI-Lab-V98-Independent/phase111'})
    try:
        with urlopen(req,timeout=120) as r: raw=r.read(); status=getattr(r,'status',200)
        return status,raw,None
    except HTTPError as e: return e.code,e.read(),f'HTTP {e.code}'
    except (URLError,TimeoutError,Exception) as e: return None,b'',type(e).__name__+': '+str(e)

def main():
    ms,mraw,merr=get(META); hs,hraw,herr=get(HIST)
    base={'metadata_http_status':ms,'history_http_status':hs,'metadata_error':merr,'history_error':herr,
          'metadata_sha256':hashlib.sha256(mraw).hexdigest() if mraw else None,
          'history_sha256':hashlib.sha256(hraw).hexdigest() if hraw else None}
    checks=[]; gate='FAIL_DATA_NO_ALPHA'; ids={}
    if ms==200 and hs==200:
        try:
            meta=json.loads(mraw); hist=json.loads(hraw)
            assets=meta.get('peggedAssets',[]) if isinstance(meta,dict) else []
            for sym in SYMS:
                matches=[x for x in assets if isinstance(x,dict) and str(x.get('symbol','')).upper()==sym]
                if len(matches)==1: ids[sym]=str(matches[0].get('id'))
                else: checks.append({'symbol':sym,'resolved_ids':len(matches),'passed':False,'error':'metadata_symbol_resolution'})
            try:
                df=pd.concat([pd.DataFrame(d) for d in hist],ignore_index=False).reset_index().rename(columns={'index':'stablecoin'})
            except Exception as e:
                df=pd.DataFrame(); base['history_parse_error']=type(e).__name__+': '+str(e)
            if len(df):
                if 'date' in df.columns:
                    df['date_norm']=pd.to_datetime(df['date'],unit='s',utc=True,errors='coerce').dt.strftime('%Y-%m-%d')
                else: df['date_norm']=None
                for sym in SYMS:
                    if sym not in ids: continue
                    sid=ids[sym]
                    sub=df[df['stablecoin'].astype(str)==sid].copy()
                    if 'date_norm' in sub: sub=sub[(sub.date_norm>=START)&(sub.date_norm<=END)]
                    invalid=0
                    if 'price' not in sub.columns: invalid=len(sub)
                    else:
                        vals=pd.to_numeric(sub['price'],errors='coerce')
                        invalid=int((~vals.map(lambda x: math.isfinite(float(x)) if pd.notna(x) else False) | (vals<=0) | (vals>2.5)).sum())
                    raw_rows=len(sub)
                    if 'date_norm' in sub.columns:
                        sub=sub.dropna(subset=['date_norm']).sort_values(['date_norm']).drop_duplicates('date_norm',keep='last')
                    unique=len(sub); cov=unique/EXPECTED
                    first=sub['date_norm'].iloc[0] if unique else None; last=sub['date_norm'].iloc[-1] if unique else None
                    passed=(unique>=math.ceil(.95*EXPECTED) and first is not None and first<='2023-01-07' and last>='2025-12-24' and invalid==0)
                    checks.append({'symbol':sym,'resolved_id':sid,'raw_rows_in_window':raw_rows,'unique_daily_dates':unique,'coverage':cov,
                                   'first_date':first,'last_date':last,'invalid_values':invalid,'canonicalization':'sort date; keep last observation per UTC day','passed':bool(passed)})
            gate='PASS_DATA_ONLY' if len(checks)==2 and all(x.get('passed') is True for x in checks) else 'FAIL_DATA_NO_ALPHA'
        except Exception as e: base['parse_error']=type(e).__name__+': '+str(e)
    rep={'engine':'V98 Independent','phase':'111','mode':'DATA_ONLY_NO_ALPHA_NO_PNL','source':'stablecoins.llama.fi',
         'symbols':list(SYMS),'window':[START,END],'expected_days_per_symbol':EXPECTED,'integrity':base,'checks':checks,'gate':gate,
         'price_descriptives_exposed':False,'validation':None,'final_holdout':None,'future_holdout_required':True,
         'v16_used':False,'v99_used':False,'phase083_selection_use':False,'alpha_or_pnl_computed':False,'parameter_search':False,
         'rescue_allowed':False,'generated_at':datetime.now(timezone.utc).isoformat()}
    OUT.write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n');print(json.dumps(rep,indent=2,sort_keys=True))
if __name__=='__main__': main()
