from __future__ import annotations
import json
from pathlib import Path
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase17_blv_leadership_alpha as p17
import run_v99_r106_phase31_cross_sectional_low_vol_alpha_audit as p31
import run_v99_r106_phase32_cross_sectional_skew_alpha_audit as p32
import run_v99_r106_phase33_cross_sectional_volume_trend_alpha_audit as p33
import run_v99_r106_phase34_cross_sectional_tail_risk_alpha_audit as p34
import run_v99_r105_all_regime_structural_audit as audit
PROJECT=Path(__file__).resolve().parents[1]; REPORT=PROJECT/'reports'/'candidate_v99_r106_phase35_recent_alpha_failure_decomposition.json'; ALPHA_GROSS=.20

def main():
    cfg,data,raw,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup(); severe=float(ex['severe_cost_per_side']); benchmarks=p1.r98.r86.r55.benchmark_items(cfg,data,raw,ex,guard,gross); start=max([data.close.index[0]]+[x['data'].close.index[0] for x in benchmarks.values()]); end=min([data.close.index[-1]]+[x['data'].close.index[-1] for x in benchmarks.values()]); train_end=min(p1.TRAIN_END,end)
    families={'phase31_low_vol':p31.sleeves(data),'phase32_low_skew':p32.sleeves(data),'phase33_volume_trend':p33.sleeves(data),'phase34_low_kurtosis':p34.sleeves(data)}; rows={}
    for fam,sleeves in families.items():
        rows[fam]={}
        for name,target in sleeves.items():
            gross_r=p1.run_targets(data,target,ex,guard,0.0,ALPHA_GROSS); severe_r=p1.run_targets(data,target,ex,guard,severe,ALPHA_GROSS); g=p17.sleeve_row(gross_r,start,train_end); s=p17.sleeve_row(severe_r,start,train_end)
            rows[fam][name]={'gross_train':g,'severe_train':s,'gross_edge_exists':bool(float(g['roi'])>0 and float(g['profit_factor'])>1 and float(g['robust_mean_without_top1pct'])>0),'survives_severe':bool(float(s['roi'])>0 and float(s['profit_factor'])>1 and float(s['robust_mean_without_top1pct'])>0),'roi_cost_drag':float(g['roi'])-float(s['roi']),'robust_mean_cost_drag':float(g['robust_mean_without_top1pct'])-float(s['robust_mean_without_top1pct'])}
    gross_edges=[f'{fam}/{name}' for fam,x in rows.items() for name,r in x.items() if r['gross_edge_exists']]; severe_edges=[f'{fam}/{name}' for fam,x in rows.items() for name,r in x.items() if r['survives_severe']]
    out={'study':'V99 R106 phase 35 — recent alpha failure decomposition','status':'DIAGNOSTIC_ONLY_NO_STRATEGY_CHANGE','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'objective':'determine whether phases31-34 failed because transaction costs erased genuine broad train edge or because broad edge was absent before costs','train_only_diagnostic':True,'untouched_holdout_not_evaluated':True,'all_source_features_causal_t_minus_1':True,'no_parameter_selection':True,'strategy_change_in_phase35':False},'data':{'common_start':start.isoformat(),'common_end':end.isoformat(),'train_end':train_end.isoformat(),'severe_cost_per_side':severe},'families':rows,'gross_edges':gross_edges,'severe_edges':severe_edges,'diagnosis':'cost_limited' if gross_edges and not severe_edges else ('some_cost_robust_edge' if severe_edges else 'no_broad_gross_edge'),'quarantined_symbols':quarantined,'metadata':metadata,'disclosure':'Historical research only. Train-only failure analysis; untouched holdout deliberately not inspected. V99 Frozen and V16 Frozen unchanged.'}; REPORT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n',encoding='utf-8'); print(json.dumps({'diagnosis':out['diagnosis'],'gross_edges':gross_edges,'severe_edges':severe_edges},indent=2),flush=True)
if __name__=='__main__': main()
