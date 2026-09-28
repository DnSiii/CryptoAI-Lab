from __future__ import annotations
import io,json,time,urllib.request
from pathlib import Path
import numpy as np,pandas as pd
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase47_downside_semivariance_alpha_audit as p47
import run_v99_r105_all_regime_structural_audit as audit
PROJECT=Path(__file__).resolve().parents[1]
OUT=PROJECT/'reports'/'candidate_v99_r106_phase169_macro_risk_impulse_train_alpha.json'
TRAIN_START=pd.Timestamp('2021-12-01',tz='UTC'); TRAIN_END=pd.Timestamp('2024-01-18',tz='UTC')
SERIES=('DGS2','DGS10','DTWEXBGS','VIXCLS'); GROSS=.20

def fetch_series(s):
    u=f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={s}&cosd=2021-12-01&coed=2024-01-17'
    raw=None; last=None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'CryptoAI-v99-r106-phase169'}),timeout=120) as r: raw=r.read()
            break
        except Exception as e:
            last=e
            if attempt<3: time.sleep(2**attempt)
    if raw is None: raise RuntimeError(f'FRED fetch failed after 4 attempts for {s}: {type(last).__name__}: {last}')
    d=pd.read_csv(io.BytesIO(raw)); d.columns=['date','value']; d['date']=pd.to_datetime(d['date'],utc=True,errors='raise'); d['value']=pd.to_numeric(d['value'],errors='coerce')
    d=d[(d.date>=TRAIN_START)&(d.date<TRAIN_END)].sort_values('date').drop_duplicates('date',keep=False)
    if d.empty or d.date.max()>=TRAIN_END: raise RuntimeError('TRAIN firewall '+s)
    return d.set_index('date').value.astype(float)

def causal_z(x):
    imp=x.diff(5); mu=imp.expanding(min_periods=60).mean().shift(1); sd=imp.expanding(min_periods=60).std(ddof=1).shift(1)
    return ((imp-mu)/sd.replace(0,np.nan)).clip(-4,4)

def hourly_prior(z,index):
    # Strictly prior UTC calendar date: never consume a same-day macro value, regardless of publication time.
    day=pd.DatetimeIndex(index).normalize()-pd.Timedelta(days=1)
    return z.reindex(day,method='ffill').set_axis(index)

def main():
    assert (PROJECT/'research'/'v99_r106_phase169_macro_risk_impulse_prereg.md').exists()
    d168=json.loads((PROJECT/'reports'/'candidate_v99_r106_phase168_external_macro_data_audit.json').read_text()); assert d168['status']=='PASS_DATA_ONLY'
    cfg,data,raw,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup(); idx=data.close.index; train_idx=idx[(idx>=TRAIN_START)&(idx<TRAIN_END)]
    zs={s:causal_z(fetch_series(s)) for s in SERIES}; hz=pd.DataFrame({s:hourly_prior(z,train_idx) for s,z in zs.items()},index=train_idx)
    composite=hz.mean(axis=1).where(hz.notna().all(axis=1)); scalar=(-np.tanh(composite.abs())*np.sign(composite)).shift(1).fillna(0.0)
    targets=pd.DataFrame(0.,index=idx,columns=data.close.columns); common=[c for c in data.close.columns if c not in set(quarantined)]
    if not common: raise RuntimeError('no executable assets')
    targets.loc[train_idx,common]=np.repeat((scalar*GROSS/len(common)).to_numpy()[:,None],len(common),axis=1)
    severe=float(ex['severe_cost_per_side']); result=p1.run_targets(data,targets,ex,guard,severe,1.0); diag=p47.diag(result,idx,TRAIN_START,TRAIN_END); passed=bool(diag['stable_train'])
    out={'study':'V99 R106 Phase169 — CAUSAL MACRO RISK IMPULSE TRAIN-ONLY alpha gate','status':'TRAIN_ALPHA_PASS_FREEZE_FOR_DOWNSTREAM' if passed else 'TRAIN_ALPHA_REJECT','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'prereg':'research/v99_r106_phase169_macro_risk_impulse_prereg.md','series':list(SERIES),'impulse_business_observations':5,'standardization':'expanding prior-only mean/std min60, clip[-4,4]','orientation':'risk-off +VIX,+USD,+2Y,+10Y; contrarian crypto direction','macro_availability':'latest finite observation strictly before current UTC calendar date','entire_target_shift_hours':1,'alpha_gross':GROSS,'equal_asset_weights':True,'single_hypothesis_no_grid':True,'selection_train_only':True,'holdout_not_fetched_or_parsed':True},'train_start':TRAIN_START.isoformat(),'train_end_exclusive':TRAIN_END.isoformat(),'severe_cost_per_side':severe,'diagnostic':diag,'selected_train_only':'macro_risk_impulse' if passed else None,'holdout_rows_used_for_feature_construction':0,'holdout_rows_used_for_selection':0,'next_gate':'PASS freezes exact spec for supersevere/regime/concentration/benchmark/reproducibility before untouched holdout; FAIL permanent, no retuning.','quarantined_symbols':quarantined}; OUT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n'); print(json.dumps({'status':out['status'],'healthy_folds':diag['healthy_folds'],'valid_folds':diag['valid_folds'],'train':diag['train']},indent=2,default=audit.safe_float))
if __name__=='__main__': main()
