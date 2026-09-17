from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase37_funding_pressure_reversal_alpha_audit as p37
import run_v99_r105_all_regime_structural_audit as audit
PROJECT=Path(__file__).resolve().parents[1]; REPORT=PROJECT/'reports'/'candidate_v99_r106_phase39_tail_dependence_envelope.json'; ALPHA_GROSS=.20

def stats(result,a,b):
    r=result.equity.pct_change(fill_method=None).fillna(0.0); active=result.gross_exposure.gt(1e-12); v=r.loc[active & (r.index>=a) & (r.index<=b)].to_numpy(float); v=v[np.isfinite(v)]; pos=float(v[v>0].sum()); n=max(1,int(np.ceil(len(v)*.01))); top=np.sort(v)[-n:]; kept=np.sort(v)[:-n]; return {'n':int(len(v)),'mean':float(v.mean()),'median':float(np.median(v)),'top1_share_positive':float(top.sum()/pos) if pos>0 else 0.0,'mean_without_top1':float(kept.mean()) if len(kept) else 0.0}
def main():
    cfg,data,raw,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup(); severe=float(ex['severe_cost_per_side']); benchmarks=p1.r98.r86.r55.benchmark_items(cfg,data,raw,ex,guard,gross); start=max([data.close.index[0]]+[x['data'].close.index[0] for x in benchmarks.values()]); end=min([data.close.index[-1]]+[x['data'].close.index[-1] for x in benchmarks.values()]); train_end=min(p1.TRAIN_END,end); bench={}
    for name,item in benchmarks.items(): bench[name]=stats(audit.exact_benchmark_result(item,float(item['execution']['severe_cost_per_side'])),start,train_end)
    candidates={name:stats(p1.run_targets(data,target,ex,guard,severe,ALPHA_GROSS),start,train_end) for name,target in p37.sleeves(data).items()}; shares=[x['top1_share_positive'] for x in bench.values()]; robust=[x['mean_without_top1'] for x in bench.values()]
    out={'study':'V99 R106 phase 39 — severe-cost tail-dependence envelope','status':'DIAGNOSTIC_ONLY_NO_STRATEGY_CHANGE','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'objective':'compare phase37 tail dependence to established severe-cost benchmarks after phase38 showed every benchmark also has negative top1-removed mean','train_only_diagnostic':True,'untouched_holdout_not_evaluated':True,'does_not_relax_any_gate':True,'strategy_change_in_phase39':False},'benchmarks':bench,'benchmark_envelope':{'top1_share_positive_min':min(shares),'top1_share_positive_max':max(shares),'mean_without_top1_min':min(robust),'mean_without_top1_max':max(robust)},'phase37':candidates,'quarantined_symbols':quarantined,'metadata':metadata,'disclosure':'Calibration only; no promotion and no relaxation of anti-overfit gates.'}; REPORT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n',encoding='utf-8'); print(json.dumps({'benchmark_envelope':out['benchmark_envelope'],'phase37':candidates},indent=2),flush=True)
if __name__=='__main__': main()
