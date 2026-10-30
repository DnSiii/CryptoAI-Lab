#!/usr/bin/env python3
"""LD authenticated source-only gate. Never computes PnL or accesses 2025+."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np
from ld_sources import bundle,static_check,WARMUP,BUDGET
from phase1260_aj_authenticated_source_digest import load_official,HOURS

OUT=Path(__file__).resolve().parent/'ld_source_only_gate_receipt.json'

def main():
    assert static_check()
    frames,manifest=load_official()
    o,h,l,c,q,r,e,ml,mh=frames
    assert HOURS==18288 and len(c)==HOURS and int(e.sum())==9144
    source=bundle(o,h,l,c,r,e,q)
    intents,updates,entries,valid,regimes=source
    violations=[]
    counts={}
    for year,lo,hi in (('2023',744,9504),('2024',9504,HOURS)):
        counts[year]={name:int(entries[lo:hi,k].sum()) for k,name in
                      enumerate(('Opportunity','Relative_Value','Stress_Recovery'))}
        for name,n in counts[year].items():
            if n<8:violations.append('LD_INSUFFICIENT_'+year+'_'+name)
    if np.any(entries[~valid]):violations.append('LD_INVALID_SOURCE_ENTRY')
    if np.any(np.any(updates[:,1:],axis=1)&(~valid)&(np.any(entries,axis=1))):
        violations.append('LD_ENTRY_ON_UNSAFE_QUOTE')
    if np.any(np.abs(intents).sum(axis=(1,2))>.95+1e-10):
        violations.append('LD_HIDDEN_GROSS')
    for k in range(4):
        changed=np.any(np.diff(intents[:,k,:],axis=0)!=0,axis=1)
        if np.any(changed&~updates[1:,k]):
            violations.append('LD_SILENT_ROW_CHANGE_'+str(k))
        if np.any(np.abs(intents[:,k]).sum(axis=1)>BUDGET[k]+1e-10):
            violations.append('LD_COMPONENT_BUDGET_'+str(k))
    prefix=14000
    mutated=[z.copy() for z in (o,h,l,c,r,e,q)]
    for k in (0,1,2,3):mutated[k][prefix:]*=1.45
    mutated[4][prefix:]*=-1.;mutated[6][prefix:]*=3.
    other=bundle(*mutated)
    causal=all(np.array_equal(a[:prefix],b[:prefix]) for a,b in zip(source,other))
    if not causal:violations.append('LD_REAL_FUTURE_MUTATION_LEAK')
    report={'architecture':'LD','hours':HOURS,'source_only':True,
      'pnl_computed':False,'source':'pinned_clean4_2022_2024_native_signed_funding',
      'prospective_feature_aware_quote_gate':True,
      'events':int(e.sum()),'manifest_sha256':hashlib.sha256(
          json.dumps(manifest,sort_keys=True).encode()).hexdigest(),
      'entries_by_year':counts,
      'max_intended_gross':float(np.abs(intents).sum(axis=(1,2)).max()),
      'future_mutation_prefix_hours':prefix,'future_mutation_pass':causal,
      'invalid_quote_decision_hours':int((~valid[WARMUP:]).sum()),
      'violations':violations,
      'decision':'PASS_SOURCE_ONLY' if not violations else 'REJECT_SOURCE_ONLY_NO_PNL',
      'validation_2025_read':False,'holdout_accessed':False,
      'benchmark_internals_read':False}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('LD_SOURCE_ONLY_GATE',json.dumps(report,sort_keys=True),flush=True)
    return report
if __name__=='__main__':
    raise SystemExit(0 if not main()['violations'] else 2)
