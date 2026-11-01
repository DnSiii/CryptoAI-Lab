#!/usr/bin/env python3
"""V98 PB preregistered funding-dislocation / cross-asset leadership seven-slot complete engine.
Only exposed Clean-4 2022-25 training; no V99/benchmarks/2026+/paper/holdout.
"""
import json, math
import numpy as np
from ot_breadth_dispersion import source_gate, independent_accounting, COSTS, ORDERS, HOURS, WARMUP, STEP, YEAREND
from ot_independent_oracle import independent_fills
from v98_oneway_net_atomic_planner import plan_virtual, settle_virtual
from v98_mark_envelope_settlement import worst_funding

BOOKS={"PB_full":(0,1,2,3),"PB_core_only":(0,),
       "PB_minus_opportunity":(0,2,3),"PB_minus_RV":(0,1,3),
       "PB_minus_stress":(0,1,2)}
PRIORITY={"risk_on":(1,2,3),"risk_off":(3,2,1),"mixed":(2,1,3)}
MULT={"risk_on":(1.,1.,.50),"risk_off":(.50,.75,1.),"mixed":(.75,1.,.75)}
CLOCK=tuple(range(WARMUP,HOURS,STEP))

def physical(d,targets,book,tier,order,record=False):
    fee,slip=COSTS[tier]
    qty=np.zeros((4,4),dtype=float)
    nav=10000.
    equity_path=[];hour_changes=[];ledger=[]
    turnover=fees=slippage=funding=0.
    max_intermediate=max_gross=max_concentration=0.
    min_intrabar=10000.;fills=forced=0
    annual={};annual_start={2023:10000.}
    def reject(why,t):
        return {"passed":False,"book":book,"tier":tier,"order":order,"failure":why,"hour":t,
                "training_only":True},ledger
    for t in range(WARMUP+1,HOURS):
        before=nav
        px=d["o"][t]; close=d["c"][t]; previous=d["c"][t-1]
        gap_cash=float(np.sum(qty*(px-previous)))
        nav+=gap_cash
        if not math.isfinite(nav) or nav<=0:return reject("INSOLVENT_OPEN",t)
        pre_gross=float(np.sum(np.abs(qty)*px))
        pre_net=float(np.sum(np.abs(qty.sum(axis=0))*px))
        max_gross=max(max_gross,pre_gross/nav)
        if max(pre_gross,pre_net)>nav*(1+1e-9):return reject("GAP_GROSS_ABOVE_NAV",t)
        weekly=(t-1) in targets
        event=bool(d["event"][t].any())
        guard=(pre_gross>.82*nav or (event and pre_gross>.80*nav))
        plan=None
        if weekly or guard:
            if weekly:
                weights=targets[t-1]
            else:
                weights=qty*px/nav
                gross=float(np.abs(weights).sum())
                if gross>0:weights*=((.76 if event else .78)/gross)
            try:
                plan=plan_virtual(qty,weights,px,nav,fee,slip,funding_event=event,target_virtual_cap=.88)
            except ValueError as exc:return reject("PLAN_"+str(exc),t)
            if np.any((np.abs(plan["net_delta"])>1e-12)&(~d["execution_allowed"][t])):
                return reject("ZERO_VOLUME_EXECUTION",t)
            max_intermediate=max(max_intermediate,plan["max_intermediate_net_gross_fraction"])
            if plan["turnover"]>1e-8:fills+=1
            if guard and not weekly:forced+=1
        next_qty=plan["virtual_quantity"] if plan is not None else qty
        cash=worst_funding(qty.sum(axis=0),next_qty.sum(axis=0),d["rate"][t],d["event"][t],
                           d["mark_lower"][t],d["mark_upper"][t],order) if event else 0.
        if plan is not None:
            try:nav=settle_virtual(plan,cash,order,nav,qty,px)
            except ValueError as exc:return reject("SETTLEMENT_"+str(exc),t)
            qty=next_qty
            turnover+=plan["turnover"];fees+=plan["fees"];slippage+=plan["slippage"]
        else:nav+=cash
        funding+=cash
        if nav<=0 or not math.isfinite(nav):return reject("INSOLVENT_AFTER_SETTLEMENT",t)
        gross=float(np.sum(np.abs(qty)*px))
        netgross=float(np.sum(np.abs(qty.sum(axis=0))*px))
        max_gross=max(max_gross,gross/nav)
        if max(gross,netgross)>.90*nav+1e-6:return reject("POST_FUNDING_GROSS_CAP",t)
        if gross>0:
            max_concentration=max(max_concentration,float(np.max(np.sum(np.abs(qty)*px,axis=0)))/gross)
        net=qty.sum(axis=0)
        adverse=np.where(net>=0,d["l"][t],d["h"][t])
        intra=nav+float(np.dot(net,adverse-px))
        min_intrabar=min(min_intrabar,intra)
        if intra<=0:return reject("INSOLVENT_INTRABAR",t)
        nav+=float(np.dot(net,close-px))
        if nav<=0 or not math.isfinite(nav):return reject("INSOLVENT_CLOSE",t)
        if float(np.sum(np.abs(qty)*close))>nav*(1+1e-9):
            return reject("CLOSE_VIRTUAL_GROSS_ABOVE_NAV",t)
        if record:
            ledger.append((t,before,nav,cash,float(plan["fees"] if plan else 0.),
                           float(plan["slippage"] if plan else 0.),
                           qty.copy(),gap_cash))
        equity_path.append(nav);hour_changes.append(nav-before)
        if t in YEAREND:
            y=YEAREND[t];annual[y]=nav/annual_start[y]-1
            if y<2025:annual_start[y+1]=nav
    curve=np.asarray(equity_path)
    peak=np.maximum.accumulate(np.r_[10000.,curve])
    dd=float(np.min(np.r_[10000.,curve]/peak-1))
    daily=curve[22::24]
    daily_returns=np.diff(np.r_[10000.,daily])/np.r_[10000.,daily[:-1]]
    changes=np.asarray(hour_changes)
    wins=changes[changes>1e-10];loss=-changes[changes< -1e-10]
    log_growth=math.log(nav/10000.)
    return {"passed":True,"book":book,"tier":tier,"order":order,
            "final_equity":float(nav),"cagr":float((nav/10000.)**(365.25/1096.)-1),
            "log_growth":log_growth,"year_returns":{str(y):float(v) for y,v in annual.items()},
            "max_dd":dd,"turnover":turnover,"fees":fees,"slippage":slippage,"funding":funding,
            "max_intermediate_gross_fraction":max_intermediate,"max_pretrade_post_gross_fraction":max_gross,
            "max_single_asset_gross_concentration":max_concentration,
            "min_intrabar_equity":min_intrabar,"physical_fills":fills,"forced_safety_fills":forced,
            "positive_days":int(np.sum(daily_returns>0)),"daily_count":len(daily_returns),
            "daily_win_rate":float(np.mean(daily_returns>0)),
            "daily_cvar_1pct":float(np.mean(np.sort(daily_returns)[:max(1,len(daily_returns)//100)])),
            "hourly_net_pf":float(wins.sum()/loss.sum()) if len(loss) else None,
            "hourly_net_payoff":float(wins.mean()/loss.mean()) if len(wins) and len(loss) else None,
            "hourly_net_win_rate":float(len(wins)/(len(wins)+len(loss))) if len(wins)+len(loss) else 0.,
            "trade_pf_payoff_win_rate_independent":False,
            "training_only":True,"exact_tick_mark":False},ledger


def signals(d):
    c=np.asarray(d["c"],float)
    rate=np.asarray(d["rate"],float)
    if c.shape!=(HOURS,4) or rate.shape!=(HOURS,4) or not np.isfinite(c).all() or not np.isfinite(rate).all() or np.any(c<=0):
        raise ValueError("PB_BAD_CLOSE_OR_FUNDING")
    p=np.log(c);out={}
    for t in CLOCK:
        r672=p[t]-p[t-672]
        r168=p[t]-p[t-168]
        r24=p[t]-p[t-24]
        # Only the 21 funding events that settled BEFORE the decision t.
        past=rate[t-168:t:8]
        if past.shape!=(21,4):raise ValueError("PB_FUNDING_WINDOW")
        mean_funding=np.mean(past,axis=0)
        score=r672+.65*r168-120.*mean_funding
        positive=int(np.sum(r168>0))
        negative=int(np.sum(r168<0))
        mode=("risk_on" if positive>=3 and r168[0]>0 else
              "risk_off" if negative>=3 and r168[0]<0 else "mixed")
        raw=np.zeros((4,4),float)
        if mode=="risk_on":
            ranked=sorted((j for j in range(4) if score[j]>0),key=lambda j:(-score[j],j))
            for j,w in zip(ranked[:2],(.50,.18)):raw[0,j]=w
        elif mode=="risk_off":
            ranked=sorted((j for j in range(4) if score[j]<0),key=lambda j:(score[j],j))
            for j,w in zip(ranked[:2],(-.42,-.20)):raw[0,j]=w
        else:
            best=min(range(4),key=lambda j:(-score[j],j))
            worst=min(range(4),key=lambda j:(score[j],j))
            if score[best]>0 and r168[best]>0:raw[0,best]=.35
            elif score[worst]<0 and r168[worst]<0:raw[0,worst]=-.30
        ups=[j for j in (1,2,3) if mean_funding[j]<-.00005 and r24[j]>.04 and r168[j]>0]
        downs=[j for j in (1,2,3) if mean_funding[j]>.00015 and r24[j]<-.05 and r168[j]<0]
        if ups:raw[1,min(ups,key=lambda j:(-r24[j],j))]=.20
        elif downs:raw[1,min(downs,key=lambda j:(r24[j],j))]=-.20
        low=min((1,2,3),key=lambda j:(mean_funding[j],j))
        high=min((1,2,3),key=lambda j:(-mean_funding[j],j))
        if low!=high and mean_funding[high]-mean_funding[low]>.00015 and r168[low]-r168[high]>.04 and r168[low]>0:
            raw[2,low]=.12;raw[2,high]=-.12
        if r168[0]<-.10 and negative>=3:
            raw[3,0]=-.18
        elif r168[0]<-.10 and r24[0]>.035 and int(np.sum(r24>0))>=3:
            raw[3,0]=.18
        raw[1:]*=np.asarray(MULT[mode])[:,None]
        out[t]=(raw,mode)
    if len(out)!=157:raise ValueError("PB_WEEKLY_CLOCK")
    return out

def allocate(raw,mode,active):
    if raw.shape!=(4,4) or mode not in PRIORITY or not np.isfinite(raw).all():
        raise ValueError("PB_ALLOC_INPUT")
    held=np.zeros((4,4),float)
    if 0 in active:held[0]=raw[0]
    room=min(.30,max(0.,.88-float(np.abs(held).sum())))
    for slot in PRIORITY[mode]:
        if slot not in active:continue
        wanted=float(np.abs(raw[slot]).sum())
        if wanted>0 and room>0:
            use=min(wanted,room)
            held[slot]=raw[slot]*(use/wanted)
            room-=use
    if float(np.abs(held).sum())>.88+1e-10 or float(np.abs(held[1:]).sum())>.30+1e-10:
        raise ValueError("PB_GROSS_BREACH")
    return held

def target_books(decisions):
    return {name:{t:allocate(raw,mode,active) for t,(raw,mode) in decisions.items()}
            for name,active in BOOKS.items()}

def synthetic_test():
    tt=np.arange(HOURS)[:,None];jj=np.arange(4)[None,:]
    c=100*np.exp(.00007*tt*(1+jj/8)+.04*np.sin(tt/79+jj)+.02*np.cos(tt/43+jj))
    rate=np.zeros_like(c)
    a=signals({"c":c,"rate":rate})
    modified=c.copy();modified[15000:]*=np.array([.7,1.5,.8,1.8])
    b=signals({"c":modified,"rate":rate})
    for t in CLOCK:
        if t<15000 and (a[t][1]!=b[t][1] or not np.array_equal(a[t][0],b[t][0])):
            raise ValueError("PB_FUTURE_LEAK")
    altered_rate=rate.copy();altered_rate[15000:]=.0003
    d=signals({"c":c,"rate":altered_rate})
    for t in CLOCK:
        if t<15000 and (a[t][1]!=d[t][1] or not np.array_equal(a[t][0],d[t][0])):
            raise ValueError("PB_FUTURE_FUNDING_LEAK")
    books=target_books(a)
    if len(books)!=5 or any(len(v)!=157 for v in books.values()):
        raise ValueError("PB_BOOK_CLOCK")
    return {"decision":"PASS_PB_SYNTHETIC_CAUSALITY_NOT_PNL","decisions":157,
            "previous_settled_funding_only":True}

def run(d):
    source=source_gate(d)
    decisions=signals(d);books=target_books(decisions)
    from pb_independent_oracle import independent_decisions
    oracle=independent_decisions(d,decisions,books)
    if oracle["signal_and_allocation_mismatches"]:
        raise ValueError("PB_INDEPENDENT_DECISION_MISMATCH")
    print("PB_INDEPENDENT_DECISION_ORACLE",json.dumps(oracle,sort_keys=True),flush=True)
    cells=[];ledger=None
    for tier in COSTS:
        for order in ORDERS:
            for book in BOOKS:
                capture=(tier=="base" and order=="carried_before_fill" and book=="PB_full")
                row,detail=physical(d,books[book],book,tier,order,record=capture)
                cells.append(row)
                if capture:ledger=detail
                print("PB_CELL",tier,order,book,"PHYSICAL",row["passed"],
                      "CAGR",round(100*row.get("cagr",-1),3),"FAIL",row.get("failure",""),flush=True)
    audit=independent_accounting(d,ledger) if ledger and len(ledger)==HOURS-WARMUP-1 else None
    fill_oracle=independent_fills(d,ledger) if audit is not None else None
    failures=[];marginals={}
    for tier in COSTS:
        for order in ORDERS:
            group={x["book"]:x for x in cells if x["tier"]==tier and x["order"]==order}
            if not all(x["passed"] for x in group.values()):
                failures.append(tier+"/"+order+":physical")
                continue
            full=group["PB_full"];key=tier+"/"+order
            marginals[key]={slot:full["log_growth"]-group[book]["log_growth"]
                for slot,book in (("Opportunity","PB_minus_opportunity"),
                                  ("Relative_Value","PB_minus_RV"),
                                  ("Stress_Recovery","PB_minus_stress"))}
            if tier not in ("base","severe"):continue
            if full["cagr"]<=(.80 if tier=="base" else .60):failures.append(key+":CAGR")
            if full["turnover"]>1_000_000:failures.append(key+":turnover")
            if tier=="severe":
                if full["max_dd"]<=-.45:failures.append(key+":DD")
                if any(v<=0 for v in full["year_returns"].values()):failures.append(key+":annual")
            for slot,book in (("Opportunity","PB_minus_opportunity"),
                              ("Relative_Value","PB_minus_RV"),
                              ("Stress_Recovery","PB_minus_stress")):
                if marginals[key][slot]<=.02:failures.append(key+":"+slot+":marginal")
                for year in ("2023","2024","2025"):
                    diff=math.log1p(full["year_returns"][year])-math.log1p(group[book]["year_returns"][year])
                    if diff<-.03:failures.append(key+":"+slot+":"+year+":annual_marginal")
    if audit is None or audit["cash_identity_mismatches"]:failures.append("independent_accounting")
    if fill_oracle is None or fill_oracle["independent_fee_slippage_funding_mismatches"]:
        failures.append("independent_fills")
    out={"architecture":"PB","preregistration":"pb_funding_dislocation_prereg_20261031.md",
         "source":source,"weekly_decisions":len(decisions),"cells":cells,
         "marginals":marginals,"audit":audit,"independent_decision_oracle":oracle,
         "independent_fill_oracle":fill_oracle,"gate_failures":failures,
         "decision":"REJECT_PB_TRAINING" if failures else "PASS_PROVISIONAL_PB_TRAINING_NOT_VALIDATED",
         "training_only":True,"year_2025_exposed":True,"exact_event_mark_attested":False,
         "holdout_accessed":False,"benchmarks_accessed":False,"paper_or_live_authorized":False}
    print("PB_RESULT_JSON",json.dumps(out,separators=(",",":"),allow_nan=False),flush=True)
    return out

if __name__=="__main__":
    print(json.dumps(synthetic_test(),sort_keys=True))
