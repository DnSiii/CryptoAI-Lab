#!/usr/bin/env python3
"""V98 VY: full Clean-4 2023-25 exposed-training physical perpetual cash ledger.
Not authenticated account execution, not future validation, not paper/live.
"""
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path
import numpy as np
from v98_2025_full_training_source_bridge import load
from vy_cross_sectional_spread import HOURS,CLOCK,BOOKS,books,targets,incidence,source_gate

TIERS={"base":.0010,"severe":.0020,"supersevere":.0035}
ORDERS=("carried_before_fill","new_after_fill")
INITIAL=10000.
HEADER=("hour","cash_before","cash_after","equity_before","equity_after",
        "gap_pnl","intrahour_pnl","funding","cost","trade_notional",
        "qty","open","close","rate","lower","upper","target_weight")
def get_data(a):
    return load(a.old_root,a.old_envelope,a.new_root,a.corrected_root)

def simulate(d,target,tier,order,record=False):
    if tier not in TIERS or order not in ORDERS:raise ValueError("VY_COST_ORDER")
    source_gate(d)
    q=np.zeros(4);cash=INITIAL;peak=INITIAL;dd=0.;min_adverse=INITIAL
    funding_sum=fees=turnover=0.;funding_count=0;trade_count=0
    equities=[];changes=[];daily=[];year_ends={};ledger=[]
    max_gross=0.;gross_contribution=np.zeros(4);pos_hours=np.zeros(4,int)
    price=np.asarray(d["c"],float)
    def fund(t):
        nonlocal cash,funding_sum,funding_count
        if t%8:return 0.
        funding_count+=4
        rates=d["rate"][t]
        marks=np.where(q*rates>0,d["mark_upper"][t],d["mark_lower"][t])
        val=-float(np.dot(q,rates*marks))
        cash+=val;funding_sum+=val
        return val
    def fail(reason,t):
        return {"passed":False,"reason":reason,"hour":t,"tier":tier,"order":order},ledger
    for t in range(HOURS):
        before=cash
        op=d["o"][t];cl=price[t]
        gap=float(np.dot(q,op-(price[t-1] if t else op)))
        cash+=gap
        f=0.;cost=0.;traded=0.;w=np.zeros(4)
        if order=="carried_before_fill":f+=fund(t)
        if t==HOURS-1 or t-1 in target:
            eq=cash
            if not math.isfinite(eq) or eq<=0:return fail("INSOLVENT_PRETRADE",t)
            if t!=HOURS-1:w=np.asarray(target[t-1],float)
            if (not np.isfinite(w).all() or np.abs(w).sum()>.90+1e-8
                or abs(float(w.sum()))>1e-8):
                return fail("GROSS_OR_NET_TARGET",t)
            desired=w*eq/op
            delta=desired-q
            if np.any((np.abs(delta)>1e-12)&(d["q"][t]<=0)):
                return fail("ZERO_VOLUME_FILL",t)
            traded=float(np.dot(np.abs(delta),op))
            cost=TIERS[tier]*traded
            cash-=cost;fees+=cost;turnover+=traded
            trade_count+=int(np.sum(np.abs(delta)>1e-12))
            q=desired
        if order=="new_after_fill":f+=fund(t)
        gross=float(np.dot(np.abs(q),op))
        if (not math.isfinite(cash) or cash<=0 or gross>cash*(1+1e-8)
            or cash<.10*gross-1e-7):
            return fail("CASH_OR_HIDDEN_LEVERAGE",t)
        worst=np.where(q>=0,d["l"][t],d["h"][t])
        adverse=cash+float(np.dot(q,worst-op))
        min_adverse=min(min_adverse,adverse)
        if adverse<=.10*gross:return fail("INTRAHOUR_ADVERSE_MARGIN",t)
        intrahour=float(np.dot(q,cl-op))
        cash+=intrahour
        if not math.isfinite(cash) or cash<=0:return fail("CLOSE_INSOLVENCY",t)
        if float(np.dot(np.abs(q),cl))>cash*(1+1e-8):
            return fail("CLOSE_HIDDEN_LEVERAGE",t)
        max_gross=max(max_gross,float(np.dot(np.abs(q),cl))/cash)
        peak=max(peak,cash);dd=min(dd,cash/peak-1.)
        changes.append(cash-before);equities.append(cash)
        gross_contribution+=np.abs(q*cl);pos_hours+=(np.abs(q)>1e-12)
        if t%24==23:daily.append(cash)
        if t in (743,9503,18287,27047):year_ends[t]=cash
        if record:
            ledger.append((t,before,cash,before,cash,gap,intrahour,f,cost,traded,
                           q.copy(),op.copy(),cl.copy(),d["rate"][t].copy(),
                           d["mark_lower"][t].copy(),d["mark_upper"][t].copy(),w.copy()))
    if np.any(np.abs(q)>1e-10) or funding_count!=13524:
        return fail("TERMINAL_POSITION_OR_EVENT_COUNT",HOURS)
    x=np.asarray(changes)
    pos=x[x>1e-10];neg=-x[x< -1e-10]
    days=np.asarray(daily)
    dayret=np.diff(np.r_[INITIAL,days])/np.r_[INITIAL,days[:-1]]
    # 2023 8760h: index 744..9503; 2024 leap-year 8784h: 9504..18287.
    annual={"2023":year_ends[9503]/year_ends[743]-1.,
            "2024":year_ends[18287]/year_ends[9503]-1.,
            "2025":year_ends[27047]/year_ends[18287]-1.}
    final=float(cash)
    years=3.
    return {"passed":True,"tier":tier,"order":order,"final_equity":final,
            "compounded_return":final/INITIAL-1.,
            "cagr":(final/INITIAL)**(1./years)-1.,
            "log_growth":math.log(final/INITIAL),"annual_returns":annual,
            "max_dd":dd,"min_adverse_equity":min_adverse,"max_gross_fraction":max_gross,
            "fees_spread_impact":fees,"signed_funding":funding_sum,
            "turnover":turnover,"trades":trade_count,
            "funding_events_checked":funding_count,
            "positive_days":int((dayret>0).sum()),"days":len(dayret),
            "worst_day":float(dayret.min()),"best_day":float(dayret.max()),
            "hourly_net_pf":float(pos.sum()/neg.sum()) if len(neg) else None,
            "hourly_net_payoff":float(pos.mean()/neg.mean()) if len(pos) and len(neg) else None,
            "hourly_net_win_rate":float(len(pos)/(len(pos)+len(neg))) if len(pos)+len(neg) else 0.,
            "position_hours":pos_hours.tolist(),
            "gross_concentration":(gross_contribution/max(gross_contribution.sum(),1.)).tolist(),
            "trade_level_pf_pending_independent_lot_audit":True,
            "account_costs_authenticated":False,"exact_exchange_marks_authenticated":False},ledger

def run(d,out_dir):
    source_gate(d)
    decisions=targets(d)
    counts={k:int(v) for k,v in incidence(decisions).items()}
    if any(counts[k]<int(.15*len(CLOCK)) for k in list(counts)[1:]):
        raise ValueError("VY_SOURCE_INCIDENCE_FAILED_BEFORE_PNL")
    b=books(d)
    out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    cells=[];frozen_ledger=None
    for tier in TIERS:
        for order in ORDERS:
            for name,tgt in b.items():
                keep=tier=="base" and order==ORDERS[0] and name=="VY_full"
                result,ledger=simulate(d,tgt,tier,order,record=keep)
                result["book"]=name;cells.append(result)
                if keep:frozen_ledger=ledger
                print("VY_PHYSICAL",tier,order,name,result.get("passed"),result.get("cagr"),result.get("reason"),flush=True)
    fails=[];marginals={}
    for tier in TIERS:
        for order in ORDERS:
            group={x["book"]:x for x in cells if x["tier"]==tier and x["order"]==order}
            label=tier+"/"+order
            if not all(x["passed"] for x in group.values()):
                fails.append(label+":physical");continue
            full=group["VY_full"]
            marginals[label]={slot:full["log_growth"]-group[other]["log_growth"]
                              for slot,other in (("Opportunity","VY_minus_opportunity"),
                                                 ("Relative_Value","VY_minus_RV"),
                                                 ("Stress_Recovery","VY_minus_stress"))}
            if tier in ("base","severe"):
                if full["cagr"]<=(.80 if tier=="base" else .60):fails.append(label+":cagr")
                if tier=="severe" and full["max_dd"]<=-.45:fails.append(label+":drawdown")
                if tier=="severe" and any(x<=0 for x in full["annual_returns"].values()):
                    fails.append(label+":negative_annual")
                for slot,val in marginals[label].items():
                    if val<=.02:fails.append(label+":"+slot+":marginal")
    receipt={"architecture":"VY","source":"Clean-4 2022-12 warmup + 2023-25 EXPOSED TRAINING",
             "preregistration":"vy_cross_sectional_spread_prereg_20261102.md",
             "cells":cells,"marginals":marginals,"failures":fails,
             "decision":"REJECT_VY_EXPOSED_TRAINING" if fails else "PASS_VY_EXPOSED_TRAINING_ONLY_NOT_VALIDATED",
             "independent_physical_audit_pending":True,"2026_accessed":False,
             "holdout_accessed":False,"benchmarks_accessed":False,
             "account_costs_authenticated":False,"exact_exchange_marks_authenticated":False,
             "paper_live_authorized":False}
    (out/"vy_exposed_physical.json").write_text(json.dumps(receipt,indent=2,sort_keys=True,allow_nan=False)+"\n")
    if frozen_ledger:
        with (out/"vy_base_full_hourly_ledger.csv").open("w",newline="") as handle:
            writer=csv.writer(handle,lineterminator="\n");writer.writerow(HEADER)
            for row in frozen_ledger:
                writer.writerow([json.dumps(v.tolist(),separators=(",",":")) if isinstance(v,np.ndarray)
                                 else format(v,".16g") if isinstance(v,float) else v for v in row])
    print("VY_EXPOSED_DECISION",receipt["decision"],len(fails),flush=True)
    return receipt

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in ("old-root","old-envelope","new-root","corrected-root","out-dir"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    run(get_data(a),a.out_dir)
