from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import run_v99_r106_phase92_global_positioning_robust_distance_train_alpha as p92
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase47_downside_semivariance_alpha_audit as p47
import run_v99_r105_all_regime_structural_audit as audit
PROJECT=Path(__file__).resolve().parents[1]
OUT=PROJECT/'reports'/'candidate_v99_r106_phase93_global_positioning_robust_distance_continuation_train_alpha.json'
ALPHA_GROSS=.20

def cs_weights(feature,close):
 x=feature.reindex(index=close.index,columns=close.columns);n=x.notna().sum(axis=1);med=x.median(axis=1,skipna=True);dev=x.sub(med,axis=0);mad=dev.abs().median(axis=1,skipna=True);valid=(n>=10)&np.isfinite(mad)&(mad>1e-12);z=dev.div(mad.where(valid),axis=0);raw=np.tanh(z);raw=raw.where(valid,0.0).fillna(0.0);den=raw.abs().sum(axis=1).replace(0,np.nan);return raw.div(den,axis=0).fillna(0.0)

def main():
 assert (PROJECT/'research'/'v99_r106_phase93_global_positioning_robust_distance_continuation_prereg.md').exists()
 prev=json.loads((PROJECT/'reports'/'candidate_v99_r106_phase92_global_positioning_robust_distance_train_alpha.json').read_text());assert prev['status']=='TRAIN_ALPHA_REJECT' and prev['precommitment']['holdout_not_parsed']
 da=json.loads((PROJECT/'reports'/'candidate_v99_r106_phase63_metrics_data_audit.json').read_text());assert da['status']=='DATA_AUDIT_COMPLETE' and da['holdout_not_listed_or_parsed'];jobs=[]
 for s,v in da['symbols'].items():
  if not v['first']:continue
  missing=set(v['missing_dates']);dates=pd.date_range(v['first'],da['train_end'],freq='D');jobs += [(s,d.date().isoformat()) for d in dates if d.date().isoformat() not in missing]
 import concurrent.futures
 with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:loaded=list(pool.map(p92.load,jobs))
 cfg,data,raw,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup();f=pd.DataFrame(index=data.close.index,columns=data.close.columns,dtype=float)
 for s,rows in loaded:
  if s not in f.columns:continue
  ser=pd.Series(dict(rows),dtype=float);ix=f.index.intersection(ser.index);f.loc[ix,s]=ser.reindex(ix).values
 feature=f.shift(1);targets=cs_weights(feature,data.close);severe=float(ex['severe_cost_per_side']);result=p1.run_targets(data,targets,ex,guard,severe,ALPHA_GROSS);train_end=pd.Timestamp(da['train_end'],tz='UTC');start=max(data.close.index[0],pd.Timestamp('2021-12-01',tz='UTC'));d=p47.diag(result,data.close.index,start,train_end);passed=bool(d['stable_train'])
 out={'study':'V99 R106 Phase93 — ROBUST GLOBAL POSITIONING DISTANCE CONTINUATION TRAIN-ONLY alpha gate','status':'TRAIN_ALPHA_PASS_FREEZE_FOR_DOWNSTREAM' if passed else 'TRAIN_ALPHA_REJECT','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'prereg':'research/v99_r106_phase93_global_positioning_robust_distance_continuation_prereg.md','source':'Binance USD-M daily metrics count_long_short_ratio','transform':'log level shifted t-1; simultaneous median/MAD robust z; raw=+tanh(z); L1 normalized; min 10 assets','direction':'continuation robust distance','single_hypothesis_no_grid':True,'alpha_gross':ALPHA_GROSS,'selection_train_only':True,'holdout_not_parsed':True,'missing_archives_not_filled':True,'simultaneous_crosssection_required':True,'min_assets':10,'unit_tanh_scale_fixed':True},'train_end':train_end.isoformat(),'diagnostic':d,'selected_train_only':'native_global_positioning_robust_distance_continuation' if passed else None,'archives_consumed':len(jobs),'next_gate':'If pass, freeze exact specification and evaluate supersevere/regime/benchmark/reproducibility gates before untouched holdout; if reject, no retuning.','quarantined_symbols':quarantined,'disclosure':'Phase93 consumes native metrics only through train_end; every archive SHA256+CRC verified by Phase92 loader; positive finite ratio; feature shifted t-1; simultaneous median/MAD >=10 assets; degenerate MAD zero exposure; fixed +tanh(z), no tuning; no holdout inspected.'};OUT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n');print(json.dumps({'status':out['status'],'archives_consumed':len(jobs),'healthy_folds':d['healthy_folds'],'valid_folds':d['valid_folds'],'train':d['train']},indent=2,default=audit.safe_float))
if __name__=='__main__':main()
