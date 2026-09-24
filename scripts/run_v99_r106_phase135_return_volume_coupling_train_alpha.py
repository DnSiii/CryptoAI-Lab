# Phase135 preregistered return/volume coupling continuation; train-only, holdout prohibited.
from __future__ import annotations
import json
from pathlib import Path
import numpy as np,pandas as pd
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase47_downside_semivariance_alpha_audit as p47
import run_v99_r105_all_regime_structural_audit as audit
PROJECT=Path(__file__).resolve().parents[1]
OUT=PROJECT/'reports'/'candidate_v99_r106_phase135_return_volume_coupling_train_alpha.json'
TRAIN_END=pd.Timestamp('2024-01-18',tz='UTC');BASE_WIN=168;STATE_WIN=72;ALPHA_GROSS=.20;MIN_ASSETS=8

def robust_z(x):
    n=x.notna().sum(axis=1);med=x.median(axis=1);dev=x.sub(med,axis=0);mad=dev.abs().median(axis=1)
    scale=(1.4826*mad).where((n>=MIN_ASSETS)&np.isfinite(mad)&(mad>1e-12))
    return dev.div(scale,axis=0)

def main():
    prereg=PROJECT/'research'/'v99_r106_phase134_rejection_and_phase135_prereg.md';assert prereg.exists()
    txt=prereg.read_text();assert 'Return/Volume Coupling Continuation' in txt and 'rolling 72h' in txt and '168h median' in txt
    cfg,data,raw,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup()
    c=data.close.astype(float);v=data.frames['volume'].astype(float)
    assert c.index.equals(v.index) and c.columns.equals(v.columns) and c.index.is_monotonic_increasing and c.index.tz is not None
    ct=c.loc[c.index<TRAIN_END].copy();vt=v.loc[v.index<TRAIN_END].reindex_like(ct);assert len(ct) and ct.index.max()<TRAIN_END
    ret=ct.pct_change(fill_method=None)
    dv=(ct*vt).where((ct>0)&(vt>=0))
    base=dv.rolling(BASE_WIN,min_periods=BASE_WIN).median()
    surprise=np.log((dv+1e-12)/(base+1e-12))
    coupling=(ret*surprise).rolling(STATE_WIN,min_periods=STATE_WIN).mean()
    z=robust_z(coupling);score=np.tanh(z).shift(1)
    score=score.where(score.notna().sum(axis=1)>=MIN_ASSETS,0).fillna(0)
    w=score.div(score.abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
    targets=pd.DataFrame(0.,index=c.index,columns=c.columns);targets.loc[w.index,w.columns]=w
    assert float(targets.abs().sum(axis=1).max())<=1.000000001
    assert (targets.loc[targets.index>=TRAIN_END].abs().sum(axis=1)==0).all()
    result=p1.run_targets(data,targets,ex,guard,float(ex['severe_cost_per_side']),ALPHA_GROSS)
    start=max(data.close.index[0],pd.Timestamp('2021-12-01',tz='UTC'));d=p47.diag(result,data.close.index,start,TRAIN_END);passed=bool(d['stable_train'])
    out={'study':'V99 R106 Phase135 — RETURN/VOLUME COUPLING CONTINUATION TRAIN-ONLY alpha gate','status':'TRAIN_ALPHA_PASS_FREEZE_FOR_DOWNSTREAM' if passed else 'TRAIN_ALPHA_REJECT','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'prereg':'research/v99_r106_phase134_rejection_and_phase135_prereg.md','feature':'hourly return * log(dollar_volume/trailing median168); rolling mean72; robust cross-sectional z; tanh continuation; complete alpha t-1; L1','direction':'return_volume_coupling_continuation','state_hours':STATE_WIN,'baseline_hours':BASE_WIN,'min_assets':MIN_ASSETS,'alpha_gross':ALPHA_GROSS,'single_hypothesis_no_grid':True,'selection_train_only':True,'holdout_not_parsed':True,'no_sign_flip':True},'train_end_exclusive':TRAIN_END.isoformat(),'causality_invariants':{'feature_input_max_timestamp':ct.index.max().isoformat(),'post_train_targets_zero':True,'full_score_shift_hours':1,'max_l1':float(targets.abs().sum(axis=1).max())},'diagnostic':d,'selected_train_only':'return_volume_coupling_continuation_72_168' if passed else None,'next_gate':'PASS freezes exact spec for supersevere/regime/tails/concentration/benchmark/reproducibility before untouched holdout; FAIL permanent, no retuning.','quarantined_symbols':quarantined,'metadata':metadata}
    OUT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n')
    print(json.dumps({'status':out['status'],'healthy_folds':d['healthy_folds'],'valid_folds':d['valid_folds'],'train':d['train'],'causality_invariants':out['causality_invariants']},indent=2,default=audit.safe_float),flush=True)
if __name__=='__main__':main()
