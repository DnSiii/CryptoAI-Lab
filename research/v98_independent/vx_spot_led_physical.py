#!/usr/bin/env python3
"""V98 VX spot-led seven-slot exposed-2025 PHYSICAL FALSIFICATION.
Not validation, not account-authenticated fills or funding marks, not paper/live.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from pathlib import Path
import numpy as np
from vw_native_carry_physical import load as load_vw
from vx_spot_led_composed import ASSETS,HOURS,BOOKS,books,from_vw_data,source_gate

TIERS={"base":(.0015,.0010),"severe":(.0025,.0020),
       "supersevere":(.0040,.0035)}
ORDERS=("carried_before_fill","new_after_fill")
INITIAL=10000.
FIELDS=("hour","equity_before","equity_after","cash_before","cash_after",
        "perp_gap","spot_gap","funding","cost","spot_trade_cash",
        "perp_intrahour_pnl","spot_qty","perp_qty","spot_open","spot_close",
        "perp_open","perp_close")

def geometry(data):
    spot=np.array([[data[a][0][t][:4] for a in ASSETS] for t in range(HOURS)],float)
    perp=np.array([[data[a][1][t][:4] for a in ASSETS] for t in range(HOURS)],float)
    spot_volume=np.array([[data[a][0][t][4] for a in ASSETS] for t in range(HOURS)],float)
    perp_volume=np.array([[data[a][1][t][4] for a in ASSETS] for t in range(HOURS)],float)
    rates=np.zeros((HOURS,4));lower=np.zeros((HOURS,4));upper=np.zeros((HOURS,4))
    for j,a in enumerate(ASSETS):
        for t,(r,lo,hi) in data[a][2].items():
            rates[t,j]=float(r);lower[t,j]=float(lo);upper[t,j]=float(hi)
    if not np.isfinite(spot).all() or not np.isfinite(perp).all():
        raise ValueError("VX_PHYSICAL_SOURCE_NONFINITE")
    return spot,perp,spot_volume,perp_volume,rates,lower,upper

def replay(data,targets,tier,order,record=False):
    if tier not in TIERS or order not in ORDERS:raise ValueError("VX_SCENARIO")
    spot,perp,sv,pv,rates,lower,upper=geometry(data)
    spot_cost,perp_cost=TIERS[tier]
    sq=np.zeros(4);pq=np.zeros(4);cash=INITIAL
    ledger=[];equities=[];changes=[];daily=[];funding_total=fees=turnover=0.
    max_dd=0.;peak=INITIAL;min_adverse=INITIAL;max_gross=0.
    rebalance_count=0;events_checked=0
    def funding(t):
        nonlocal cash,funding_total,events_checked
        if t%8: return 0.
        events_checked+=4
        # Short USD-M receives positive funding at lower mark, pays negative
        # funding at upper mark. No exact event mark is claimed.
        mark=np.where(rates[t]>=0,lower[t],upper[t])
        delta=float(-np.dot(pq,rates[t]*mark))
        cash+=delta;funding_total+=delta
        return delta
    def reject(why,t):
        return {"passed":False,"tier":tier,"order":order,
                "failure":why,"hour":t},ledger
    for t in range(HOURS):
        before=cash+float(np.dot(sq,spot[t-1,:,3])) if t else INITIAL
        cash_before=cash
        so=spot[t,:,0];po=perp[t,:,0]
        spot_gap=float(np.dot(sq,so-(spot[t-1,:,3] if t else so)))
        perp_gap=float(np.dot(pq,po-(perp[t-1,:,3] if t else po)))
        cash+=perp_gap
        funding_delta=0.;cost=0.;spot_trade_cash=0.
        if order=="carried_before_fill":funding_delta+=funding(t)
        if t==HOURS-1 or (t-1) in targets:
            eq_open=cash+float(np.dot(sq,so))
            if not math.isfinite(eq_open) or eq_open<=0:return reject("INSOLVENT_AT_OPEN",t)
            w=targets.get(t-1)
            if w is None:w=np.zeros((4,2,4))
            target_spot=w[:,0,:].sum(axis=0)*eq_open/so
            target_perp=w[:,1,:].sum(axis=0)*eq_open/po
            if (np.any(target_spot< -1e-12) or np.any(target_perp>1e-12)
                or np.sum(np.abs(w))>.80+1e-9
                or np.sum(np.abs(w[:,0]))>.65+1e-9
                or np.sum(np.abs(w[:,1]))>.20+1e-9):
                return reject("TARGET_GROSS_OR_SIGN",t)
            delta_spot=target_spot-sq;delta_perp=target_perp-pq
            if np.any((np.abs(delta_spot)>1e-12)&(sv[t]<=0)) or np.any((np.abs(delta_perp)>1e-12)&(pv[t]<=0)):
                return reject("ZERO_VOLUME_FILL",t)
            spot_trade_cash=float(-np.dot(delta_spot,so))
            trade_spot=float(np.sum(np.abs(delta_spot)*so))
            trade_perp=float(np.sum(np.abs(delta_perp)*po))
            cost=spot_cost*trade_spot+perp_cost*trade_perp
            cash+=spot_trade_cash-cost
            fees+=cost;turnover+=trade_spot+trade_perp
            sq=target_spot;pq=target_perp;rebalance_count+=1
        if order=="new_after_fill":funding_delta+=funding(t)
        short=float(np.dot(-pq,po))
        spotgross=float(np.dot(sq,so))
        equity_open=cash+spotgross
        if (not math.isfinite(equity_open) or equity_open<=0
            or cash<.20*short-1e-7 or spotgross+short>equity_open*(1+1e-8)):
            return reject("CASH_MARGIN_OR_HIDDEN_LEVERAGE",t)
        adverse=cash+float(np.dot(sq,spot[t,:,2]))+float(np.dot(pq,perp[t,:,1]-po))
        min_adverse=min(min_adverse,adverse)
        if adverse<=max(0.,.05*short):return reject("ADVERSE_MARGIN",t)
        perp_pnl=float(np.dot(pq,perp[t,:,3]-po))
        cash+=perp_pnl
        equity=cash+float(np.dot(sq,spot[t,:,3]))
        if not math.isfinite(equity) or equity<=0:return reject("CLOSE_INSOLVENCY",t)
        gross=float(np.dot(sq,spot[t,:,3])+np.dot(-pq,perp[t,:,3]))
        max_gross=max(max_gross,gross/equity)
        if gross>equity*(1+1e-8):return reject("CLOSE_HIDDEN_LEVERAGE",t)
        peak=max(peak,equity);max_dd=min(max_dd,equity/peak-1.)
        equities.append(equity);changes.append(equity-before)
        if t%24==23:daily.append(equity)
        if record:
            ledger.append((t,before,equity,cash_before,cash,perp_gap,spot_gap,
                           funding_delta,cost,spot_trade_cash,perp_pnl,
                           sq.copy(),pq.copy(),so.copy(),spot[t,:,3].copy(),
                           po.copy(),perp[t,:,3].copy()))
    if np.max(np.abs(sq))>1e-12 or np.max(np.abs(pq))>1e-12 or events_checked!=4380:
        return reject("UNCLOSED_OR_FUNDING_COUNT",HOURS)
    x=np.array(changes);pos=x[x>1e-10];neg=-x[x< -1e-10]
    days=np.array(daily)
    dayret=np.diff(np.r_[INITIAL,days])/np.r_[INITIAL,days[:-1]]
    final=float(equities[-1])
    return {"passed":True,"tier":tier,"order":order,
            "final_equity":final,"return_2025":final/INITIAL-1.,
            "log_growth":math.log(final/INITIAL),"max_dd":max_dd,
            "min_adverse_equity":min_adverse,"max_gross_fraction":max_gross,
            "fees_spread_impact":fees,"funding":funding_total,
            "turnover":turnover,"rebalance_count":rebalance_count,
            "funding_events_checked":events_checked,
            "positive_days":int((dayret>0).sum()),"days":len(dayret),
            "hourly_net_pf":float(pos.sum()/neg.sum()) if len(neg) else None,
            "hourly_net_payoff":float(pos.mean()/neg.mean()) if len(pos) and len(neg) else None,
            "hourly_net_win_rate":float(len(pos)/(len(pos)+len(neg))) if len(pos)+len(neg) else 0.,
            "trade_level_pf_not_yet_audited":True,
            "historical_account_fees_authenticated":False,
            "exact_exchange_funding_mark_authenticated":False},ledger

def run(spot_dir,nh_dir,out_dir):
    data=load_vw(spot_dir,nh_dir)
    targets=books(from_vw_data(data))
    out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    cells=[];record=None
    for tier in TIERS:
        for order in ORDERS:
            for name,target in targets.items():
                row,ledger=replay(data,target,tier,order,record=(tier=="base" and order=="carried_before_fill" and name=="VX_full"))
                row["book"]=name;cells.append(row)
                if ledger:record=ledger
                print("VX_PHYSICAL",tier,order,name,row["passed"],row.get("return_2025"),row.get("failure"),flush=True)
    fails=[];marginals={}
    for tier in TIERS:
        for order in ORDERS:
            group={x["book"]:x for x in cells if x["tier"]==tier and x["order"]==order}
            label=tier+"/"+order
            if not all(x["passed"] for x in group.values()):
                fails.append(label+":physical");continue
            full=group["VX_full"]
            marginals[label]={slot:full["log_growth"]-group[other]["log_growth"] for slot,other in (
                ("Opportunity","VX_minus_opportunity"),("Relative_Value","VX_minus_RV"),
                ("Stress_Recovery","VX_minus_stress"))}
            if tier in ("base","severe"):
                if full["return_2025"]<=(.80 if tier=="base" else .60):fails.append(label+":2025_growth")
                if tier=="severe" and full["max_dd"]<=-.45:fails.append(label+":drawdown")
                for slot,v in marginals[label].items():
                    if v<=.02:fails.append(label+":"+slot+":marginal")
    receipt={"architecture":"VX","preregistration":"vx_spot_led_composed_prereg_20261102.md",
             "source_period":"2025 EXPOSED TRAINING ONLY","cells":cells,"marginals":marginals,
             "gate_failures":fails,
             "decision":"REJECT_VX_EXPOSED_TRAINING" if fails else "PASS_VX_EXPOSED_TRAINING_ONLY_NOT_VALIDATED",
             "independent_cash_and_fill_oracle_pending":True,
             "account_costs_authenticated":False,"exact_funding_marks_authenticated":False,
             "2026_accessed":False,"holdout_accessed":False,"benchmarks_accessed":False,
             "paper_live_authorized":False}
    (out/"vx_exposed_physical.json").write_text(json.dumps(receipt,indent=2,sort_keys=True,allow_nan=False)+"\n")
    if record:
        with (out/"vx_base_full_hourly_ledger.csv").open("w",newline="") as f:
            writer=csv.writer(f,lineterminator="\n")
            writer.writerow(FIELDS)
            for row in record:
                writer.writerow([json.dumps(v.tolist(),separators=(",",":")) if isinstance(v,np.ndarray)
                                 else format(v,".15g") if isinstance(v,float) else v for v in row])
    print("VX_EXPOSED_TRAINING_DECISION",receipt["decision"],len(fails),flush=True)
    return receipt

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in ("spot-dir","nh-dir","out-dir"):p.add_argument("--"+k,required=True)
    a=p.parse_args();run(a.spot_dir,a.nh_dir,a.out_dir)
