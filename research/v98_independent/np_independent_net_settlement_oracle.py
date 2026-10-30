#!/usr/bin/env python3
"""V98 NP independent one-way NET ledger settlement oracle, training only.

Independent of strategy, planner and original physical runner. Consumes an
immutable hourly JSONL execution ledger and authenticated Clean-4 OHLC/funding.
No benchmark/holdout access, no claim of validated PnL without an actual ledger.
"""
import argparse,json,math
import numpy as np
from v98_mark_envelope_settlement import worst_funding,read_envelope
from v98_clean4_training_reader import load
def replay(d,rows,lo,hi,fee,slip,order,start=745,end=18288,initial_equity=10000.,
           initial_qty=None):
    if order not in ('carried_before_fill','new_after_fill'):raise ValueError('V98_ORACLE_ORDER')
    if not np.isfinite([fee,slip,initial_equity]).all() or min(fee,slip)<0 or initial_equity<=0:
        raise ValueError('V98_ORACLE_INPUT')
    qty=np.zeros((4,4)) if initial_qty is None else np.asarray(initial_qty,float)
    if qty.shape!=(4,4):raise ValueError('V98_ORACLE_INLTIAL_SHAPE')
    equity=float(initial_equity);total_turn=total_fee=total_slip=total_funding=0.
    n=0;maxgross=0.;min_intrabar=equity
    for row in rows:
        t=start+n
        if t>=end or int(row.get('t',-1))!=t:raise ValueError('V98_ORACLE_MISSING_OR_DUPLICATE_HOUR')
        before=np.asarray(row['qty_before'],float)
        after=np.asarray(row['qty_after'],float)
        if before.shape!=(4,4) or after.shape!=(4,4) or not np.isfinite(before).all() or not np.isfinite(after).all():
            raise ValueError('V98_ORACLE_QTY')
        if not np.allclose(before,qty,rtol=0,atol=1e-10):
            raise ValueError('V98_ORACLE_POSITION_CONTINUITY')
        if not math.isclose(float(row['equity_before']),equity,rel_tol=1e-10,abs_tol=1e-7):
            raise ValueError('V98_ORACLE_EQUITY_CONTINUITY')
        px=d['o'][t]
        opening=equity+float(np.sum(qty*(px-d['c'][t-1])))
        if opening<=0:raise ValueError('V98_ORACLE_INSOLVENT_OPEN')
        pre_gross=float(np.sum(np.abs(qty)*px))
        pre_net=float(np.sum(np.abs(qty.sum(axis=0))*px))
        if max(pre_gross,pre_net)>opening*(1+1e-9):raise ValueError('NP_ORACLE_PRETRADE_GROSS')
        old_net=qty.sum(axis=0);new_net=after.sum(axis=0)
        delta_net=new_net-old_net
        turnover=float(np.sum(np.abs(delta_net)*px))
        fees=turnover*fee;slippage=turnover*slip
        if 'net_before' in row and not np.allclose(row['net_before'],old_net,rtol=0,atol=1e-10):
            raise ValueError('NP_ORACLE_NET_BEFORE_TAMPER')
        if 'net_after' in row and not np.allclose(row['net_after'],new_net,rtol=0,atol=1e-10):
            raise ValueError('NP_ORACLE_NET_AFTER_TAMPER')
        # Non-event hours carry NaN mark envelopes by design; no funding is due.
        # The original physical runner only invokes signed settlement on events.
        funding=(worst_funding(qty.sum(axis=0),after.sum(axis=0),
                             d['rate'][t],d['event'][t],lo[t],hi[t],order)
                 if np.any(d['event'][t]) else 0.)
        # Independently reconstruct one-way close-first NET order path.
        mid=old_net.copy()
        for j in range(4):
            old=float(old_net[j]);new=float(new_net[j])
            if old*new<=0:mid[j]=0.
            elif abs(new)<abs(old):mid[j]=new
        close_turn=float(np.sum(np.abs(mid-old_net)*px))
        close_equity=opening-(close_turn*(fee+slip))
        if order=='carried_before_fill':close_equity+=funding
        mid_gross=float(np.sum(np.abs(mid)*px))
        after_cost=opening-fees-slippage
        if order=='carried_before_fill':
            if opening+funding<=0 or pre_net>(opening+funding)*(1+1e-9):
                raise ValueError('V98_ORACLE_CARRIED_PRE_FILL')
        if close_equity<=0 or mid_gross>close_equity*(1+1e-9):
            raise ValueError('V98_ORACLE_INTERMEDIATE_LEVERAGE')
        fill_equity=after_cost+(funding if order=='carried_before_fill' else 0.)
        final_equity=after_cost+funding
        after_gross=float(np.sum(np.abs(after)*px))
        after_net_gross=float(np.sum(np.abs(new_net)*px))
        if fill_equity<=0 or max(after_gross,after_net_gross)>fill_equity*(1+1e-9):
            raise ValueError('V98_ORACLE_POSTFILL_LEVERAGE')
        if final_equity<=0 or max(after_gross,after_net_gross)>final_equity*.90+1e-7:
            raise ValueError('V98_ORACLE_POSTFUNDING_CAP')
        net=after.sum(axis=0)
        worst=np.where(net>=0,d['l'][t],d['h'][t])
        intrabar=final_equity+float(np.dot(net,worst-px))
        if intrabar<=0:raise ValueError('V98_ORACLE_INTRABAR_INSOLVENCY')
        close=final_equity+float(np.dot(net,d['c'][t]-px))
        if close<=0 or np.sum(np.abs(after)*d['c'][t])>close*(1+1e-9):
            raise ValueError('V98_ORACLE_CLOSE_LEVERAGE')
        for key,expected in (('fee_cash',fees),('slippage_cash',slippage),
                             ('funding_cash',funding),('equity_close',close)):
            actual=float(row[key])
            if not math.isclose(actual,expected,rel_tol=1e-9,abs_tol=1e-6):
                raise ValueError('V98_ORACLE_'+key.upper()+'_MISMATCH')
        total_turn+=turnover;total_fee+=fees;total_slip+=slippage;total_funding+=funding
        maxgross=max(maxgross,pre_gross/opening,pre_net/opening,mid_gross/close_equity,
                     after_gross/fill_equity,after_gross/final_equity)
        min_intrabar=min(min_intrabar,intrabar)
        qty=after;equity=close;n+=1
    if n!=end-start:raise ValueError('V98_ORACLE_INCOMPLETE_HOURLY_LEDGER')
    return {'decision':'PASS_INDEPENDENT_ALL_HOUR_SETTLEMENT_REPLAY',
            'hours_replayed':n,'one_way_netting':True,'final_equity':equity,'turnover':total_turn,
            'fees':total_fee,'slippage':total_slip,'funding':total_funding,
            'max_intermediate_gross_fraction':maxgross,
            'min_intrabar_equity':min_intrabar,
            'actual_future_funding_used_to_size_verified':False,
            'strategy_signals_independently_replayed':False,
            'training_only':True,'holdout_accessed':False}
def synthetic_tests():
    shape=(3,4)
    o=np.full(shape,100.);c=o.copy();h=o.copy();l=o.copy()
    rate=np.zeros(shape);event=np.zeros(shape,bool);rate[1,0]=.0001;event[1,0]=True
    d={'o':o,'h':h,'l':l,'c':c,'rate':rate,'event':event}
    q0=np.zeros((4,4));q1=q0.copy();q1[0,0]=10.
    # Signed event settled against NEW position, with exact known synthetic mark.
    rows=[{'t':1,'qty_before':q0.tolist(),'qty_after':q1.tolist(),
           'equity_before':10000.,'fee_cash':.4,'slippage_cash':.2,
           'funding_cash':-.1,'equity_close':9999.3},
          {'t':2,'qty_before':q1.tolist(),'qty_after':q1.tolist(),
           'equity_before':9999.3,'fee_cash':0.,'slippage_cash':0.,
           'funding_cash':0.,'equity_close':9999.3}]
    marklo=np.full_like(o,np.nan);markhi=np.full_like(o,np.nan)
    marklo[1,:]=markhi[1,:]=100.
    out=replay(d,rows,marklo,markhi,.0004,.0002,'new_after_fill',1,3)
    assert out['hours_replayed']==2 and abs(out['final_equity']-9999.3)<1e-8
    bad=[dict(x) for x in rows];bad[0]['fee_cash']=0.
    try:replay(d,bad,marklo,markhi,.0004,.0002,'new_after_fill',1,3)
    except ValueError as e:assert 'FEE' in str(e)
    else:raise AssertionError('V98_ORACLE_FEE_TAMPER_UNDETECTED')
    bad=[dict(x) for x in rows];bad[1]['qty_before']=q0.tolist()
    try:replay(d,bad,marklo,markhi,.0004,.0002,'new_after_fill',1,3)
    except ValueError as e:assert 'POSITION_CONTINUITY' in str(e)
    else:raise AssertionError('V98_ORACLE_POSITION_TAMPER_UNDETECTED')
    # Carried-before-fill signed event on a preexisting long position.
    d2={k:v.copy() for k,v in d.items()}
    d2['event'][2,0]=True;d2['rate'][2,0]=.0001
    carried=[dict(x) for x in rows]
    # At t=1 the old position was zero, so carried funding is zero.
    # At t=2 the 10-unit long position pays 0.1 at the signed event.
    carried[0]['funding_cash']=0.;carried[0]['equity_close']=9999.4
    carried[1]['equity_before']=9999.4
    carried[1]['funding_cash']=-.1;carried[1]['equity_close']=9999.3
    marklo[2,:]=markhi[2,:]=100.
    out2=replay(d2,carried,marklo,markhi,.0004,.0002,'carried_before_fill',1,3)
    assert abs(out2['final_equity']-9999.3)<1e-8
    tampered=[dict(x) for x in carried];tampered[1]['funding_cash']=+.1
    try:replay(d2,tampered,marklo,markhi,.0004,.0002,'carried_before_fill',1,3)
    except ValueError as e:assert 'FUNDING' in str(e)
    else:raise AssertionError('V98_ORACLE_FUNDING_SIGN_TAMPER_UNDETECTED')
    return True
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root');p.add_argument('--envelope-csv')
    p.add_argument('--ledger-jsonl');p.add_argument('--fee',type=float);p.add_argument('--slip',type=float)
    p.add_argument('--order',choices=('carried_before_fill','new_after_fill'))
    a=p.parse_args()
    if not a.root:
        assert synthetic_tests();print('V98_INDEPENDENT_LEDGER_ORACLE_SYNTHETIC_PASS')
    else:
        if not all([a.envelope_csv,a.ledger_jsonl,a.fee is not None,a.slip is not None,a.order]):
            raise ValueError('V98_ORACLE_INCOMPLETE_CLI')
        d=load(a.root);lo,hi,_=read_envelope(a.envelope_csv,d)
        with open(a.ledger_jsonl) as f:rows=(json.loads(line) for line in f)
        print(json.dumps(replay(d,rows,lo,hi,a.fee,a.slip,a.order),indent=2))
