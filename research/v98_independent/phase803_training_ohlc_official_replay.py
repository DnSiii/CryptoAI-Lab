#!/usr/bin/env python3
"""V98 Phase803: restore ONLY pinned Dec-2022..Dec-2024 Clean-4 OHLC.

Official Binance USD-M 1h monthly ZIP/CHECKSUM, fresh same-run SHA256,
strict 18,288-hour UTC chronology and original Phase687 %.12g canonical
format. No 2025+, funding, PnL, signals, external benchmarks or promotion.
Never overwrites an existing file unless its exact pinned digest matches.
"""
from __future__ import annotations
import calendar
import hashlib
import io
import json
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import numpy as np

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'phase243_clean4_canonical'
ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
MONTHS=tuple(f'{y}-{m:02d}' for y in (2022,2023,2024) for m in range(1,13) if (y,m)>=(2022,12))
BASE='https://data.binance.vision/data/futures/um/monthly/klines'
PINS={'BTCUSDT':('5fecf1d58c8f998c9bba2a3f937c384896bf8d794b98a2755b17af807b3f0190',1451038),
      'ETHUSDT':('541748f469cddf34579a3f7865bdec04dab86f886dbd029e90b69ae24ab1325f',1479522),
      'BNBUSDT':('f0776970a530a37fe8f5c434b080fe46919ddb5194d3aa98d02589fed0a2d058',1384866),
      'SOLUSDT':('fa7b07c0892370da2375fb4be2ba1dc82fe700173f0eb8b0807ef16b303ca085',1371664)}
FIELDS=('open','high','low','close','volume','quote_volume')
PASS='PASS_PHASE803_100_OFFICIAL_KLINE_ARCHIVES_TRAINING_ONLY'


def download(url):
    if not url.startswith(BASE+'/') or not (url.endswith('.zip') or url.endswith('.zip.CHECKSUM')):
        raise ValueError('official Binance training kline URL required')
    last=None
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'V98-Independent-Phase803/1.0'})
            with urllib.request.urlopen(req,timeout=50) as response:
                if response.status!=200 or response.geturl()!=url:
                    raise ValueError('official kline redirect/status mismatch')
                raw=response.read(10_000_001)
            if len(raw)>10_000_000:raise ValueError('official kline ZIP too large')
            return raw
        except (OSError,TimeoutError) as exc:
            last=exc
            if attempt<2:time.sleep(2**attempt)
    raise RuntimeError('official kline transport failed: '+str(last))


def checksum(raw,filename):
    p=raw.decode('utf-8-sig').strip().split()
    if len(p)!=2 or p[-1].lstrip('*./')!=filename or len(p[0])!=64 or any(c not in '0123456789abcdef' for c in p[0].lower()):
        raise ValueError('official kline checksum schema mismatch')
    return p[0].lower()


def month_frame(raw,asset,month):
    if asset not in ASSETS or month not in MONTHS:raise ValueError('training Clean-4 month only')
    filename=f'{asset}-1h-{month}.csv'
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.namelist()!=[filename]:raise ValueError('official ZIP member mismatch')
        member=z.read(filename)
    df=pd.read_csv(io.BytesIO(member),dtype=str,keep_default_na=False)
    if len(df.columns)!=12 or str(df.columns[0]).strip().lower()!='open_time':
        raise ValueError('official futures 12-column header mismatch')
    df.columns=['open_time','open','high','low','close','volume','close_time',
                'quote_volume','trade_count','taker_buy_base','taker_buy_quote','ignore']
    year,mon=map(int,month.split('-'))
    first=int(datetime(year,mon,1,tzinfo=timezone.utc).timestamp()*1000)
    expected=pd.Index(range(first,first+calendar.monthrange(year,mon)[1]*24*3600000,3600000))
    t=pd.to_numeric(df.open_time,errors='raise')
    end=pd.to_numeric(df.close_time,errors='raise')
    if len(df)!=len(expected) or not t.reset_index(drop=True).equals(pd.Series(expected)) or not (end.to_numpy()==t.to_numpy()+3599999).all():
        raise ValueError('official hourly calendar/close_time mismatch')
    out=pd.DataFrame({'open_time':pd.to_datetime(t,unit='ms',utc=True)})
    for field in FIELDS:out[field]=pd.to_numeric(df[field],errors='raise').astype(float)
    v=out[list(FIELDS)].to_numpy(float)
    if not np.isfinite(v).all() or (out['low']<=0).any() or (out['low']>out[['open','close']].min(axis=1)).any() or (out['high']<out[['open','close']].max(axis=1)).any() or (out[['volume','quote_volume']]<0).any().any():
        raise ValueError('official hourly OHLCV geometry invalid')
    return out


def run(get=download,root=ROOT):
    root=Path(root)
    result={'phase':803,'decision':'BLOCKED_OFFICIAL_TRAINING_OHLC',
            'vendor_origin_attested':False,'historical_pnl_computed':False,
            'validation_2025_read':False,'holdout_accessed':False,
            'external_benchmarks_used':False,'promotion_eligible':False,'assets':{}}
    try:
        if len(MONTHS)!=25 or MONTHS[-1]!='2024-12':raise ValueError('training calendar changed')
        staged={}
        for asset in ASSETS:
            frames=[];digests={}
            for month in MONTHS:
                filename=f'{asset}-1h-{month}.zip'
                url=f'{BASE}/{asset}/1h/{filename}'
                expected=checksum(get(url+'.CHECKSUM'),filename)
                raw=get(url)
                sha=hashlib.sha256(raw).hexdigest()
                if sha!=expected:raise ValueError('official kline ZIP checksum mismatch '+asset+'/'+month)
                frames.append(month_frame(raw,asset,month))
                digests[month]=sha
            joined=pd.concat(frames,ignore_index=True)
            if len(joined)!=18288:raise ValueError('training prefix hours mismatch '+asset)
            raw=joined.to_csv(index=False,float_format='%.12g').encode()
            pin,size=PINS[asset]
            if len(raw)!=size or hashlib.sha256(raw).hexdigest()!=pin:
                raise ValueError('immutable training prefix digest mismatch '+asset)
            staged[asset]=raw
            result['assets'][asset]={'monthly_archives':25,'hours':18288,'sha256':pin,
                'archive_digest_manifest_sha256':hashlib.sha256(json.dumps(digests,sort_keys=True).encode()).hexdigest()}
        out=root/'phase243_clean4_canonical';out.mkdir(parents=True,exist_ok=True)
        for asset,raw in staged.items():
            dest=out/f'{asset}_1h.csv'
            if dest.exists() and dest.read_bytes()!=raw:
                raise ValueError('existing pinned source differs: '+asset)
        for asset,raw in staged.items():
            dest=out/f'{asset}_1h.csv'
            if not dest.exists():dest.write_bytes(raw)
        result['decision']=PASS
        result['vendor_origin_attested']=True
    except Exception as exc:
        result['reason']=type(exc).__name__+': '+str(exc)[:350]
    (root/'phase803_official_training_ohlc_receipt.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return result

if __name__=='__main__':
    out=run()
    print(json.dumps({'decision':out['decision'],'reason':out.get('reason'),'assets':len(out['assets'])},sort_keys=True))
    raise SystemExit(0 if out['decision']==PASS else 2)
