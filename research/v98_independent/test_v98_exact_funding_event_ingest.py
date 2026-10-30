#!/usr/bin/env python3
"""V98-only synthetic fixture contract test against authenticated 2022-24 data.
No real funding tick marks are invented, accepted or persisted.
"""
import argparse,hashlib,json,tempfile
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,ASSETS,START
from v98_mark_envelope_settlement import read_envelope
from v98_exact_funding_event_ingest import read_exact_funding_marks

def dump(path,rows):
    raw=json.dumps(rows,separators=(',',':')).encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()

def run(root,envelope):
    d=load(root)
    lo,hi,_=read_envelope(envelope,d)
    first=int(START.timestamp()*1000)
    with tempfile.TemporaryDirectory() as folder:
        rootp=Path(folder)
        meta={}
        rows={}
        for j,symbol in enumerate(ASSETS):
            rows[symbol]=[{'symbol':symbol,'fundingTime':first+int(t)*3600000,
                'fundingRate':format(float(d['rate'][t,j]),'.16g'),
                'markPrice':format(float(d['mark'][t,j]),'.16g')}
                for t in np.flatnonzero(d['event'][:,j])]
            name=symbol+'.json'
            sha=dump(rootp/name,rows[symbol])
            meta[symbol]={'path':name,'sha256':sha,
                'source_url':'https://fapi.binance.com/fapi/v1/fundingRate?symbol='+symbol}
        manifest={'scope':'V98_CLEAN4_2022_2024_TRAINING_ONLY','assets':meta}
        mp=rootp/'manifest.json'
        mp.write_text(json.dumps(manifest))
        exact,out=read_exact_funding_marks(mp,d,envelope)
        if out['events']!=9144 or not np.array_equal(exact[d['event']],d['mark'][d['event']]):
            raise ValueError('V98_EXACT_SYNTHETIC_FIXTURE_MISMATCH')
        # Tamper with a native rate, but update digest: semantic gate must catch.
        symbol=ASSETS[0]
        rows[symbol][0]['fundingRate']=str(float(rows[symbol][0]['fundingRate'])+.001)
        meta[symbol]['sha256']=dump(rootp/(symbol+'.json'),rows[symbol])
        mp.write_text(json.dumps(manifest))
        try:read_exact_funding_marks(mp,d,envelope)
        except ValueError as e:
            if 'NATIVE_RATE_MISMATCH' not in str(e):raise
        else:raise AssertionError('V98_EXACT_RATE_TAMPER_UNDETECTED')
        # Restore rate; tamper mark outside authenticated envelope.
        rows[symbol][0]['fundingRate']=format(float(d['rate'][0,0]),'.16g')
        rows[symbol][0]['markPrice']=str(float(hi[0,0])*2)
        meta[symbol]['sha256']=dump(rootp/(symbol+'.json'),rows[symbol])
        mp.write_text(json.dumps(manifest))
        try:read_exact_funding_marks(mp,d,envelope)
        except ValueError as e:
            if 'MARK_OUTSIDE_PINNED' not in str(e):raise
        else:raise AssertionError('V98_EXACT_MARK_TAMPER_UNDETECTED')
        return {'decision':'PASS_SYNTHETIC_IMPORT_CONTRACT_NOT_REAL_EXACT_FUNDING',
                'synthetic_events':9144,'rate_tamper_detected':True,
                'mark_tamper_detected':True,'official_tick_source_provenance_attested':False,
                '2025_validation_accessed':False,'future_holdout_accessed':False,
                'pnl_computed':False}
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True);p.add_argument('--envelope-csv',required=True)
    a=p.parse_args()
    print(json.dumps(run(a.root,a.envelope_csv),indent=2,sort_keys=True))
