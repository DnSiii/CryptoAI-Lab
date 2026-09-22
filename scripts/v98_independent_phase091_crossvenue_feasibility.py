#!/usr/bin/env python3
"""V98 Independent Phase091: Bybit linear-perpetual hourly data feasibility only.
NO alpha, NO crypto return join, NO strategy PnL.
"""
from __future__ import annotations
import datetime as dt, hashlib, json, time, urllib.parse, urllib.request
from pathlib import Path

OUT=Path('reports/v98_independent_phase091_crossvenue_feasibility.json')
START=int(dt.datetime(2023,1,1,tzinfo=dt.timezone.utc).timestamp()*1000)
END=int(dt.datetime(2025,12,31,23,tzinfo=dt.timezone.utc).timestamp()*1000)
H=3_600_000
SYMS=['BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT','XRPUSDT']
BASE='https://api.bybit.com/v5/market/kline'

def get(params, attempts=4):
    url=BASE+'?'+urllib.parse.urlencode(params)
    err=None
    for i in range(attempts):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'CryptoAI-Lab-V98-Phase091/1.0'})
            with urllib.request.urlopen(req,timeout=30) as r: raw=r.read()
            obj=json.loads(raw)
            if obj.get('retCode')!=0: raise RuntimeError(obj.get('retMsg'))
            return url,raw,obj
        except Exception as e:
            err=e; time.sleep(1.5*(i+1))
    raise RuntimeError(f'fetch failed: {err}')

def main():
    expected=(END-START)//H+1
    results={}; manifest=[]
    for sym in SYMS:
        rows=[]; cursor=START
        while cursor<=END:
            req_end=min(END,cursor+999*H)
            url,raw,obj=get({'category':'linear','symbol':sym,'interval':'60','start':cursor,'end':req_end,'limit':1000})
            manifest.append({'symbol':sym,'start_ms':cursor,'end_ms':req_end,'url':url,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
            batch=obj['result']['list']
            rows.extend(batch)
            cursor=req_end+H
            time.sleep(.06)
        ts=[int(r[0]) for r in rows if START<=int(r[0])<=END]
        uniq=sorted(set(ts))
        dup=len(ts)-len(uniq)
        gaps=[(b-a)//H-1 for a,b in zip(uniq,uniq[1:]) if b-a>H]
        cov=len(uniq)/expected
        results[sym]={'expected_hours':expected,'observed_rows':len(ts),'unique_hours':len(uniq),'coverage':cov,
                      'duplicates':dup,'duplicate_rate':dup/max(1,len(ts)),'max_unexplained_gap_hours':max(gaps,default=0),
                      'first_ms':uniq[0] if uniq else None,'last_ms':uniq[-1] if uniq else None}
    btceth=all(results[s]['coverage']>=.99 and results[s]['max_unexplained_gap_hours']<=24 for s in ['BTCUSDT','ETHUSDT'])
    four=sum(v['coverage']>=.95 for v in results.values())>=4
    dups=all(v['duplicate_rate']<.001 for v in results.values())
    bounded=all(v['last_ms'] is not None and v['last_ms']<=END for v in results.values())
    gates={'btc_eth_99pct_and_no_gap_gt24h':btceth,'four_of_five_95pct':four,'duplicate_rate_lt_0_1pct':dups,
           'point_in_time_hourly_kline_no_revision_field_required':True,'deterministic_contract_mapping_quote_usdt':True,
           'documented_reacquirable_identifiers_and_hashes':True,'training_boundary_enforced':bounded}
    decision='PASS_DATA_ONLY' if all(gates.values()) else 'FAIL_DATA_NO_ALPHA'
    payload={'engine':'V98 Independent','phase':'091','kind':'DATA_FEASIBILITY_ONLY','decision':decision,
             'source':'Bybit V5 public market kline, category=linear, interval=60','source_endpoint':BASE,
             'period_utc':['2023-01-01T00:00:00Z','2025-12-31T23:00:00Z'],'symbols':SYMS,'results':results,'gates':gates,
             'request_manifest':manifest,'alpha_executed':False,'pnl_executed':False,'crypto_return_join':False,
             'direction_selected':False,'parameter_search':False,'phase083_selection_use':False,'v99_used':False,'v16_used':False,
             'preregistration':'reports/v98_independent_phase091_crossvenue_feasibility_prereg.md'}
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'decision':decision,'results':results,'gates':gates},indent=2))
    if decision!='PASS_DATA_ONLY': raise SystemExit(2)
if __name__=='__main__': main()
