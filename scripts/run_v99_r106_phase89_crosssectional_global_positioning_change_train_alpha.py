from __future__ import annotations
import concurrent.futures,csv,hashlib,io,json,time,urllib.error,urllib.request,zipfile
from pathlib import Path
import numpy as np,pandas as pd
import run_v99_r106_phase31_cross_sectional_low_vol_alpha_audit as p31
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase47_downside_semivariance_alpha_audit as p47
import run_v99_r105_all_regime_structural_audit as audit
PROJECT=Path(__file__).resolve().parents[1];OUT=PROJECT/'reports'/'candidate_v99_r106_phase89_crosssectional_global_positioning_change_train_alpha.json';BASE='https://data.binance.vision/data/futures/um/daily/metrics';ALPHA_GROSS=.20
GLOBAL='count_long_short_ratio'
def get(u):
 last=None
 for attempt in range(5):
  try:
   req=urllib.request.Request(u,headers={'User-Agent':'CryptoAI-v99-r106-phase89'})
   with urllib.request.urlopen(req,timeout=90) as r:return r.read()
  except (urllib.error.URLError,TimeoutError,ConnectionError) as e:last=e;time.sleep(2**attempt)
 raise last
def load(job):
 s,d=job;stem=f'{s}-metrics-{d}.zip';u=f'{BASE}/{s}/{stem}';raw=get(u);chk=get(u+'.CHECKSUM')
 if hashlib.sha256(raw).hexdigest()!=chk.decode().split()[0]:raise RuntimeError('checksum '+stem)
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  if z.testzip() is not None:raise RuntimeError('crc '+stem)
  rd=csv.DictReader(io.TextIOWrapper(z.open(z.namelist()[0]),encoding='utf-8'));rows=[];need={'create_time',GLOBAL}
  if not need.issubset(set(rd.fieldnames or [])):raise RuntimeError('schema '+stem+': '+repr(rd.fieldnames))
  for r in rd:
   t=pd.to_datetime(r['create_time'],utc=True);a=(r.get(GLOBAL) or '').strip()
   if not a:continue
   try:a=float(a)
   except ValueError:continue
   if not np.isfinite(a) or a<=0:continue
   rows.append((t,a))
 if not rows:return s,[]
 df=pd.DataFrame(rows,columns=['t','global']).sort_values('t').drop_duplicates('t',keep='last').set_index('t').resample('1h').last();adj=(df.index.to_series().diff()==pd.Timedelta(hours=1));chg=np.log(df['global']/df['global'].shift(1)).where(adj).replace([np.inf,-np.inf],np.nan).dropna();return s,list(chg.items())
def cs_weights(feature,close):
 x=feature.reindex(index=close.index,columns=close.columns);r=x.rank(axis=1,pct=True,method='average');n=x.notna().sum(axis=1);raw=-(r-.5);raw=raw.where(n>=10,0.0);den=raw.abs().sum(axis=1).replace(0,np.nan);return raw.div(den,axis=0).fillna(0.0)
def main():
 prev=json.loads((PROJECT/'reports'/'candidate_v99_r106_phase87_oi_confirmed_topcapital_change_train_alpha.json').read_text());assert prev['status']=='TRAIN_ALPHA_REJECT' and prev['precommitment']['holdout_not_parsed']
 da=json.loads((PROJECT/'reports'/'candidate_v99_r106_phase63_metrics_data_audit.json').read_text());assert da['status']=='DATA_AUDIT_COMPLETE' and da['holdout_not_listed_or_parsed'];jobs=[]
 for s,v in da['symbols'].items():
  if not v['first']:continue
  missing=set(v['missing_dates']);dates=pd.date_range(v['first'],da['train_end'],freq='D');jobs += [(s,d.date().isoformat()) for d in dates if d.date().isoformat() not in missing]
 with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:loaded=list(pool.map(load,jobs))
 cfg,data,raw,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup();f=pd.DataFrame(index=data.close.index,columns=data.close.columns,dtype=float)
 for s,rows in loaded:
  if s not in f.columns:continue
  ser=pd.Series(dict(rows),dtype=float);ix=f.index.intersection(ser.index);f.loc[ix,s]=ser.reindex(ix).values
 feature=f.shift(1);targets=cs_weights(feature,data.close);severe=float(ex['severe_cost_per_side']);result=p1.run_targets(data,targets,ex,guard,severe,ALPHA_GROSS);train_end=pd.Timestamp(da['train_end'],tz='UTC');start=max(data.close.index[0],pd.Timestamp('2021-12-01',tz='UTC'));d=p47.diag(result,data.close.index,start,train_end);passed=bool(d['stable_train'])
 out={'study':'V99 R106 Phase89 — CROSS-SECTIONAL GLOBAL POSITIONING CHANGE TRAIN-ONLY alpha gate','status':'TRAIN_ALPHA_PASS_FREEZE_FOR_DOWNSTREAM' if passed else 'TRAIN_ALPHA_REJECT','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'prereg':'research/v99_r106_phase89_crosssectional_global_positioning_change_prereg.md','source':'Binance USD-M daily metrics count_long_short_ratio','transform':'cross-sectional percentile rank of log(global_t/global_t-1).shift(1), contrarian centered rank, min 10 simultaneous assets','direction':'contrarian','single_hypothesis_no_grid':True,'alpha_gross':ALPHA_GROSS,'selection_train_only':True,'holdout_not_parsed':True,'missing_archives_not_filled':True,'adjacent_hour_changes_required':True,'simultaneous_crosssection_required':True,'min_assets':10},'train_end':train_end.isoformat(),'diagnostic':d,'selected_train_only':'native_crosssectional_global_positioning_change' if passed else None,'archives_consumed':len(jobs),'next_gate':'If pass, freeze exact specification and evaluate supersevere/regime/benchmark/reproducibility gates before untouched holdout; if reject, no retuning.','quarantined_symbols':quarantined,'disclosure':'Phase89 consumes native metrics only through train_end; every archive SHA256+CRC verified; global ratio must be positive finite; changes require adjacent hours; feature shifted t-1; ranking is simultaneous cross-sectional with >=10 assets; fixed contrarian direction; no holdout metrics/returns inspected.'};OUT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n');print(json.dumps({'status':out['status'],'archives_consumed':len(jobs),'healthy_folds':d['healthy_folds'],'valid_folds':d['valid_folds'],'train':d['train']},indent=2,default=audit.safe_float))
if __name__=='__main__':main()
