#!/usr/bin/env python3
"""Independent V98 source-only 4-asset 1m envelope receipt and signed-cost bound oracle.
Not exact native funding tick; no PnL, no holdout, no model promotion.
"""
import argparse,csv,hashlib,json,math
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import ASSETS,START,load
from v98_mark_envelope_settlement import read_envelope
COLUMNS=('symbol','funding_time_ms','one_minute_lower','one_minute_upper',
         'original_conservative_mark','one_hour_lower','one_hour_upper')

def locate(root,name):
    hits=list(Path(root).rglob(name))
    if len(hits)!=1:raise ValueError('V98_1M_ORACLE_FILE_NOT_UNIQUE_'+name+'_'+str(len(hits)))
    return hits[0]

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(root,d,oldlo,oldhi):
    by_symbol={};rows=[];hashes={}
    start=int(START.timestamp()*1000)
    for j,symbol in enumerate(ASSETS):
        receipt_path=locate(root,f'v98_1m_{symbol}_full_receipt.json')
        bounds_path=locate(root,f'v98_1m_{symbol}_full_bounds.csv')
        receipt=json.loads(receipt_path.read_text())
        if receipt.get('decision')!='PASS_OFFICIAL_CHECKSUMMED_1M_MARK_INTERVAL_NOT_EXACT_FUNDING_TICK' or receipt.get('mode')!='full' or receipt.get('events')!=2286 or receipt.get('exact_funding_tick_attested') is not False or receipt.get('pnl_computed') is not False:
            raise ValueError('V98_1M_ORACLE_INVALID_SOURCE_RECEIPT_'+symbol)
        if receipt.get('one_minute_bounds_sha256')!=sha(bounds_path):
            raise ValueError('V98_1M_ORACLE_CSV_SHA_MISMATCH_'+symbol)
        monthly=receipt.get('source_manifest',{})
        if sum(k.startswith('monthly/') for k in monthly)!=25:
            raise ValueError('V98_1M_ORACLE_INCOMPLETE_MONTH_MANIFEST_'+symbol)
        if any(not isinstance(v.get('sha256'),str) or len(v['sha256'])!=64 for v in monthly.values()):
            raise ValueError('V98_1M_ORACLE_INVALID_SOURCE_HASH_'+symbol)
        hashes[symbol]=sha(bounds_path)
        expected=np.flatnonzero(d['event'][:,j]);seen=set();last=-1
        with bounds_path.open(newline='') as f:
            reader=csv.DictReader(f)
            if tuple(reader.fieldnames or ())!=COLUMNS:
                raise ValueError('V98_1M_ORACLE_SCHEMA_'+symbol)
            for row in reader:
                if row['symbol']!=symbol:raise ValueError('V98_1M_ORACLE_SYMBOL')
                ms=int(row['funding_time_ms'])
                delta=ms-start
                if delta%3600000:raise ValueError('V98_1M_ORACLE_OFF_HOUR')
                t=delta//3600000
                if not 0<=t<len(d['event']) or not d['event'][t,j] or ms<=last or t in seen:
                    raise ValueError('V98_1M_ORACLE_CALENDAR_OR_DUPLICATE')
                last=ms;seen.add(t)
                low=float(row['one_minute_lower']);high=float(row['one_minute_upper'])
                orig=float(row['original_conservative_mark'])
                oldl=float(row['one_hour_lower']);oldh=float(row['one_hour_upper'])
                if not all(math.isfinite(x) for x in (low,high,orig,oldl,oldh)) or low<=0 or low>high:
                    raise ValueError('V98_1M_ORACLE_INVALID_BOUNDS')
                if abs(oldl-oldlo[t,j])>1e-8 or abs(oldh-oldhi[t,j])>1e-8 or abs(orig-d['mark'][t,j])>1e-8:
                    raise ValueError('V98_1M_ORACLE_PINNED_SOURCE_MISMATCH')
                if low<oldl-1e-7 or high>oldh+1e-7:
                    raise ValueError('V98_1M_ORACLE_NOT_NESTED')
                rows.append((symbol,ms,low,high,orig,oldl,oldh,int(t),int(j)))
        if len(seen)!=2286 or seen!=set(map(int,expected)):
            raise ValueError('V98_1M_ORACLE_INCOMPLETE_EVENTS_'+symbol)
        by_symbol[symbol]=receipt
    if len(rows)!=9144 or len({(r[0],r[1]) for r in rows})!=9144:
        raise ValueError('V98_1M_ORACLE_INCOMPLETE_CLEAN4')
    return rows,by_symbol,hashes

def cash_bounds(rows,d):
    """Bound differences per hypothetical unit notional, not strategy PnL."""
    old=[];new=[];old_width=[];new_width=[];outside=0
    for symbol,ms,low,high,orig,oldl,oldh,t,j in rows:
        old_width.append(oldh/oldl-1);new_width.append(high/low-1)
        outside+=int(not low<=orig<=high)
        rate=float(d['rate'][t,j]);close=float(d['c'][t,j])
        # Compare worst-side funding cash for hypothetical long and short
        # each with USD 10k reference notional at the original close.
        for sign in (-1,1):
            obligation=sign*10000/close*rate
            cashold=-obligation*(oldh if obligation>=0 else oldl)
            cashnew=-obligation*(high if obligation>=0 else low)
            if cashnew+1e-7<cashold:
                raise ValueError('V98_1M_ORACLE_WORST_CASH_ORDER_VIOLATION')
            old.append(cashold);new.append(cashnew)
    a=np.asarray(old_width);b=np.asarray(new_width)
    return {'events':len(rows),'signed_hypothetical_cost_checks':len(old),
            'original_conservative_mark_outside_1m_interval':outside,
            'median_width_1h':float(np.median(a)),'median_width_1m':float(np.median(b)),
            'p95_width_1h':float(np.quantile(a,.95)),'p95_width_1m':float(np.quantile(b,.95)),
            'median_width_reduction_pct':float(100*(1-np.median(b)/np.median(a))),
            'max_signed_cash_bound_improvement_usd_per_10k_reference_notional':float(np.max(np.array(new)-np.array(old))),
            'sum_hypothetical_cash_bound_improvement_usd_not_strategy_pnl':float(np.sum(np.array(new)-np.array(old)))}

def synthetic():
    # Independent side-aware worst-cash monotonicity for both signs of funding.
    for rate in (-.0003,.0002):
        for side in (-1.,1.):
            obligation=side*rate
            old=-obligation*(110. if obligation>=0 else 90.)
            new=-obligation*(102. if obligation>=0 else 98.)
            assert new>=old-1e-10
    return True

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True);p.add_argument('--envelope-csv',required=True)
    p.add_argument('--artifacts',required=True);p.add_argument('--output',required=True)
    p.add_argument('--combined-csv',required=True)
    a=p.parse_args();synthetic()
    d=load(a.root);lo,hi,envelope_sha=read_envelope(a.envelope_csv,d)
    rows,receipts,hashes=read(a.artifacts,d,lo,hi)
    result=cash_bounds(rows,d)
    with open(a.combined_csv,'w',newline='') as f:
        writer=csv.writer(f);writer.writerow(COLUMNS)
        for row in sorted(rows,key=lambda r:(r[0],r[1])):writer.writerow(row[:7])
    result.update({'decision':'PASS_INDEPENDENT_9144_EVENT_1M_ENVELOPE_SOURCE_ORACLE_NOT_EXACT_TICK',
        'source_envelope_sha256':envelope_sha,'per_asset_bounds_sha256':hashes,
        'combined_csv_sha256':sha(a.combined_csv),
        'exact_native_funding_tick_mark_attested':False,'training_only':True,
        'holdout_read':False,'pnl_computed':False,'live_authorized':False})
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print('V98_1M_INDEPENDENT_ORACLE_RESULT',json.dumps(result,sort_keys=True),flush=True)
if __name__=='__main__':main()
