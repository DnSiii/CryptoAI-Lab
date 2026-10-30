#!/usr/bin/env python3
"""AD four-runner authenticated static source hashes; no NAV/PnL feedback."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
from phase1189_ad_online_core_router import ASSETS,online_core_router
from phase1191_ad_funding_event_opportunity import opportunity_intents
from phase1192_ad_covariance_neutral_rv import relative_value_intents
from phase1190_ad_authenticated_core_source import (
    run as vendor_attest,source_frames,parse_native,BOUNDS,OUT as CORE_RECEIPT,sha256)

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'phase1199_ad_static_source_receipt.json'
PATHS=('AD_core_only','AD_full','AD_minus_opportunity',
       'AD_minus_relative_value','AD_minus_stress')
MODES=('immediate','capacity_1m','capacity_10m')


def static_hash(index,core,router,opp,rv,path,mode):
    if path not in PATHS or mode not in MODES:
        raise ValueError('AD1199_PATH_MODE')
    n=len(index)
    if (core.shape!=(n,4) or router.shape!=(n,3) or
            opp.shape!=(n,4) or rv.shape!=(n,4)):
        raise ValueError('AD1199_SHAPE')
    o=opp.astype(float).copy()
    v=rv.astype(float).copy()
    if path in ('AD_core_only','AD_minus_opportunity'):o[:]=0
    if path in ('AD_core_only','AD_minus_relative_value'):v[:]=0
    payload=np.column_stack((core,router,o,v))
    if not np.isfinite(payload).all():
        raise ValueError('AD1199_NONFINITE')
    quant=np.rint(payload*1_000_000).astype('<i8')
    header=('AD1199_STATIC_SOURCE_V1|'+path+'|'+mode+'|'+str(n)+'|'+
            ','.join(ASSETS)+'\n').encode('ascii')
    time=index.tz_convert('UTC').asi8.astype('<i8').tobytes()
    return hashlib.sha256(header+time+quant.tobytes()).hexdigest()


def run():
    receipt={'phase':1199,'decision':'BLOCKED_BEFORE_AD_SYSTEM_PNL',
             'source_only':True,'historical_system_pnl_computed':False,
             'validation_2025_read':False,'external_benchmarks_used':False,
             'promotion_eligible':False,'nav_feedback_hashed':False}
    try:
        if vendor_attest()!=0:
            raise PermissionError('AD1199_VENDOR_ATTESTATION')
        core_receipt=json.loads(CORE_RECEIPT.read_text())
        if core_receipt.get('decision')!='PASS_AD_AUTHENTICATED_CORE_ROUTER_SOURCE_ONLY_NOT_FROZEN':
            raise PermissionError('AD1199_CORE_RECEIPT')
        idx,data=source_frames()
        funding,event=parse_native(idx,BOUNDS)
        frames=(data['open'],data['high'],data['low'],data['close'],
                data['quote_volume'],funding,event)
        core,router=online_core_router(*frames)
        opp=opportunity_intents(*frames)
        rv=relative_value_intents(*frames)
        hashes={path+'__'+mode:static_hash(idx,core,router,opp,rv,path,mode)
                for path in PATHS for mode in MODES}
        if len(hashes)!=15 or len(set(hashes.values()))!=15:
            raise ValueError('AD1199_HASH_GEOMETRY')
        receipt.update({'decision':'PASS_AD_15_STATIC_SOURCE_HASHES_NOT_FULL_FREEZE',
            'official_hours':len(idx),'native_funding_events':int(event.to_numpy().sum()),
            'native_bounds_sha256':sha256(BOUNDS),
            'core_router_observer_sha256':core_receipt['observer_sha256'],
            'static_hashes':dict(sorted(hashes.items())),
            'opportunity_active_asset_hours':int(np.count_nonzero(opp)),
            'rv_active_hours':int(np.any(rv!=0,axis=1).sum())})
    except Exception as exc:
        receipt['reason']=type(exc).__name__+': '+str(exc)[:350]
    OUT.write_text(json.dumps(receipt,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:receipt.get(k) for k in ('decision','reason','official_hours',
          'native_funding_events','native_bounds_sha256','static_hashes')},sort_keys=True))
    return 0 if receipt['decision'].startswith('PASS_') else 2


if __name__=='__main__':raise SystemExit(run())
