#!/usr/bin/env python3
"""AC frozen 90-cell official chronological training; one path/18 cells per job.

Fails closed on fresh provenance/hash drift; no 2025+, XRP or benchmarks.
All economic failures are preserved, never rescued by parameter changes.
"""
from __future__ import annotations
import csv
import json
import subprocess
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from phase1174_ac_discrete_intents import ASSETS, MODES, PATHS, compose_intents, canonical_hash
from phase1175_ac_authenticated_source import run as fresh_source, source_frames, native_bounds, BOUNDS
from phase1177_ac_actual_open_executor import execute_hour, FEES, ORDERS

ROOT=Path(__file__).resolve().parent
CAPITAL={'immediate':10000.,'capacity_1m':1e6,'capacity_10m':1e7}
FROZEN_BLOBS={
 'phase1174_ac_discrete_intents.py':'b82fce7cec9495471872d1bcbb74d45a36d62a4c',
 'phase1175_ac_authenticated_source.py':'fe9c5c1d15823b2d72839013273b1aa694e3c504',
 'phase1176_ac_discrete_allocator.py':'336efc89c9fecee95a3ebdd2bd8be518e1d51c2c',
 'phase1177_ac_actual_open_executor.py':'e4986da3ad76605df4eff3fb65abb87d038ccdd9',
 'phase1179_ac_90cell_synthetic.py':'d6dc98bb5d1ea25ae34d61cd4dd899a946a091b0'}
FROZEN_HASHES={
 'AC_core_only__immediate':'5515e80e4886fc4533d4500417c6b5c63575c4c048999d34f6313174b6ed824e',
 'AC_core_only__capacity_1m':'83f9527d8b346b062d964ef1a9bbaeaaa370d3010a20768f782af3d5f1d66155',
 'AC_core_only__capacity_10m':'26bfce383c21a6fce49b29076db853fb62b0b46b0625ee2e82d8da4d07a29bd9',
 'AC_full__immediate':'8afd529beacbc5b189382cc96a9b11685f5ab4c1775356337984dbb45772027b',
 'AC_full__capacity_1m':'bf7e8106a21fc452735553dc3fd7dd704e3cdf2670c3bc16761b058796405138',
 'AC_full__capacity_10m':'99ea0a4adc1330cd405ff7d18d1a6beae92bbef608e7bf7d3569d28af51d288d',
 'AC_minus_opportunity__immediate':'e031c859a41cdd594cf11af122e433320ab1f1633156f8bee554cab5f5aad4c8',
 'AC_minus_opportunity__capacity_1m':'48d7c88d283fdf065b8b5e01897e960e3bcacd30ab1e0ec3015693066b215dbe',
 'AC_minus_opportunity__capacity_10m':'5f7fe204e08bceaf7fd9313d57fd9eaa932204adfe9498c5e9d85b6700994f1f',
 'AC_minus_relative_value__immediate':'e658b40aec9922b98d3135a42f1a799a8b5160b405e20c984d48a1bd9bad92dd',
 'AC_minus_relative_value__capacity_1m':'ab9726fbccf65eb0d5df3eab891b06617092f5e3c546af71e675433e6b49b64f',
 'AC_minus_relative_value__capacity_10m':'896c26e06a2c74dfc2e57c76136b81a871c674ecd05e5c178bb9b6d2e3fecead',
 'AC_minus_stress__immediate':'42ff0b83ecba3fa3164ca1d1e95c495c551ddfcf5cf718b4caaaf3fc17b9b4c4',
 'AC_minus_stress__capacity_1m':'7a3c0d4994431eeb82bd65bbaecc220108e1b182eadae4a4b1de569191d071f0',
 'AC_minus_stress__capacity_10m':'47340b31e66f6ddb135850424f7c5cc8cf952ae7b81a4ef59c67a4c69d0ef9d9'}


def frozen_gate():
    for name,expected in FROZEN_BLOBS.items():
        sha=subprocess.check_output(['git','hash-object',str(ROOT/name)],
                                    cwd=ROOT.parents[1],text=True).strip()
        if sha!=expected:raise PermissionError('AC1182_FROZEN_BLOB_DRIFT_'+name)
    if fresh_source()!=0:raise PermissionError('AC1182_OFFICIAL_SOURCE_FAILURE')
    receipt=json.loads((ROOT/'phase1175_ac_authenticated_source_receipt.json').read_text())
    if (receipt.get('decision')!='PASS_AC_AUTHENTICATED_SOURCE_ONLY_NOT_FROZEN'
        or receipt.get('canonical_sha256')!=dict(sorted(FROZEN_HASHES.items()))
        or receipt.get('historical_pnl_computed') is not False
        or receipt.get('validation_2025_read') is not False):
        raise PermissionError('AC1182_FROZEN_15_HASH_DRIFT')
    return receipt


def signed_bounds(index,event):
    n=len(index);bounds=np.full((n,4,2),np.nan)
    first=int(index[0].timestamp()*1000)
    with BOUNDS.open(newline='') as stream:
        reader=csv.DictReader(stream)
        for row in reader:
            a=row['asset'];slot=int(row['funding_slot_ms'])
            if a not in ASSETS or (slot-first)%3_600_000:
                raise ValueError('AC1182_MARK_SOURCE')
            t=(slot-first)//3_600_000;j=ASSETS.index(a)
            if not 0<=t<n or not event[t,j] or np.isfinite(bounds[t,j]).any():
                raise ValueError('AC1182_MARK_DUPLICATE')
            bounds[t,j]=[float(row['mark_low']),float(row['mark_high'])]
    if not np.isfinite(bounds[event]).all() or np.isfinite(bounds[~event]).any():
        raise ValueError('AC1182_MARK_INCOMPLETE')
    return bounds


def causal_risk(data,rate):
    close=data['close'].to_numpy(float);high=data['high'].to_numpy(float)
    low=data['low'].to_numpy(float);quote=data['quote_volume'].to_numpy(float)
    n=len(close)
    lowloss=np.zeros_like(close);upgain=np.zeros_like(close)
    lowloss[1:]=1-low[1:]/close[:-1]
    upgain[1:]=high[1:]/close[:-1]-1
    down=np.maximum(.25,pd.DataFrame(lowloss).rolling(336,min_periods=336).max().shift(1).to_numpy(float))
    up=np.maximum(.30,pd.DataFrame(upgain).rolling(336,min_periods=336).max().shift(1).to_numpy(float))
    down=np.minimum(.99,down)
    qmin=pd.DataFrame(quote).rolling(336,min_periods=336).min().shift(1).to_numpy(float)
    fbound=np.maximum(.001,pd.DataFrame(np.abs(rate)).rolling(720,min_periods=720).sum().shift(1).to_numpy(float))
    returns=np.diff(np.log(close),axis=0)
    cov={}
    for t in range(744,n,12):
        w=returns[t-337:t-1]
        if w.shape!=(336,4):raise ValueError('AC1182_COV_WINDOW')
        cov[t]=np.cov(w.T,ddof=0)*24+np.eye(4)*1e-8
    return down,up,qmin,fbound,cov


def fold_metrics(index,nav,capital):
    s=pd.Series(np.asarray(nav,float),index=pd.DatetimeIndex(index))
    if len(s)<2 or not np.isfinite(s.to_numpy()).all() or (s<=0).any():
        raise ValueError('AC1182_INVALID_NAV_SERIES')
    output={}
    start_equity=capital
    for year in (2023,2024):
        fold=s[s.index.year==year]
        if fold.empty:raise ValueError('AC1182_MISSING_FOLD')
        arr=np.r_[start_equity,fold.to_numpy()]
        peak=np.maximum.accumulate(arr)
        dd=arr/peak-1
        final=float(arr[-1]);hours=len(fold)
        daily=fold.resample('D').last()
        daily_pnl=daily.diff();daily_pnl.iloc[0]=daily.iloc[0]-start_equity
        wins=daily_pnl[daily_pnl>0];losses=daily_pnl[daily_pnl<0]
        daily_return=(daily / daily.shift(1)-1).fillna(daily.iloc[0]/start_equity-1)
        cutoff=float(daily_return.quantile(.05))
        tail=daily_return[daily_return<=cutoff]
        output[str(year)]={
            'hours':hours,'starting_equity':float(start_equity),'ending_equity':final,
            'net_return':final/start_equity-1,
            'cagr_annualized':(final/start_equity)**(8760/hours)-1,
            'max_drawdown':float(dd.min()),'positive_days':int((daily_pnl>0).sum()),
            'daily_win_rate':float((daily_pnl>0).sum()/max(1,(daily_pnl!=0).sum())),
            'daily_gain_loss_ratio':float(wins.sum()/-losses.sum()) if len(losses) else None,
            'daily_payoff':float(wins.mean()/-losses.mean()) if len(wins) and len(losses) else None,
            'daily_cvar5':float(tail.mean()) if len(tail) else None,
            'trade_level_pf_payoff_win_rate':'PENDING_SEPARATE_FROZEN_FIFO_AUDIT'}
        start_equity=final
    return output


def cell(path,mode,fee_name,order,idx,data,rate,event,bounds,risk,intents):
    close=data['close'].to_numpy(float);op=data['open'].to_numpy(float)
    hi=data['high'].to_numpy(float);lo=data['low'].to_numpy(float)
    quote=data['quote_volume'].to_numpy(float)
    down,up,qmin,fbound,cov=risk
    capital=CAPITAL[mode];cash=capital;units=np.zeros(4)
    fee=FEES[fee_name];scores=intents[path,mode]
    nav=[];times=[];turnover=fees=funding=0.;gaps=0
    max_gross=max_net=max_asset=0.;reason=None;first_failure=None
    for t in range(744,len(idx)):
        r=execute_hour(prior=close[t-1],opening=op[t],high=hi[t],low=lo[t],closing=close[t],
            cash=cash,old_units=units,scores=scores[t-1],cov24=cov[t] if t%12==0 else np.eye(4)*1e-8,
            down=down[t],up=up[t],funding_bound=fbound[t],prior_quote=quote[t-1],
            min336_quote=qmin[t],fee=fee,funding_rate=rate[t],mark_bounds=bounds[t],
            funding_event=event[t],order=order,rebalance=t%12==0)
        if not r['ok']:
            reason=r['reason'];first_failure=str(idx[t]);break
        cash=r['cash'];units=r['units'];nav.append(r['equity']);times.append(idx[t])
        turnover+=r['turnover'];fees+=r['fees'];funding+=r['funding_cash_delta'];gaps+=int(r['gap'])
        w=units*close[t]/r['equity']
        max_gross=max(max_gross,float(np.abs(w).sum()))
        max_net=max(max_net,float(abs(w.sum())))
        max_asset=max(max_asset,float(np.abs(w).max()))
    passed=reason is None and len(nav)==17544
    out={'path':path,'mode':mode,'fee':fee_name,'funding_order':order,
         'passed':passed,'reason':reason,'first_failure_utc':first_failure,
         'hours_completed':len(nav),'historical_pnl_computed':len(nav)>0,
         'final_equity':float(nav[-1]) if nav else capital,
         'turnover':turnover,'fees_paid':fees,'funding_cash':funding,'gap_events':gaps,
         'max_gross':max_gross,'max_abs_net':max_net,'max_asset_concentration':max_asset,
         'folds':fold_metrics(times,nav,capital) if passed else None}
    return out


def run(path):
    receipt={'phase':1182,'path':path,'decision':'BLOCKED_BEFORE_PNL',
             'historical_pnl_computed':False,'validation_2025_read':False,
             'external_benchmarks_used':False,'promotion_eligible':False,'cells':[]}
    out=ROOT/('phase1182_ac_official_'+path+'.json')
    try:
        if path not in PATHS:raise ValueError('AC1182_UNKNOWN_PATH')
        source_receipt=frozen_gate()
        idx,data=source_frames()
        rate_frame,event=native_bounds(idx)
        rate=rate_frame.to_numpy(float)
        bounds=signed_bounds(idx,event)
        intents=compose_intents(data['open'],data['high'],data['low'],
                                data['close'],data['quote_volume'],rate_frame)
        for mode in MODES:
            if canonical_hash(intents[path,mode],idx,path,mode)!=FROZEN_HASHES[path+'__'+mode]:
                raise PermissionError('AC1182_LATE_SOURCE_HASH_DRIFT')
        risk=causal_risk(data,rate)
        receipt['official_source_mark_sha256']=source_receipt['typed_mark_csv_sha256']
        receipt['historical_pnl_computed']=True  # before first attempted cell; never hide partial work
        for mode in MODES:
            for fee_name in FEES:
                for order in ORDERS:
                    receipt['cells'].append(cell(path,mode,fee_name,order,idx,data,rate,event,bounds,risk,intents))
        receipt['historical_pnl_computed']=True
        receipt['decision']='PASS_AC_PATH_TRAINING_ONLY_PENDING_90CELL_AND_FIFO' if all(c['passed'] for c in receipt['cells']) else 'REJECT_AC_PATH_TRAINING_NO_RESCUE'
    except Exception as exc:
        receipt['decision']='BLOCKED_AFTER_PARTIAL_PNL_NO_PROMOTION' if receipt['historical_pnl_computed'] else 'BLOCKED_BEFORE_PNL'
        receipt['reason']=type(exc).__name__+': '+str(exc)[:350]
    out.write_text(json.dumps(receipt,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'decision':receipt['decision'],'path':path,
                      'cells_attempted':len(receipt['cells']),
                      'cells_passed':sum(c['passed'] for c in receipt['cells']),
                      'reason':receipt.get('reason')},sort_keys=True))
    return 0 if receipt['decision'].startswith('PASS_') else 2

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('AC1182_PATH_REQUIRED')
    raise SystemExit(run(sys.argv[1]))
