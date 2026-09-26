#!/usr/bin/env python3
"""V99 R106 Phase140 data-only gate for comparable hourly notional volume.
No PnL is computed here. Holdout is not inspected or constructed.
"""
from __future__ import annotations
import hashlib, json, time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import numpy as np
import pandas as pd

PROJECT=Path(__file__).resolve().parents[1]
OUT=PROJECT/'reports'/'candidate_v99_r106_phase140_crossvenue_volume_data_gate.json'
PREREG=PROJECT/'docs'/'v99_r106_phase140_crossvenue_volume_participation_preregister.md'
PH136=PROJECT/'reports'/'candidate_v99_r106_phase136_okx_crossvenue_data_audit.json'
TRAIN_START=pd.Timestamp('2021-12-01',tz='UTC'); TRAIN_END=pd.Timestamp('2024-01-18',tz='UTC')
START_MS=int(TRAIN_START.timestamp()*1000); END_MS=int(TRAIN_END.timestamp()*1000); HOUR_MS=3_600_000
BASE='https://www.okx.com/api/v5/market/history-candles'
MAP={'BTCUSDT':'BTC-USDT-SWAP','ETHUSDT':'ETH-USDT-SWAP','SOLUSDT':'SOL-USDT-SWAP','XRPUSDT':'XRP-USDT-SWAP','DOGEUSDT':'DOGE-USDT-SWAP'}

# OKX history-candles schema documents volCcyQuote as quote-currency volume for derivatives.
# Binance USD-M futures kline quote asset volume is quote-asset notional over the interval.
SEMANTIC_CONTRACT={
 'okx_field':'volCcyQuote','okx_row_index':7,'unit':'USDT quote-currency notional per completed 1h candle',
 'binance_field':'quote_asset_volume','binance_source':'canonical futures klines','binance_expected_quote_asset':'USDT',
 'comparison':'direct quote-notional; no price*base-volume proxy permitted'
}

def fetch_json(params,retries=5):
    last=None
    for attempt in range(retries):
        try:
            req=Request(BASE+'?'+urlencode(params),headers={'User-Agent':'CryptoAI-Lab-V99-R106-Phase140/1.0','Accept':'application/json','Connection':'close'})
            with urlopen(req,timeout=45) as r: obj=json.loads(r.read().decode())
            if obj.get('code')!='0': raise RuntimeError(f"OKX code={obj.get('code')} msg={obj.get('msg')}")
            return obj
        except Exception as exc:
            last=exc
            if attempt+1<retries: time.sleep(min(10,1.5*(attempt+1)))
    raise RuntimeError(f'OKX request failed: {last!r}')

def acquire(inst):
    cursor=END_MS; rows={}; reqs=0
    while True:
        data=(fetch_json({'instId':inst,'bar':'1H','after':str(cursor),'limit':'300'}).get('data') or []); reqs+=1
        if not data: break
        page=[]
        for row in data:
            if len(row)<9: raise RuntimeError(f'{inst}: bad candle row')
            ts=int(row[0]); page.append(ts)
            if START_MS<=ts<END_MS:
                norm='|'.join(str(x) for x in row)
                if ts in rows and rows[ts]!=norm: raise RuntimeError(f'{inst}: conflicting duplicate')
                rows[ts]=norm
        oldest=min(page)
        if oldest<=START_MS: break
        if oldest>=cursor: raise RuntimeError(f'{inst}: pagination stalled')
        cursor=oldest; time.sleep(.12)
        if reqs>1000: raise RuntimeError('pagination safety')
    ts=sorted(rows); idx=pd.to_datetime(ts,unit='ms',utc=True)
    expected=(END_MS-START_MS)//HOUR_MS
    if len(ts)!=expected or idx.duplicated().any(): raise RuntimeError(f'{inst}: incomplete/duplicate rows={len(ts)} expected={expected}')
    # Check the source timestamps in their native millisecond unit.  Using
    # DatetimeIndex.view('i8') is dtype-resolution dependent in pandas 3.x
    # (it may be microseconds), which previously caused a false hourly-gap
    # failure despite complete rows.
    gaps=sum(1 for a,b in zip(ts,ts[1:]) if b-a!=HOUR_MS)
    if gaps: raise RuntimeError(f'{inst}: hourly gaps={gaps}')
    qv=pd.Series([float(rows[t].split('|')[7]) for t in ts],index=idx,dtype=float)
    valid=np.isfinite(qv.to_numpy()) & (qv.to_numpy()>=0)
    digest=hashlib.sha256(('\n'.join(rows[t] for t in ts)).encode()).hexdigest()
    return {'rows_expected':int(expected),'rows_observed':len(ts),'valid_rows':int(valid.sum()),'coverage':float(valid.mean()),'duplicates':int(idx.duplicated().sum()),'hourly_gaps':int(gaps),'normalized_full_rows_sha256':digest,'requests':reqs,'positive_volume_ratio':float((qv>0).mean())}

def main():
    text=PREREG.read_text(); assert 'No PnL may be computed unless' in text and '>=98%' in text and 'without proxy substitution' in text
    ph136=json.loads(PH136.read_text()); assert ph136['status']=='PASS_DATA_ONLY' and ph136['passing_instruments']==5
    instruments={}; passing=0
    for _,inst in MAP.items():
        d=acquire(inst); d['phase136_hash_match']=d['normalized_full_rows_sha256']==ph136['instruments'][inst]['normalized_full_rows_sha256']
        d['pass']=bool(d['coverage']>=.98 and d['duplicates']==0 and d['hourly_gaps']==0 and d['phase136_hash_match'])
        passing+=int(d['pass']); instruments[inst]=d
    status='PASS_DATA_ONLY' if passing==5 else 'DATA_INADMISSIBLE'
    out={'study':'V99 R106 Phase140 — cross-venue volume participation DATA ONLY gate','status':status,'pnl_computed':False,'holdout_rows_used':0,'frozen_assets_untouched':{'v16':True,'v99_frozen':True},'semantic_contract':SEMANTIC_CONTRACT,'passing_instruments':passing,'instruments':instruments,'anti_overfit':{'no_proxy_substitution':True,'no_symbol_substitution':True,'no_parameter_search':True,'train_only':True},'next_gate':'Only PASS_DATA_ONLY permits implementation of the preregistered participation feature and TRAIN alpha gate.'}
    OUT.write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps({'status':status,'passing_instruments':passing,'pnl_computed':False},indent=2))
    if status!='PASS_DATA_ONLY': raise SystemExit(2)
if __name__=='__main__': main()
