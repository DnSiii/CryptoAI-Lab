#!/usr/bin/env python3
"""Phase186 frozen TRAIN-only evaluator: volatility-shock conditional ETH/BTC relative continuation."""
import csv,json,math,hashlib
from pathlib import Path
from datetime import datetime,timezone
CUTOFF=datetime(2024,1,18,tzinfo=timezone.utc); START=datetime(2021,12,1,tzinfo=timezone.utc)
N=168; THRESH=2.0; LEG=.10; SEVERE=.0007; SUPERSEVERE=.0014

def ts(x): return datetime.fromisoformat(x.replace('Z','+00:00')).astimezone(timezone.utc)
def load_train(path):
 out=[];h=hashlib.sha256()
 with open(path,newline='',encoding='utf-8') as f:
  rd=csv.DictReader(f);req=('timestamp','open','high','low','close','volume')
  if not rd.fieldnames or any(x not in rd.fieldnames for x in req): raise ValueError('columns')
  for r in rd:
   t=ts(r['timestamp'])
   if t>=CUTOFF: break
   vals=tuple(float(r[x]) for x in ('open','high','low','close','volume'));out.append((t,*vals));h.update((r['timestamp']+'|'+'|'.join(r[x] for x in ('open','high','low','close','volume'))+'\n').encode())
 return out,h.hexdigest()

def signal_series(b,e):
 rb=[math.log(b[i][4]/b[i-1][4]) for i in range(1,len(b))]; re=[math.log(e[i][4]/e[i-1][4]) for i in range(1,len(e))]; out=[]
 for t in range(N+2,len(b)-1):
  # Position for hour t uses only information through close(t-1).
  # rb[t-2] is BTC return ending t-1; volatility slice ends at return ending t-2.
  hist=rb[t-N-2:t-2]; mu=sum(hist)/N; sd=math.sqrt(sum((q-mu)**2 for q in hist)/(N-1))
  shock=abs(rb[t-2]) / sd if sd>1e-12 else 0.
  rel=re[t-2]-rb[t-2]
  direction=1. if rel>0 else -1. if rel<0 else 0.
  pe=LEG*direction if shock>=THRESH else 0.; pb=-pe
  out.append((b[t][0],pb,pe,shock,rel,b[t][4],b[t+1][4],e[t][4],e[t+1][4]))
 return out

def evaluate(b,e,cost):
 rs=[];prev_b=prev_e=0.;active=0
 for t,pb,pe,shock,rel,bc,bn,ec,en in signal_series(b,e):
  if t<START: prev_b,prev_e=pb,pe;continue
  gross=pb*(bn/bc-1)+pe*(en/ec-1); turnover=abs(pb-prev_b)+abs(pe-prev_e)
  rs.append(gross-turnover*cost); active+=abs(pe)>0; prev_b,prev_e=pb,pe
 if not rs: raise ValueError('empty train')
 eq=peak=1.;mdd=0.
 for r in rs: eq*=1+r;peak=max(peak,eq);mdd=min(mdd,eq/peak-1)
 folds=[]
 for q in range(5):
  a=q*len(rs)//5; z=(q+1)*len(rs)//5; w=1.
  for r in rs[a:z]: w*=1+r
  folds.append(w-1)
 imax=max(range(len(rs)),key=rs.__getitem__); w=1.
 for i,r in enumerate(rs):
  if i!=imax: w*=1+r
 return {'return':eq-1,'max_drawdown':mdd,'worst_hour':min(rs),'fold_returns':folds,'healthy_folds':sum(x>0 for x in folds),'remove_best_hour_return':w-1,'hours':len(rs),'active_hours':active,'cost_per_side':cost}

def main(btc='data/canonical/BTCUSDT_1h.csv',eth='data/canonical/ETHUSDT_1h.csv',out='reports/candidate_v99_r106_phase186_train_alpha.json'):
 b,bh=load_train(btc);e,eh=load_train(eth)
 if [x[0] for x in b]!=[x[0] for x in e]: raise ValueError('timestamp mismatch')
 sev=evaluate(b,e,SEVERE); sup=evaluate(b,e,SUPERSEVERE)
 passed=sev['healthy_folds']>=4 and sup['healthy_folds']>=3 and sup['return']>0 and sup['remove_best_hour_return']>0
 r={'study':'V99 R106 Phase186 volatility-shock conditional ETH/BTC relative continuation','status':'TRAIN_ALPHA_PASS_FREEZE_FOR_DOWNSTREAM' if passed else 'TRAIN_ALPHA_REJECT','train_end_exclusive':CUTOFF.isoformat(),'holdout_market_values_parsed':False,'preregistered_parameters':{'vol_window_hours':N,'shock_threshold':THRESH,'gross':2*LEG,'direction':'sign(ETH-BTC return t-1), continuation during BTC standardized shock'},'btc_train_stream_sha256':bh,'eth_train_stream_sha256':eh,'severe':sev,'supersevere':sup,'reproducibility':'deterministic pure-python evaluator','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'next_gate':'PASS: freeze then regime/benchmark/tail audit before any holdout; FAIL: permanent rejection without retuning.'}
 Path(out).parent.mkdir(parents=True,exist_ok=True);Path(out).write_text(json.dumps(r,sort_keys=True,indent=2)+'\n');print(json.dumps(r,sort_keys=True,indent=2));return r
if __name__=='__main__': main()
