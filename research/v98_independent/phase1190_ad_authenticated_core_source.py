#!/usr/bin/env python3
"""V98 AD official Clean-4 source-only core/router four-runner attestor.

Only V98 Phase803/1000 vendor provenance helpers; never AC signals or PnL.
"""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from phase1189_ad_online_core_router import ASSETS, START, online_core_router, observer_digest
from phase803_training_ohlc_official_replay import run as vendor_ohlc, PASS as OHLC_PASS, PINS
from phase1000_four_asset_source_policy import run as vendor_native, OUT as NATIVE_RECEIPT, BOUNDS

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'phase1190_ad_authenticated_core_source_receipt.json'
FIELDS = ('asset','funding_slot_ms','funding_time_ms','funding_rate',
          'mark_low','mark_high','conservative_mark')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def receipt_diagnostics(value):
    """Reporting-only stable decimal JSON; never alters model state or hashes."""
    if isinstance(value, float):
        return round(value, 10)
    if isinstance(value, list):
        return [receipt_diagnostics(x) for x in value]
    if isinstance(value, dict):
        return {k: receipt_diagnostics(v) for k, v in value.items()}
    return value


def source_frames():
    idx = pd.date_range(START, periods=18288, freq='h')
    frames = {}
    for asset in ASSETS:
        path = ROOT / 'phase243_clean4_canonical' / (asset + '_1h.csv')
        digest, size = PINS[asset]
        if path.stat().st_size != size or sha256(path) != digest:
            raise PermissionError('AD1190_OHLC_PIN_'+asset)
        frame = pd.read_csv(path)
        if (len(frame) != len(idx) or tuple(frame.columns) !=
                ('open_time','open','high','low','close','volume','quote_volume')):
            raise ValueError('AD1190_OHLC_SCHEMA_'+asset)
        if not pd.DatetimeIndex(pd.to_datetime(frame['open_time'],utc=True)).equals(idx):
            raise ValueError('AD1190_OHLC_CHRONOLOGY_'+asset)
        frames[asset] = frame
    data = {name:pd.DataFrame({asset:frames[asset][name].to_numpy(float)
                               for asset in ASSETS},index=idx)
            for name in ('open','high','low','close','quote_volume')}
    return idx, data


def parse_native(idx, path, strict=True):
    n=len(idx)
    rate=np.zeros((n,4),dtype=float)
    event=np.zeros((n,4),dtype=np.int8)
    first=int(idx[0].timestamp()*1000)
    with Path(path).open(newline='') as stream:
        reader=csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError('AD1190_NATIVE_SCHEMA')
        for row in reader:
            asset=row['asset']
            if asset not in ASSETS:
                raise ValueError('AD1190_NON_CLEAN4')
            j=ASSETS.index(asset)
            slot=int(row['funding_slot_ms'])
            timestamp=int(row['funding_time_ms'])
            if ((slot-first)%28_800_000 or slot<first or slot>int(idx[-1].timestamp()*1000)
                    or not slot<=timestamp<=slot+29):
                raise ValueError('AD1190_FUNDING_CLOCK')
            t=(slot-first)//3_600_000
            if event[t,j]:
                raise ValueError('AD1190_DUPLICATE_EVENT')
            f,low,high,mark=map(float,(row['funding_rate'],row['mark_low'],
                                       row['mark_high'],row['conservative_mark']))
            if (not np.isfinite([f,low,high,mark]).all() or low<=0 or high<low
                    or mark!=(high if f>=0 else low)):
                raise ValueError('AD1190_SIGNED_NATIVE_MARK')
            rate[t,j]=f
            event[t,j]=1
    if strict and (n!=18288 or int(event.sum())!=9144
                   or any(int(event[:,j].sum())!=2286 for j in range(4))):
        raise ValueError('AD1190_NATIVE_COVERAGE')
    return (pd.DataFrame(rate,index=idx,columns=ASSETS),
            pd.DataFrame(event,index=idx,columns=ASSETS))


def run():
    receipt={'phase':1190,'decision':'BLOCKED_BEFORE_AD_PNL',
             'source_only':True,'historical_system_pnl_computed':False,
             'validation_2025_read':False,'external_benchmarks_used':False,
             'promotion_eligible':False}
    try:
        o=vendor_ohlc()
        if (o.get('decision')!=OHLC_PASS or o.get('vendor_origin_attested') is not True
            or any(o.get('assets',{}).get(a,{}).get('sha256')!=PINS[a][0] for a in ASSETS)):
            raise PermissionError('AD1190_OFFICIAL_OHLC_FAILED')
        if vendor_native()!=0:
            raise PermissionError('AD1190_OFFICIAL_MARK_FUNDING_FAILED')
        r=json.loads(NATIVE_RECEIPT.read_text())
        if (r.get('decision')!='PASS_100_MARK_100_FUNDING_FOUR_FEB24_DAILY_GAPS_SOURCE_ONLY'
            or r.get('vendor_archive_checksum_attested') is not True
            or r.get('verified_asset_events')!=9144
            or r.get('validation_2025_read') is not False
            or r.get('bounds_csv_sha256')!=sha256(BOUNDS)):
            raise PermissionError('AD1190_NATIVE_PROVENANCE_FAILED')
        idx,data=source_frames()
        funding,event=parse_native(idx,BOUNDS)
        core,router,diag=online_core_router(data['open'],data['high'],data['low'],
            data['close'],data['quote_volume'],funding,event,diagnostics=True)
        receipt.update({'decision':'PASS_AD_AUTHENTICATED_CORE_ROUTER_SOURCE_ONLY_NOT_FROZEN',
            'official_hours':len(idx),'native_funding_events':int(event.to_numpy().sum()),
            'native_bounds_sha256':sha256(BOUNDS),
            'observer_sha256':observer_digest(core,router,idx),'diagnostics':receipt_diagnostics(diag)})
    except Exception as exc:
        receipt['reason']=type(exc).__name__+': '+str(exc)[:350]
    OUT.write_text(json.dumps(receipt,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:receipt.get(k) for k in ('decision','reason','official_hours',
          'native_funding_events','native_bounds_sha256','observer_sha256')},sort_keys=True))
    return 0 if receipt['decision'].startswith('PASS_') else 2


if __name__=='__main__':
    raise SystemExit(run())
