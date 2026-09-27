#!/usr/bin/env python3
"""V98 Independent Phase162 — DATA_ONLY activation audit for frozen NFCI.
No crypto/PnL/validation/holdout access. Diagnoses Phase161 zero-exposure mechanism only.
"""
from __future__ import annotations
import json, hashlib
from pathlib import Path
import numpy as np
import sys
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'scripts'))
import v98_independent_phase160_nfci_data_only as p160
GATE=PROJECT/'reports'/'v98_independent_phase160_nfci_data_only.json'
OUT=PROJECT/'reports'/'v98_independent_phase162_nfci_activation_audit.json'
def main():
 g=json.loads(GATE.read_text()); assert g['status']=='PASS_DATA_ONLY'
 rows,qa=p160.parse(p160.acquire()); h=hashlib.sha256(p160.canonical(rows)).hexdigest(); assert h==g['sha256'][0]
 vals=np.array([v for _,v in rows],dtype=float)
 years={str(y):[v for d,v in rows if d.startswith(str(y))] for y in (2023,2024,2025)}
 r={'engine':'V98 Independent','phase':'162','kind':'DATA_ONLY_DIAGNOSTIC','dependency_hash':h,'reacquisition_hash_verified':True,'observations':len(vals),'min':float(vals.min()),'max':float(vals.max()),'mean':float(vals.mean()),'median':float(np.median(vals)),'positive_count':int((vals>0).sum()),'zero_count':int((vals==0).sum()),'negative_count':int((vals<0).sum()),'positive_share':float((vals>0).mean()),'annual':{y:{'n':len(v),'min':float(min(v)),'max':float(max(v)),'positive_count':sum(x>0 for x in v)} for y,v in years.items()},'phase161_mechanism':'NO_ACTIVATION' if not (vals>0).any() else 'ACTIVATION_PRESENT','economic_firewall':True,'validation':None,'final_holdout':None,'v16_used':False,'v99_used':False}
 OUT.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n'); print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
