#!/usr/bin/env python3
"""V98-only Phase339: native-funded frozen Phase305 A/B/C training smoke."""
from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd
import phase244_growth_core as P
import phase252_carry_subsidized_opportunity as F
R=Path(__file__).resolve().parent
BASE="f18fe648a9994de28a8e8f13eb85d7031d818baf629fe90d561d7cb5a31ea8a4"
CAND="158240cddf2aed3678e5b64dc2536090c186a60e9d0032713fc058acd1bb80cf"
def h(x):return hashlib.sha256(x.to_csv(float_format="%.12g").encode()).hexdigest()
def run():
 d=P.load_data(R/"phase243_clean4_canonical",R/"data/phase206_funding")
 if d.close.index[-1]>=pd.Timestamp("2026-01-01",tz="UTC"):raise ValueError("future")
 _,_,b,_=F.targets(d)
 if h(b)!=BASE:raise ValueError("frozen base")
 c=d.close.loc[:,P.ASSETS];ret=np.log(c/c.shift(1))
 corr=pd.concat([ret[a].rolling(168,min_periods=168).corr(ret[z]) for i,a in enumerate(P.ASSETS) for z in P.ASSETS[i+1:]],axis=1).mean(axis=1,skipna=False)
 impulse=np.log(c/c.shift(168)).mean(axis=1);ok=(corr>=.70)&(impulse>=.05)&corr.notna()&impulse.notna()
 active=np.zeros(len(c),dtype=bool);remaining=cooldown=events=0
 for i,t in enumerate(c.index):
  if t<P.START:continue
  if remaining:
   active[i]=True;remaining-=1
   if remaining==0:cooldown=168
  elif cooldown:cooldown-=1
  elif t.hour==23 and bool(ok.iat[i]):active[i]=True;remaining=167;events+=1
 add=pd.DataFrame(np.repeat((active*.05)[:,None],4,axis=1),index=c.index,columns=P.ASSETS)
 candidate=b+add
 if h(candidate)!=CAND or events!=31 or candidate.abs().sum(axis=1).max()>1.45+1e-10:raise ValueError("frozen candidate")
 official=json.loads((R/"phase252_carry_subsidized_opportunity_results.json").read_text())
 if official["combined_targets_sha256"]!=BASE:raise ValueError("official base")
 out={"engine":"V98 Independent","phase":339,"kind":"NATIVE_FUNDED_PHASE305_ABC_SMOKE","training_only":True,"holdout_accessed":False,"validation_accessed":False,"v99_used":False,"funding_included":True,"bnB_vendor_provenance_resolved":False,"promotion_eligible":False,"events":events,"tiers":{}}
 for name,(fee,debit,credit) in P.TIERS.items():
  kw=dict(cost_per_side=fee,funding_debit_multiplier=debit,funding_credit_multiplier=credit)
  a=P.exact_fast(d,b,gross_guard_cap=1.25,**kw)
  x=P.exact_fast(d,b,gross_guard_cap=1.45,**kw)
  y=P.exact_fast(d,candidate,gross_guard_cap=1.45,**kw)
  A,B,C=[P.metric(z,P.START,P.CUT) for z in (a,x,y)]
  for k in ("return","cagr","max_drawdown","profit_factor_daily","worst_day"):
   if abs(A[k]-official["combined"][name][k])>1e-9:raise ValueError("official mismatch "+name+" "+k)
  folds={}
  for yr,(s,e) in P.FOLDS.items():
   ba=P.metric(x,s,e);ca=P.metric(y,s,e)
   folds[yr]={"relative_wealth":(1+ca["return"])/(1+ba["return"])-1,"return_pp":100*(ca["return"]-ba["return"])}
  out["tiers"][name]={"A":A,"B":B,"C":C,"relative_wealth":(1+C["return"])/(1+B["return"])-1,"folds":folds}
 return out
if __name__=="__main__":
 import argparse
 p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True);a=p.parse_args()
 r=run();a.out.write_text(json.dumps(r,sort_keys=True,indent=2,allow_nan=False)+"\n")
 print(json.dumps({k:{"relative_wealth":v["relative_wealth"],"folds":v["folds"]} for k,v in r["tiers"].items()},indent=2))
