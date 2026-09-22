from __future__ import annotations
import hashlib,json
from collections import Counter
from pathlib import Path
import pandas as pd
P=Path(__file__).resolve().parents[1];OUT=P/'reports'/'v98_independent_phase086_funding_interval_feasibility.json';PRE=P/'reports'/'v98_independent_phase086_funding_interval_feasibility_prereg.md'
SYMS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT','XRPUSDT');A=pd.Timestamp('2023-01-01',tz='UTC');B=pd.Timestamp('2025-12-31 23:59:59',tz='UTC')
def main():
 per={};pool=[];fail=[]
 for s in SYMS:
  p=P/'data'/'canonical'/f'{s}_funding.csv';sha=hashlib.sha256(p.read_bytes()).hexdigest();df=pd.read_csv(p)
  if 'funding_interval_hours' not in df.columns: fail.append(f'{s}_missing_interval_column');per[s]={'sha256':sha,'error':'missing_column'};continue
  ts=pd.to_datetime(df['timestamp'],utc=True,format='mixed',errors='coerce');x=pd.to_numeric(df['funding_interval_hours'],errors='coerce');x=x[(ts>=A)&(ts<=B)&x.notna()&(x>0)];vals=[float(v) for v in x]
  if len(vals)<100: fail.append(f'{s}_finite_positive_obs<100')
  pool.extend(vals);per[s]={'sha256':sha,'finite_positive_obs':len(vals),'frequencies':{str(k):v for k,v in sorted(Counter(vals).items())}}
 freq=Counter(pool);distinct=len(freq);modal=max(freq,key=freq.get) if freq else None;nonmodal=(sum(v for k,v in freq.items() if k!=modal)/len(pool)) if pool else 0.
 if distinct<2: fail.append('pooled_distinct_values<2')
 if nonmodal<.01: fail.append('pooled_nonmodal_share<1%')
 rep={'engine':'V98 Independent','phase':'086','kind':'DATA_ONLY_FEASIBILITY','hypothesis_family':'exchange funding-interval state','preregistration':'reports/v98_independent_phase086_funding_interval_feasibility_prereg.md','training_window':['2023-01-01','2025-12-31'],'symbols':SYMS,'per_symbol':per,'pooled':{'finite_positive_obs':len(pool),'frequencies':{str(k):v for k,v in sorted(freq.items())},'distinct_values':distinct,'modal_interval_hours':modal,'nonmodal_share':nonmodal},'gate':{'passed':not fail,'decision':'PASS_DATA_ONLY' if not fail else 'FAIL_DATA_NO_ALPHA','failures':fail},'alpha_executed':False,'returns_inspected':False,'phase083_selection_use':False,'v99_used':False,'v16_used':False,'prereg_sha256':hashlib.sha256(PRE.read_bytes()).hexdigest()};OUT.write_text(json.dumps(rep,indent=2,default=str)+'\n');print(json.dumps(rep,indent=2,default=str))
if __name__=='__main__':main()
