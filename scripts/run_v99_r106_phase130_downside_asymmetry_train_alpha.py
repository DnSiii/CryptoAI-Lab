# Phase130 preregistered downside-semivariance asymmetry continuation; train-only, holdout prohibited.
from __future__ import annotations
import json
from pathlib import Path
import numpy as np,pandas as pd
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase47_downside_semivariance_alpha_audit as p47
import run_v99_r105_all_regime_structural_audit as audit
PROJECT=Path(__file__).resolve().parents[1]
OUT=PROJECT/'reports'/'candidate_v99_r106_phase130_downside_asymmetry_train_alpha.json'
TRAIN_END=pd.Timestamp('2024-01-18',tz='UTC');SEMI_WIN=24;ALPHA_GROSS=.20;MIN_ASSETS=8

def robust_z(x):
 n=x.notna().sum(axis=1);med=x.median(axis=1);dev=x.sub(med,axis=0);mad=dev.abs().median(axis=1)
 scale=(1.4826*mad).where((n>=MIN_ASSETS)&np.isfinite(mad)&(mad>1e-12))
 return dev.div(scale,axis=0)

def main():
 prereg=PROJECT/'research'/'v99_r106_phase129_rejection_and_phase130_prereg.md';assert prereg.exists()
 txt=prereg.read_text();assert 'Phase130' in txt and 'Downside-Semivariance Asymmetry Continuation' in txt and '24h semivariance window is frozen' in txt
 cfg,data,raw,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup()
 c=data.close.astype(float);assert c.index.is_monotonic_increasing and c.index.tz is not None
 ct=c.loc[c.index<TRAIN_END].copy();assert len(ct) and ct.index.max()<TRAIN_END
 r=np.log(ct/ct.shift(1));down=r.clip(upper=0).pow(2).rolling(SEMI_WIN,min_periods=SEMI_WIN).sum();up=r.clip(lower=0).pow(2).rolling(SEMI_WIN,min_periods=SEMI_WIN).sum()
 asym=(down-up)/(down+up+1e-12);z=robust_z(asym);score=-np.tanh(z).shift(1);score=score.where(score.notna().sum(axis=1)>=MIN_ASSETS,0).fillna(0)
 w=score.div(score.abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
 targets=pd.DataFrame(0.,index=c.index,columns=c.columns);targets.loc[w.index,w.columns]=w
 assert float(targets.abs().sum(axis=1).max())<=1.000000001;assert (targets.loc[targets.index>=TRAIN_END].abs().sum(axis=1)==0).all()
 result=p1.run_targets(data,targets,ex,guard,float(ex['severe_cost_per_side']),ALPHA_GROSS)
 start=max(data.close.index[0],pd.Timestamp('2021-12-01',tz='UTC'));d=p47.diag(result,data.close.index,start,TRAIN_END);passed=bool(d['stable_train'])
 out={'study':'V99 R106 Phase130 — DOWNSIDE-SEMIVARIANCE ASYMMETRY CONTINUATION TRAIN-ONLY alpha gate','status':'TRAIN_ALPHA_PASS_FREEZE_FOR_DOWNSTREAM' if passed else 'TRAIN_ALPHA_REJECT','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'prereg':'research/v99_r106_phase129_rejection_and_phase130_prereg.md','feature':'hourly log returns; trailing 24h downside/upside realized semivariance asymmetry; robust cross-sectional median/(1.4826*MAD); negative tanh continuation; entire alpha t-1; L1','direction':'continuation','semivariance_hours':SEMI_WIN,'min_assets':MIN_ASSETS,'alpha_gross':ALPHA_GROSS,'single_hypothesis_no_grid':True,'selection_train_only':True,'holdout_not_parsed':True,'no_sign_flip':True},'train_end_exclusive':TRAIN_END.isoformat(),'causality_invariants':{'feature_input_max_timestamp':ct.index.max().isoformat(),'post_train_targets_zero':True,'full_score_shift_hours':1,'max_l1':float(targets.abs().sum(axis=1).max())},'diagnostic':d,'selected_train_only':'downside_semivariance_asymmetry_24h' if passed else None,'next_gate':'PASS freezes exact spec for supersevere/regime/tails/concentration/benchmark/reproducibility before untouched holdout; FAIL permanent, no retuning.','quarantined_symbols':quarantined,'metadata':metadata};OUT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n');print(json.dumps({'status':out['status'],'healthy_folds':d['healthy_folds'],'valid_folds':d['valid_folds'],'train':d['train'],'causality_invariants':out['causality_invariants']},indent=2,default=audit.safe_float),flush=True)
if __name__=='__main__':main()
