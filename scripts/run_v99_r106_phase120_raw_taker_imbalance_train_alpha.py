# Phase120 frozen preregistered raw aggTrades implementation; train-only.
from __future__ import annotations
import concurrent.futures,csv,hashlib,io,json,time,urllib.error,urllib.request,zipfile
from pathlib import Path
import numpy as np,pandas as pd
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase47_downside_semivariance_alpha_audit as p47
import run_v99_r105_all_regime_structural_audit as audit
PROJECT=Path(__file__).resolve().parents[1]
OUT=PROJECT/'reports'/'candidate_v99_r106_phase120_raw_taker_imbalance_train_alpha.json'
BASE='https://data.binance.vision/data/futures/um/daily/aggTrades'; ALPHA_GROSS=.20; N=12; MIN_ASSETS=8

def get(u):
 last=None
 for attempt in range(6):
  try:
   with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'CryptoAI-v99-r106-phase120'}),timeout=180) as r:return r.read()
  except (urllib.error.URLError,TimeoutError,ConnectionError) as e:last=e;time.sleep(min(32,2**attempt))
 raise last

def load(job):
 s,d=job; stem=f'{s}-aggTrades-{d}.zip'; u=f'{BASE}/{s}/{stem}'; raw=get(u); chk=get(u+'.CHECKSUM').decode().split()[0]
 if hashlib.sha256(raw).hexdigest()!=chk: raise RuntimeError('checksum '+stem)
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  if z.testzip() is not None: raise RuntimeError('crc '+stem)
  names=[n for n in z.namelist() if not n.endswith('/')]
  if len(names)!=1: raise RuntimeError('member '+stem)
  rd=csv.reader(io.TextIOWrapper(z.open(names[0]),encoding='utf-8')); acc={}
  for row in rd:
   if not row: continue
   try:
    q=float(row[2]); ts=int(row[5]); bm=str(row[6]).strip().lower()
   except (ValueError,TypeError,IndexError): continue # official header if present
   if not np.isfinite(q) or q<=0 or bm not in ('true','false'): continue
   h=pd.Timestamp(ts,unit='ms',tz='UTC').floor('1h'); buy=q if bm=='false' else 0.; sell=q if bm=='true' else 0.
   a=acc.setdefault(h,[0.,0.]); a[0]+=buy; a[1]+=sell
 return s,[(h,b,sell) for h,(b,sell) in acc.items()]

def rz(x):
 n=x.notna().sum(axis=1); med=x.median(axis=1); dev=x.sub(med,axis=0); mad=dev.abs().median(axis=1); valid=(n>=MIN_ASSETS)&np.isfinite(mad)&(mad>1e-12)
 return dev.div(mad.where(valid),axis=0).where(valid,np.nan)

def main():
 assert (PROJECT/'research'/'v99_r106_phase120_raw_taker_imbalance_prereg.md').exists()
 p119=json.loads((PROJECT/'reports'/'candidate_v99_r106_phase119_aggtrades_integrity_probe.json').read_text()); assert p119['status']=='INTEGRITY_PROBE_PASS'; assert p119['holdout_market_values_not_downloaded_or_parsed'] and p119['alpha_prohibited']
 av=json.loads((PROJECT/'reports'/'candidate_v99_r106_phase118_aggtrades_availability_audit.json').read_text()); assert av['status']=='AVAILABILITY_AUDIT_COMPLETE' and av['holdout_market_values_not_downloaded_or_parsed']
 selected=sorted(av['symbols'],key=lambda s:(int(av['symbols'][s]['listed_compressed_bytes']),s))[:N]
 jobs=[]
 for s in selected:
  v=av['symbols'][s]; miss=set(v['missing_dates']); jobs += [(s,d.date().isoformat()) for d in pd.date_range(v['first'],'2024-01-17',freq='D') if d.date().isoformat() not in miss]
 cfg,data,raw,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup(); x=pd.DataFrame(index=data.close.index,columns=selected,dtype=float)
 # bounded concurrency; each worker holds one daily zip only
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for s,rows in pool.map(load,jobs):
   for h,b,sl in rows:
    den=b+sl
    if den>0 and h in x.index:x.at[h,s]=(b-sl)/den
 z=rz(x); sig=np.tanh(z).shift(1); sig=sig.where(sig.notna().sum(axis=1)>=MIN_ASSETS,0).fillna(0); targets=pd.DataFrame(0.,index=data.close.index,columns=data.close.columns)
 common=[s for s in selected if s in targets.columns]; targets.loc[:,common]=sig[common].div(sig[common].abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
 result=p1.run_targets(data,targets,ex,guard,float(ex['severe_cost_per_side']),ALPHA_GROSS); te=pd.Timestamp('2024-01-18',tz='UTC'); d=p47.diag(result,data.close.index,max(data.close.index[0],pd.Timestamp('2021-12-01',tz='UTC')),te); passed=bool(d['stable_train'])
 out={'study':'V99 R106 Phase120 — RAW aggTrades TAKER IMBALANCE TRAIN-ONLY alpha gate','status':'TRAIN_ALPHA_PASS_FREEZE_FOR_DOWNSTREAM' if passed else 'TRAIN_ALPHA_REJECT','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'prereg':'research/v99_r106_phase120_raw_taker_imbalance_prereg.md','source':'official Binance USD-M daily aggTrades + CHECKSUM','feature':'hourly raw aggressive quantity imbalance; cross-sectional median/MAD z; tanh; entire alpha t-1; L1','direction':'continuation','resource_universe_rule':'12 smallest Phase118 listed pre-holdout compressed byte totals; tie lexical','selected_symbols':selected,'min_assets':MIN_ASSETS,'alpha_gross':ALPHA_GROSS,'single_hypothesis_no_grid':True,'selection_train_only':True,'holdout_not_parsed':True,'missing_archives_not_filled':True},'train_end_exclusive':te.isoformat(),'archives_consumed':len(jobs),'diagnostic':d,'selected_train_only':'raw_aggtrades_taker_imbalance' if passed else None,'next_gate':'PASS freezes exact spec for supersevere/regime/benchmark/reproducibility before untouched holdout; FAIL permanent, no retuning.','quarantined_symbols':quarantined}; OUT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n'); print(json.dumps({'status':out['status'],'selected_symbols':selected,'archives_consumed':len(jobs),'healthy_folds':d['healthy_folds'],'valid_folds':d['valid_folds'],'train':d['train']},indent=2,default=audit.safe_float))
if __name__=='__main__':main()
