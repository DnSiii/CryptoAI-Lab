#!/usr/bin/env python3
"""Phase181 deterministic DATA gate. No trading/PnL logic."""
import argparse, csv, hashlib, json
from datetime import datetime, timezone
from pathlib import Path

CUTOFF = datetime(2024,1,18,tzinfo=timezone.utc)
PRE_ROLL = 2048

def utc(s):
    d=datetime.fromisoformat(s.replace('Z','+00:00'))
    if d.tzinfo is None: raise ValueError('naive timestamp')
    return d.astimezone(timezone.utc)

def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def gate(path, train_start):
    rows=[]
    with open(path,newline='',encoding='utf-8') as f:
        for r in csv.DictReader(f):
            rows.append({**r,'slot':int(r['slot']),'observed_at':utc(r['observed_at'])})
    errors=[]
    if not rows: errors.append('empty source')
    rows.sort(key=lambda r:r['slot'])
    seen={}
    for r in rows:
        if r['slot'] in seen and (r['block_root'],r['parent_root']) != seen[r['slot']]: errors.append(f'conflicting slot {r["slot"]}')
        seen[r['slot']] = (r['block_root'],r['parent_root'])
        if r['observed_at'] >= CUTOFF: errors.append(f'holdout firewall slot {r["slot"]}')
    gaps=[]
    for a,b in zip(rows,rows[1:]):
        if b['slot'] <= a['slot']: errors.append('non-increasing slots')
        if b['parent_root'] != a['block_root']: errors.append(f'parent discontinuity {a["slot"]}->{b["slot"]}')
        if b['slot']>a['slot']+1:
            gaps.append({'after_slot':a['slot'],'before_slot':b['slot'],'missed_count':b['slot']-a['slot']-1,'known_at':b['observed_at'].isoformat()})
    start=utc(train_start)
    eligible=[r for r in rows if r['observed_at'] < start]
    if len(eligible)<PRE_ROLL: errors.append(f'insufficient pre-roll: {len(eligible)} < {PRE_ROLL}')
    if rows and max(r['observed_at'] for r in rows) < CUTOFF.replace(hour=0)-__import__('datetime').timedelta(days=1): errors.append('coverage does not reach cutoff vicinity')
    return {'status':'PASS' if not errors else 'FAIL','source_sha256':sha256(path),'rows':len(rows),'gaps':len(gaps),'errors':sorted(set(errors)),'availability_rule':'gap known only at next observed canonical block; downstream market t-1 still mandatory'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('csv'); ap.add_argument('--train-start',default='2021-12-01T00:00:00Z'); ap.add_argument('--out',default='phase181_gate.json'); a=ap.parse_args()
    out=gate(a.csv,a.train_start); Path(a.out).write_text(json.dumps(out,sort_keys=True,indent=2)+'\n'); print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out['status']=='PASS' else 2)
if __name__=='__main__': main()
