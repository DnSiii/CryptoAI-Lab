from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase33_cross_sectional_volume_trend_alpha_audit as p33
import run_v99_r106_phase34_cross_sectional_tail_risk_alpha_audit as p34
import run_v99_r105_all_regime_structural_audit as audit
PROJECT=Path(__file__).resolve().parents[1]; REPORT=PROJECT/'reports'/'candidate_v99_r106_phase36_tail_concentration_diagnostic.json'; ALPHA_GROSS=.20

def tail_stats(result,a,b):
    r=result.equity.pct_change(fill_method=None).fillna(0.0); active=result.gross_exposure.gt(1e-12); v=r.loc[active & (r.index>=a) & (r.index<=b)].to_numpy(float); v=v[np.isfinite(v)]
    if not len(v): return {}
    total=float(v.sum()); pos=float(v[v>0].sum()); out={'n':int(len(v)),'sum_return':total,'mean':float(v.mean()),'median':float(np.median(v)),'positive_sum':pos}
    for pct in (.001,.005,.01,.02,.05):
        n=max(1,int(np.ceil(len(v)*pct))); top=np.sort(v)[-n:]; out[f'top_{pct*100:g}pct_sum']=float(top.sum()); out[f'top_{pct*100:g}pct_share_of_positive']=float(top.sum()/pos) if pos>0 else 0.0; kept=np.sort(v)[:-n] if n<len(v) else np.array([]); out[f'mean_without_top_{pct*100:g}pct']=float(kept.mean()) if len(kept) else 0.0
    return out

def main():
    cfg,data,raw,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup(); benchmarks=p1.r98.r86.r55.benchmark_items(cfg,data,raw,ex,guard,gross); start=max([data.close.index[0]]+[x['data'].close.index[0] for x in benchmarks.values()]); end=min([data.close.index[-1]]+[x['data'].close.index[-1] for x in benchmarks.values()]); train_end=min(p1.TRAIN_END,end); families={'phase33_volume_trend':p33.sleeves(data),'phase34_low_kurtosis':p34.sleeves(data)}; rows={}
    for fam,sleeves in families.items(): rows[fam]={name:tail_stats(p1.run_targets(data,target,ex,guard,0.0,ALPHA_GROSS),start,train_end) for name,target in sleeves.items()}
    out={'study':'V99 R106 phase 36 — train-only tail concentration diagnostic','status':'DIAGNOSTIC_ONLY_NO_STRATEGY_CHANGE','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'objective':'quantify whether positive gross ROI in phase33/34 is dominated by rare top-return hours after phase35 found no broad gross edge','train_only_diagnostic':True,'untouched_holdout_not_evaluated':True,'no_parameter_selection':True,'strategy_change_in_phase36':False},'data':{'common_start':start.isoformat(),'train_end':train_end.isoformat()},'families':rows,'quarantined_symbols':quarantined,'metadata':metadata,'disclosure':'Historical research only. Train-only concentration analysis; untouched holdout not inspected. V99 Frozen and V16 Frozen unchanged.'}; REPORT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n',encoding='utf-8'); print(json.dumps({'families':{f:{n:{'top_1pct_share_of_positive':r.get('top_1pct_share_of_positive'),'mean_without_top_1pct':r.get('mean_without_top_1pct')} for n,r in x.items()} for f,x in rows.items()}},indent=2),flush=True)
if __name__=='__main__': main()
