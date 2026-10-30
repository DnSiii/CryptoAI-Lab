#!/usr/bin/env python3
"""V98 Independent: pinned branch-byte identity, NOT Binance vendor attestation.

No trading signals, PnL, optimization, XRP, external engines, or holdout.
Fails closed on any missing or modified branch-native source byte.
"""
from __future__ import annotations
import csv
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path

ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
ROOT=Path(__file__).resolve().parent
PREREG_SHA='c8a57f38d1d91fc0806f506f19f556c86718771b9c3c0f05e284051e45a82aac'
PREREG_GIT_BLOB='6d0e57235f03c3ee032feba7a3a3e790720626af'
PREREG_COMMIT='725937a2990c34b9c5e25cd3d024b721153a8afd'
MANIFEST_SHA='14899951e71821a11ee8443f597dfe4aff30351c71cae309a351e971f1062833'
NATIVE_SHA={
 'BTCUSDT':'10839ac3f83a2d5dd92bb2bdf17a6de00ebad0def6f81358c9bd557a58342e47',
 'ETHUSDT':'29033fb7d429696172d964042d6cdf3be784d0e81c0d50c7cb914a9757eeea51',
 'BNBUSDT':'229c8eeaef1b0b0dd34d78aeb8584ea471b360344bc3c1e0f4158f3cf06f5484',
 'SOLUSDT':'86430b3443ae1980e00a181c3d2f8dd47ddede05b8c4b4b86052696594626c06',
}
START=1669852800000  # 2022-12-01 UTC inclusive
CUT=1767225600000    # 2026-01-01 UTC exclusive
STEP=28800000         # 8h; fundingTime jitter 0..29ms
EXPECTED=(CUT-START)//STEP


def _sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


def _native_calendar(raw:bytes,asset:str)->dict:
    rd=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    if rd.fieldnames!=['fundingTime_ms','fundingTime_utc','fundingRate','fundingIntervalHours']:
        raise ValueError(f'{asset}: funding schema drift')
    slots=set();zeros=0;previous=-1;total=0
    for row in rd:
        total+=1
        ms=int(row['fundingTime_ms'])
        if ms>=CUT:
            raise ValueError(f'{asset}: 2026+ funding row forbidden')
        if ms<=previous:
            raise ValueError(f'{asset}: unsorted/duplicate funding timestamp')
        previous=ms
        if ms<START:
            continue
        slot=(ms//STEP)*STEP
        if ms-slot>29 or slot in slots:
            raise ValueError(f'{asset}: duplicate/off-slot funding event')
        interval=Decimal(row['fundingIntervalHours'])
        rate=Decimal(row['fundingRate'])
        if interval!=8 or not rate.is_finite():
            raise ValueError(f'{asset}: invalid rate/interval')
        slots.add(slot)
        zeros+=int(rate==0)
    if slots!=set(range(START,CUT,STEP)) or len(slots)!=EXPECTED:
        raise ValueError(f'{asset}: incomplete Clean-4 funding calendar')
    return {'training_events':len(slots),'training_zero_events':zeros,'full_rows':total}


def audit(root:Path=ROOT)->dict:
    pre=(root/'phase460_bipower_jump_diffusion_prereg.md').read_bytes()
    if _sha(pre)!=PREREG_SHA:
        raise ValueError('Phase460 immutable prereg SHA256 mismatch')
    blob=hashlib.sha1(b'blob '+str(len(pre)).encode()+b'\0'+pre).hexdigest()
    if blob!=PREREG_GIT_BLOB:
        raise ValueError('Phase460 remote prereg Git blob mismatch')
    native_root=root/'data'/'phase206_funding'
    manifest_raw=(native_root/'manifest.json').read_bytes()
    if _sha(manifest_raw)!=MANIFEST_SHA:
        raise ValueError('pinned funding manifest drift')
    manifest=json.loads(manifest_raw)
    result={}
    for asset in ASSETS:
        raw=(native_root/f'{asset}_funding.csv').read_bytes()
        if _sha(raw)!=NATIVE_SHA[asset] or _sha(raw)!=manifest['symbols'][asset]['canonical_csv_sha256']:
            raise ValueError(f'{asset}: branch-native funding SHA256 mismatch')
        result[asset]=_native_calendar(raw,asset)
    return {'engine':'V98 Independent','phase':581,
            'decision':'PASS_BRANCH_BYTES_VENDOR_ORIGIN_UNATTESTED',
            'prereg_commit':PREREG_COMMIT,'prereg_git_blob':blob,
            'assets':result,'vendor_origin_attested':False,
            'bnb_vendor_zero_conflict_resolved':False,
            'historical_pnl_computed':False,'promotion_eligible':False,
            'holdout_accessed':False,'xrp_used':False}


def main():
    try:result=audit()
    except (OSError,ValueError,KeyError,UnicodeError) as exc:
        result={'engine':'V98 Independent','phase':581,
                'decision':'BLOCKED_BRANCH_NATIVE_SOURCE_LOCK',
                'reason':f'{type(exc).__name__}: {str(exc)[:220]}',
                'vendor_origin_attested':False,'historical_pnl_computed':False,
                'promotion_eligible':False,'holdout_accessed':False}
    print(json.dumps(result,sort_keys=True,allow_nan=False))
    if result['decision']!='PASS_BRANCH_BYTES_VENDOR_ORIGIN_UNATTESTED':
        raise SystemExit(2)

if __name__=='__main__':main()
