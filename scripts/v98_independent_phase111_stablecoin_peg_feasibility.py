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
        with urlopen(req,timeout=120) as r:
            raw=r.read(); status=getattr(r,'status',200)
        return status,raw,None
    except HTTPError as e:
        return e.code,e.read(),f'HTTP {e.code}'
    except (URLError,TimeoutError,Exception) as e:
        return None,b'',type(e).__name__+': '+str(e)

def canonical_history(hist, stablecoin_id):
    """Parse frozen /stablecoinprices flat records without exposing price descriptives."""
    if not isinstance(hist,list):
        return pd.DataFrame(columns=['date_norm','price']), {'schema_ok':False,'raw_records_for_id':0,'collapsed_duplicate_days':0}
    rows=[]
    sid=str(stablecoin_id)
    for x in hist:
        if not isinstance(x,dict) or str(x.get('id'))!=sid:
            continue
        try:
            ts=pd.to_datetime(int(x['timestamp']),unit='s',utc=True)
            price=float(x['price'])
            rows.append((ts,ts.strftime('%Y-%m-%d'),price))
        except Exception:
            rows.append((pd.NaT,None,np.nan))
    df=pd.DataFrame(rows,columns=['timestamp','date_norm','price'])
    raw_records=len(df)
    if not len(df):
        return pd.DataFrame(columns=['date_norm','price']), {'schema_ok':True,'raw_records_for_id':0,'collapsed_duplicate_days':0}
    df=df.dropna(subset=['date_norm']).sort_values(['timestamp'])
    before=len(df)
    df=df.drop_duplicates('date_norm',keep='last').sort_values('date_norm')
    return df[['date_norm','price']].reset_index(drop=True), {
        'schema_ok':True,
        'raw_records_for_id':raw_records,
        'collapsed_duplicate_days':before-len(df),
    }

def main():
    ms,mraw,merr=get(META); hs,hraw,herr=get(HIST)
    base={'metadata_http_status':ms,'history_http_status':hs,'metadata_error':merr,'history_error':herr,
          'metadata_sha256':hashlib.sha256(mraw).hexdigest() if mraw else None,
          'history_sha256':hashlib.sha256(hraw).hexdigest() if hraw else None,
          'history_schema_contract':'flat list of records with id,price,timestamp'}
    checks=[]; gate='FAIL_DATA_NO_ALPHA'; ids={}
    if ms==200 and hs==200:
        try:
            meta=json.loads(mraw); hist=json.loads(hraw)
            assets=meta.get('peggedAssets',[]) if isinstance(meta,dict) else []
            for sym in SYMS:
                matches=[x for x in assets if isinstance(x,dict) and str(x.get('symbol','')).upper()==sym]
                if len(matches)==1 and matches[0].get('id') is not None:
                    ids[sym]=str(matches[0].get('id'))
                else:
                    checks.append({'symbol':sym,'resolved_ids':len(matches),'passed':False,'error':'metadata_symbol_resolution'})
            for sym in SYMS:
                if sym not in ids: continue
                sid=ids[sym]
                sub,parse=canonical_history(hist,sid)
                sub=sub[(sub.date_norm>=START)&(sub.date_norm<=END)].copy() if len(sub) else sub
                vals=pd.to_numeric(sub['price'],errors='coerce') if len(sub) else pd.Series(dtype=float)
                invalid=int((~vals.map(lambda x: math.isfinite(float(x)) if pd.notna(x) else False) | (vals<=0) | (vals>2.5)).sum()) if len(vals) else 0
                unique=int(sub['date_norm'].nunique()) if len(sub) else 0
                cov=unique/EXPECTED
                first=sub['date_norm'].iloc[0] if unique else None
                last=sub['date_norm'].iloc[-1] if unique else None
                post_dup=int(sub['date_norm'].duplicated().sum()) if len(sub) else 0
                passed=(parse['schema_ok'] and unique>=math.ceil(.95*EXPECTED) and first is not None and first<='2023-01-07'
                        and last>='2025-12-24' and invalid==0 and post_dup==0)
                checks.append({'symbol':sym,'resolved_id':sid,'schema_ok':parse['schema_ok'],
                               'raw_records_for_id':parse['raw_records_for_id'],
                               'collapsed_duplicate_days':parse['collapsed_duplicate_days'],
                               'unique_daily_dates':unique,'coverage':cov,'first_date':first,'last_date':last,
                               'invalid_values':invalid,'post_canonical_duplicate_days':post_dup,
                               'canonicalization':'timestamp ascending; keep last observation per UTC day',
                               'passed':bool(passed)})
            gate='PASS_DATA_ONLY' if len(checks)==2 and all(x.get('passed') is True for x in checks) else 'FAIL_DATA_NO_ALPHA'
        except Exception as e:
            base['parse_error']=type(e).__name__+': '+str(e)
    rep={'engine':'V98 Independent','phase':'111','mode':'DATA_ONLY_NO_ALPHA_NO_PNL','source':'stablecoins.llama.fi',
         'symbols':list(SYMS),'window':[START,END],'expected_days_per_symbol':EXPECTED,'integrity':base,'checks':checks,'gate':gate,
         'price_descriptives_exposed':False,'validation':None,'final_holdout':None,'future_holdout_required':True,
         'v16_used':False,'v99_used':False,'phase083_selection_use':False,'alpha_or_pnl_computed':False,'parameter_search':False,
         'rescue_allowed':False,'parser_correction_only':True,'generated_at':datetime.now(timezone.utc).isoformat()}
    OUT.write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
    print(json.dumps(rep,indent=2,sort_keys=True))

if __name__=='__main__': main()
