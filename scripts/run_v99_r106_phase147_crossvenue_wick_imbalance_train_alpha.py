#!/usr/bin/env python3
"""V99 R106 Phase147 preregistered cross-venue wick-imbalance divergence reversion."""
from __future__ import annotations
import hashlib,json,time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
import numpy as np,pandas as pd
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase47_downside_semivariance_alpha_audit as p47
import run_v99_r105_all_regime_structural_audit as audit
PROJECT=Path(__file__).resolve().parents[1]; OUT=PROJECT/'reports'/'candidate_v99_r106_phase147_crossvenue_wick_imbalance_train_alpha.json'; PH136=PROJECT/'reports'/'candidate_v99_r106_phase136_okx_crossvenue_data_audit.json'; PREREG=PROJECT/'docs'/'v99_r106_phase147_crossvenue_wick_imbalance_divergence_preregister.md'
TRAIN_START=pd.Timestamp('2021-12-01',tz='UTC'); TRAIN_END=pd.Timestamp('2024-01-18',tz='UTC'); BASE='https://www.okx.com/api/v5/market/history-candles'; HOUR_MS=3_600_000; START_MS=int(TRAIN_START.timestamp()*1000); END_MS=int(TRAIN_END.timestamp()*1000); LOOKBACK=168; ALPHA_GROSS=.20
MAP={'BTCUSDT':'BTC-USDT-SWAP','ETHUSDT':'ETH-USDT-SWAP','SOLUSDT':'SOL-USDT-SWAP','XRPUSDT':'XRP-USDT-SWAP','DOGEUSDT':'DOGE-USDT-SWAP'}
def fetch_json(params,retries=5):
    last=None
    for attempt in range(retries):
        try:
            req=Request(BASE+'?'+urlencode(params),headers={'User-Agent':'CryptoAI-Lab-V99-R106-Phase147/1.0','Accept':'application/json','Connection':'close'})
            with urlopen(req,timeout=45) as r: obj=json.loads(r.read().decode())
            if obj.get('code')!='0': raise RuntimeError(f"OKX code={obj.get('code')} msg={obj.get('msg')}")
            return obj
        except Exception as exc:
            last=exc
            if attempt+1<retries: time.sleep(min(10,1.5*(attempt+1)))
    raise RuntimeError(f'OKX request failed: {last!r}')
def acquire(inst):
    cursor=END_MS; rows={}; reqs=0
    while True:
        data=(fetch_json({'instId':inst,'bar':'1H','after':str(cursor),'limit':'300'}).get('data') or []); reqs+=1
        if not data: break
        page=[]
        for row in data:
            if len(row)<9: raise RuntimeError(f'{inst}: bad row')
            ts=int(row[0]); page.append(ts)
            if START_MS<=ts<END_MS:
                norm='|'.join(str(x) for x in row)
                if ts in rows and rows[ts]!=norm: raise RuntimeError(f'{inst}: conflicting duplicate')
                rows[ts]=norm
        oldest=min(page)
        if oldest<=START_MS: break
        if oldest>=cursor: raise RuntimeError(f'{inst}: pagination stalled')
        cursor=oldest; time.sleep(.12)
        if reqs>1000: raise RuntimeError('pagination safety')
    ts=sorted(rows); expected=(END_MS-START_MS)//HOUR_MS
    if len(ts)!=expected or any(b-a!=HOUR_MS for a,b in zip(ts,ts[1:])): raise RuntimeError(f'{inst}: incomplete/gapped')
    digest=hashlib.sha256(('\n'.join(rows[t] for t in ts)).encode()).hexdigest(); idx=pd.to_datetime(ts,unit='ms',utc=True)
    vals=np.array([[float(x) for x in rows[t].split('|')[1:5]] for t in ts]); o,h,l,c=vals.T; valid=np.isfinite(vals).all(axis=1)&(o>0)&(h>=np.maximum(o,c))&(l<=np.minimum(o,c)); wi=np.full(len(ts),np.nan); upper=h-np.maximum(o,c); lower=np.minimum(o,c)-l; wi[valid]=(upper[valid]-lower[valid])/o[valid]
    return pd.Series(wi,index=idx),digest,reqs,int(valid.sum())
def exact_mad(frame,window): return frame.rolling(window,min_periods=window).apply(lambda x: float(np.median(np.abs(x-np.median(x)))),raw=True)
def main():
    pt=PREREG.read_text(); assert LOOKBACK==168 and 'direction: reversion' in pt and 'exactly t-1' in pt and '>=98%' in pt and 'wick repair' in pt
    ph136=json.loads(PH136.read_text()); assert ph136['status']=='PASS_DATA_ONLY' and ph136['passing_instruments']==5
    idx=pd.date_range(TRAIN_START,TRAIN_END-pd.Timedelta(hours=1),freq='h',tz='UTC'); okx={}; hashes={}; integrity={}
    for b,inst in MAP.items():
        s,h,n,v=acquire(inst); expected=ph136['instruments'][inst]['normalized_full_rows_sha256']
        if h!=expected: raise RuntimeError(f'{inst}: Phase136 hash mismatch')
        cov=v/len(idx); integrity[inst]={'valid_rows':v,'expected_rows':len(idx),'coverage':cov,'requests':n}
        if cov<.98: raise RuntimeError(f'{inst}: OKX valid coverage below 98%')
        okx[b]=s; hashes[inst]=h
    okx_wi=pd.DataFrame(okx).reindex(idx)
    cfg,data,raw,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup(); bo=data.frames['open'].astype(float).reindex(idx)[list(MAP)]; bh=data.frames['high'].astype(float).reindex(idx)[list(MAP)]; bl=data.frames['low'].astype(float).reindex(idx)[list(MAP)]; bc=data.close.astype(float).reindex(idx)[list(MAP)]; valid=np.isfinite(bo)&np.isfinite(bh)&np.isfinite(bl)&np.isfinite(bc)&(bo>0)&(bh>=np.maximum(bo,bc))&(bl<=np.minimum(bo,bc)); bin_wi=((bh-np.maximum(bo,bc))-(np.minimum(bo,bc)-bl)).div(bo).where(valid); bin_integrity={}
    for sym in MAP:
        cov=float(valid[sym].mean()); bin_integrity[sym]={'valid_rows':int(valid[sym].sum()),'expected_rows':len(idx),'coverage':cov}
        if cov<.98: raise RuntimeError(f'{sym}: Binance valid coverage below 98%')
    aligned=okx_wi.notna()&bin_wi.notna()
    for sym,inst in MAP.items():
        cov=float(aligned[sym].mean()); integrity[inst]['aligned_valid_coverage']=cov
        if cov<.98: raise RuntimeError(f'{sym}: aligned valid coverage below 98%')
    divergence=okx_wi-bin_wi; med=divergence.rolling(LOOKBACK,min_periods=LOOKBACK).median(); mad=exact_mad(divergence,LOOKBACK); robust=(divergence-med)/(1.4826*mad).where(mad>1e-12); centered=robust.sub(robust.mean(axis=1),axis=0); score=(-centered).shift(1); score=score.where(score.notna().sum(axis=1)>=4,0).fillna(0); weights=score.div(score.abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
    c=data.close.astype(float); targets=pd.DataFrame(0.,index=c.index,columns=c.columns); common=targets.index.intersection(weights.index); targets.loc[common,list(MAP)]=weights.loc[common,list(MAP)]
    assert float(targets.abs().sum(axis=1).max())<=1.000000001 and (targets.loc[targets.index>=TRAIN_END].abs().sum(axis=1)==0).all()
    result=p1.run_targets(data,targets,ex,guard,float(ex['severe_cost_per_side']),ALPHA_GROSS); d=p47.diag(result,data.close.index,TRAIN_START,TRAIN_END); passed=bool(d['stable_train'])
    out={'study':'V99 R106 Phase147 — CROSS-VENUE WICK-IMBALANCE DIVERGENCE REVERSION TRAIN-ONLY alpha gate','status':'TRAIN_ALPHA_PASS_FREEZE_FOR_DOWNSTREAM' if passed else 'TRAIN_ALPHA_REJECT','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'lookback_hours':168,'direction':'reversion','selection_train_only':True,'no_sign_flip':True,'no_grid':True,'no_wick_repair':True,'holdout_rows_used_for_feature_construction':0,'holdout_rows_used_for_selection':0},'source_integrity':{'all_phase136_hashes_reproduced':True,'hashes':hashes,'okx':integrity,'binance':bin_integrity,'imputation':False},'causality_invariants':{'complete_score_shift_hours':1,'post_train_targets_zero':True,'max_l1':float(targets.abs().sum(axis=1).max())},'diagnostic':d,'selected_train_only':'crossvenue_wick_imbalance_reversion_mad168' if passed else None,'next_gate':'PASS: severe/supersevere then regimes/tails/concentration/benchmark/reproducibility; FAIL: permanent, no tuning/sign flip.','quarantined_symbols':quarantined,'metadata':metadata}; OUT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n'); print(json.dumps({'status':out['status'],'healthy_folds':d['healthy_folds'],'valid_folds':d['valid_folds'],'train':d['train'],'integrity':integrity},indent=2,default=audit.safe_float),flush=True)
if __name__=='__main__': main()
