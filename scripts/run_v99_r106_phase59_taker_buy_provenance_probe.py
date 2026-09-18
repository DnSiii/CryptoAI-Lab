from __future__ import annotations
import csv, hashlib, io, json, urllib.request, zipfile
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[1]
OUT=PROJECT/'reports'/'candidate_v99_r106_phase59_taker_buy_provenance_probe.json'
BASE='https://data.binance.vision/data/futures/um/monthly/klines'
SCHEMA=['open_time','open','high','low','close','volume','close_time','quote_volume','trades','taker_buy_base_volume','taker_buy_quote_volume','ignore']
# Deterministic sentinels chosen before seeing any taker-buy values: two liquid anchors,
# early/middle/late non-holdout-era archive months. This phase never evaluates returns.
SENTINELS=[(s,m) for s in ('BTCUSDT','ETHUSDT') for m in ('2020-06','2023-01','2025-01')]

def get(url:str)->bytes:
    req=urllib.request.Request(url,headers={'User-Agent':'CryptoAI-research-v99-r106/59'})
    with urllib.request.urlopen(req,timeout=60) as r: return r.read()

def audit(symbol:str,month:str)->dict:
    stem=f'{symbol}-1h-{month}.zip'; url=f'{BASE}/{symbol}/1h/{stem}'
    raw=get(url); checksum=get(url+'.CHECKSUM').decode().split()[0]
    actual=hashlib.sha256(raw).hexdigest()
    if actual!=checksum: raise RuntimeError(f'checksum mismatch {stem}')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        bad=z.testzip()
        if bad is not None: raise RuntimeError(f'CRC failure {stem}: {bad}')
        names=z.namelist()
        if len(names)!=1: raise RuntimeError(f'unexpected members {stem}: {names}')
        rows=list(csv.reader(io.TextIOWrapper(z.open(names[0]),encoding='utf-8')))
    # Binance archives may include a header in newer files. Normalize without inferring fields.
    if rows and rows[0] and rows[0][0] in ('open_time','open_time_ms'): rows=rows[1:]
    if not rows or any(len(r)<12 for r in rows): raise RuntimeError(f'bad schema {stem}')
    numeric=[]
    for r in rows:
        ot=int(r[0]); vol=float(r[5]); ct=int(r[6]); qv=float(r[7]); tb=float(r[9]); tbq=float(r[10])
        if not (0<=tb<=vol+1e-12 and 0<=tbq<=qv+1e-9): raise RuntimeError(f'volume invariant {stem}@{ot}')
        numeric.append((ot,ct))
    opens=[x[0] for x in numeric]
    if len(opens)!=len(set(opens)) or opens!=sorted(opens): raise RuntimeError(f'timestamp uniqueness/order {stem}')
    gaps=[b-a for a,b in zip(opens,opens[1:]) if b-a!=3_600_000]
    return {'symbol':symbol,'month':month,'url':url,'sha256':actual,'rows':len(rows),'first_open_time':opens[0],'last_open_time':opens[-1],
            'hourly_gap_count':len(gaps),'taker_buy_fields_present':True,'checksum_pass':True,'zip_crc_pass':True,'volume_invariants_pass':True}

def main():
    results=[audit(s,m) for s,m in SENTINELS]
    out={'study':'V99 R106 phase 59 — exchange-native taker-buy provenance/schema probe','status':'PROVENANCE_PROBE_PASS',
         'frozen_assets_untouched':{'v16':True,'v99_frozen':True},
         'precommitment':{'data_integrity_only':True,'no_returns':True,'no_direction_choice':True,'no_parameter_search':True,'no_holdout_inspection':True,'no_ohlcv_proxy':True},
         'sentinel_rule':'BTCUSDT/ETHUSDT x 2020-06, 2023-01, 2025-01 fixed before inspecting taker-buy values',
         'results':results,'all_pass':all(r['checksum_pass'] and r['zip_crc_pass'] and r['taker_buy_fields_present'] and r['volume_invariants_pass'] for r in results),
         'next_gate':'build full train/validation-only coverage manifest for the PIT48 universe; do not evaluate alpha until coverage/integrity gate passes',
         'disclosure':'This probe establishes source/schema/provenance only. It does not create or evaluate a candidate.'}
    OUT.parent.mkdir(exist_ok=True); OUT.write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))
if __name__=='__main__': main()
