from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import run_v99_r106_phase31_cross_sectional_low_vol_alpha_audit as p31
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase17_blv_leadership_alpha as p17
import run_v99_r106_phase4_bear_subregimes as p4
import run_v99_r105_all_regime_structural_audit as audit
PROJECT=Path(__file__).resolve().parents[1]; REPORT=PROJECT/'reports'/'candidate_v99_r106_phase47_downside_semivariance_alpha_audit.json'; ALPHA_GROSS=.20; MIN_TRAIN_ACTIVE_HOURS=720; MIN_FOLD_ACTIVE_HOURS=120; MIN_HOLDOUT_ACTIVE_HOURS=240

def sleeves(data):
    c=data.close.astype(float); r=c.pct_change(fill_method=None); neg=r.clip(upper=0.0); out={}
    # Pre-registered orthogonal risk-quality hypothesis: prefer assets with lower lagged downside semivariance.
    # This differs from phase31 total volatility and phase34 kurtosis; no thresholds/grid, all features t-1.
    for h in (168,336,720):
        downside=np.sqrt((neg.pow(2)).rolling(h,min_periods=max(96,h//2)).mean()).shift(1)
        out[f'low_downside_semivariance_{h}h']=p31.weights(-downside,c)
    return out

def diag(result,index,a,b):
    train=p17.sleeve_row(result,a,b); folds=[]; valid=good=0
    for i,(lo,hi) in enumerate(p4.fold_bounds(index,a,b),1):
        row=p17.sleeve_row(result,lo,hi); eligible=int(row['active_hours'])>=MIN_FOLD_ACTIVE_HOURS; healthy=False
        if eligible:
            valid+=1; healthy=bool(float(row['roi'])>0 and float(row['profit_factor'])>1 and float(row['robust_mean_without_top1pct'])>0); good+=int(healthy)
        folds.append({'fold':i,'start':lo.isoformat(),'end':hi.isoformat(),'eligible':eligible,'healthy':healthy,**row})
    stable=bool(int(train['active_hours'])>=MIN_TRAIN_ACTIVE_HOURS and float(train['roi'])>0 and float(train['profit_factor'])>1.08 and float(train['robust_mean_without_top1pct'])>0 and valid>=3 and good>=3)
    q=np.log(max(1+float(train['roi']),1e-12))*max(float(train['profit_factor']),.25)/max(float(train['max_drawdown_abs']),.05) if stable else -1e9
    return {'stable_train':stable,'quality_score':float(q),'train':train,'valid_folds':valid,'healthy_folds':good,'folds':folds}

def main():
    cfg,data,raw,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup(); severe=float(ex['severe_cost_per_side']); benchmarks=p1.r98.r86.r55.benchmark_items(cfg,data,raw,ex,guard,gross); start=max([data.close.index[0]]+[x['data'].close.index[0] for x in benchmarks.values()]); end=min([data.close.index[-1]]+[x['data'].close.index[-1] for x in benchmarks.values()]); train_end=min(p1.TRAIN_END,end); hidx=data.close.index[(data.close.index>p1.TRAIN_END)&(data.close.index<=end)]; hold_start=hidx[0] if len(hidx) else end
    ss=sleeves(data); results={n:p1.run_targets(data,t,ex,guard,severe,ALPHA_GROSS) for n,t in ss.items()}; ds={n:diag(r,data.close.index,start,train_end) for n,r in results.items()}; elig=[n for n,r in ds.items() if r['stable_train']]; selected=max(elig,key=lambda n:ds[n]['quality_score']) if elig else None; hold=p17.sleeve_row(results[selected],hold_start,end) if selected else {}; hp=bool(selected and int(hold['active_hours'])>=MIN_HOLDOUT_ACTIVE_HOURS and float(hold['roi'])>0 and float(hold['profit_factor'])>1.05 and float(hold['robust_mean_without_top1pct'])>0)
    out={'study':'V99 R106 phase 47 — downside semivariance alpha audit','status':'DIAGNOSTIC_ONLY_NO_STRATEGY_CHANGE','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'objective':'test whether lagged cross-sectional downside semivariance carries a risk-quality premium distinct from total volatility and kurtosis','distinction_from_prior':'phase31 tested total volatility; phase34 kurtosis; phase47 isolates downside-only second moment','families':list(ss),'alpha_gross':ALPHA_GROSS,'all_features_causal_t_minus_1':True,'selection_uses_train_only':True,'holdout_cannot_change_selected_family':True,'no_parameter_grid':True,'cost_for_selection':'severe','strategy_change_in_phase47':False},'data':{'common_start':start.isoformat(),'common_end':end.isoformat(),'train_end':train_end.isoformat(),'holdout_start':hold_start.isoformat(),'severe_cost_per_side':severe},'sleeves':ds,'selected_train_only':selected,'selected_holdout_descriptive':hold,'selected_holdout_pass':hp,'actionable_for_phase48':bool(selected and hp),'next_phase_policy':'If actionable, freeze exact train-selected sleeve and run severe+supersevere temporal folds, regime matrix and benchmark envelope; otherwise reject without horizon/threshold tuning and move to a distinct mechanism.','quarantined_symbols':quarantined,'metadata':metadata,'disclosure':'Historical research only. No real orders. Phase47 cannot alter V99 Frozen or V16 Frozen.'}; REPORT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n',encoding='utf-8'); print(json.dumps({'selected_train_only':selected,'selected_holdout_pass':hp,'actionable_for_phase48':out['actionable_for_phase48'],'train_summary':{n:{'stable_train':r['stable_train'],'healthy_folds':r['healthy_folds'],'train':r['train']} for n,r in ds.items()}},indent=2,default=audit.safe_float),flush=True)
if __name__=='__main__': main()
