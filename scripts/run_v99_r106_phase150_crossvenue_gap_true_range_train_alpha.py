#!/usr/bin/env python3
"""V99 R106 Phase150 preregistered cross-venue gap/true-range divergence reversion."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np,pandas as pd
import run_v99_r106_phase149_crossvenue_true_range_location_train_alpha as p149
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase47_downside_semivariance_alpha_audit as p47
import run_v99_r105_all_regime_structural_audit as audit
PROJECT=Path(__file__).resolve().parents[1]
OUT=PROJECT/'reports'/'candidate_v99_r106_phase150_crossvenue_gap_true_range_train_alpha.json'
PH136=PROJECT/'reports'/'candidate_v99_r106_phase136_okx_crossvenue_data_audit.json'
PREREG=PROJECT/'research'/'v99_r106_phase150_crossvenue_gap_true_range_prereg.md'
TRAIN_START=p149.TRAIN_START; TRAIN_END=p149.TRAIN_END; LOOKBACK=168; ALPHA_GROSS=.20; MAP=p149.MAP

def gaptr(o,h,l,c):
    pc=c.shift(1); tr=pd.concat([(h-l),(h-pc).abs(),(l-pc).abs()],axis=1).max(axis=1,skipna=False)
    valid=np.isfinite(o)&np.isfinite(h)&np.isfinite(l)&np.isfinite(c)&np.isfinite(pc)&np.isfinite(tr)&(tr>0)
    return ((o-pc)/tr).where(valid),valid

def main():
    pt=PREREG.read_text(); assert LOOKBACK==168 and 'direction: REVERSION' in pt and 'complete score/portfolio shift: t-1' in pt and '>= 98%' in pt
    ph136=json.loads(PH136.read_text()); assert ph136['status']=='PASS_DATA_ONLY' and ph136['passing_instruments']==5
    idx=pd.date_range(TRAIN_START,TRAIN_END-pd.Timedelta(hours=1),freq='h',tz='UTC'); okx={}; hashes={}; integrity={}
    for sym,inst in MAP.items():
        f,digest,n=p149.acquire(inst); expected=ph136['instruments'][inst]['normalized_full_rows_sha256']
        if digest!=expected: raise RuntimeError(f'{inst}: Phase136 hash mismatch')
        s,valid=gaptr(f.open,f.high,f.low,f.close); cov=float(valid.mean()); integrity[inst]={'valid_rows':int(valid.sum()),'expected_rows':len(idx),'coverage':cov,'requests':n}
        if cov<.98: raise RuntimeError(f'{inst}: OKX valid coverage below 98%')
        okx[sym]=s; hashes[inst]=digest
    okx_gap=pd.DataFrame(okx).reindex(idx)
    cfg,data,raw,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup()
    bo=data.frames['open'].astype(float).reindex(idx)[list(MAP)]; bh=data.frames['high'].astype(float).reindex(idx)[list(MAP)]; bl=data.frames['low'].astype(float).reindex(idx)[list(MAP)]; bc=data.close.astype(float).reindex(idx)[list(MAP)]
    bin_gap={}; bin_integrity={}
    for sym in MAP:
        s,valid=gaptr(bo[sym],bh[sym],bl[sym],bc[sym]); cov=float(valid.mean()); bin_gap[sym]=s; bin_integrity[sym]={'valid_rows':int(valid.sum()),'expected_rows':len(idx),'coverage':cov}
        if cov<.98: raise RuntimeError(f'{sym}: Binance valid coverage below 98%')
    bin_gap=pd.DataFrame(bin_gap,index=idx); aligned=okx_gap.notna()&bin_gap.notna()
    for sym,inst in MAP.items():
        cov=float(aligned[sym].mean()); integrity[inst]['aligned_valid_coverage']=cov
        if cov<.98: raise RuntimeError(f'{sym}: aligned valid coverage below 98%')
    divergence=okx_gap-bin_gap; med=divergence.rolling(LOOKBACK,min_periods=LOOKBACK).median(); mad=p149.exact_mad(divergence,LOOKBACK)
    robust=(divergence-med)/(1.4826*mad).where(mad>1e-12); centered=robust.sub(robust.mean(axis=1),axis=0); score=(-centered).shift(1)
    score=score.where(score.notna().sum(axis=1)>=4,0).fillna(0); weights=score.div(score.abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
    c=data.close.astype(float); targets=pd.DataFrame(0.,index=c.index,columns=c.columns); common=targets.index.intersection(weights.index); targets.loc[common,list(MAP)]=weights.loc[common,list(MAP)]
    assert float(targets.abs().sum(axis=1).max())<=1.000000001 and (targets.loc[targets.index>=TRAIN_END].abs().sum(axis=1)==0).all()
    result=p1.run_targets(data,targets,ex,guard,float(ex['severe_cost_per_side']),ALPHA_GROSS); d=p47.diag(result,data.close.index,TRAIN_START,TRAIN_END); passed=bool(d['stable_train'])
    out={'study':'V99 R106 Phase150 — CROSS-VENUE GAP/TRUE-RANGE DIVERGENCE REVERSION TRAIN-ONLY alpha gate','status':'TRAIN_ALPHA_PASS_FREEZE_FOR_DOWNSTREAM' if passed else 'TRAIN_ALPHA_REJECT','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'lookback_hours':168,'direction':'reversion','selection_train_only':True,'no_sign_flip':True,'no_grid':True,'no_rescue':True,'holdout_rows_used_for_feature_construction':0,'holdout_rows_used_for_selection':0},'source_integrity':{'all_phase136_hashes_reproduced':True,'hashes':hashes,'okx':integrity,'binance':bin_integrity,'invalid_true_range_imputed':False},'causality_invariants':{'complete_score_shift_hours':1,'post_train_targets_zero':True,'max_l1':float(targets.abs().sum(axis=1).max())},'diagnostic':d,'selected_train_only':'crossvenue_gap_true_range_reversion_mad168' if passed else None,'next_gate':'PASS: severe/supersevere then regimes/tails/concentration/benchmark/reproducibility; FAIL: permanent, no tuning/sign flip.','quarantined_symbols':quarantined,'metadata':metadata}
    OUT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n'); print(json.dumps({'status':out['status'],'healthy_folds':d['healthy_folds'],'valid_folds':d['valid_folds'],'train':d['train'],'integrity':integrity},indent=2,default=audit.safe_float),flush=True)
if __name__=='__main__': main()
