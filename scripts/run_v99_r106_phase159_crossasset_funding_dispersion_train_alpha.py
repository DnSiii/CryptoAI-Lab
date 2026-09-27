#!/usr/bin/env python3
"""Phase159 preregistered cross-asset Binance funding-dispersion reversion, TRAIN only."""
from __future__ import annotations
import json,sys
from pathlib import Path
import numpy as np,pandas as pd
P=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(P/'scripts'))
import run_v99_r106_phase159_crossasset_funding_dispersion_data_audit as d159
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase47_downside_semivariance_alpha_audit as p47
import run_v99_r105_all_regime_structural_audit as audit
OUT=P/'reports'/'candidate_v99_r106_phase159_crossasset_funding_dispersion_train_alpha.json'
DATA=P/'reports'/'candidate_v99_r106_phase159_crossasset_funding_dispersion_data_audit.json'
PRE=P/'research'/'v99_r106_phase159_crossasset_funding_dispersion_prereg.md'
LOOKBACK=168; ALPHA_GROSS=.20; SYMS=d159.SYMS; START=d159.START; END=d159.END

def exact_mad(x,w):
 return x.rolling(w,min_periods=w).apply(lambda a: np.median(np.abs(a-np.median(a))),raw=True)

def main():
 q=PRE.read_text(); da=json.loads(DATA.read_text())
 assert 'PREREGISTERED BEFORE PnL' in q and 'REVERSION only' in q and 'trailing 168 funding-event observations shifted by one event' in q
 assert da['status']=='PASS_DATA_ONLY' and da['cross_section_coverage']>=.90 and da['pnl_computed'] is False
 ser={s:d159.load(s)[0] for s in SYMS}; ev=sorted(set().union(*(set(x.index) for x in ser.values())))
 # At each native event use only observations timestamped <= event and no more than 60m old. Never nearest-future.
 rows=[]
 for t in ev:
  r={}
  for s,x in ser.items():
   ix=np.asarray(x.index,dtype=np.int64); j=np.searchsorted(ix,t,side='right')-1
   if j>=0 and 0<=t-int(ix[j])<=3600_000:r[s]=float(x.iloc[j])
  if len(r)>=4: rows.append((pd.to_datetime(t,unit='ms',utc=True),r))
 raw=pd.DataFrame({t:r for t,r in rows}).T.reindex(columns=SYMS).sort_index()
 medx=raw.median(axis=1,skipna=True); disp=raw.sub(medx,axis=0)
 z=pd.DataFrame(index=disp.index,columns=SYMS,dtype=float)
 for s in SYMS:
  hist=disp[s].shift(1); med=hist.rolling(LOOKBACK,min_periods=LOOKBACK).median(); mad=exact_mad(hist,LOOKBACK)
  z[s]=(disp[s]-med)/(1.4826*mad).where(mad>1e-12)
 score=-z
 # Bounded cross-sectional allocator at native funding events; no threshold/grid/asset deletion.
 w=score.div(score.abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
 cfg,data,rawv,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup()
 hourly=pd.date_range(START,END-pd.Timedelta(hours=1),freq='h',tz='UTC')
 # Funding known at event t can first affect the next hourly bar: ffill event state, then exact one-hour causal lag.
 wh=w.reindex(w.index.union(hourly)).sort_index().ffill().reindex(hourly).shift(1).fillna(0)
 targets=pd.DataFrame(0.,index=data.close.index,columns=data.close.columns); common=targets.index.intersection(wh.index)
 use=[s for s in SYMS if s in targets.columns]; targets.loc[common,use]=wh.loc[common,use]
 assert float(targets.abs().sum(axis=1).max())<=1.000000001
 assert (targets.loc[targets.index>=END].abs().sum(axis=1)==0).all()
 result=p1.run_targets(data,targets,ex,guard,float(ex['severe_cost_per_side']),ALPHA_GROSS)
 diag=p47.diag(result,data.close.index,START,END); passed=bool(diag['stable_train'])
 out={'study':'V99 R106 Phase159 cross-asset funding dispersion REVERSION TRAIN-only alpha gate','status':'TRAIN_ALPHA_PASS_FREEZE_FOR_DOWNSTREAM' if passed else 'TRAIN_ALPHA_REJECT','precommitment':{'lookback_funding_events':168,'direction':'reversion','alpha_gross':ALPHA_GROSS,'no_sign_flip':True,'no_grid':True,'no_rescue':True,'selection_train_only':True,'holdout_rows_used_for_feature_construction':0,'holdout_rows_used_for_selection':0},'source_integrity':{'phase159_data_audit':'PASS_DATA_ONLY','cross_section_coverage':da['cross_section_coverage'],'assets':da['assets'],'future_nearest_match_forbidden':True},'causality_invariants':{'normalizer_history_shift_events':1,'execution_lag_hours':1,'post_train_targets_zero':True,'max_l1':float(targets.abs().sum(axis=1).max())},'diagnostic':diag,'selected_train_only':'funding_dispersion_reversion_mad168' if passed else None,'frozen_assets_untouched':{'v16':True,'v99_frozen':True},'next_gate':'PASS: severe/supersevere then regimes/tails/concentration/benchmark/reproducibility; FAIL: permanent, no tuning/sign flip.','quarantined_symbols':quarantined,'metadata':metadata}
 OUT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n'); print(json.dumps({'status':out['status'],'healthy_folds':diag['healthy_folds'],'valid_folds':diag['valid_folds'],'train':diag['train'],'max_l1':out['causality_invariants']['max_l1']},indent=2,default=audit.safe_float))
if __name__=='__main__':main()
