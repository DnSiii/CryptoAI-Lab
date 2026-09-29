#!/usr/bin/env python3
"""Phase182 BTC/ETH pair integrity gate. DATA-only; no PnL logic."""
import argparse, csv, hashlib, json
from datetime import datetime, timezone
from pathlib import Path

CUTOFF=datetime(2024,1,18,tzinfo=timezone.utc)
REQ=('timestamp','open','high','low','close','volume')

def ts(s):
    d=datetime.fromisoformat(s.replace('Z','+00:00'))
    if d.tzinfo is None: raise ValueError('naive timestamp')
    return d.astimezone(timezone.utc)

def digest(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def load(path):
    with open(path,newline='',encoding='utf-8') as f:
        rd=csv.DictReader(f)
        if not rd.fieldnames or any(x not in rd.fieldnames for x in REQ): raise ValueError('missing required columns')
        out=[]
        for r in rd:
            vals=[float(r[x]) for x in ('open','high','low','close','volume')]
            out.append((ts(r['timestamp']),*vals))
    return out

def gate(btc_path,eth_path):
    errors=[]; b=load(btc_path); e=load(eth_path)
    for name,rows in [('BTC',b),('ETH',e)]:
        times=[r[0] for r in rows]
        if not rows: errors.append(f'{name} empty')
        if len(times)!=len(set(times)): errors.append(f'{name} duplicate timestamp')
        if times!=sorted(times): errors.append(f'{name} non-chronological')
        if any(t>=CUTOFF for t in times): errors.append(f'{name} holdout firewall')
        for r in rows:
            _,o,h,l,c,v=r
            if min(o,h,l,c)<=0 or v<0 or h<max(o,c,l) or l>min(o,c,h): errors.append(f'{name} invalid OHLCV')
    bt={r[0] for r in b}; et={r[0] for r in e}; common=bt&et
    if bt!=et:
        errors.append(f'timestamp mismatch btc_only={len(bt-et)} eth_only={len(et-bt)}')
    return {'status':'PASS' if not errors else 'FAIL','btc_sha256':digest(btc_path),'eth_sha256':digest(eth_path),'btc_rows':len(b),'eth_rows':len(e),'intersection_rows':len(common),'errors':sorted(set(errors)),'alignment':'exact intersection only; no forward fill','causality':'feature builder must shift all inputs by t-1'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('btc'); ap.add_argument('eth'); ap.add_argument('--out',default='phase182_pair_gate.json'); a=ap.parse_args()
    out=gate(a.btc,a.eth); Path(a.out).write_text(json.dumps(out,sort_keys=True,indent=2)+'\n'); print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out['status']=='PASS' else 2)
if __name__=='__main__': main()
