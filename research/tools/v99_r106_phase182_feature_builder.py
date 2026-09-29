#!/usr/bin/env python3
"""Phase182 preregistered BTC/ETH relative-stress features. TRAIN-only, causal t-1."""
import argparse,csv,hashlib,json,math
from pathlib import Path
from research.tools.v99_r106_phase182_pair_integrity import gate,load

N=24
FIELDS=['timestamp','relative_return_1','relative_return_24','rv_ratio_24','volume_shock_diff_24','stress_interaction']

def sha(p):
 h=hashlib.sha256(); h.update(Path(p).read_bytes()); return h.hexdigest()
def median(x):
 y=sorted(x); n=len(y); return y[n//2] if n%2 else (y[n//2-1]+y[n//2])/2

def build(btc_path,eth_path,out_path):
 g=gate(btc_path,eth_path)
 if g['status']!='PASS': raise ValueError('pair integrity gate failed: '+','.join(g['errors']))
 b=load(btc_path); e=load(eth_path)
 # At row t, features consume bars no later than t-1. One-bar returns for index i use closes i and i-1.
 rows=[]
 for t in range(N+1,len(b)):
  rb=[]; re=[]
  for i in range(t-N,t):
   rb.append(math.log(b[i][4]/b[i-1][4])); re.append(math.log(e[i][4]/e[i-1][4]))
  rel1=re[-1]-rb[-1]; rel24=sum(re)-sum(rb)
  rvb=math.sqrt(sum(x*x for x in rb)); rve=math.sqrt(sum(x*x for x in re)); rvr=rve/rvb if rvb>0 else float('nan')
  # trailing volume median also terminates at t-1; no current/t volume.
  mb=median([x[5] for x in b[t-N:t]]); me=median([x[5] for x in e[t-N:t]])
  vsb=b[t-1][5]/mb-1 if mb>0 else float('nan'); vse=e[t-1][5]/me-1 if me>0 else float('nan')
  vsd=vse-vsb; stress=max(-rel24,0.0)*max(rvr-1.0,0.0)
  rows.append([b[t][0].isoformat().replace('+00:00','Z'),rel1,rel24,rvr,vsd,stress])
 with open(out_path,'w',newline='',encoding='utf-8') as f:
  w=csv.writer(f); w.writerow(FIELDS); w.writerows(rows)
 return {'status':'PASS','rows':len(rows),'window':N,'causal_lag_bars':1,'btc_sha256':g['btc_sha256'],'eth_sha256':g['eth_sha256'],'feature_sha256':sha(out_path),'construction':'frozen phase182 preregistration; no threshold/sign/window search'}

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('btc'); ap.add_argument('eth'); ap.add_argument('out'); ap.add_argument('--manifest'); a=ap.parse_args()
 m=build(a.btc,a.eth,a.out); print(json.dumps(m,sort_keys=True));
 if a.manifest: Path(a.manifest).write_text(json.dumps(m,sort_keys=True,indent=2)+'\n')
if __name__=='__main__': main()
