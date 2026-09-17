from __future__ import annotations
import json
from pathlib import Path
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase17_blv_leadership_alpha as p17
import run_v99_r106_phase4_bear_subregimes as p4
import run_v99_r105_all_regime_structural_audit as audit
PROJECT=Path(__file__).resolve().parents[1]; REPORT=PROJECT/'reports'/'candidate_v99_r106_phase38_benchmark_robustness_calibration.json'

def rows(result,index,a,b):
    train=p17.sleeve_row(result,a,b); folds=[]; good=0
    for i,(lo,hi) in enumerate(p4.fold_bounds(index,a,b),1):
        r=p17.sleeve_row(result,lo,hi); healthy=bool(float(r['roi'])>0 and float(r['profit_factor'])>1 and float(r['robust_mean_without_top1pct'])>0); good+=int(healthy); folds.append({'fold':i,'healthy':healthy,**r})
    return {'train':train,'healthy_folds':good,'folds':folds}
def main():
    cfg,data,raw,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup(); benchmarks=p1.r98.r86.r55.benchmark_items(cfg,data,raw,ex,guard,gross); start=max([data.close.index[0]]+[x['data'].close.index[0] for x in benchmarks.values()]); end=min([data.close.index[-1]]+[x['data'].close.index[-1] for x in benchmarks.values()]); train_end=min(p1.TRAIN_END,end); outrows={}
    for name,item in benchmarks.items():
        base=audit.exact_benchmark_result(item,float(item['execution']['base_cost_per_side'])); severe=audit.exact_benchmark_result(item,float(item['execution']['severe_cost_per_side'])); outrows[name]={'base':rows(base,item['data'].close.index,start,train_end),'severe':rows(severe,item['data'].close.index,start,train_end)}
    out={'study':'V99 R106 phase 38 — benchmark robustness calibration','status':'DIAGNOSTIC_ONLY_NO_STRATEGY_CHANGE','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'objective':'calibrate the same top-1%-removed robust-mean diagnostic against the established benchmark envelope before interpreting repeated phase31-37 failures','train_only_diagnostic':True,'untouched_holdout_not_evaluated':True,'does_not_relax_any_gate':True,'strategy_change_in_phase38':False},'data':{'common_start':start.isoformat(),'train_end':train_end.isoformat()},'benchmarks':outrows,'quarantined_symbols':quarantined,'metadata':metadata,'disclosure':'Calibration only. This report cannot weaken promotion criteria or modify frozen assets.'}; REPORT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n',encoding='utf-8'); print(json.dumps({n:{c:{'roi':x[c]['train']['roi'],'pf':x[c]['train']['profit_factor'],'robust':x[c]['train']['robust_mean_without_top1pct'],'healthy_folds':x[c]['healthy_folds']} for c in ('base','severe')} for n,x in outrows.items()},indent=2),flush=True)
if __name__=='__main__': main()
