# Phase126 preregistered range-compression expansion continuation; train-only, holdout prohibited.
from __future__ import annotations
import json
from pathlib import Path
import numpy as np,pandas as pd
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase47_downside_semivariance_alpha_audit as p47
import run_v99_r105_all_regime_structural_audit as audit
PROJECT=Path(__file__).resolve().parents[1]
OUT=PROJECT/'reports'/'candidate_v99_r106_phase126_range_compression_expansion_train_alpha.json'
TRAIN_END=pd.Timestamp('2024-01-18',tz='UTC');FAST=6;SLOW=72;BREAKOUT=6;ALPHA_GROSS=.20;MIN_ASSETS=8;EPS=1e-12

def robust_z(x):
 n=x.notna().sum(axis=1);med=x.median(axis=1);dev=x.sub(med,axis=0);mad=dev.abs().median(axis=1)
 scale=(1.4826*mad).where((n>=MIN_ASSETS)&np.isfinite(mad)&(mad>1e-12))
 return dev.div(scale,axis=0)

def main():
 prereg=PROJECT/'research'/'v99_r106_phase125_rejection_and_phase126_prereg.md';assert prereg.exists()
 txt=prereg.read_text();assert 'Phase126' in txt and 'Range Compression Expansion Continuation' in txt and 'No sign flip' in txt
 cfg,data,raw,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup()
 # FuturesData intentionally exposes only close as a convenience property; OHLC
 # remains in frames. Read the preregistered high/low inputs from that canonical
 # panel rather than changing the shared data model or either frozen engine.
 c=data.close.astype(float);h=data.frames['high'].astype(float);l=data.frames['low'].astype(float)
 assert c.index.equals(h.index) and c.index.equals(l.index) and c.columns.equals(h.columns) and c.columns.equals(l.columns)
 assert c.index.is_monotonic_increasing and c.index.tz is not None
 # Hard train-only feature construction. No post-cutoff OHLC enters feature, normalization, or diagnostics.
 mask=c.index<TRAIN_END;ct=c.loc[mask].copy();ht=h.loc[mask].copy();lt=l.loc[mask].copy();assert len(ct) and ct.index.max()<TRAIN_END
 prev=ct.shift(1);tr=pd.DataFrame(np.maximum.reduce([(ht-lt).to_numpy(),(ht-prev).abs().to_numpy(),(lt-prev).abs().to_numpy()]),index=ct.index,columns=ct.columns).div(prev.where(prev>0))
 fast=tr.rolling(FAST,min_periods=FAST).mean();slow=tr.rolling(SLOW,min_periods=SLOW).mean();compression=np.log((fast+EPS)/(slow+EPS));breakout=np.log(ct/ct.shift(BREAKOUT))
 zc=robust_z(compression);zb=robust_z(breakout);raw_score=(-zc).clip(lower=0)*zb;score=np.tanh(raw_score).shift(1)
 score=score.where(score.notna().sum(axis=1)>=MIN_ASSETS,0).fillna(0);w=score.div(score.abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
 targets=pd.DataFrame(0.,index=c.index,columns=c.columns);targets.loc[w.index,w.columns]=w
 first_possible=ct.index[min(len(ct)-1,SLOW+1)];assert (targets.loc[targets.index<first_possible].abs().sum(axis=1)==0).all();assert float(targets.abs().sum(axis=1).max())<=1.000000001;assert (targets.loc[targets.index>=TRAIN_END].abs().sum(axis=1)==0).all()
 result=p1.run_targets(data,targets,ex,guard,float(ex['severe_cost_per_side']),ALPHA_GROSS)
 start=max(data.close.index[0],pd.Timestamp('2021-12-01',tz='UTC'));d=p47.diag(result,data.close.index,start,TRAIN_END);passed=bool(d['stable_train'])
 out={'study':'V99 R106 Phase126 — RANGE COMPRESSION EXPANSION CONTINUATION TRAIN-ONLY alpha gate','status':'TRAIN_ALPHA_PASS_FREEZE_FOR_DOWNSTREAM' if passed else 'TRAIN_ALPHA_REJECT','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'prereg':'research/v99_r106_phase125_rejection_and_phase126_prereg.md','feature':'true-range 6h/72h compression x 6h breakout; robust cross-sectional median/(1.4826*MAD); (-z_compression)+ only times z_breakout; tanh; entire alpha t-1; L1','direction':'continuation','fast_hours':FAST,'slow_hours':SLOW,'breakout_hours':BREAKOUT,'min_assets':MIN_ASSETS,'alpha_gross':ALPHA_GROSS,'single_hypothesis_no_grid':True,'selection_train_only':True,'holdout_not_parsed':True,'no_sign_flip':True},'train_end_exclusive':TRAIN_END.isoformat(),'causality_invariants':{'feature_input_max_timestamp':ct.index.max().isoformat(),'post_train_targets_zero':True,'full_score_shift_hours':1,'max_l1':float(targets.abs().sum(axis=1).max())},'diagnostic':d,'selected_train_only':'range_compression_expansion_continuation_6_72_6' if passed else None,'next_gate':'PASS freezes exact spec for supersevere/regime/tails/concentration/benchmark/reproducibility before untouched holdout; FAIL permanent, no retuning.','quarantined_symbols':quarantined,'metadata':metadata};OUT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n');print(json.dumps({'status':out['status'],'healthy_folds':d['healthy_folds'],'valid_folds':d['valid_folds'],'train':d['train'],'causality_invariants':out['causality_invariants']},indent=2,default=audit.safe_float),flush=True)
if __name__=='__main__':main()
