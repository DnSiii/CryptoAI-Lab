#!/usr/bin/env python3
"""Deterministic Phase180 feature builder. TRAIN-only, no PnL logic.

Causality invariant: row h contains features computed only from inter-block deltas
whose newest endpoint is h-1.  The current block timestamp is never part of its
own feature vector; this makes the required one-block (t-1) lag structural rather
than a downstream convention.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,statistics
from pathlib import Path

WINDOWS=(6,36,144)
FIREWALL=1705536000  # 2024-01-18T00:00:00Z

def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def verify_gate(src:Path,gate_report:Path):
    g=json.loads(gate_report.read_text(encoding='utf-8'))
    digest=sha256(src)
    if g.get('status')!='PASS': raise ValueError('header gate did not PASS')
    if g.get('source_sha256')!=digest: raise ValueError('gate/source sha256 mismatch')
    if g.get('firewall_utc')!='2024-01-18T00:00:00Z': raise ValueError('unexpected gate firewall')
    if g.get('consensus_scope')!='bitcoin-mainnet': raise ValueError('unexpected consensus scope')
    return digest

def build(src:Path,dst:Path,gate_report:Path):
    digest=verify_gate(src,gate_report)
    rows=list(csv.DictReader(src.open(newline='',encoding='utf-8')))
    if not rows: raise ValueError('empty input')
    for c in ('height','hash','time'):
        if c not in rows[0]: raise ValueError(f'missing column:{c}')
    x=sorted(({**r,'height':int(r['height']),'time':int(r['time'])} for r in rows),key=lambda r:r['height'])
    if any(r['time']>=FIREWALL for r in x): raise ValueError('holdout firewall violation')
    for a,b in zip(x,x[1:]):
        if b['height']!=a['height']+1: raise ValueError(f'height gap:{a["height"]}->{b["height"]}')
    fields=['height','hash','time']+[f'{m}_{w}' for w in WINDOWS for m in ('mean_stress','median_stress','frac_gt_1200','frac_gt_3600')]
    out=[]; deltas=[]
    for i,r in enumerate(x):
        # IMPORTANT: compute row i from history available strictly before block i.
        # Append delta ending at i only after row i has been materialized.
        o={'height':r['height'],'hash':r['hash'],'time':r['time']}
        for w in WINDOWS:
            ds=deltas[-w:]
            vals=(None,None,None,None) if len(ds)<w else (sum(ds)/w/600-1,statistics.median(ds)/600-1,sum(d>1200 for d in ds)/w,sum(d>3600 for d in ds)/w)
            for m,v in zip(('mean_stress','median_stress','frac_gt_1200','frac_gt_3600'),vals): o[f'{m}_{w}']=v
        out.append(o)
        if i: deltas.append(r['time']-x[i-1]['time'])
    with dst.open('w',newline='',encoding='utf-8') as f:
        wr=csv.DictWriter(f,fieldnames=fields); wr.writeheader()
        for r in out: wr.writerow({k:('' if v is None else (format(v,'.17g') if isinstance(v,float) else v)) for k,v in r.items()})
    return {'rows':len(out),'source_sha256':digest,'gate_report_sha256':sha256(gate_report),'output_sha256':sha256(dst),'windows':list(WINDOWS),'causal_lag_blocks':1,'status':'PASS'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--gate-report',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    print(json.dumps(build(a.csv,a.out,a.gate_report),sort_keys=True,indent=2))
if __name__=='__main__': main()
