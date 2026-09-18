from __future__ import annotations
import concurrent.futures,csv,hashlib,io,json,urllib.error,urllib.request,zipfile
from pathlib import Path
import numpy as np,pandas as pd
import run_v99_r106_phase31_cross_sectional_low_vol_alpha_audit as p31
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase47_downside_semivariance_alpha_audit as p47
import run_v99_r105_all_regime_structural_audit as audit
PROJECT=Path(__file__).resolve().parents[1];OUT=PROJECT/'reports'/'candidate_v99_r106_phase64_oi_expansion_train_alpha.json';BASE='https://data.binance.vision/data/futures/um/daily/metrics';H=24;ALPHA_GROSS=.20

def get(u):
 req=urllib.request.Request(u,headers={'User-Agent':'CryptoAI-v99-r106-phase64'})
 with urllib.request.urlopen(req,timeout=90) as r:return r.read()

def load(job):
 s,d=job;stem=f'{s}-metrics-{d}.zip';u=f'{BASE}/{s}/{stem}';raw=get(u);chk=get(u+'.CHECKSUM')
 if hashlib.sha256(raw).hexdigest()!=chk.decode().split()[0]:raise RuntimeError('checksum '+stem)
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  if z.testzip() is not None:raise RuntimeError('crc '+stem)
  rd=csv.DictReader(io.TextIOWrapper(z.open(z.namelist()[0]),encoding='utf-8'));rows=[]
  for r in rd:
   t=pd.to_datetime(r['create_time'],utc=True);v=float(r['sum_open_interest_value']);rows.append((t,v))
 if not rows:raise RuntimeError('empty '+stem)
 # Native metrics are intraday; retain last completed observation in each UTC hour.
 df=pd.DataFrame(rows,columns=['t','v']).sort_values('t').drop_duplicates('t',keep='last').set_index('t');h=df['v'].resample('1h').last().dropna();return s,list(h.items())

def main():
 da=json.loads((PROJECT/'reports'/'candidate_v99_r106_phase63_metrics_data_audit.json').read_text());assert da['status']=='DATA_AUDIT_COMPLETE' and da['holdout_not_listed_or_parsed'];jobs=[]
 for s,v in da['symbols'].items():
  if not v['first']:continue
  missing=set(v['missing_dates']);dates=pd.date_range(v['first'],da['train_end'],freq='D')
  jobs += [(s,d.date().isoformat()) for d in dates if d.date().isoformat() not in missing]
 with concurrent.futures.ThreadPoolExecutor(max_workers=32) as pool:loaded=list(pool.map(load,jobs))
 cfg,data,raw,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup();idx=data.close.index;oi=pd.DataFrame(index=idx,columns=data.close.columns,dtype=float)
 for s,rows in loaded:
  if s not in oi.columns:continue
  ser=pd.Series(dict(rows));ix=oi.index.intersection(ser.index);oi.loc[ix,s]=ser.reindex(ix).values
 oi_chg=oi/oi.shift(H)-1.0;ret=data.close/data.close.shift(H)-1.0;raw_score=np.sign(ret)*oi_chg.clip(lower=0.0);lo=raw_score.quantile(.05,axis=1);hi=raw_score.quantile(.95,axis=1);feature=raw_score.clip(lower=lo,upper=hi,axis=0).shift(1)
 targets=p31.weights(feature,data.close);severe=float(ex['severe_cost_per_side']);result=p1.run_targets(data,targets,ex,guard,severe,ALPHA_GROSS);train_end=pd.Timestamp(da['train_end'],tz='UTC');start=max(data.close.index[0],pd.Timestamp('2021-12-01',tz='UTC'));d=p47.diag(result,data.close.index,start,train_end);passed=bool(d['stable_train'])
 out={'study':'V99 R106 Phase64 — native OI expansion confirmation TRAIN-ONLY alpha gate','status':'TRAIN_ALPHA_PASS_FREEZE_FOR_HOLDOUT' if passed else 'TRAIN_ALPHA_REJECT','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'prereg':'research/v99_r106_phase64_oi_expansion_confirmation_prereg.md','source':'Binance USD-M daily metrics sum_open_interest_value','transform':'winsor05/95[sign(ret24)*max(oi_value/oi_value.shift24-1,0)].shift(1)','single_hypothesis_no_grid':True,'alpha_gross':ALPHA_GROSS,'selection_train_only':True,'holdout_not_parsed':True,'missing_archives_not_filled':True},'train_end':train_end.isoformat(),'diagnostic':d,'selected_train_only':'native_oi_expansion_confirmation_24h' if passed else None,'archives_consumed':len(jobs),'next_gate':'If pass, freeze exact specification and evaluate untouched holdout separately; if reject, no sign/horizon/OI-field/winsor retuning.','quarantined_symbols':quarantined,'disclosure':'Phase64 consumes native metrics only through train_end; every consumed archive is SHA256+CRC verified; no holdout metrics/returns are inspected.'};OUT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n');print(json.dumps({'status':out['status'],'archives_consumed':len(jobs),'healthy_folds':d['healthy_folds'],'valid_folds':d['valid_folds'],'train':d['train']},indent=2,default=audit.safe_float))
if __name__=='__main__':main()
