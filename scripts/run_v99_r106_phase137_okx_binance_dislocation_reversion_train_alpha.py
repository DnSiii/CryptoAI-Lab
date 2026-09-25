#!/usr/bin/env python3
"""V99 R106 Phase137 preregistered OKX/Binance cross-venue dislocation reversion."""
from __future__ import annotations
import hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
import numpy as np,pandas as pd
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase47_downside_semivariance_alpha_audit as p47
import run_v99_r105_all_regime_structural_audit as audit

PROJECT=Path(__file__).resolve().parents[1]
OUT=PROJECT/'reports'/'candidate_v99_r106_phase137_okx_binance_dislocation_reversion_train_alpha.json'
PH136=PROJECT/'reports'/'candidate_v99_r106_phase136_okx_crossvenue_data_audit.json'
TRAIN_START=pd.Timestamp('2021-12-01',tz='UTC')
TRAIN_END=pd.Timestamp('2024-01-18',tz='UTC')
BASE='https://www.okx.com/api/v5/market/history-candles'
HOUR_MS=3_600_000
START_MS=int(TRAIN_START.timestamp()*1000);END_MS=int(TRAIN_END.timestamp()*1000)
LOOKBACK=168;ALPHA_GROSS=.20
MAP={
 'BTCUSDT':'BTC-USDT-SWAP',
 'ETHUSDT':'ETH-USDT-SWAP',
 'SOLUSDT':'SOL-USDT-SWAP',
 'XRPUSDT':'XRP-USDT-SWAP',
 'DOGEUSDT':'DOGE-USDT-SWAP',
}

def fetch_json(params,retries=5):
    last=None
    for attempt in range(retries):
        try:
            req=Request(BASE+'?'+urlencode(params),headers={'User-Agent':'CryptoAI-Lab-V99-R106-Phase137/1.0','Accept':'application/json','Connection':'close'})
            with urlopen(req,timeout=45) as r: obj=json.loads(r.read().decode())
            if obj.get('code')!='0':raise RuntimeError(f"OKX code={obj.get('code')} msg={obj.get('msg')}")
            return obj
        except Exception as exc:
            last=exc
            if attempt+1<retries:time.sleep(min(10,1.5*(attempt+1)))
    raise RuntimeError(f'OKX request failed: {last!r}')

def acquire(inst):
    cursor=END_MS;rows={};reqs=0
    while True:
        obj=fetch_json({'instId':inst,'bar':'1H','after':str(cursor),'limit':'300'});reqs+=1
        data=obj.get('data') or []
        if not data:break
        page=[]
        for row in data:
            if len(row)<9:raise RuntimeError(f'{inst}: bad row')
            ts=int(row[0]);page.append(ts)
            if START_MS<=ts<END_MS:
                norm='|'.join(str(x) for x in row)
                if ts in rows and rows[ts]!=norm:raise RuntimeError(f'{inst}: conflicting duplicate')
                rows[ts]=norm
        oldest=min(page)
        if oldest<=START_MS:break
        if oldest>=cursor:raise RuntimeError(f'{inst}: pagination stalled')
        cursor=oldest;time.sleep(.12)
        if reqs>1000:raise RuntimeError('pagination safety')
    ts=sorted(rows)
    digest=hashlib.sha256(('\n'.join(rows[t] for t in ts)).encode()).hexdigest()
    idx=pd.to_datetime(ts,unit='ms',utc=True)
    close=pd.Series([float(rows[t].split('|')[4]) for t in ts],index=idx,dtype=float)
    if len(ts)!=(END_MS-START_MS)//HOUR_MS:raise RuntimeError(f'{inst}: incomplete rows={len(ts)}')
    if not np.isfinite(close.to_numpy()).all() or (close<=0).any():raise RuntimeError(f'{inst}: invalid close')
    return close,digest,reqs

def main():
    prereg=PROJECT/'research'/'v99_r106_phase137_okx_binance_dislocation_reversion_prereg.md'
    assert prereg.exists()
    txt=prereg.read_text()
    assert 'rolling 168h median' in txt and 'raw reversion score = -tanh' in txt and 'shift the complete score by exactly 1 hour' in txt
    ph136=json.loads(PH136.read_text())
    assert ph136['status']=='PASS_DATA_ONLY' and ph136['passing_instruments']==5

    okx={};hashes={};requests={}
    for b,inst in MAP.items():
        s,h,n=acquire(inst)
        expected=ph136['instruments'][inst]['normalized_full_rows_sha256']
        if h!=expected:raise RuntimeError(f'{inst}: Phase136 hash mismatch before PnL')
        okx[b]=s;hashes[inst]=h;requests[inst]=n
    okx_close=pd.DataFrame(okx).sort_index()
    expected_index=pd.date_range(TRAIN_START,TRAIN_END-pd.Timedelta(hours=1),freq='h',tz='UTC')
    assert okx_close.index.equals(expected_index)

    cfg,data,raw,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup()
    c=data.close.astype(float)
    bclose=c.loc[(c.index>=TRAIN_START)&(c.index<TRAIN_END),list(MAP)].reindex(expected_index)
    assert bclose.notna().all().all() and (bclose>0).all().all()

    spread=np.log(bclose/okx_close)
    med=spread.rolling(LOOKBACK,min_periods=LOOKBACK).median()
    dev=spread-med
    mad=dev.abs().rolling(LOOKBACK,min_periods=LOOKBACK).median()
    scale=(1.4826*mad).where(mad>1e-12)
    z=dev/scale
    raw_score=-np.tanh(z)
    centered=raw_score.sub(raw_score.mean(axis=1),axis=0)
    score=centered.shift(1)
    score=score.where(score.notna().sum(axis=1)>=4,0).fillna(0)
    weights=score.div(score.abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)

    targets=pd.DataFrame(0.,index=c.index,columns=c.columns)
    common=targets.index.intersection(weights.index)
    targets.loc[common,list(MAP)]=weights.loc[common,list(MAP)]
    assert float(targets.abs().sum(axis=1).max())<=1.000000001
    assert (targets.loc[targets.index>=TRAIN_END].abs().sum(axis=1)==0).all()

    result=p1.run_targets(data,targets,ex,guard,float(ex['severe_cost_per_side']),ALPHA_GROSS)
    d=p47.diag(result,data.close.index,TRAIN_START,TRAIN_END)
    passed=bool(d['stable_train'])
    out={
      'study':'V99 R106 Phase137 — OKX/BINANCE CROSS-VENUE DISLOCATION REVERSION TRAIN-ONLY alpha gate',
      'status':'TRAIN_ALPHA_PASS_FREEZE_FOR_DOWNSTREAM' if passed else 'TRAIN_ALPHA_REJECT',
      'frozen_assets_untouched':{'v16':True,'v99_frozen':True},
      'precommitment':{
        'prereg':'research/v99_r106_phase137_okx_binance_dislocation_reversion_prereg.md',
        'source':'OKX public 1H USDT-SWAP + canonical Binance USD-M closes',
        'feature':'log(Binance/OKX) minus rolling median168, divided by 1.4826*MAD168; -tanh; cross-sectional demean; complete score t-1; L1',
        'direction':'cross_venue_dislocation_mean_reversion',
        'lookback_hours':LOOKBACK,'alpha_gross':ALPHA_GROSS,
        'frozen_symbols':list(MAP.keys()),'single_hypothesis_no_grid':True,
        'selection_train_only':True,'no_sign_flip':True,'no_symbol_substitution':True,
        'canonical_replay_may_materialize_full_panel':True,
        'holdout_rows_used_for_feature_construction':0,'holdout_rows_used_for_selection':0,
      },
      'source_integrity':{
        'phase136_report':'reports/candidate_v99_r106_phase136_okx_crossvenue_data_audit.json',
        'all_phase136_hashes_reproduced':True,'normalized_full_rows_sha256':hashes,'requests':requests,
        'okx_rows_per_instrument':len(okx_close),
      },
      'train_start':TRAIN_START.isoformat(),'train_end_exclusive':TRAIN_END.isoformat(),
      'causality_invariants':{
        'complete_score_shift_hours':1,
        'feature_input_max_timestamp':okx_close.index.max().isoformat(),
        'feature_inputs_strictly_pre_train_end':bool(okx_close.index.max()<TRAIN_END),
        'post_train_targets_zero':True,
        'max_l1':float(targets.abs().sum(axis=1).max()),
        'common_venue_component_removed_by_cross_sectional_demean':True,
      },
      'diagnostic':d,
      'selected_train_only':'okx_binance_dislocation_reversion_168h' if passed else None,
      'next_gate':'PASS freezes exact spec for supersevere/regimes/tails/concentration/benchmark/reproducibility before untouched holdout; FAIL permanent, no sign flip or lookback rescue.',
      'quarantined_symbols':quarantined,'metadata':metadata,
    }
    OUT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n')
    print(json.dumps({'status':out['status'],'healthy_folds':d['healthy_folds'],'valid_folds':d['valid_folds'],'train':d['train'],'source_integrity':out['source_integrity'],'causality':out['causality_invariants']},indent=2,default=audit.safe_float),flush=True)

if __name__=='__main__':main()
