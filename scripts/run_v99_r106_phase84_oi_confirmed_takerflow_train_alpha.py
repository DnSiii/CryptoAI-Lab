from __future__ import annotations
import concurrent.futures,csv,hashlib,io,json,time,urllib.error,urllib.request,zipfile
from pathlib import Path
import numpy as np,pandas as pd
import run_v99_r106_phase31_cross_sectional_low_vol_alpha_audit as p31
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase47_downside_semivariance_alpha_audit as p47
import run_v99_r105_all_regime_structural_audit as audit
PROJECT=Path(__file__).resolve().parents[1];OUT=PROJECT/'reports'/'candidate_v99_r106_phase84_oi_confirmed_takerflow_train_alpha.json';BASE='https://data.binance.vision/data/futures/um/daily/metrics';ALPHA_GROSS=.20
TAKER='sum_taker_long_short_vol_ratio';OI='sum_open_interest_value'
def get(u):
 last=None
 for attempt in range(5):
  try:
   req=urllib.request.Request(u,headers={'User-Agent':'CryptoAI-v99-r106-phase84'})
   with urllib.request.urlopen(req,timeout=90) as r:return r.read()
  except (urllib.error.URLError,TimeoutError,ConnectionError) as e:last=e;time.sleep(2**attempt)
 raise last
def load(job):
 s,d=job;stem=f'{s}-metrics-{d}.zip';u=f'{BASE}/{s}/{stem}';raw=get(u);chk=get(u+'.CHECKSUM')
 if hashlib.sha256(raw).hexdigest()!=chk.decode().split()[0]:raise RuntimeError('checksum '+stem)
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  if z.testzip() is not None:raise RuntimeError('crc '+stem)
  rd=csv.DictReader(io.TextIOWrapper(z.open(z.namelist()[0]),encoding='utf-8'));rows=[];need={'create_time',TAKER,OI}
  if not need.issubset(set(rd.fieldnames or [])):raise RuntimeError('schema '+stem+': '+repr(rd.fieldnames))
  for r in rd:
   t=pd.to_datetime(r['create_time'],utc=True);a=(r.get(TAKER) or '').strip();b=(r.get(OI) or '').strip()
   if not a or not b:continue
   try:a=float(a);b=float(b)
   except ValueError:continue
   if not np.isfinite(a) or not np.isfinite(b) or a<=0 or b<=0:continue
   rows.append((t,a,b))
 if not rows:return s,[]
 df=pd.DataFrame(rows,columns=['t','taker','oi']).sort_values('t').drop_duplicates('t',keep='last').set_index('t').resample('1h').last()
 # Adjacent completed UTC hours only: pct/log growth is invalid across any missing hour.
 prev=df['oi'].shift(1);adj=(df.index.to_series().diff()==pd.Timedelta(hours=1));growth=np.log(df['oi']/prev).where(adj);raw=np.log(df['taker'])*growth.clip(lower=0);raw=raw.replace([np.inf,-np.inf],np.nan).dropna();return s,list(raw.items())
def main():
 prev=json.loads((PROJECT/'reports'/'candidate_v99_r106_phase83_topaccount_takerflow_divergence_train_alpha.json').read_text());assert prev['status']=='TRAIN_ALPHA_REJECT' and prev['precommitment']['holdout_not_parsed']
 da=json.loads((PROJECT/'reports'/'candidate_v99_r106_phase63_metrics_data_audit.json').read_text());assert da['status']=='DATA_AUDIT_COMPLETE' and da['holdout_not_listed_or_parsed'];jobs=[]
 for s,v in da['symbols'].items():
  if not v['first']:continue
  missing=set(v['missing_dates']);dates=pd.date_range(v['first'],da['train_end'],freq='D');jobs += [(s,d.date().isoformat()) for d in dates if d.date().isoformat() not in missing]
 with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:loaded=list(pool.map(load,jobs))
 cfg,data,raw,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup();f=pd.DataFrame(index=data.close.index,columns=data.close.columns,dtype=float)
 for s,rows in loaded:
  if s not in f.columns:continue
  ser=pd.Series(dict(rows),dtype=float);ix=f.index.intersection(ser.index);f.loc[ix,s]=ser.reindex(ix).values
 feature=f.shift(1);targets=p31.weights(feature,data.close);severe=float(ex['severe_cost_per_side']);result=p1.run_targets(data,targets,ex,guard,severe,ALPHA_GROSS);train_end=pd.Timestamp(da['train_end'],tz='UTC');start=max(data.close.index[0],pd.Timestamp('2021-12-01',tz='UTC'));d=p47.diag(result,data.close.index,start,train_end);passed=bool(d['stable_train'])
 out={'study':'V99 R106 Phase84 — native OI-CONFIRMED TAKER-FLOW TRAIN-ONLY alpha gate','status':'TRAIN_ALPHA_PASS_FREEZE_FOR_DOWNSTREAM' if passed else 'TRAIN_ALPHA_REJECT','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'prereg':'research/v99_r106_phase84_oi_confirmed_takerflow_prereg.md','source':'Binance USD-M daily metrics sum_taker_long_short_vol_ratio + sum_open_interest_value','transform':'[log(taker_t) * max(log(OI_t/OI_t-1),0)].shift(1)','direction':'continuation','single_hypothesis_no_grid':True,'alpha_gross':ALPHA_GROSS,'selection_train_only':True,'holdout_not_parsed':True,'missing_archives_not_filled':True,'adjacent_hour_oi_growth_required':True,'same_hour_pair_required':True},'train_end':train_end.isoformat(),'diagnostic':d,'selected_train_only':'native_oi_confirmed_takerflow' if passed else None,'archives_consumed':len(jobs),'next_gate':'If pass, freeze exact specification and evaluate supersevere/regime/benchmark/reproducibility gates before untouched holdout; if reject, no retuning.','quarantined_symbols':quarantined,'disclosure':'Phase84 consumes native metrics only through train_end; every archive SHA256+CRC verified; taker and OI must be positive finite in same hour; OI growth requires adjacent hours; interaction shifted t-1; no holdout metrics/returns inspected.'};OUT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n');print(json.dumps({'status':out['status'],'archives_consumed':len(jobs),'healthy_folds':d['healthy_folds'],'valid_folds':d['valid_folds'],'train':d['train']},indent=2,default=audit.safe_float))
if __name__=='__main__':main()
