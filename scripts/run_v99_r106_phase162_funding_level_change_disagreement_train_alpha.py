#!/usr/bin/env python3
"""Phase162 preregistered funding level/change disagreement reversion; TRAIN only."""
from __future__ import annotations
import json,sys
from pathlib import Path
import numpy as np,pandas as pd
P=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(P/'scripts'))
import run_v99_r106_phase159_crossasset_funding_dispersion_data_audit as d159
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase47_downside_semivariance_alpha_audit as p47
import run_v99_r105_all_regime_structural_audit as audit
OUT=P/'reports'/'candidate_v99_r106_phase162_funding_level_change_disagreement_train_alpha.json'; PRE=P/'research'/'v99_r106_phase162_funding_level_change_disagreement_prereg.md'; DATA=P/'reports'/'candidate_v99_r106_phase159_crossasset_funding_dispersion_data_audit.json'; P161=P/'reports'/'candidate_v99_r106_phase161_crossasset_funding_acceleration_dispersion_train_alpha.json'
LOOKBACK=168; ALPHA_GROSS=.20; START=d159.START; END=d159.END; SYMS=d159.SYMS

def mad(x,w): return x.rolling(w,min_periods=w).apply(lambda a:np.median(np.abs(a-np.median(a))),raw=True)
def zscore(frame):
 out=pd.DataFrame(index=frame.index,columns=SYMS,dtype=float)
 for s in SYMS:
  h=frame[s].shift(1); m=h.rolling(LOOKBACK,min_periods=LOOKBACK).median(); a=mad(h,LOOKBACK); out[s]=(frame[s]-m)/(1.4826*a).where(a>1e-12)
 return out
def main():
 q=PRE.read_text(); da=json.loads(DATA.read_text()); prev=json.loads(P161.read_text()); assert 'BEFORE ANY Phase162 PnL' in q and 'REVERSION only' in q and da['status']=='PASS_DATA_ONLY' and prev['status']=='TRAIN_ALPHA_REJECT'
 levels={s:d159.load(s)[0] for s in SYMS}; ev=sorted(set().union(*(set(x.index) for x in levels.values()))); rows=[]
 for t in ev:
  r={}
  for s,x in levels.items():
   ix=np.asarray(x.index,dtype=np.int64); j=np.searchsorted(ix,t,side='right')-1
   if j>=0 and 0<=t-int(ix[j])<=3600_000 and np.isfinite(x.iloc[j]): r[s]=float(x.iloc[j])
  if len(r)>=4: rows.append((pd.to_datetime(t,unit='ms',utc=True),r))
 raw=pd.DataFrame({t:r for t,r in rows}).T.reindex(columns=SYMS).sort_index(); level=raw.sub(raw.median(axis=1),axis=0); change=raw.diff(); change=change.sub(change.median(axis=1),axis=0)
 zl=zscore(level); zd=zscore(change); inter=zl*zd; w=(-inter).div(inter.abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
 cfg,data,rawv,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup(); hourly=pd.date_range(START,END-pd.Timedelta(hours=1),freq='h',tz='UTC'); wh=w.reindex(w.index.union(hourly)).sort_index().ffill().reindex(hourly).shift(1).fillna(0)
 targets=pd.DataFrame(0.,index=data.close.index,columns=data.close.columns); common=targets.index.intersection(wh.index); use=[s for s in SYMS if s in targets.columns]; targets.loc[common,use]=wh.loc[common,use]
 assert float(targets.abs().sum(axis=1).max())<=1.000000001 and (targets.loc[targets.index>=END].abs().sum(axis=1)==0).all()
 result=p1.run_targets(data,targets,ex,guard,float(ex['severe_cost_per_side']),ALPHA_GROSS); dg=p47.diag(result,data.close.index,START,END); passed=bool(dg['stable_train'])
 out={'study':'V99 R106 Phase162 funding level/change disagreement REVERSION TRAIN-only','status':'TRAIN_ALPHA_PASS_FREEZE_FOR_DOWNSTREAM' if passed else 'TRAIN_ALPHA_REJECT','precommitment':{'lookback_valid_events':168,'direction':'reversion','interaction':'z_level_times_z_change','no_grid':True,'no_sign_flip':True,'no_rescue':True,'holdout_rows_used_for_feature_construction':0,'holdout_rows_used_for_selection':0},'causality_invariants':{'normalizer_history_shift_events':1,'execution_lag_hours':1,'post_train_targets_zero':True,'max_l1':float(targets.abs().sum(axis=1).max())},'diagnostic':dg,'frozen_assets_untouched':{'v16':True,'v99_frozen':True},'selected_train_only':'funding_level_change_disagreement_reversion_mad168' if passed else None,'quarantined_symbols':quarantined,'metadata':metadata}
 OUT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n'); print(json.dumps({'status':out['status'],'healthy_folds':dg['healthy_folds'],'valid_folds':dg['valid_folds'],'train':dg['train']},indent=2,default=audit.safe_float))
if __name__=='__main__': main()
