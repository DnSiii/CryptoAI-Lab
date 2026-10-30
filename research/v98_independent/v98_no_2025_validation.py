#!/usr/bin/env python3
"""V98 NO frozen strategy 2025-only prospective physical validation.
Fresh USD10k account at 2025-01-01 00:00 open, 2024 close state causal warmup.
No 2023-24 PnL recomputation, no 2026+ holdout or benchmark.
"""
import argparse,json,math
import numpy as np
from v98_no_2025_validation_reader import load,TOTAL,TRAIN_HOURS,HOURS_2025
from no_sources import bundle as frozen_training_bundle,BOOKS,WARMUP
from v98_oneway_net_atomic_planner import plan_virtual,settle_virtual
from v98_next_pretrade_projection import project
from v98_mark_envelope_settlement import worst_funding
COSTS={'base':(.0004,.0002),'severe':(.001,.001),'supersevere':(.0015,.002)}
ORDERS=('carried_before_fill','new_after_fill')
LEDGER=[]

def extended_bundle(d):
    # Exact frozen NO signals, computed chronologically with no training PnL.
    p=np.log(d['c'])
    target=np.zeros((TOTAL,4,4));updates=np.zeros((TOTAL,4),bool)
    active=np.zeros((TOTAL,3),bool)
    state=np.zeros((4,4));previous=np.zeros((4,4));mult=np.ones(3)
    for t in range(WARMUP,TOTAL):
        k=t-WARMUP
        if k%336==0:
            if np.any(d['q'][t]<=0):raise ValueError('NO_2025_CORE_ZERO_VOLUME_'+str(t))
            state[0]=[.16,.16,.16,.16]
        if k%168==0:
            if np.any(d['q'][t]<=0):raise ValueError('NO_2025_WEEKLY_ZERO_VOLUME_'+str(t))
            r24=p[t]-p[t-24];r168=p[t]-p[t-168]
            state[1:]=0.
            leader=sorted((1,2,3),key=lambda j:(-r168[j],j))[0]
            if r168[leader]>0:state[1,leader]=.12
            if t%8!=0 or not np.all(d['event'][t-160:t+1:8]):
                raise ValueError('NO_2025_FUNDING_LOOKBACK_NOT_SETTLED')
            carry=np.mean(d['rate'][t-160:t+1:8],axis=0)
            ranking=sorted(range(4),key=lambda j:(carry[j],j))
            state[2,ranking[0]]=.04
            state[2,ranking[-1]]=-.04
            state[3,0]=.10 if r24[0]>0 and r168[0]>0 else 0.
            mult[:]=[1.,1.,1.] if np.count_nonzero(r168>0)>=2 else [.5,1.,.5]
            active[t]=np.any(np.abs(state[1:])>1e-12,axis=1)
        w=state.copy();w[1:]*=mult[:,None]
        room=.84-float(np.abs(w[0]).sum())
        optional=float(np.abs(w[1:]).sum())
        if room<0:raise ValueError('NO_2025_CORE_GROSS')
        if optional>room and optional>0:w[1:]*=room/optional
        if np.abs(w).sum()>.84+1e-10:raise ValueError('NO_2025_VIRTUAL_GROSS')
        updates[t]=np.any(np.abs(w-previous)>1e-12,axis=1)
        if k%336==0:updates[t,0]=True
        target[t]=w;previous=w
    # Verify every 2022-24 target, update and activity against frozen NO code.
    frozen=frozen_training_bundle(*(d[k][:TRAIN_HOURS] for k in ('o','h','l','c','q','rate','event')))
    if not all(np.array_equal(a,b) for a,b in zip(frozen[:3],
               (target[:TRAIN_HOURS],updates[:TRAIN_HOURS],active[:TRAIN_HOURS]))):
        raise ValueError('NO_2025_FROZEN_STRATEGY_PREFIX_DRIFT')
    return target,updates,active

def physical(d,intents,updates,book,tier,order):
    fee,slip=COSTS[tier];enabled=BOOKS[book]
    o,h,l,c,rate,event=[d[k] for k in ('o','h','l','c','rate','event')]
    qty=np.zeros((4,4));equity=10000.;prev=c[TRAIN_HOURS-1]
    turn=fees=slippage=funding=0.;scales=0;intramin=10000.
    hist=[];deltas=[];grosspeak=0.;condpeak=0.;max_intermediate=0.
    def fail(why,t):
        return {'passed':False,'failure':why,'t':t,'book':book,'tier':tier,'order':order,
                'turnover_until_failure':turn,'validation_2025_only':True}
    for t in range(TRAIN_HOURS,TOTAL):
        before=equity;before_qty=qty.copy();px=o[t]
        equity+=float(np.sum(qty*(px-prev)))
        if equity<=0 or not math.isfinite(equity):return fail('INSOLVENT_OPEN',t)
        pre_gross=float(np.sum(np.abs(qty)*px))
        pre_net=float(np.sum(np.abs(qty.sum(axis=0))*px))
        grosspeak=max(grosspeak,pre_gross/equity)
        if max(pre_gross,pre_net)>equity*(1+1e-9):return fail('PREEXISTING_GAP_LEVERAGE',t)
        guard=bool(pre_gross>.84*equity or (bool(event[t].any()) and pre_gross>.82*equity))
        need=bool(t==TRAIN_HOURS or any(updates[t-1,k] for k in enabled) or guard)
        planned=None
        if need:
            source_w=intents[t-1].copy();mask=np.zeros(4,bool);updated=np.zeros(4,bool)
            for k in enabled:
                mask[k]=True
                updated[k]=bool(t==TRAIN_HOURS or updates[t-1,k])
            source_w[~mask]=0.
            try:
                projection=project(qty,source_w,updated,px,equity,funding_event=bool(event[t].any()))
                planned=plan_virtual(qty,projection['weights'],px,equity,fee,slip,funding_event=bool(event[t].any()))
            except ValueError as exc:return fail('ATOMIC_'+str(exc),t)
            max_intermediate=max(max_intermediate,planned['max_intermediate_net_gross_fraction'])
        if planned is not None:
            traded=np.abs(planned['net_delta'])>1e-12
            if np.any(traded & (d['q'][t]<=0)):return fail('ZERO_VOLUME_EXECUTION',t)
        newqty=planned['virtual_quantity'] if planned is not None else qty
        cash=worst_funding(qty.sum(axis=0),newqty.sum(axis=0),rate[t],event[t],
            d['lo'][t-TRAIN_HOURS],d['hi'][t-TRAIN_HOURS],order) if event[t].any() else 0.
        if planned is not None:
            try:equity=settle_virtual(planned,cash,order,equity,qty,px)
            except ValueError as exc:return fail('SETTLE_'+str(exc),t)
            qty=newqty;turn+=planned['turnover'];fees+=planned['fees'];slippage+=planned['slippage']
            if planned['scale']<1-1e-10:scales+=1
        else:equity+=cash
        funding+=cash
        if equity<=0 or not math.isfinite(equity):return fail('INSOLVENT_AFTER_FUNDING',t)
        gross=float(np.sum(np.abs(qty)*px))
        netgross=float(np.sum(np.abs(qty.sum(axis=0))*px))
        grosspeak=max(grosspeak,gross/equity)
        if max(gross,netgross)>equity*(1+1e-9):return fail('POST_FUNDING_LEVERAGE',t)
        if max(gross,netgross)>equity*.90+1e-7:return fail('POST_FUNDING_GROSS_CAP',t)
        if gross:condpeak=max(condpeak,float(np.max(np.sum(np.abs(qty)*px,axis=0)))/gross)
        net=qty.sum(axis=0);worst=np.where(net>=0,l[t],h[t])
        intramin=min(intramin,equity+float(np.dot(net,worst-px)))
        if intramin<=0:return fail('INSOLVENT_INTRABAR',t)
        equity+=float(np.dot(net,c[t]-px));prev=c[t]
        if equity<=0 or not math.isfinite(equity):return fail('INSOLVENT_CLOSE',t)
        if max(float(np.sum(np.abs(qty)*c[t])),float(np.sum(np.abs(qty.sum(axis=0))*c[t])))>equity*(1+1e-9):
            return fail('CLOSE_MARK_GROSS_ABOVE_NAV',t)
        if book=='NO_full' and tier=='base' and order=='carried_before_fill':
            LEDGER.append({'t':t,'qty_before':before_qty.tolist(),'qty_after':qty.tolist(),
                'equity_before':float(before),'fee_cash':float(planned['fees'] if planned else 0.),
                'slippage_cash':float(planned['slippage'] if planned else 0.),
                'funding_cash':float(cash),'equity_close':float(equity),
                'net_before':before_qty.sum(axis=0).tolist(),'net_after':qty.sum(axis=0).tolist()})
        hist.append(equity);deltas.append(equity-before)
    curve=np.asarray(hist);peak=np.maximum.accumulate(np.r_[10000.,curve])
    dd=float(np.min(np.r_[10000.,curve]/peak-1))
    daily=curve[23::24];dr=np.diff(np.r_[10000.,daily])/np.r_[10000.,daily[:-1]]
    changes=np.asarray(deltas);wins=changes[changes>1e-10];loss=-changes[changes< -1e-10]
    return {'passed':True,'book':book,'tier':tier,'order':order,'final_equity':float(equity),
        'cagr_2025':float(equity/10000.-1),'log_growth':float(np.log(equity/10000.)),
        'max_dd':dd,'turnover':turn,'fees':fees,'slippage':slippage,'funding':funding,
        'scaled_atomic_fills':scales,'max_intermediate_gross_fraction':max_intermediate,
        'max_pretrade_or_post_gross_fraction':grosspeak,'min_intrabar_equity':intramin,
        'max_single_asset_gross_concentration':condpeak,'positive_days':int((dr>0).sum()),
        'daily_count':len(dr),'daily_win_rate':float(np.mean(dr>0)),
        'cvar_1pct':float(np.mean(np.sort(dr)[:max(1,len(dr)//100)])),
        'hourly_net_pf':float(wins.sum()/loss.sum()) if len(loss) else None,
        'hourly_net_payoff':float(wins.mean()/loss.mean()) if len(wins) and len(loss) else None,
        'hourly_net_win_rate':float(len(wins)/(len(wins)+len(loss))) if len(wins)+len(loss) else 0.,
        'one_way_netting':True,'validation_2025_only':True}

def run(train_root,validation_root):
    d=load(train_root,validation_root)
    intents,updates,active=extended_bundle(d)
    cells=[]
    for tier in COSTS:
        for order in ORDERS:
            for book in BOOKS:
                x=physical(d,intents,updates,book,tier,order)
                cells.append(x)
                print('NO_2025_CELL',tier,order,book,'PHYSICAL',x['passed'],
                    'RETURN',round(x.get('cagr_2025',-1)*100,3),
                    'TURN',round(x.get('turnover',-1)),x.get('failure',''),flush=True)
    failures=[];marg={}
    for tier in COSTS:
        for order in ORDERS:
            group={x['book']:x for x in cells if x['tier']==tier and x['order']==order}
            key=tier+'/'+order
            if not all(x['passed'] for x in group.values()):
                failures.append(key+':physical_invariant');continue
            full=group['NO_full']
            marg[key]={s:float(full['log_growth']-group[b]['log_growth'])
                for s,b in [('Opportunity','NO_minus_opportunity'),
                            ('Relative_Value','NO_minus_RV'),('Stress_Recovery','NO_minus_stress')]}
            if tier not in ('base','severe'):continue
            if full['log_growth']<=0:failures.append(key+':nonpositive_growth')
            if full['turnover']>350000:failures.append(key+':turnover')
            if tier=='severe' and full['max_dd']<=-.45:failures.append(key+':max_dd')
            for s,v in marg[key].items():
                if v<=0:failures.append(key+':'+s+':marginal')
    return {'architecture':'NO','validation_year':2025,'cells':cells,'marginals':marg,
        'gate_failures':failures,'decision':('REJECT_SEALED_2025_VALIDATION' if failures
        else 'PASS_PROVISIONAL_2025_PHYSICAL_AWAIT_INDEPENDENT_ORACLES'),
        'source_frozen_prefix_reproduced':True,'native_30cell_executed':len(cells)==30,
        'validation_2025_only':True,'2026_future_holdout_accessed':False,
        'eligible_for_promotion':False,'external_benchmarks_accessed':False,
        'live_authorized':False,'exact_funding_tick_mark_attested':False}
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--training-root',required=True);p.add_argument('--validation-root',required=True)
    p.add_argument('--output',required=True);p.add_argument('--ledger-output',default='v98_no_2025_base_full_hourly_forensic.jsonl')
    a=p.parse_args()
    result=run(a.training_root,a.validation_root)
    with open(a.output,'w') as f:json.dump(result,f,indent=2,sort_keys=True,allow_nan=False)
    if len(LEDGER)==HOURS_2025:
        with open(a.ledger_output,'w') as f:
            for row in LEDGER:f.write(json.dumps(row,allow_nan=False,separators=(',',':'))+'\n')
        print('NO_2025_FULL_BASE_LEDGER',len(LEDGER),flush=True)
    print('NO_2025_GATE',result['decision'],result['gate_failures'],flush=True)
    raise SystemExit(0 if result['decision']=='PASS_PROVISIONAL_2025_PHYSICAL_AWAIT_INDEPENDENT_ORACLES' else 2)
