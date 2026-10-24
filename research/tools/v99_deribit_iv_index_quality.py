"""Independent quality screen for trade IV + contemporaneous index moneyness; no PnL."""
from __future__ import annotations
import hashlib
import json
import math
import sys
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path

def evaluate(root):
    root=Path(root)
    data=json.loads((root/'pit_coverage.json').read_text())
    assert data['schema']=='V99_DERIBIT_OPTIONS_WEEKLY_PIT_TRAIN_COVERAGE_V2'
    assert data['max_recent_trades']==1000
    summary=[]
    total_trades=0
    index_ok=0
    iv_ok=0
    for row in data['rows']:
        assert row['status']=='SOURCE_OK'
        raw=(root/row['receipt_file']).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==row['sha256']
        trades=json.loads(raw)['result']['trades']
        t=row['decision_ms']; c=row['currency']
        counts=defaultdict(set)
        valid_index=0
        valid_iv=0
        recent_atm=0
        for v in trades:
            ts=int(v['timestamp'])
            assert t-86400000<=ts<t
            total_trades+=1
            try:
                iv=float(v['iv'])
                idx=float(v['index_price'])
            except (ValueError,TypeError,KeyError):
                continue
            if not (math.isfinite(iv) and 0<iv<=1000 and math.isfinite(idx) and idx>0):
                continue
            valid_index+=1
            valid_iv+=1
            index_ok+=1
            iv_ok+=1
            if t-ts>21600000:
                continue
            bits=str(v.get('instrument_name','')).split('-')
            if len(bits)!=4 or bits[0]!=c or bits[3] not in ('C','P'):
                continue
            try:
                strike=float(bits[2])
                exp=datetime.strptime(bits[1].upper(),'%d%b%y').replace(tzinfo=timezone.utc)
            except (ValueError,OverflowError):
                continue
            if not (math.isfinite(strike) and strike>0):
                continue
            if abs(math.log(strike/idx))>0.15:
                continue
            recent_atm+=1
            d=(int(exp.timestamp()*1000)+28800000-t)/86400000
            band='short' if 7<=d<=45 else ('long' if 46<=d<=120 else None)
            if band:
                counts[(band,bits[3])].add(strike)
        covered=all(len(counts[(b,s)])>=2 for b in ('short','long') for s in ('C','P'))
        summary.append({'decision_ms':t,'fold':row['fold'],'currency':c,
                        'source_trades':len(trades),'valid_iv_and_index':valid_index,
                        'recent_near_atm':recent_atm,'near_atm_2strike_4group':covered,
                        'counts':{b+'_'+s:len(counts[(b,s)])
                                  for b in ('short','long') for s in ('C','P')}})
    folds=[]
    for f in range(1,6):
        for c in ('BTC','ETH'):
            rows=[x for x in summary if x['fold']==f and x['currency']==c]
            folds.append({'fold':f,'currency':c,'weeks':len(rows),
                          'near_atm_covered':sum(x['near_atm_2strike_4group'] for x in rows)})
    report={'schema':'V99_OPTIONS_TRADE_IV_INDEX_MONEYNESS_SOURCE_QUALITY_V1',
            'source_depth':1000,'source_run':40067965880,
            'sampled_trades':total_trades,'trades_with_iv_and_index':index_ok,
            'folds':folds,'rows':summary,
            'not_proven':['historical index_price semantics at trade time',
                          'full chain completeness','executable bid ask',
                          'native OKX fee tier and actual fills','predictive edge'],
            'economic_train_executed':False,'validation_opened':False,
            'holdout_opened':False,'orders_enabled':False,'promotion_authorized':False}
    (root/'iv_index_quality.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('INDEX+IV TRADE ROWS:',index_ok,'/',total_trades)
    print('NEAR-ATM 2STRIKE FOUR GROUPS:',[(x['fold'],x['currency'],x['near_atm_covered'],x['weeks']) for x in folds])
    print('DATA_ONLY/HOLD — NO PROMOTION / NO PNL')
    return report

if __name__=='__main__':
    if len(sys.argv)!=2:
        raise SystemExit('usage: python -m research.tools.v99_deribit_iv_index_quality SOURCE_DIR')
    evaluate(sys.argv[1])
