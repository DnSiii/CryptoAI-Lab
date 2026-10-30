#!/usr/bin/env python3
"""V98 NH sealed 2025 ONLY official Clean-4 source acquisition, no signals/PnL/benchmarks.
Run ONLY after frozen NH training candidate; vendor SHA checks on every archive.
"""
from __future__ import annotations
import calendar,csv,hashlib,io,json,time,urllib.request,zipfile
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pandas as pd

ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
MONTHS=tuple(f'2025-{m:02d}' for m in range(1,13))
BASE='https://data.binance.vision/data/futures/um'
START=int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp()*1000)
END=int(datetime(2026,1,1,tzinfo=timezone.utc).timestamp()*1000)
STEP=3600000
EVENT_STEP=8*STEP
HOURS=8760
EVENTS=1095
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'v98_nh_2025_official_source'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def download(url):
    if not url.startswith(BASE+'/') or not (url.endswith('.zip') or url.endswith('.zip.CHECKSUM')):
        raise ValueError('NH_2025_FORBIDDEN_SOURCE')
    err=None
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'V98-NH-2025-Sealed-Official-Source/1.0'})
            with urllib.request.urlopen(req,timeout=60) as resp:
                if resp.status!=200 or resp.geturl()!=url:raise ValueError('NH_2025_VENDOR_REDIRECT')
                raw=resp.read(15000001)
            if len(raw)>15000000:raise ValueError('NH_2025_ARCHIVE_TOO_LARGE')
            return raw
        except (OSError,TimeoutError) as exc:
            err=exc
            if attempt<2:time.sleep(2**attempt)
    raise RuntimeError('NH_2025_VENDOR_TRANSPORT_'+str(err))

def verified(kind,asset,period,daily=False):
    if kind not in ('klines','fundingRate','markPriceKlines') or asset not in ASSETS:
        raise ValueError('NH_2025_VENDOR_KIND')
    if not (period in MONTHS or (daily and period.startswith('2025-'))):
        raise ValueError('NH_2025_PERIOD')
    if kind=='fundingRate':
        name=f'{asset}-fundingRate-{period}.zip'
        url=f'{BASE}/{"daily" if daily else "monthly"}/fundingRate/{asset}/{name}'
    else:
        name=f'{asset}-1h-{period}.zip'
        url=f'{BASE}/{"daily" if daily else "monthly"}/{kind}/{asset}/1h/{name}'
    declaration=download(url+'.CHECKSUM').decode('utf-8-sig').strip().split()
    if len(declaration)!=2 or declaration[1].lstrip('*./')!=name or len(declaration[0])!=64:
        raise ValueError('NH_2025_VENDOR_CHECKSUM_SCHEMA_'+name)
    raw=download(url);digest=sha(raw)
    if digest!=declaration[0].lower():raise ValueError('NH_2025_VENDOR_SHA_MISMATCH_'+name)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.namelist()!=[name[:-4]+'.csv']:
            raise ValueError('NH_2025_VENDOR_ZIP_MEMBER_'+name)
        data=z.read(z.namelist()[0])
    return data,digest

def month_hours(month):
    y,m=map(int,month.split('-'))
    start=int(datetime(y,m,1,tzinfo=timezone.utc).timestamp()*1000)
    return list(range(start,start+calendar.monthrange(y,m)[1]*24*STEP,STEP))

def parse_ohlc(raw,month,asset,kind):
    df=pd.read_csv(io.BytesIO(raw),dtype=str,keep_default_na=False)
    if len(df.columns)!=12 or str(df.columns[0]).strip().lower()!='open_time':
        raise ValueError('NH_2025_OHLC_HEADER_'+kind+'_'+asset+'_'+month)
    df.columns=['open_time','open','high','low','close','volume','close_time',
                'quote_volume','trade_count','taker_buy_base','taker_buy_quote','ignore']
    stamps=pd.to_numeric(df['open_time'],errors='raise').to_numpy(np.int64)
    closes=pd.to_numeric(df['close_time'],errors='raise').to_numpy(np.int64)
    expected=np.array(month_hours(month),dtype=np.int64)
    if len(stamps)!=len(expected) or not np.array_equal(stamps,expected) or not np.array_equal(closes,stamps+STEP-1):
        raise ValueError('NH_2025_OHLC_CALENDAR_'+kind+'_'+asset+'_'+month)
    price=df[['open','high','low','close']].to_numpy(float)
    if not np.isfinite(price).all() or np.any(price<=0) or np.any(price[:,2]>np.minimum(price[:,0],price[:,3])) or np.any(price[:,1]<np.maximum(price[:,0],price[:,3])):
        raise ValueError('NH_2025_OHLC_GEOMETRY_'+kind+'_'+asset+'_'+month)
    if kind=='klines':
        q=pd.to_numeric(df['quote_volume'],errors='raise').to_numpy(float)
        if not np.isfinite(q).all() or np.any(q<0):raise ValueError('NH_2025_QUOTE_VOLUME')
        return [(int(ts),*map(float,row),float(v)) for ts,row,v in zip(stamps,price,q)]
    return [(int(ts),*map(float,row)) for ts,row in zip(stamps,price)]

def parse_funding(raw,asset,period):
    reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    if not {'calc_time','funding_interval_hours','last_funding_rate'}.issubset(reader.fieldnames or []):
        raise ValueError('NH_2025_FUNDING_HEADER_'+asset+'_'+period)
    out={}
    for row in reader:
        ms=int(row['calc_time']);rate=float(row['last_funding_rate'])
        interval=float(row['funding_interval_hours'])
        slot=int(round(ms/EVENT_STEP))*EVENT_STEP
        if abs(ms-slot)>60000 or slot in out or not np.isfinite([rate,interval]).all() or interval!=8.:
            raise ValueError('NH_2025_FUNDING_INTERVAL_OR_SLOT_'+asset+'_'+period)
        out[slot]=(rate,ms-slot)
    if not out:raise ValueError('NH_2025_FUNDING_EMPTY_'+asset+'_'+period)
    return out

def run():
    receipt={'decision':'BLOCKED_NH_2025_OFFICIAL_SOURCE','source_only':True,
             '2025_independent_validation_data':True,'pnl_computed':False,
             '2026_holdout_accessed':False,'xrp_accessed':False,'benchmark_accessed':False,
             'frozen_training_commit':'a9a2454282c2f97d92a1a58cbcfe305945306ab4',
             'exact_funding_tick_mark_attested':False,'assets':{}}
    OUT.mkdir(parents=True,exist_ok=True)
    try:
        for asset in ASSETS:
            candles=[];marks={};funding={};digests={}
            for month in MONTHS:
                print('NH_2025_VENDOR_FETCH',asset,month,flush=True)
                k,ksha=verified('klines',asset,month)
                m,msha=verified('markPriceKlines',asset,month)
                f,fsha=verified('fundingRate',asset,month)
                candles.extend(parse_ohlc(k,month,asset,'klines'))
                marks.update({x[0]:x[1:] for x in parse_ohlc(m,month,asset,'markPriceKlines')})
                funding.update(parse_funding(f,asset,month))
                digests[month]={'klines':ksha,'markPriceKlines':msha,'fundingRate':fsha}
            if len(candles)!=HOURS or [x[0] for x in candles]!=list(range(START,END,STEP)):
                raise ValueError('NH_2025_ASSET_HOUR_COVERAGE_'+asset)
            expected=list(range(START,END,EVENT_STEP))
            if sorted(funding)!=expected or len(funding)!=EVENTS:
                raise ValueError('NH_2025_FUNDING_CALENDAR_'+asset+'_'+str((len(funding),EVENTS)))
            if sorted(marks)!=list(range(START,END,STEP)):
                raise ValueError('NH_2025_MARK_CALENDAR_'+asset)
            with (OUT/(asset+'_1h_2025.csv')).open('w',newline='') as fh:
                w=csv.writer(fh,lineterminator='\n')
                w.writerow(['open_time_ms','open','high','low','close','quote_volume'])
                for row in candles:w.writerow([row[0]]+[format(v,'.12g') for v in row[1:5]]+[format(row[5],'.12g')])
            with (OUT/(asset+'_funding_2025.csv')).open('w',newline='') as fh:
                w=csv.writer(fh,lineterminator='\n');w.writerow(['funding_slot_ms','funding_rate','exchange_offset_ms','mark_lower_bound','mark_upper_bound'])
                for slot in expected:
                    prev=marks.get(slot-STEP)
                    current=marks[slot]
                    lower=min(current[2],prev[2]) if prev is not None else current[2]
                    upper=max(current[1],prev[1]) if prev is not None else current[1]
                    rate,offset=funding[slot]
                    w.writerow([slot,format(rate,'.12g'),offset,format(lower,'.12g'),format(upper,'.12g')])
            receipt['assets'][asset]={
                'hours':HOURS,'funding_events':EVENTS,'official_monthly_archives':36,
                'monthly_archive_digest_manifest_sha256':sha(json.dumps(digests,sort_keys=True).encode()),
                'ohlc_csv_sha256':sha((OUT/(asset+'_1h_2025.csv')).read_bytes()),
                'funding_envelope_csv_sha256':sha((OUT/(asset+'_funding_2025.csv')).read_bytes()),
                'max_abs_funding_calc_time_offset_ms':max(abs(v[1]) for v in funding.values())}
        receipt['decision']='PASS_NH_2025_OFFICIAL_SOURCE_ONLY_NOT_VALIDATION'
        receipt['vendor_sha_verified']=True
        receipt['official_archives_verified']=144
        receipt['hourly_rows_verified']=HOURS*4
        receipt['funding_events_verified']=EVENTS*4
    except Exception as exc:
        receipt['reason']=type(exc).__name__+': '+str(exc)[:400]
    (OUT/'nh_2025_official_source_receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'decision':receipt['decision'],'reason':receipt.get('reason'),
        'assets_completed':len(receipt['assets'])},sort_keys=True),flush=True)
    return receipt
if __name__=='__main__':
    result=run()
    raise SystemExit(0 if result['decision']=='PASS_NH_2025_OFFICIAL_SOURCE_ONLY_NOT_VALIDATION' else 2)
