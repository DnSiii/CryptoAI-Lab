from __future__ import annotations
import concurrent.futures,csv,hashlib,io,json,time,urllib.error,urllib.request,zipfile
from pathlib import Path
import numpy as np,pandas as pd
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase47_downside_semivariance_alpha_audit as p47
import run_v99_r105_all_regime_structural_audit as audit
PROJECT=Path(__file__).resolve().parents[1];OUT=PROJECT/'reports'/'candidate_v99_r106_phase99_toptrader_crowd_spread_train_alpha.json';BASE='https://data.binance.vision/data/futures/um/daily/metrics';TOP='count_toptrader_long_short_ratio';CROWD='count_long_short_ratio';ALPHA_GROSS=.20

def get(u):
 last=None
 for attempt in range(5):
  try:
   req=urllib.request.Request(u,headers={'User-Agent':'CryptoAI-v99-r106-phase99'})
   with urllib.request.urlopen(req,timeout=90) as r:return r.read()
  except (urllib.error.URLError,TimeoutError,ConnectionError) as e:last=e;time.sleep(2**attempt)
 raise last

def load(job):
 s,d=job;stem=f'{s}-metrics-{d}.zip';u=f'{BASE}/{s}/{stem}';raw=get(u);chk=get(u+'.CHECKSUM')
 if hashlib.sha256(raw).hexdigest()!=chk.decode().split()[0]:raise RuntimeError('checksum '+stem)
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  if z.testzip() is not None:raise RuntimeError('crc '+stem)
  rd=csv.DictReader(io.TextIOWrapper(z.open(z.namelist()[0]),encoding='utf-8'));rows=[];need={'create_time',TOP,CROWD}
  if not need.issubset(set(rd.fieldnames or [])):raise RuntimeError('schema '+stem+': '+repr(rd.fieldnames))
  for r in rd:
   t=pd.to_datetime(r['create_time'],utc=True);a=(r.get(TOP) or '').strip();b=(r.get(CROWD) or '').strip()
   if not a or not b:continue
   try:a=float(a);b=float(b)
   except ValueError:continue
   if not np.isfinite(a) or not np.isfinite(b) or a<=0 or b<=0:continue
   rows.append((t,float(np.log(a)-np.log(b))))
 if not rows:return s,[]
 df=pd.DataFrame(rows,columns=['t','spread']).sort_values('t').drop_duplicates('t',keep='last').set_index('t').resample('1h').last();return s,list(df['spread'].dropna().items())

def robust_z(x,min_assets=10):
 n=x.notna().sum(axis=1);med=x.median(axis=1,skipna=True);dev=x.sub(med,axis=0);mad=dev.abs().median(axis=1,skipna=True);valid=(n>=min_assets)&np.isfinite(mad)&(mad>1e-12);return dev.div(mad.where(valid),axis=0).where(valid,np.nan)

def main():
 assert (PROJECT/'research'/'v99_r106_phase99_toptrader_crowd_spread_prereg.md').exists();prev=json.loads((PROJECT/'reports'/'candidate_v99_r106_phase98_oi_confirmed_momentum_train_alpha.json').read_text());assert prev['status']=='TRAIN_ALPHA_REJECT' and prev['precommitment']['holdout_not_parsed']
 da=json.loads((PROJECT/'reports'/'candidate_v99_r106_phase63_metrics_data_audit.json').read_text());assert da['status']=='DATA_AUDIT_COMPLETE' and da['holdout_not_listed_or_parsed'];jobs=[]
 for s,v in da['symbols'].items():
  if not v['first']:continue
  missing=set(v['missing_dates']);dates=pd.date_range(v['first'],da['train_end'],freq='D');jobs += [(s,d.date().isoformat()) for d in dates if d.date().isoformat() not in missing]
 with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:loaded=list(pool.map(load,jobs))
 cfg,data,raw,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup();spread=pd.DataFrame(index=data.close.index,columns=data.close.columns,dtype=float)
 for s,rows in loaded:
  if s not in spread.columns:continue
  ser=pd.Series(dict(rows),dtype=float);ix=spread.index.intersection(ser.index);spread.loc[ix,s]=ser.reindex(ix).values
 causal=spread.shift(1);z=robust_z(causal);rawsig=np.tanh(z);valid=z.notna().sum(axis=1)>=10;rawsig=rawsig.where(valid,0.0).fillna(0.0);den=rawsig.abs().sum(axis=1).replace(0,np.nan);targets=rawsig.div(den,axis=0).fillna(0.0)
 severe=float(ex['severe_cost_per_side']);result=p1.run_targets(data,targets,ex,guard,severe,ALPHA_GROSS);train_end=pd.Timestamp(da['train_end'],tz='UTC');start=max(data.close.index[0],pd.Timestamp('2021-12-01',tz='UTC'));d=p47.diag(result,data.close.index,start,train_end);passed=bool(d['stable_train'])
 out={'study':'V99 R106 Phase99 — TOP-TRADER VS CROWD SPREAD TRAIN-ONLY alpha gate','status':'TRAIN_ALPHA_PASS_FREEZE_FOR_DOWNSTREAM' if passed else 'TRAIN_ALPHA_REJECT','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'prereg':'research/v99_r106_phase99_toptrader_crowd_spread_prereg.md','source':'Binance USD-M daily metrics count_toptrader_long_short_ratio + count_long_short_ratio','transform':'log(top-trader account L/S)-log(broad account L/S), complete spread shifted t-1; simultaneous median/MAD z; raw=tanh(z_spread); L1 normalized; min 10 assets','direction':'continuation toward relative top-trader-vs-crowd positioning spread','single_hypothesis_no_grid':True,'alpha_gross':ALPHA_GROSS,'selection_train_only':True,'holdout_not_parsed':True,'missing_archives_not_filled':True,'simultaneous_crosssection_required':True,'min_assets':10,'unit_tanh_scale_fixed':True},'train_end':train_end.isoformat(),'diagnostic':d,'selected_train_only':'native_toptrader_crowd_spread' if passed else None,'archives_consumed':len(jobs),'next_gate':'If pass, freeze exact specification and evaluate supersevere/regime/benchmark/reproducibility gates before untouched holdout; if reject, no retuning.','quarantined_symbols':quarantined,'disclosure':'Phase99 consumes native positioning metrics only through train_end; every archive SHA256+CRC verified; complete spread shifted t-1; simultaneous robust cross-section >=10 assets; fixed transform and direction; no tuning; no holdout inspected.'};OUT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n');print(json.dumps({'status':out['status'],'archives_consumed':len(jobs),'healthy_folds':d['healthy_folds'],'valid_folds':d['valid_folds'],'train':d['train']},indent=2,default=audit.safe_float))
if __name__=='__main__':main()
