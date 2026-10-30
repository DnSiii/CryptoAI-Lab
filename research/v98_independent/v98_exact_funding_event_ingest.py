#!/usr/bin/env python3
"""V98-only strict exact funding-tick import contract. NO implicit proxy or live PnL.

Official Binance USD-M fundingRate JSON must be separately retrieved and attested
with immutable per-symbol SHA256. This module cannot create missing historical data.
"""
import argparse,hashlib,json,math
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,ASSETS,START,HOURS
from v98_mark_envelope_settlement import read_envelope,worst_funding

FIRST_MS=int(START.timestamp()*1000)
INTERVAL_MS=8*3600*1000
EXPECTED_PER_ASSET=HOURS//8
EXPECTED_TOTAL=EXPECTED_PER_ASSET*len(ASSETS)
OFFICIAL_PREFIX='https://fapi.binance.com/fapi/v1/fundingRate'

def _digest(data):
    return hashlib.sha256(data).hexdigest()

def validate_rows(rows,symbol,d,lo,hi):
    """Reject missing, duplicate, non-8h, wrong-rate or out-of-envelope marks."""
    j=ASSETS.index(symbol)
    if not isinstance(rows,list) or len(rows)!=EXPECTED_PER_ASSET:
        raise ValueError('V98_EXACT_EVENT_COUNT_'+symbol)
    seen=set()
    marks=np.zeros(HOURS,dtype=float)
    for row in rows:
        if not isinstance(row,dict) or row.get('symbol')!=symbol:
            raise ValueError('V98_EXACT_SYMBOL')
        if not all(k in row for k in ('fundingTime','fundingRate','markPrice')):
            raise ValueError('V98_EXACT_MISSING_FIELDS')
        try:
            timestamp=int(row['fundingTime'])
            rate=float(row['fundingRate'])
            mark=float(row['markPrice'])
        except (TypeError,ValueError,OverflowError):
            raise ValueError('V98_EXACT_INVALID_VALUES')
        if not math.isfinite(rate) or not math.isfinite(mark) or mark<=0:
            raise ValueError('V98_EXACT_NONFINITE_OR_NEGATIVE')
        offset=timestamp-FIRST_MS
        if offset<0:
            raise ValueError('V98_EXACT_OUT_OF_TRAINING_OR_OFF_CALENDAR')
        slot=offset//INTERVAL_MS
        lag_ms=offset-slot*INTERVAL_MS
        t=slot*8
        # Native archive calc_time can lag the settlement boundary by milliseconds.
        # Preserve that evidence; never shift a row into a different 8h slot.
        if lag_ms>60000 or t>=HOURS:
            raise ValueError('V98_EXACT_OUT_OF_TRAINING_OR_OFF_CALENDAR')
        if t in seen or not bool(d['event'][t,j]):
            raise ValueError('V98_EXACT_DUPLICATE_OR_NOT_EVENT')
        if not math.isclose(rate,float(d['rate'][t,j]),rel_tol=0,abs_tol=1e-11):
            raise ValueError('V98_EXACT_NATIVE_RATE_MISMATCH_'+symbol+'_'+str(t))
        if not lo[t,j]-1e-7<=mark<=hi[t,j]+1e-7:
            raise ValueError('V98_EXACT_MARK_OUTSIDE_PINNED_OFFICIAL_ENVELOPE_'+symbol+'_'+str(t))
        seen.add(t)
        marks[t]=mark
    expected=set(np.flatnonzero(d['event'][:,j]))
    if seen!=expected:raise ValueError('V98_EXACT_MISSING_OR_EXTRA_EVENT_'+symbol)
    return marks

def read_exact_funding_marks(manifest_path,d,envelope_path):
    """Only accepts four independently SHA-pinned official event JSON payloads."""
    manifest_file=Path(manifest_path).resolve()
    raw_manifest=manifest_file.read_bytes()
    manifest=json.loads(raw_manifest)
    if manifest.get('scope')!='V98_CLEAN4_2022_2024_TRAINING_ONLY':
        raise ValueError('V98_EXACT_SCOPE')
    files=manifest.get('assets')
    if not isinstance(files,dict) or set(files)!=set(ASSETS):
        raise ValueError('V98_EXACT_ASSET_SET')
    lo,hi,envelope_sha=read_envelope(envelope_path,d)
    exact=d['mark'].copy()
    receipt={}
    for j,symbol in enumerate(ASSETS):
        meta=files[symbol]
        if not isinstance(meta,dict) or set(('path','sha256','source_url'))-set(meta):
            raise ValueError('V98_EXACT_MANIFEST_FIELDS')
        # A URL assertion is not proof of origin: transport logs and artifact
        # attestation are required separately before "official" acceptance.
        if not str(meta['source_url']).startswith(OFFICIAL_PREFIX+'?'):
            raise ValueError('V98_EXACT_NOT_OFFICIAL_ENDPOINT_CLAIM')
        p=(manifest_file.parent/meta['path']).resolve()
        if not p.is_relative_to(manifest_file.parent):
            raise ValueError('V98_EXACT_PATH_ESCAPE')
        raw=p.read_bytes()
        sha=_digest(raw)
        if sha!=meta['sha256']:raise ValueError('V98_EXACT_SHA_MISMATCH_'+symbol)
        parsed=json.loads(raw)
        marks=validate_rows(parsed,symbol,d,lo,hi)
        offsets=[(int(row['fundingTime'])-FIRST_MS)%INTERVAL_MS for row in parsed]
        exact[d['event'][:,j],j]=marks[d['event'][:,j]]
        receipt[symbol]={'sha256':sha,'events':int(d['event'][:,j].sum()),
                         'nonzero_timestamp_offsets':sum(x>0 for x in offsets),
                         'max_timestamp_offset_ms':max(offsets),
                         'mark_min':float(np.min(marks[d['event'][:,j]])),
                         'mark_max':float(np.max(marks[d['event'][:,j]]))}
    if int(d['event'].sum())!=EXPECTED_TOTAL:
        raise ValueError('V98_EXACT_TOTAL_EVENT_COUNT')
    return exact,{'decision':'PASS_STRICT_EXACT_EVENT_CONTENT_CONTRACT_PROVENANCE_STILL_REQUIRED',
                  'events':EXPECTED_TOTAL,'per_symbol':receipt,
                  'manifest_sha256':_digest(raw_manifest),'envelope_sha256':envelope_sha,
                  'source_urls_are_not_transport_attestation':True,
                  '2025_validation_accessed':False,'future_holdout_accessed':False,
                  'economic_pnl_computed':False,'live_authorized':False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True)
    p.add_argument('--envelope-csv',required=True)
    p.add_argument('--manifest',required=True)
    p.add_argument('--receipt',required=True)
    a=p.parse_args()
    d=load(a.root)
    exact,out=read_exact_funding_marks(a.manifest,d,a.envelope_csv)
    # The exact mark must lie inside the pre-existing worst-side envelope for
    # either funding settlement ordering and arbitrary signed positions.
    lo,hi,_=read_envelope(a.envelope_csv,d)
    for t in np.flatnonzero(d['event'][:,0]):
        for direction in (-1.,1.):
            pos=np.full(4,direction)
            for order in ('carried_before_fill','new_after_fill'):
                worst=worst_funding(pos,pos,d['rate'][t],d['event'][t],lo[t],hi[t],order)
                exact_cash=worst_funding(pos,pos,d['rate'][t],d['event'][t],exact[t],exact[t],order)
                if worst>exact_cash+1e-7:raise ValueError('V98_EXACT_NOT_BOUNDED_BY_CONSERVATIVE_ENVELOPE')
    Path(a.receipt).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
