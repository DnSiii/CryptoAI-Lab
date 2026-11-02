#!/usr/bin/env python3
"""V98 WC: full 2023-25 exposed-training directional USD-M physical cash ledger.
Native funding with conservative envelope; costs illustrative, never account-authenticated.
"""
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path
import numpy as np
from v98_2025_full_training_source_bridge import load
from vy_cross_sectional_spread import HOURS,CLOCK,source_gate
from wc_structural_beta import targets,books,incidence,SLOTS
TIERS={"base":.0010,"severe":.0020,"supersevere":.0035}
ORDERS=("carried_before_fill","new_after_fill")
INITIAL=10000.
HEADER=("hour","cash_before","cash_after","equity_before","equity_after",
        "gap_pnl","intrahour_pnl","funding","cost","trade_notional",
        "qty","open","close","rate","lower","upper","target_weight")

def simulate(d,target,tier,order,record=False):
    if tier not in TIERS or order not in ORDERS:raise ValueError("WC_TIER_ORDER")
    source_gate(d)
    q=np.zeros(4);cash=INITIAL;peak=INITIAL;dd=0.;min_adverse=INITIAL
    funding_sum=fees=turnover=0.;funding_count=0;trade_count=0
    changes=[];daily=[];year_ends={};ledger=[]
    max_gross=0.;gross_contribution=np.zeros(4);pos_hours=np.zeros(4,int)
    price=np.asarray(d["c"],float)
    def fund(t):
        nonlocal cash,funding_sum,funding_count
        if t%8:return 0.
        funding_count+=4
        marks=np.where(q*d["rate"][t]>0,d["mark_upper"][t],d["mark_lower"][t])
        val=-float(np.dot(q,d["rate"][t]*marks))
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
            if not np.isfinite(w).all() or np.abs(w).sum()>.90+1e-8:
                return fail("GROSS_TARGET",t)
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
        grossclose=float(np.dot(np.abs(q),cl))
        if grossclose>cash*(1+1e-8):return fail("CLOSE_HIDDEN_LEVERAGE",t)
        max_gross=max(max_gross,grossclose/cash)
        peak=max(peak,cash);dd=min(dd,cash/peak-1.)
        changes.append(cash-before)
        gross_contribution+=np.abs(q*cl);pos_hours+=(np.abs(q)>1e-12)
        if t%24==23:daily.append(cash)
        if t in (743,9503,18287,27047):year_ends[t]=cash
        if record:
            ledger.append((t,before,cash,before,cash,gap,intrahour,f,cost,traded,
                           q.copy(),op.copy(),cl.copy(),d["rate"][t].copy(),
                           d["mark_lower"][t].copy(),d["mark_upper"][t].copy(),w.copy()))
    if np.any(np.abs(q)>1e-10) or funding_count!=13524:
        return fail("UNCLOSED_OR_FUNDING_COUNT",HOURS)
    x=np.asarray(changes);pos=x[x>1e-10];neg=-x[x< -1e-10]
    days=np.asarray(daily)
    dayret=np.diff(np.r_[INITIAL,days])/np.r_[INITIAL,days[:-1]]
    annual={"2023":year_ends[9503]/year_ends[743]-1.,
            "2024":year_ends[18287]/year_ends[9503]-1.,
            "2025":year_ends[27047]/year_ends[18287]-1.}
    final=float(cash)
    return {"passed":True,"tier":tier,"order":order,"final_equity":final,
            "compounded_return":final/INITIAL-1.,"cagr":(final/INITIAL)**(1./3.)-1.,
            "log_growth":math.log(final/INITIAL),"annual_returns":annual,
            "max_dd":dd,"min_adverse_equity":min_adverse,"max_gross_fraction":max_gross,
            "fees_spread_impact":fees,"signed_funding":funding_sum,"turnover":turnover,
            "trades":trade_count,"funding_events_checked":funding_count,
            "positive_days":int((dayret>0).sum()),"days":len(dayret),
            "worst_day":float(dayret.min()),"best_day":float(dayret.max()),
            "hourly_net_pf":float(pos.sum()/neg.sum()) if len(neg) else None,
            "hourly_net_payoff":float(pos.mean()/neg.mean()) if len(pos) and len(neg) else None,
            "hourly_net_win_rate":float(len(pos)/(len(pos)+len(neg))) if len(pos)+len(neg) else 0.,
            "position_hours":pos_hours.tolist(),
            "gross_concentration":(gross_contribution/max(gross_contribution.sum(),1.)).tolist(),
            "trade_level_pf_pending_independent_lot_audit":True,
            "account_costs_authenticated":False,"exact_exchange_marks_authenticated":False},ledger

def run(d,outdir):
    out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    dec=targets(d);counts=incidence(dec);threshold=int(.10*len(CLOCK))
    failures=[k for k in SLOTS[1:] if counts[k]<threshold]
    source={"decision":"REJECT_WC_PRE_PNL_INCIDENCE" if failures else "PASS_WC_SOURCE_NOT_PNL",
            "decisions":len(CLOCK),"sleeve_incidence":counts,"min_incidence":threshold,
            "hours":HOURS,"native_funding_events":int(d["event"].sum()),
            "pnl_computed":False,"2026_accessed":False,"holdout_accessed":False}
    (out/"wc_source.json").write_text(json.dumps(source,indent=2,sort_keys=True)+"\n")
    print("WC_SOURCE",json.dumps(source,sort_keys=True),flush=True)
    if failures:
        print("WC_PRE_PNL_REJECTED",failures,flush=True)
        return {"decision":"REJECT_WC_PRE_PNL_INCIDENCE","failures":failures}
    b=books(d);cells=[];ledger=None
    for tier in TIERS:
        for order in ORDERS:
            for name,tgt in b.items():
                keep=tier=="base" and order==ORDERS[0] and name=="WC_full"
                r,rows=simulate(d,tgt,tier,order,record=keep)
                r["book"]=name;cells.append(r)
                if keep:ledger=rows
                print("WC_PHYSICAL",tier,order,name,r.get("passed"),r.get("cagr"),r.get("reason"),flush=True)
    failures=[];marginals={}
    for tier in TIERS:
        for order in ORDERS:
            group={x["book"]:x for x in cells if x["tier"]==tier and x["order"]==order}
            label=tier+"/"+order
            if not all(x["passed"] for x in group.values()):
                failures.append(label+":physical");continue
            full=group["WC_full"]
            marginals[label]={slot:full["log_growth"]-group[other]["log_growth"]
                for slot,other in (("Opportunity","WC_minus_opportunity"),
                                   ("Relative_Value","WC_minus_RV"),
                                   ("Stress_Recovery","WC_minus_stress"))}
            if tier in ("base","severe"):
                if full["cagr"]<=(.80 if tier=="base" else .60):failures.append(label+":cagr")
                if tier=="severe" and full["max_dd"]<=-.45:failures.append(label+":dd")
                if tier=="severe" and any(x<=0 for x in full["annual_returns"].values()):
                    failures.append(label+":annual")
                for slot,v in marginals[label].items():
                    if v<=.02:failures.append(label+":"+slot+":marginal")
    receipt={"architecture":"WC","source":source,"cells":cells,"marginals":marginals,
             "failures":failures,"decision":"REJECT_WC_EXPOSED_TRAINING" if failures else "PASS_WC_EXPOSED_TRAINING_ONLY_NOT_VALIDATED",
             "independent_physical_audit_pending":True,"account_costs_authenticated":False,
             "exact_exchange_marks_authenticated":False,"2026_accessed":False,
             "holdout_accessed":False,"benchmarks_accessed":False,"paper_live_authorized":False}
    (out/"wc_exposed_physical.json").write_text(json.dumps(receipt,indent=2,sort_keys=True,allow_nan=False)+"\n")
    if ledger is not None:
        with (out/"wc_base_full_hourly_ledger.csv").open("w",newline="") as handle:
            w=csv.writer(handle,lineterminator="\n");w.writerow(HEADER)
            for row in ledger:
                w.writerow([json.dumps(v.tolist(),separators=(",",":")) if isinstance(v,np.ndarray)
                            else format(v,".16g") if isinstance(v,float) else v for v in row])
    print("WC_EXPOSED_DECISION",receipt["decision"],len(failures),flush=True)
    return receipt

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in ("old-root","old-envelope","new-root","corrected-root","out-dir"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    run(load(a.old_root,a.old_envelope,a.new_root,a.corrected_root),a.out_dir)
