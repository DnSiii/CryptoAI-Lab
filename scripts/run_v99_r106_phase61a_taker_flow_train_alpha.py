from __future__ import annotations
import concurrent.futures,csv,datetime as dt,hashlib,io,json,urllib.error,urllib.request,zipfile
from pathlib import Path
import numpy as np,pandas as pd
import run_v99_r106_phase31_cross_sectional_low_vol_alpha_audit as p31
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase47_downside_semivariance_alpha_audit as p47
import run_v99_r105_all_regime_structural_audit as audit
PROJECT=Path(__file__).resolve().parents[1]; OUT=PROJECT/'reports'/'candidate_v99_r106_phase61a_taker_flow_train_alpha.json'; BASE='https://data.binance.vision/data/futures/um/monthly/klines'; H=24; ALPHA_GROSS=.20

def months(a,b):
 y,m=a.year,a.month
 while (y,m)<=(b.year,b.month):
  yield f'{y:04d}-{m:02d}';m+=1
  if m==13:y,m=y+1,1

def get(u):
 req=urllib.request.Request(u,headers={'User-Agent':'CryptoAI-v99-r106-phase61a'})
 try:
  with urllib.request.urlopen(req,timeout=60) as r:return r.read()
 except urllib.error.HTTPError as e:
  if e.code==404:return None
  raise

def load(job):
 s,m,first_ms,end_ms=job;stem=f'{s}-1h-{m}.zip';u=f'{BASE}/{s}/1h/{stem}';raw=get(u);chk=get(u+'.CHECKSUM')
 if raw is None or chk is None:raise RuntimeError(f'missing {s} {m}')
 if hashlib.sha256(raw).hexdigest()!=chk.decode().split()[0]:raise RuntimeError(f'checksum {s} {m}')
 rows=[]
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  if z.testzip() is not None:raise RuntimeError(f'crc {s} {m}')
  rd=csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]),encoding='utf-8'))
  for r in rd:
   if not r or r[0] in ('open_time','open_time_ms'):continue
   t=int(r[0])
   if t<first_ms or t>end_ms:continue
   q=float(r[7]);tbq=float(r[10]); pressure=(2*tbq/q-1) if q>0 else np.nan
   rows.append((t,pressure))
 return s,rows

def main():
 cov=json.loads((PROJECT/'reports'/'candidate_v99_r106_phase60_taker_buy_train_coverage_audit.json').read_text());assert cov['all_train_coverage_pass']
 manifest=json.loads((PROJECT/'data'/'CANONICAL_MANIFEST_RESEARCH_PIT48.json').read_text()); train_end=dt.datetime.fromisoformat(cov['train_end']);end_ms=int(train_end.timestamp()*1000);jobs=[]
 for s,meta in manifest['symbols'].items():
  first=dt.datetime.fromisoformat(meta['first']);fm=int(first.timestamp()*1000);jobs += [(s,m,fm,end_ms) for m in months(first,train_end)]
 with concurrent.futures.ThreadPoolExecutor(max_workers=24) as pool: loaded=list(pool.map(load,jobs))
 by={s:[] for s in manifest['symbols']}
 for s,rs in loaded:by[s].extend(rs)
 cfg,data,raw,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup(); idx=data.close.index; pressure=pd.DataFrame(index=idx,columns=data.close.columns,dtype=float)
 for s,rs in by.items():
  if s not in pressure.columns:continue
  ser=pd.Series({pd.to_datetime(t,unit='ms',utc=True):v for t,v in rs});pressure.loc[pressure.index.intersection(ser.index),s]=ser.reindex(pressure.index.intersection(ser.index)).values
 # Strict train-only construction: all downloaded/assigned feature values end at train_end; t-1 after 24 completed hours.
 feature=pressure.rolling(H,min_periods=H).mean().shift(1); targets=p31.weights(feature,data.close); severe=float(ex['severe_cost_per_side']); result=p1.run_targets(data,targets,ex,guard,severe,ALPHA_GROSS)
 start=max(data.close.index[0],min(x for x in feature.index if x<=train_end)); d=p47.diag(result,data.close.index,start,train_end); passed=bool(d['stable_train'])
 out={'study':'V99 R106 phase61A — native taker-flow 24h continuation TRAIN-ONLY alpha gate','status':'TRAIN_ALPHA_PASS_FREEZE_FOR_HOLDOUT' if passed else 'TRAIN_ALPHA_REJECT','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'source':'Binance USD-M native taker_buy_quote_volume/quote_volume','transform':'rolling24_mean(2*taker_buy_quote_volume/quote_volume-1).shift(1)','direction':'continuation','single_hypothesis_no_grid':True,'alpha_gross':ALPHA_GROSS,'selection_train_only':True,'holdout_not_parsed':True},'train_end':train_end.isoformat(),'diagnostic':d,'selected_train_only':'native_taker_flow_24h_continuation' if passed else None,'next_gate':'If pass, freeze exact specification and evaluate untouched holdout separately; if reject, do not flip sign/horizon or retune.','quarantined_symbols':quarantined,'disclosure':'Phase61A downloads/parses native taker-flow only through train_end. No holdout feature values or returns are inspected.'};OUT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n');print(json.dumps({'status':out['status'],'stable_train':passed,'healthy_folds':d['healthy_folds'],'valid_folds':d['valid_folds'],'train':d['train']},indent=2,default=audit.safe_float))
if __name__=='__main__':main()
