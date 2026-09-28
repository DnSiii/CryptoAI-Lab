from __future__ import annotations
import json
from pathlib import Path
import numpy as np,pandas as pd
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase47_downside_semivariance_alpha_audit as p47
import run_v99_r105_all_regime_structural_audit as audit
PROJECT=Path(__file__).resolve().parents[1]
OUT=PROJECT/'reports'/'candidate_v99_r106_phase173_macro_acceleration_train_alpha.json'
SNAP=PROJECT/'data'/'research'/'v99_r106_phase168_external_macro_train.csv'
TRAIN_START=pd.Timestamp('2021-12-01',tz='UTC'); TRAIN_END=pd.Timestamp('2024-01-18',tz='UTC'); GROSS=.20

def causal_accel_z(x):
    finite=x.dropna(); shock=finite.diff(5); accel=shock.diff(1)
    mu=accel.expanding(min_periods=60).mean().shift(1); sd=accel.expanding(min_periods=60).std(ddof=1).shift(1)
    return ((accel-mu)/sd.replace(0,np.nan)).clip(-4,4)

def hourly_prior(z,index):
    day=pd.DatetimeIndex(index).normalize()-pd.Timedelta(days=1)
    return z.dropna().reindex(day,method='ffill').set_axis(index)

def main():
    assert (PROJECT/'research'/'v99_r106_phase173_macro_acceleration_prereg.md').exists()
    prev=[('phase168_external_macro_data_audit','PASS_DATA_ONLY'),('phase169_macro_risk_impulse_train_alpha','TRAIN_ALPHA_REJECT'),('phase170_curve_liquidity_shock_train_alpha','TRAIN_ALPHA_REJECT'),('phase171_vix_rates_interaction_train_alpha','TRAIN_ALPHA_REJECT'),('phase172_macro_breadth_train_alpha','TRAIN_ALPHA_REJECT')]
    for stem,status in prev:
        d=json.loads((PROJECT/'reports'/f'candidate_v99_r106_{stem}.json').read_text()); assert d['status']==status; assert d['holdout_rows_used_for_feature_construction']==d['holdout_rows_used_for_selection']==0; assert d['frozen_assets_untouched']=={'v16':True,'v99_frozen':True}
    panel=pd.read_csv(SNAP); dc='date' if 'date' in panel else panel.columns[0]; panel[dc]=pd.to_datetime(panel[dc],utc=True); panel=panel[(panel[dc]>=TRAIN_START)&(panel[dc]<TRAIN_END)].sort_values(dc); assert not panel.empty and not panel[dc].duplicated().any() and panel[dc].max()<TRAIN_END
    def s(col): return pd.Series(pd.to_numeric(panel[col],errors='coerce').to_numpy(),index=panel[dc])
    zv,zu,zf=causal_accel_z(s('VIXCLS')),causal_accel_z(s('DTWEXBGS')),causal_accel_z(s('DGS2')-s('DFF'))
    cfg,data,raw,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup(); idx=data.close.index; train_idx=idx[(idx>=TRAIN_START)&(idx<TRAIN_END)]
    composite=(hourly_prior(zv,train_idx)+hourly_prior(zu,train_idx)+hourly_prior(zf,train_idx))/3.0
    scalar=(-composite/4.0).clip(-1,1).shift(1).fillna(0.0)
    targets=pd.DataFrame(0.,index=idx,columns=data.close.columns); common=[c for c in data.close.columns if c not in set(quarantined)]; assert common
    targets.loc[train_idx,common]=np.repeat((scalar*GROSS/len(common)).to_numpy()[:,None],len(common),axis=1)
    severe=float(ex['severe_cost_per_side']); result=p1.run_targets(data,targets,ex,guard,severe,1.0); diag=p47.diag(result,idx,TRAIN_START,TRAIN_END); passed=bool(diag['stable_train'])
    out={'study':'V99 R106 Phase173 — MACRO SHOCK ACCELERATION TRAIN-ONLY alpha gate','status':'TRAIN_ALPHA_PASS_FREEZE_FOR_DOWNSTREAM' if passed else 'TRAIN_ALPHA_REJECT','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'prereg':'research/v99_r106_phase173_macro_acceleration_prereg.md','series':['VIXCLS','DTWEXBGS','DGS2','DFF'],'front_spread':'DGS2-DFF','shock_change_finite_observations':5,'acceleration_difference_finite_observations':1,'standardization':'expanding prior-only mean/std min60, clip[-4,4]','composite':'equal mean of three acceleration z-scores','orientation':'positive acceleration short crypto; negative long','macro_availability':'latest finite observation strictly before current UTC calendar date','entire_target_shift_hours':1,'alpha_gross':GROSS,'single_hypothesis_no_grid':True,'selection_train_only':True,'holdout_not_fetched_or_parsed':True},'train_start':TRAIN_START.isoformat(),'train_end_exclusive':TRAIN_END.isoformat(),'severe_cost_per_side':severe,'diagnostic':diag,'selected_train_only':'macro_shock_acceleration' if passed else None,'holdout_rows_used_for_feature_construction':0,'holdout_rows_used_for_selection':0,'next_gate':'PASS freezes exact spec for supersevere/regime/concentration/benchmark/reproducibility before untouched holdout; FAIL permanent, no retuning.','quarantined_symbols':quarantined}; OUT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n'); print(json.dumps({'status':out['status'],'healthy_folds':diag['healthy_folds'],'valid_folds':diag['valid_folds'],'train':diag['train']},indent=2,default=audit.safe_float))
if __name__=='__main__': main()
