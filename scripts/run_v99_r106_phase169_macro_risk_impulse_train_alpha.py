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

def _get(url,attempts=6):
    last=None
    for attempt in range(attempts):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'CryptoAI-v99-r106-phase169','Accept':'text/csv'})
            with urllib.request.urlopen(req,timeout=180) as r:
                raw=r.read()
            if len(raw)<100: raise RuntimeError('implausibly short FRED response')
            return raw
        except Exception as e:
            last=e
            if attempt<attempts-1: time.sleep(min(30,2**attempt))
    raise RuntimeError(f'FRED fetch failed after {attempts} attempts: {type(last).__name__}: {last}')

def fetch_panel():
    # One immutable TRAIN-bounded request is preferred: fewer network round trips and every
    # series shares the same retrieval boundary. Individual requests are only a transport
    # fallback; they do not alter data, dates, hypothesis, or selection.
    ids=','.join(SERIES)
    base='https://fred.stlouisfed.org/graph/fredgraph.csv'
    panel=None
    try:
        raw=_get(f'{base}?id={ids}&cosd=2021-12-01&coed=2024-01-17')
        d=pd.read_csv(io.BytesIO(raw)); d.columns=[str(c).strip() for c in d.columns]
        if all(s in d.columns for s in SERIES): panel=d
    except Exception:
        panel=None
    if panel is None:
        parts=[]
        for s in SERIES:
            raw=_get(f'{base}?id={s}&cosd=2021-12-01&coed=2024-01-17')
            q=pd.read_csv(io.BytesIO(raw)); q.columns=['date',s]; parts.append(q)
        panel=parts[0]
        for q in parts[1:]: panel=panel.merge(q,on='date',how='outer',validate='one_to_one')
    date_col='DATE' if 'DATE' in panel.columns else ('observation_date' if 'observation_date' in panel.columns else panel.columns[0])
    panel=panel.rename(columns={date_col:'date'}); panel['date']=pd.to_datetime(panel['date'],utc=True,errors='raise')
    panel=panel[(panel.date>=TRAIN_START)&(panel.date<TRAIN_END)].sort_values('date')
    if panel.empty or panel.date.max()>=TRAIN_END or panel.date.duplicated().any(): raise RuntimeError('TRAIN panel firewall')
    out={}
    for s in SERIES:
        if s not in panel: raise RuntimeError('missing FRED series '+s)
        v=pd.to_numeric(panel[s],errors='coerce'); out[s]=pd.Series(v.to_numpy(dtype=float),index=panel.date,name=s)
        if out[s].dropna().empty: raise RuntimeError('empty finite FRED series '+s)
    return out

def causal_z(x):
    finite=x.dropna(); imp=finite.diff(5); mu=imp.expanding(min_periods=60).mean().shift(1); sd=imp.expanding(min_periods=60).std(ddof=1).shift(1)
    return ((imp-mu)/sd.replace(0,np.nan)).clip(-4,4)

def hourly_prior(z,index):
    finite=z.dropna(); day=pd.DatetimeIndex(index).normalize()-pd.Timedelta(days=1)
    return finite.reindex(day,method='ffill').set_axis(index)

def main():
    assert (PROJECT/'research'/'v99_r106_phase169_macro_risk_impulse_prereg.md').exists()
    d168=json.loads((PROJECT/'reports'/'candidate_v99_r106_phase168_external_macro_data_audit.json').read_text()); assert d168['status']=='PASS_DATA_ONLY'
    cfg,data,raw,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup(); idx=data.close.index; train_idx=idx[(idx>=TRAIN_START)&(idx<TRAIN_END)]
    panel=fetch_panel(); zs={s:causal_z(panel[s]) for s in SERIES}; hz=pd.DataFrame({s:hourly_prior(z,train_idx) for s,z in zs.items()},index=train_idx)
    composite=hz.mean(axis=1).where(hz.notna().all(axis=1)); scalar=(-np.tanh(composite.abs())*np.sign(composite)).shift(1).fillna(0.0)
    targets=pd.DataFrame(0.,index=idx,columns=data.close.columns); common=[c for c in data.close.columns if c not in set(quarantined)]
    if not common: raise RuntimeError('no executable assets')
    targets.loc[train_idx,common]=np.repeat((scalar*GROSS/len(common)).to_numpy()[:,None],len(common),axis=1)
    severe=float(ex['severe_cost_per_side']); result=p1.run_targets(data,targets,ex,guard,severe,1.0); diag=p47.diag(result,idx,TRAIN_START,TRAIN_END); passed=bool(diag['stable_train'])
    out={'study':'V99 R106 Phase169 — CAUSAL MACRO RISK IMPULSE TRAIN-ONLY alpha gate','status':'TRAIN_ALPHA_PASS_FREEZE_FOR_DOWNSTREAM' if passed else 'TRAIN_ALPHA_REJECT','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'prereg':'research/v99_r106_phase169_macro_risk_impulse_prereg.md','series':list(SERIES),'impulse_business_observations':5,'standardization':'expanding prior-only mean/std min60, clip[-4,4]','orientation':'risk-off +VIX,+USD,+2Y,+10Y; contrarian crypto direction','macro_availability':'latest finite observation strictly before current UTC calendar date','entire_target_shift_hours':1,'alpha_gross':GROSS,'equal_asset_weights':True,'single_hypothesis_no_grid':True,'selection_train_only':True,'holdout_not_fetched_or_parsed':True},'train_start':TRAIN_START.isoformat(),'train_end_exclusive':TRAIN_END.isoformat(),'severe_cost_per_side':severe,'diagnostic':diag,'selected_train_only':'macro_risk_impulse' if passed else None,'holdout_rows_used_for_feature_construction':0,'holdout_rows_used_for_selection':0,'next_gate':'PASS freezes exact spec for supersevere/regime/concentration/benchmark/reproducibility before untouched holdout; FAIL permanent, no retuning.','quarantined_symbols':quarantined}; OUT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n'); print(json.dumps({'status':out['status'],'healthy_folds':diag['healthy_folds'],'valid_folds':diag['valid_folds'],'train':diag['train']},indent=2,default=audit.safe_float))
if __name__=='__main__': main()
