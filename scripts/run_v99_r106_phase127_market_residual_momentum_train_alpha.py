# Phase127 preregistered market-residual momentum continuation; train-only, holdout prohibited.
from __future__ import annotations
import json
from pathlib import Path
import numpy as np,pandas as pd
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase47_downside_semivariance_alpha_audit as p47
import run_v99_r105_all_regime_structural_audit as audit
PROJECT=Path(__file__).resolve().parents[1]
OUT=PROJECT/'reports'/'candidate_v99_r106_phase127_market_residual_momentum_train_alpha.json'
TRAIN_END=pd.Timestamp('2024-01-18',tz='UTC');BETA_WIN=72;BETA_MIN=48;MOM_WIN=24;ALPHA_GROSS=.20;MIN_ASSETS=8

def robust_z(x):
 n=x.notna().sum(axis=1);med=x.median(axis=1);dev=x.sub(med,axis=0);mad=dev.abs().median(axis=1)
 scale=(1.4826*mad).where((n>=MIN_ASSETS)&np.isfinite(mad)&(mad>1e-12))
 return dev.div(scale,axis=0)

def main():
 prereg=PROJECT/'research'/'v99_r106_phase126_rejection_and_phase127_prereg.md';assert prereg.exists()
 txt=prereg.read_text();assert 'Phase127' in txt and 'Market-Residual Momentum Continuation' in txt and 'No sign flip' in txt
 cfg,data,raw,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup()
 c=data.close.astype(float);assert c.index.is_monotonic_increasing and c.index.tz is not None
 # Hard train-only feature construction: post-cutoff close data never enters feature, normalization, beta, or diagnostics.
 ct=c.loc[c.index<TRAIN_END].copy();assert len(ct) and ct.index.max()<TRAIN_END
 r=np.log(ct/ct.shift(1));valid_n=r.notna().sum(axis=1);m=r.median(axis=1).where(valid_n>=MIN_ASSETS)
 # Rolling beta uses only trailing/current feature-time observations; execution gets an additional full-score t-1 shift below.
 beta=r.rolling(BETA_WIN,min_periods=BETA_MIN).cov(m).div(m.rolling(BETA_WIN,min_periods=BETA_MIN).var().replace(0,np.nan),axis=0)
 resid=r.sub(beta.mul(m,axis=0));resmom=resid.rolling(MOM_WIN,min_periods=MOM_WIN).sum()
 z=robust_z(resmom);score=np.tanh(z).shift(1);score=score.where(score.notna().sum(axis=1)>=MIN_ASSETS,0).fillna(0)
 w=score.div(score.abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
 targets=pd.DataFrame(0.,index=c.index,columns=c.columns);targets.loc[w.index,w.columns]=w
 assert float(targets.abs().sum(axis=1).max())<=1.000000001;assert (targets.loc[targets.index>=TRAIN_END].abs().sum(axis=1)==0).all()
 result=p1.run_targets(data,targets,ex,guard,float(ex['severe_cost_per_side']),ALPHA_GROSS)
 start=max(data.close.index[0],pd.Timestamp('2021-12-01',tz='UTC'));d=p47.diag(result,data.close.index,start,TRAIN_END);passed=bool(d['stable_train'])
 out={'study':'V99 R106 Phase127 — MARKET-RESIDUAL MOMENTUM CONTINUATION TRAIN-ONLY alpha gate','status':'TRAIN_ALPHA_PASS_FREEZE_FOR_DOWNSTREAM' if passed else 'TRAIN_ALPHA_REJECT','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'prereg':'research/v99_r106_phase126_rejection_and_phase127_prereg.md','feature':'hourly log returns; cross-sectional median market; trailing 72h beta min48; 24h residual momentum; robust cross-sectional median/(1.4826*MAD); tanh; entire alpha t-1; L1','direction':'continuation','beta_window_hours':BETA_WIN,'beta_min_observations':BETA_MIN,'residual_momentum_hours':MOM_WIN,'min_assets':MIN_ASSETS,'alpha_gross':ALPHA_GROSS,'single_hypothesis_no_grid':True,'selection_train_only':True,'holdout_not_parsed':True,'no_sign_flip':True},'train_end_exclusive':TRAIN_END.isoformat(),'causality_invariants':{'feature_input_max_timestamp':ct.index.max().isoformat(),'post_train_targets_zero':True,'full_score_shift_hours':1,'max_l1':float(targets.abs().sum(axis=1).max()),'market_definition':'cross-sectional median valid hourly log return, min 8 assets'},'diagnostic':d,'selected_train_only':'market_residual_momentum_72_48_24' if passed else None,'next_gate':'PASS freezes exact spec for supersevere/regime/tails/concentration/benchmark/reproducibility before untouched holdout; FAIL permanent, no retuning.','quarantined_symbols':quarantined,'metadata':metadata};OUT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n');print(json.dumps({'status':out['status'],'healthy_folds':d['healthy_folds'],'valid_folds':d['valid_folds'],'train':d['train'],'causality_invariants':out['causality_invariants']},indent=2,default=audit.safe_float),flush=True)
if __name__=='__main__':main()
