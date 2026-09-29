#!/usr/bin/env python3
"""Phase182 frozen TRAIN-only evaluator. Never parses OHLCV values at/after holdout."""
import csv,json,math,hashlib
from pathlib import Path
from datetime import datetime,timezone
CUTOFF=datetime(2024,1,18,tzinfo=timezone.utc); START=datetime(2021,12,1,tzinfo=timezone.utc)
SEVERE=0.0007; SUPERSEVERE=0.0014; GROSS=0.20; N=24
SIGNS=(1.,1.,-1.,1.,-1.)
def ts(x): return datetime.fromisoformat(x.replace('Z','+00:00')).astimezone(timezone.utc)
def load_train(path):
 out=[]; h=hashlib.sha256()
 with open(path,newline='',encoding='utf-8') as f:
  rd=csv.DictReader(f); req=('timestamp','open','high','low','close','volume')
  if not rd.fieldnames or any(x not in rd.fieldnames for x in req): raise ValueError('columns')
  for r in rd:
   t=ts(r['timestamp'])
   if t>=CUTOFF: break # firewall BEFORE numeric market values are parsed
   vals=tuple(float(r[x]) for x in ('open','high','low','close','volume'))
   out.append((t,*vals)); h.update((r['timestamp']+'|'+ '|'.join(r[x] for x in ('open','high','low','close','volume'))+'\n').encode())
 return out,h.hexdigest()
def median(x):
 y=sorted(x); n=len(y); return y[n//2] if n%2 else (y[n//2-1]+y[n//2])/2
def features(b,e):
 out=[]
 for t in range(N+1,len(b)):
  rb=[math.log(b[i][4]/b[i-1][4]) for i in range(t-N,t)]; re=[math.log(e[i][4]/e[i-1][4]) for i in range(t-N,t)]
  rel1=re[-1]-rb[-1]; rel24=sum(re)-sum(rb); rvb=math.sqrt(sum(x*x for x in rb)); rve=math.sqrt(sum(x*x for x in re)); rvr=rve/rvb if rvb else 0.
  mb=median([x[5] for x in b[t-N:t]]); me=median([x[5] for x in e[t-N:t]]); vsd=(e[t-1][5]/me-1 if me else 0)-(b[t-1][5]/mb-1 if mb else 0)
  stress=max(-rel24,0)*max(rvr-1,0); out.append((b[t][0],(rel1,rel24,rvr,vsd,stress),b[t][4],e[t][4]))
 return out
def eval_pair(b,e,cost):
 f=features(b,e); hist=[[] for _ in range(5)]; pos=[]; rets=[]; dates=[]; prev=0.
 for i,(t,x,bc,ec) in enumerate(f):
  zs=[]
  for j,v in enumerate(x):
   h=hist[j]; mu=sum(h)/len(h) if h else 0.; sd=math.sqrt(sum((q-mu)**2 for q in h)/(len(h)-1)) if len(h)>1 else 0.; zs.append((v-mu)/sd if sd>1e-12 else 0.); h.append(v)
  score=sum(s*z for s,z in zip(SIGNS,zs))/5; p=GROSS*math.tanh(score)
  if i+1<len(f) and t>=START:
   nbc=f[i+1][2]; nec=f[i+1][3]; spread=(nec/ec-1)-(nbc/bc-1); turnover=abs(p-prev); rets.append(p*spread-turnover*cost); dates.append(t); prev=p
 if not rets: raise ValueError('empty train')
 eq=1.; peak=1.; mdd=0.; worst=min(rets)
 for r in rets: eq*=1+r; peak=max(peak,eq); mdd=min(mdd,eq/peak-1)
 folds=[]; k=5
 for q in range(k):
  a=q*len(rets)//k; z=(q+1)*len(rets)//k; w=1.
  for r in rets[a:z]: w*=1+r
  folds.append(w-1)
 top=sorted(rets,reverse=True); base=eq-1; no_best=1.
 for r in rets:
  if r==max(rets): continue
  no_best*=1+r
 return {'return':base,'max_drawdown':mdd,'worst_hour':worst,'positive_hour_rate':sum(r>0 for r in rets)/len(rets),'fold_returns':folds,'healthy_folds':sum(r>0 for r in folds),'remove_best_hour_return':no_best-1,'hours':len(rets),'cost_per_side':cost}
def main(btc='data/canonical/BTCUSDT_1h.csv',eth='data/canonical/ETHUSDT_1h.csv',out='reports/candidate_v99_r106_phase182_train_alpha.json'):
 b,bh=load_train(btc); e,eh=load_train(eth)
 if [x[0] for x in b] != [x[0] for x in e]: raise ValueError('timestamp mismatch')
 sev=eval_pair(b,e,SEVERE); sup=eval_pair(b,e,SUPERSEVERE); passed=sev['healthy_folds']>=4 and sup['healthy_folds']>=3 and sup['return']>0 and sup['remove_best_hour_return']>0
 r={'study':'V99 R106 Phase182 BTC/ETH relative stress','status':'TRAIN_ALPHA_PASS_FREEZE_FOR_DOWNSTREAM' if passed else 'TRAIN_ALPHA_REJECT','train_end_exclusive':CUTOFF.isoformat(),'holdout_market_values_parsed':False,'mapping':'research/V99_R106_PHASE182_TRAIN_ALPHA_FREEZE.md','btc_train_stream_sha256':bh,'eth_train_stream_sha256':eh,'severe':sev,'supersevere':sup,'reproducibility':'deterministic pure-python evaluator','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'next_gate':'PASS: independent regime/benchmark-envelope audit before any holdout; FAIL: permanent rejection without retuning.'}
 Path(out).write_text(json.dumps(r,sort_keys=True,indent=2)+'\n'); print(json.dumps(r,sort_keys=True,indent=2)); return r
if __name__=='__main__': main()
