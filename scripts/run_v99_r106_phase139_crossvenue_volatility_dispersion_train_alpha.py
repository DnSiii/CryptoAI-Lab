#!/usr/bin/env python3
"""V99 R106 Phase139 preregistered cross-venue RV24 dispersion reversion."""
from __future__ import annotations
import hashlib,json,time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
import numpy as np,pandas as pd
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase47_downside_semivariance_alpha_audit as p47
import run_v99_r105_all_regime_structural_audit as audit
PROJECT=Path(__file__).resolve().parents[1];OUT=PROJECT/'reports'/'candidate_v99_r106_phase139_crossvenue_volatility_dispersion_train_alpha.json';PH136=PROJECT/'reports'/'candidate_v99_r106_phase136_okx_crossvenue_data_audit.json';DEC138=PROJECT/'docs'/'v99_r106_phase138_return_innovation_decision.md';PREREG=PROJECT/'docs'/'v99_r106_phase139_crossvenue_volatility_dispersion_preregister.md';ADDENDUM=PROJECT/'docs'/'v99_r106_phase139_rv_definition_addendum.md'
TRAIN_START=pd.Timestamp('2021-12-01',tz='UTC');TRAIN_END=pd.Timestamp('2024-01-18',tz='UTC');BASE='https://www.okx.com/api/v5/market/history-candles';HOUR_MS=3_600_000;START_MS=int(TRAIN_START.timestamp()*1000);END_MS=int(TRAIN_END.timestamp()*1000);LOOKBACK=168;RV_WINDOW=24;ALPHA_GROSS=.20
MAP={'BTCUSDT':'BTC-USDT-SWAP','ETHUSDT':'ETH-USDT-SWAP','SOLUSDT':'SOL-USDT-SWAP','XRPUSDT':'XRP-USDT-SWAP','DOGEUSDT':'DOGE-USDT-SWAP'}
def fetch_json(params,retries=5):
    last=None
    for attempt in range(retries):
        try:
            req=Request(BASE+'?'+urlencode(params),headers={'User-Agent':'CryptoAI-Lab-V99-R106-Phase139/1.0','Accept':'application/json','Connection':'close'})
            with urlopen(req,timeout=45) as r: obj=json.loads(r.read().decode())
            if obj.get('code')!='0': raise RuntimeError(f"OKX code={obj.get('code')} msg={obj.get('msg')}")
            return obj
        except Exception as exc:
            last=exc
            if attempt+1<retries: time.sleep(min(10,1.5*(attempt+1)))
    raise RuntimeError(f'OKX request failed: {last!r}')
def acquire(inst):
    cursor=END_MS;rows={};reqs=0
    while True:
        obj=fetch_json({'instId':inst,'bar':'1H','after':str(cursor),'limit':'300'});reqs+=1;data=obj.get('data') or []
        if not data: break
        page=[]
        for row in data:
            if len(row)<9: raise RuntimeError(f'{inst}: bad row')
            ts=int(row[0]);page.append(ts)
            if START_MS<=ts<END_MS:
                norm='|'.join(str(x) for x in row)
                if ts in rows and rows[ts]!=norm: raise RuntimeError(f'{inst}: conflicting duplicate')
                rows[ts]=norm
        oldest=min(page)
        if oldest<=START_MS: break
        if oldest>=cursor: raise RuntimeError(f'{inst}: pagination stalled')
        cursor=oldest;time.sleep(.12)
        if reqs>1000: raise RuntimeError('pagination safety')
    ts=sorted(rows);digest=hashlib.sha256(('\n'.join(rows[t] for t in ts)).encode()).hexdigest();idx=pd.to_datetime(ts,unit='ms',utc=True);close=pd.Series([float(rows[t].split('|')[4]) for t in ts],index=idx,dtype=float)
    if len(ts)!=(END_MS-START_MS)//HOUR_MS: raise RuntimeError(f'{inst}: incomplete rows={len(ts)}')
    if not np.isfinite(close.to_numpy()).all() or (close<=0).any(): raise RuntimeError(f'{inst}: invalid close')
    return close,digest,reqs
def exact_mad(frame,window): return frame.rolling(window,min_periods=window).apply(lambda x: float(np.median(np.abs(x-np.median(x)))),raw=True)
def rv24(close):
    r=np.log(close).diff();return np.sqrt(r.pow(2).rolling(RV_WINDOW,min_periods=RV_WINDOW).sum())
def main():
    assert RV_WINDOW==24 and LOOKBACK==168;assert DEC138.exists() and 'TRAIN_ALPHA_REJECT' in DEC138.read_text();pt=PREREG.read_text();at=ADDENDUM.read_text();assert 'direction as **reversion**' in pt and '168h' in pt and 'sqrt(sum_' in at and 'BEFORE ANY PHASE139 PNL' in at
    ph136=json.loads(PH136.read_text());assert ph136['status']=='PASS_DATA_ONLY' and ph136['passing_instruments']==5;okx={};hashes={};requests={}
    for b,inst in MAP.items():
        s,h,n=acquire(inst);expected=ph136['instruments'][inst]['normalized_full_rows_sha256']
        if h!=expected: raise RuntimeError(f'{inst}: Phase136 hash mismatch before PnL')
        okx[b]=s;hashes[inst]=h;requests[inst]=n
    idx=pd.date_range(TRAIN_START,TRAIN_END-pd.Timedelta(hours=1),freq='h',tz='UTC');okx_close=pd.DataFrame(okx).sort_index();assert okx_close.index.equals(idx);cfg,data,raw,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup();c=data.close.astype(float);bclose=c.loc[(c.index>=TRAIN_START)&(c.index<TRAIN_END),list(MAP)].reindex(idx);binance_integrity={}
    for sym in MAP:
        valid=bclose[sym].notna() & np.isfinite(bclose[sym]) & bclose[sym].gt(0);coverage=float(valid.mean())
        if coverage<.98: raise RuntimeError(f'{sym}: Binance training coverage below 98%: {coverage:.6f}')
        binance_integrity[sym]={'rows_expected':len(idx),'valid_rows':int(valid.sum()),'missing_or_invalid_rows':int((~valid).sum()),'coverage':coverage};bclose.loc[~valid,sym]=np.nan
    gap=rv24(okx_close)-rv24(bclose);med=gap.rolling(LOOKBACK,min_periods=LOOKBACK).median();mad=exact_mad(gap,LOOKBACK);robust=(gap-med)/(1.4826*mad).where(mad>1e-12);centered=robust.sub(robust.mean(axis=1),axis=0);score=(-centered).shift(1);score=score.where(score.notna().sum(axis=1)>=4,0).fillna(0);weights=score.div(score.abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0);targets=pd.DataFrame(0.,index=c.index,columns=c.columns);common=targets.index.intersection(weights.index);targets.loc[common,list(MAP)]=weights.loc[common,list(MAP)]
    assert float(targets.abs().sum(axis=1).max())<=1.000000001 and (targets.loc[targets.index>=TRAIN_END].abs().sum(axis=1)==0).all();result=p1.run_targets(data,targets,ex,guard,float(ex['severe_cost_per_side']),ALPHA_GROSS);d=p47.diag(result,data.close.index,TRAIN_START,TRAIN_END);passed=bool(d['stable_train'])
    out={'study':'V99 R106 Phase139 — CROSS-VENUE RV24 DISPERSION REVERSION TRAIN-ONLY alpha gate','status':'TRAIN_ALPHA_PASS_FREEZE_FOR_DOWNSTREAM' if passed else 'TRAIN_ALPHA_REJECT','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'prereg':str(PREREG.relative_to(PROJECT)),'rv_definition_addendum':str(ADDENDUM.relative_to(PROJECT)),'rv_window_hours':24,'lookback_hours':168,'direction':'reversion','alpha_gross':ALPHA_GROSS,'single_hypothesis_no_grid':True,'selection_train_only':True,'no_sign_flip':True,'no_symbol_substitution':True,'holdout_rows_used_for_feature_construction':0,'holdout_rows_used_for_selection':0},'source_integrity':{'all_phase136_hashes_reproduced':True,'normalized_full_rows_sha256':hashes,'requests':requests,'binance_training_integrity':binance_integrity,'missing_binance_prices_filled':False},'causality_invariants':{'complete_score_shift_hours':1,'feature_inputs_strictly_pre_train_end':bool(okx_close.index.max()<TRAIN_END),'post_train_targets_zero':True,'max_l1':float(targets.abs().sum(axis=1).max()),'common_venue_component_removed_by_cross_sectional_demean':True},'diagnostic':d,'selected_train_only':'crossvenue_rv24_dispersion_reversion_mad168' if passed else None,'next_gate':'PASS: severe/supersevere then regimes/tails/concentration/benchmark/reproducibility; FAIL: permanent, no tuning/sign flip.','quarantined_symbols':quarantined,'metadata':metadata};OUT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n');print(json.dumps({'status':out['status'],'healthy_folds':d['healthy_folds'],'valid_folds':d['valid_folds'],'train':d['train'],'causality':out['causality_invariants']},indent=2,default=audit.safe_float),flush=True)
if __name__=='__main__': main()
