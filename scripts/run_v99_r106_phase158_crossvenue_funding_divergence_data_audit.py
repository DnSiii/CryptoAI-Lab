#!/usr/bin/env python3
"""V99 R106 Phase158 preregistered TRAIN-only cross-venue funding data audit.
Binance transport uses deterministic public Binance Vision monthly archives because
fapi.binance.com is HTTP-451 blocked on GitHub-hosted runners. Scientific contract unchanged.
"""
from __future__ import annotations
import io,json,time,zipfile
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request,urlopen
import numpy as np,pandas as pd
PROJECT=Path(__file__).resolve().parents[1]
OUT=PROJECT/'reports'/'candidate_v99_r106_phase158_crossvenue_funding_divergence_data_audit.json'
PREREG=PROJECT/'research'/'v99_r106_phase158_crossvenue_funding_divergence_data_prereg.md'
TRAIN_START=pd.Timestamp('2021-12-01',tz='UTC'); TRAIN_END=pd.Timestamp('2024-01-18',tz='UTC')
START_MS=int(TRAIN_START.timestamp()*1000); END_MS=int(TRAIN_END.timestamp()*1000)
MAP={'BTCUSDT':'BTC-USDT-SWAP','ETHUSDT':'ETH-USDT-SWAP','SOLUSDT':'SOL-USDT-SWAP','XRPUSDT':'XRP-USDT-SWAP','DOGEUSDT':'DOGE-USDT-SWAP'}
OKX='https://www.okx.com/api/v5/public/funding-rate-history'
VISION='https://data.binance.vision/data/futures/um/monthly/fundingRate/{sym}/{sym}-fundingRate-{ym}.zip'

def get_json(url,params,retries=5):
    last=None
    for k in range(retries):
        try:
            req=Request(url+'?'+urlencode(params),headers={'User-Agent':'CryptoAI-Lab-V99-R106-Phase158/1.1','Accept':'application/json','Connection':'close'})
            with urlopen(req,timeout=45) as r:return json.loads(r.read().decode())
        except Exception as e:
            last=e
            if k+1<retries:time.sleep(min(8,1.5*(k+1)))
    raise RuntimeError(repr(last))

def get_bytes(url,retries=4):
    last=None
    for k in range(retries):
        try:
            req=Request(url,headers={'User-Agent':'CryptoAI-Lab-V99-R106-Phase158/1.1','Accept':'application/zip','Connection':'close'})
            with urlopen(req,timeout=60) as r:return r.read()
        except HTTPError as e:
            if e.code==404:return None
            last=e
        except Exception as e:last=e
        if k+1<retries:time.sleep(min(8,1.5*(k+1)))
    raise RuntimeError(f'archive transport failed {url}: {last!r}')

def okx(inst):
    cursor=END_MS; rows={}; reqs=0
    while cursor>START_MS:
        obj=get_json(OKX,{'instId':inst,'after':str(cursor),'limit':'400'}); reqs+=1
        if obj.get('code')!='0':raise RuntimeError(f"OKX {inst} code={obj.get('code')} msg={obj.get('msg')}")
        data=obj.get('data') or []
        if not data:break
        stamps=[]
        for x in data:
            ts=int(x['fundingTime']); stamps.append(ts)
            if START_MS<=ts<END_MS: rows[ts]=float(x['fundingRate'])
        oldest=min(stamps)
        if oldest<=START_MS:break
        if oldest>=cursor:raise RuntimeError(f'{inst}: OKX pagination stalled')
        cursor=oldest; time.sleep(.12)
        if reqs>100:raise RuntimeError('OKX pagination safety')
    return pd.Series(rows,dtype=float).sort_index(),reqs,[]

def months():
    # Full months intersecting TRAIN; rows are clipped exactly to TRAIN afterwards.
    return pd.period_range(TRAIN_START.tz_localize(None).to_period('M'),(TRAIN_END-pd.Timedelta(milliseconds=1)).tz_localize(None).to_period('M'),freq='M')

def binance(sym):
    rows={}; reqs=0; missing=[]
    for per in months():
        ym=str(per); url=VISION.format(sym=sym,ym=ym); raw=get_bytes(url); reqs+=1
        if raw is None:
            missing.append(ym); continue
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            names=[n for n in z.namelist() if n.lower().endswith('.csv')]
            if len(names)!=1:raise RuntimeError(f'{sym} {ym}: expected one CSV, got {names}')
            df=pd.read_csv(z.open(names[0]))
        # Binance Vision funding archives have changed column order/names historically;
        # resolve semantically and fail closed if the required fields are absent.
        cols={str(c).strip().lower():c for c in df.columns}
        tcol=next((cols[k] for k in ('fundingtime','funding_time','calctime','calc_time') if k in cols),None)
        rcol=next((cols[k] for k in ('fundingrate','funding_rate','lastfundingrate','last_funding_rate') if k in cols),None)
        if tcol is None or rcol is None:raise RuntimeError(f'{sym} {ym}: unknown archive schema {list(df.columns)}')
        for ts,rate in zip(pd.to_numeric(df[tcol],errors='coerce'),pd.to_numeric(df[rcol],errors='coerce')):
            if pd.isna(ts) or pd.isna(rate):continue
            ts=int(ts)
            # Defensive support if an archive ever stores microseconds.
            if ts>10**14:ts//=1000
            if START_MS<=ts<END_MS:rows[ts]=float(rate)
    return pd.Series(rows,dtype=float).sort_index(),reqs,missing

def stats(s,expected,reqs,missing=None):
    idx=np.array(s.index,dtype=np.int64); finite=bool(np.isfinite(s.to_numpy()).all())
    return {'rows':int(len(s)),'expected_8h_events':expected,'coverage_vs_8h':float(len(s)/expected),'requests':reqs,'missing_monthly_archives':missing or [],'strictly_increasing':bool(len(idx)<2 or np.all(np.diff(idx)>0)),'all_finite':finite,'inside_train':bool(len(idx)==0 or (idx.min()>=START_MS and idx.max()<END_MS))}

def main():
    pt=PREREG.read_text(); assert 'DATA-ONLY' in pt and '95%' in pt and '90%' in pt and 'No PnL is computed' in pt
    expected=int((END_MS-START_MS)//(8*3600_000)); assets={}; all_pass=True
    for sym,inst in MAP.items():
        o,orq,om=okx(inst); b,brq,bm=binance(sym); os=stats(o,expected,orq,om); bs=stats(b,expected,brq,bm)
        odf=pd.DataFrame({'ts':pd.to_datetime(o.index,unit='ms',utc=True),'okx':o.values}).sort_values('ts')
        bdf=pd.DataFrame({'tsb':pd.to_datetime(b.index,unit='ms',utc=True),'binance':b.values}).sort_values('tsb')
        if len(odf) and len(bdf):
            m=pd.merge_asof(odf,bdf,left_on='ts',right_on='tsb',direction='nearest',tolerance=pd.Timedelta(minutes=60)); aligned=int(m.binance.notna().sum())
        else:aligned=0
        denom=max(1,min(len(o),len(b))); align_cov=float(aligned/denom)
        passed=all([os['coverage_vs_8h']>=.95,bs['coverage_vs_8h']>=.95,os['strictly_increasing'],bs['strictly_increasing'],os['all_finite'],bs['all_finite'],os['inside_train'],bs['inside_train'],align_cov>=.90])
        all_pass &= passed
        assets[sym]={'okx':os,'binance':bs,'aligned_within_60m':aligned,'aligned_coverage_of_smaller':align_cov,'pass':passed}
    out={'study':'V99 R106 Phase158 — CROSS-VENUE FUNDING DIVERGENCE DATA-ONLY AUDIT','status':'PASS_DATA_ONLY' if all_pass else 'FAIL_DATA_ONLY','train_start':str(TRAIN_START),'train_end_exclusive':str(TRAIN_END),'binance_transport':'data.binance.vision monthly fundingRate archives (deterministic public archive fallback after independently observed fapi HTTP 451)','assets':assets,'holdout_rows_used_for_feature_construction':0,'holdout_rows_used_for_selection':0,'pnl_computed':False,'frozen_assets_untouched':{'v16':True,'v99_frozen':True},'decision':'Eligible only for separately preregistered causal alpha hypothesis.' if all_pass else 'Data source fails frozen integrity gates; no alpha test permitted.'}
    OUT.write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':main()
