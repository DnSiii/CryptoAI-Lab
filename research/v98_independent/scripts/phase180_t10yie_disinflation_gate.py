#!/usr/bin/env python3
"""V98 Independent Phase180 — preregistered T10YIE disinflation gate.
Training-only 2023-2025. Validation/final holdout remain unopened.
"""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
NS=ROOT/'research/v98_independent'
PREREG=NS/'prereg/phase180_t10yie_disinflation_prereg.json'
OUT=NS/'reports/phase180_t10yie_disinflation_result.json'
ASSETS=['BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT']
START=pd.Timestamp('2023-01-01',tz='UTC'); END=pd.Timestamp('2025-12-31 23:00',tz='UTC')

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_macro():
    # Reuse only Phase179's independently-audited DATA_ONLY acquisition code; never its economic output.
    subprocess.run([sys.executable,str(NS/'scripts/phase179_t10yie_data_only.py')],cwd=ROOT,check=True)
    p=NS/'reports/phase179_t10yie_data_only.json'
    r=json.loads(p.read_text())
    if r.get('decision')!='PASS_DATA_ONLY': raise RuntimeError('Phase179 DATA_ONLY not PASS')
    import urllib.request, io
    url='https://fred.stlouisfed.org/graph/fredgraph.csv?id=T10YIE'
    raw=urllib.request.urlopen(url,timeout=90).read()
    d=pd.read_csv(io.BytesIO(raw)); dc='DATE' if 'DATE' in d else 'observation_date'
    d[dc]=pd.to_datetime(d[dc],utc=True); d['T10YIE']=pd.to_numeric(d['T10YIE'],errors='coerce'); d=d.dropna()
    d=d[(d[dc]>=START)&(d[dc]<=END)].sort_values(dc)
    # Conservative availability: observation becomes usable only next UTC day; hourly forward-fill thereafter.
    s=pd.Series(d.T10YIE.values,index=d[dc]+pd.Timedelta(days=1)).sort_index()
    h=s.reindex(pd.date_range(START,END,freq='h')).ffill()
    # Fixed prereg transform: 63 observations, computed on releases before hourly expansion.
    obs=pd.Series(d.T10YIE.values,index=d[dc]+pd.Timedelta(days=1)).sort_index()
    delta=obs-obs.shift(63)
    dh=delta.reindex(h.index).ffill()
    return dh

def metrics(r):
    eq=(1+r.fillna(0)).cumprod(); dd=eq/eq.cummax()-1
    pos=r[r>0]; neg=r[r<0]
    return {'return':float(eq.iloc[-1]-1),'max_drawdown':float(dd.min()),'profit_factor':float(pos.sum()/abs(neg.sum())) if len(neg) else None,'payoff':float(pos.mean()/abs(neg.mean())) if len(pos) and len(neg) else None,'win_rate':float((r>0).mean()),'positive_days':float((r.resample('1D').sum()>0).mean())}

def main():
    pre=json.loads(PREREG.read_text()); macro=load_macro()
    rets=[]
    for a in ASSETS:
        p=ROOT/f'data/canonical/{a}_1h.csv'
        if not p.exists(): raise FileNotFoundError(p)
        d=pd.read_csv(p); tc=next(c for c in d.columns if c.lower() in ('timestamp','datetime','date','open_time'))
        cc=next(c for c in d.columns if c.lower()=='close')
        t=pd.to_datetime(d[tc],utc=True,errors='coerce'); x=pd.Series(pd.to_numeric(d[cc],errors='coerce').values,index=t).dropna().sort_index(); x=x[(x.index>=START)&(x.index<=END)]
        rets.append(x.pct_change().rename(a))
    R=pd.concat(rets,axis=1).dropna(how='all').fillna(0)
    # Fixed economic comparison only: control 1.0 vs disinflation gate 0.5/1.0.
    # Disinflation stress = 63-observation breakeven change < 0 => halve gross exposure.
    gate=pd.Series(np.where(macro.reindex(R.index).ffill()<0,0.5,1.0),index=R.index)
    gross_control=R.mean(axis=1)
    gross_gate=gross_control*gate
    # Cost stress is deliberately explicit and symmetric; values are fixed here, never optimized.
    scenarios={'base':0.00010,'severe':0.00020,'supersevere':0.00035}
    out={'phase':'180','prereg_sha256':sha(PREREG),'window':['2023-01-01','2025-12-31'],'holdout_inspected':False,'validation_inspected':False,'variants':{}}
    for name,cost in scenarios.items():
        turnover=gate.diff().abs().fillna(0)
        c=gross_control.copy() # control has no macro resizing turnover
        g=gross_gate-turnover*cost
        out['variants'][name]={'control':metrics(c),'gate':metrics(g)}
    out['folds']={str(y):metrics(gross_gate[gross_gate.index.year==y]) for y in (2023,2024,2025)}
    out['gate_half_fraction']=float((gate==0.5).mean()); out['decision']='TRAINING_RESULT_REQUIRES_AUDIT'
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__': main()
