# Phase107 frozen preregistered implementation; train-only execution.
from __future__ import annotations
import concurrent.futures,csv,hashlib,io,json,time,urllib.error,urllib.request,zipfile
from pathlib import Path
import numpy as np,pandas as pd
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase47_downside_semivariance_alpha_audit as p47
import run_v99_r105_all_regime_structural_audit as audit
PROJECT=Path(__file__).resolve().parents[1];OUT=PROJECT/'reports'/'candidate_v99_r106_phase107_toptrader_conviction_train_alpha.json';BASE='https://data.binance.vision/data/futures/um/daily/metrics';FIELD='sum_toptrader_long_short_ratio';ALPHA_GROSS=.20

def get(u):
 last=None
 for attempt in range(5):
  try:
   with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'CryptoAI-v99-r106-phase107'}),timeout=90) as r:return r.read()
  except (urllib.error.URLError,TimeoutError,ConnectionError) as e:last=e;time.sleep(2**attempt)
 raise last

def load(job):
 s,d=job;stem=f'{s}-metrics-{d}.zip';u=f'{BASE}/{s}/{stem}';raw=get(u);chk=get(u+'.CHECKSUM')
 if hashlib.sha256(raw).hexdigest()!=chk.decode().split()[0]:raise RuntimeError('checksum '+stem)
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  if z.testzip() is not None:raise RuntimeError('crc '+stem)
  rd=csv.DictReader(io.TextIOWrapper(z.open(z.namelist()[0]),encoding='utf-8'));rows=[]
  if not {'create_time',FIELD}.issubset(set(rd.fieldnames or [])):raise RuntimeError('schema '+stem)
  for r in rd:
   try:t=pd.to_datetime(r['create_time'],utc=True);a=float(r[FIELD])
   except (ValueError,TypeError):continue
   if np.isfinite(a) and a>0:rows.append((t,np.log(a)))
 if not rows:return s,[]
 df=pd.DataFrame(rows,columns=['t','x']).sort_values('t').drop_duplicates('t',keep='last').set_index('t').resample('1h').last();return s,[(t,r.x) for t,r in df.dropna().iterrows()]

def rz(x):
 n=x.notna().sum(axis=1);m=x.median(axis=1);d=x.sub(m,axis=0);mad=d.abs().median(axis=1);v=(n>=10)&np.isfinite(mad)&(mad>1e-12);return d.div(mad.where(v),axis=0).where(v,np.nan)

def main():
 assert (PROJECT/'research'/'v99_r106_phase107_toptrader_conviction_prereg.md').exists();prev=json.loads((PROJECT/'reports'/'candidate_v99_r106_phase106_toptrader_size_divergence_train_alpha.json').read_text());assert prev['status']=='TRAIN_ALPHA_REJECT' and prev['precommitment']['holdout_not_parsed']
 da=json.loads((PROJECT/'reports'/'candidate_v99_r106_phase63_metrics_data_audit.json').read_text());assert da['status']=='DATA_AUDIT_COMPLETE' and da['holdout_not_listed_or_parsed'];jobs=[]
 for s,v in da['symbols'].items():
  if v['first']:
   miss=set(v['missing_dates']);jobs += [(s,d.date().isoformat()) for d in pd.date_range(v['first'],da['train_end'],freq='D') if d.date().isoformat() not in miss]
 with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:loaded=list(pool.map(load,jobs))
 cfg,data,raw,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup();x=pd.DataFrame(index=data.close.index,columns=data.close.columns,dtype=float)
 for s,rows in loaded:
  if s not in x.columns:continue
  for t,v in rows:
   if t in x.index:x.at[t,s]=v
 z=rz(x).shift(1);sig=np.tanh(z).where(z.notna().sum(axis=1)>=10,0).fillna(0);targets=sig.div(sig.abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
 result=p1.run_targets(data,targets,ex,guard,float(ex['severe_cost_per_side']),ALPHA_GROSS);te=pd.Timestamp(da['train_end'],tz='UTC');d=p47.diag(result,data.close.index,max(data.close.index[0],pd.Timestamp('2021-12-01',tz='UTC')),te);passed=bool(d['stable_train'])
 out={'study':'V99 R106 Phase107 — TOP-TRADER CONVICTION TRAIN-ONLY alpha gate','status':'TRAIN_ALPHA_PASS_FREEZE_FOR_DOWNSTREAM' if passed else 'TRAIN_ALPHA_REJECT','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'prereg':'research/v99_r106_phase107_toptrader_conviction_prereg.md','source':'Binance USD-M sum_toptrader_long_short_ratio','transform':'median/MAD robust z of log(position-weighted toptrader long/short ratio), whole alpha shifted t-1; tanh; L1 normalized','direction':'larger position-weighted top-trader long tilt continuation','single_hypothesis_no_grid':True,'alpha_gross':ALPHA_GROSS,'selection_train_only':True,'holdout_not_parsed':True,'missing_archives_not_filled':True,'simultaneous_crosssection_required':True,'min_assets':10,'unit_tanh_scale_fixed':True},'train_end':te.isoformat(),'diagnostic':d,'selected_train_only':'native_toptrader_conviction' if passed else None,'archives_consumed':len(jobs),'next_gate':'PASS freezes exact spec for supersevere/regime/benchmark/reproducibility before untouched holdout; FAIL permanent, no retuning.','quarantined_symbols':quarantined};OUT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n');print(json.dumps({'status':out['status'],'healthy_folds':d['healthy_folds'],'valid_folds':d['valid_folds'],'train':d['train']},indent=2,default=audit.safe_float))
if __name__=='__main__':main()
