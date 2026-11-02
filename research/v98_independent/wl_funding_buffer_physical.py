#!/usr/bin/env python3
"""WL full exposed-training physical ledger with hourly funding-buffer governor.

Not an execution venue, not validated, and never paper/live authorization.
"""
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path
import numpy as np
from v98_2025_full_training_source_bridge import load
from vy_cross_sectional_spread import HOURS,source_gate
from wl_funding_buffer_compound import targets,books_from_decisions,incidence,BOOKS,SLOTS,synthetic_test
TIERS={"base":.001,"severe":.002,"supersevere":.0035}
ORDERS=("carried_before_fill","new_after_fill")
HEADER=("hour","cash_before","cash_after","gap","funding","fees",
        "intrahour","trade_notional","governor_trim","qty","open","close",
        "rate","lower","upper")
INITIAL=10000.
def simulate(d,decisions,tier,order,record=False):
    if tier not in TIERS or order not in ORDERS:raise ValueError("WL_TIER_ORDER")
    q=np.zeros(4,dtype=float);cash=INITIAL;peak=INITIAL;dd=0.
    funding_sum=fees=turnover=0.;trades=0;trims=0
    daily=[];changes=[];year_ends={};ledger=[]
    gross_contribution=np.zeros(4);position_hours=np.zeros(4,dtype=int)
    min_adverse=INITIAL;max_gross=0.
    def failure(reason,t):
        return {"passed":False,"reason":reason,"hour":t,"tier":tier,
                "order":order,"governor_trims":trims},ledger
    for t in range(HOURS):
        before=cash;op=np.asarray(d["o"][t]);cl=np.asarray(d["c"][t])
        prev=np.asarray(d["c"][t-1]) if t else op
        gap=float(np.dot(q,op-prev));cash+=gap
        funding=0.;fee=0.;notional=0.;trim=False
        def settle():
            marks=np.where(q*d["rate"][t]>0,d["mark_upper"][t],d["mark_lower"][t])
            return -float(np.dot(q,d["rate"][t]*marks)) if t%8==0 else 0.
        if order=="carried_before_fill":
            funding=settle();cash+=funding;funding_sum+=funding
            if cash<=0 or float(np.dot(np.abs(q),op))>cash*(1+1e-8):
                return failure("PRE_FILL_FUNDING_MARGIN_BREACH",t)
        if not math.isfinite(cash) or cash<=0:return failure("INSOLVENT_PRETRADE",t)
        gross=float(np.dot(np.abs(q),op))
        signal=(t-1 in decisions)
        terminal=(t==HOURS-1)
        if terminal or signal:
            w=np.zeros(4) if terminal else np.asarray(decisions[t-1],dtype=float)
            if not np.isfinite(w).all() or float(np.abs(w).sum())>.70+1e-9:
                return failure("GROSS_TARGET",t)
            desired=w*cash/op
        elif gross>0 and (gross/cash>.75 or (cash-gross)/cash<.22):
            desired=q*(.65*cash/gross)
            trim=True
        else:
            desired=q.copy()
        delta=desired-q
        if np.any((np.abs(delta)>1e-12)&(np.asarray(d["q"][t])<=0)):
            return failure("ZERO_VOLUME_FILL",t)
        notional=float(np.dot(np.abs(delta),op))
        fee=TIERS[tier]*notional
        cash-=fee;fees+=fee;turnover+=notional
        trades+=int(np.sum(np.abs(delta)>1e-12))
        if trim:trims+=1
        q=desired
        if order=="new_after_fill":
            funding=settle();cash+=funding;funding_sum+=funding
        gross=float(np.dot(np.abs(q),op))
        if not math.isfinite(cash) or cash<=0 or gross>cash*(1+1e-8) or cash<.10*gross-1e-7:
            return failure("CASH_OR_HIDDEN_LEVERAGE",t)
        adverse_price=np.where(q>=0,d["l"][t],d["h"][t])
        adverse=cash+float(np.dot(q,adverse_price-op))
        min_adverse=min(min_adverse,adverse)
        if adverse<=.10*gross:return failure("INTRAHOUR_ADVERSE_MARGIN",t)
        intrahour=float(np.dot(q,cl-op));cash+=intrahour
        if not math.isfinite(cash) or cash<=0:return failure("CLOSE_INSOLVENCY",t)
        close_gross=float(np.dot(np.abs(q),cl))
        if close_gross>cash*(1+1e-8):return failure("CLOSE_HIDDEN_LEVERAGE",t)
        max_gross=max(max_gross,close_gross/cash)
        peak=max(peak,cash);dd=min(dd,cash/peak-1.)
        changes.append(cash-before)
        gross_contribution+=np.abs(q*cl);position_hours+=(np.abs(q)>1e-12)
        if t%24==23 and t>=767:daily.append(cash)
        if t in (743,9503,18287,27047):year_ends[t]=cash
        if record:
            ledger.append((t,before,cash,gap,funding,fee,intrahour,notional,int(trim),
                           q.copy(),op.copy(),cl.copy(),d["rate"][t].copy(),
                           d["mark_lower"][t].copy(),d["mark_upper"][t].copy()))
    if np.any(np.abs(q)>1e-10):return failure("UNCLOSED",HOURS)
    x=np.asarray(changes[744:]);pos=x[x>1e-10];neg=-x[x< -1e-10]
    days=np.asarray(daily);dayret=np.diff(np.r_[year_ends[743],days])/np.r_[year_ends[743],days[:-1]]
    annual={"2023":year_ends[9503]/year_ends[743]-1.,
            "2024":year_ends[18287]/year_ends[9503]-1.,
            "2025":year_ends[27047]/year_ends[18287]-1.}
    final=float(cash)
    return {"passed":True,"tier":tier,"order":order,"final_equity":final,
            "cagr":(final/INITIAL)**(1./3.)-1.,
            "log_growth":math.log(final/INITIAL),
            "compounded_return":final/INITIAL-1.,"annual_returns":annual,
            "max_dd":dd,"min_adverse_equity":min_adverse,
            "max_gross_fraction":max_gross,"governor_trims":trims,
            "signed_funding":funding_sum,"fees_spread_impact":fees,
            "turnover":turnover,"trades":trades,"positive_days":int(np.sum(dayret>0)),
            "days":len(dayret),"worst_day":float(np.min(dayret)),
            "best_day":float(np.max(dayret)),
            "hourly_net_pf":float(np.sum(pos)/np.sum(neg)) if len(neg) else None,
            "hourly_net_payoff":float(np.mean(pos)/np.mean(neg)) if len(pos) and len(neg) else None,
            "hourly_net_win_rate":float(len(pos)/(len(pos)+len(neg))) if len(pos)+len(neg) else 0.,
            "gross_concentration":(gross_contribution/max(gross_contribution.sum(),1.)).tolist(),
            "position_hours":position_hours.tolist(),"trade_level_pf_pending":True,
            "account_costs_authenticated":False,"exact_exchange_marks_authenticated":False},ledger
def run(d,outdir):
    source_gate(d)
    out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    dec=targets(d);b=books_from_decisions(dec);counts=incidence(dec)
    (out/"wl_source.json").write_text(json.dumps({
        "decision":"PASS_WL_SOURCE_GEOMETRY_ONLY_NOT_PNL","decisions":len(dec),
        "sleeve_incidence":counts,"hours":HOURS,"funding_events":int(d["event"].sum()),
        "2026_accessed":False,"holdout_accessed":False},indent=2,sort_keys=True)+"\n")
    cells=[];ledger=None
    for tier in TIERS:
        for order in ORDERS:
            for name,target in b.items():
                keep=tier=="base" and order=="carried_before_fill" and name=="WL_full"
                r,rows=simulate(d,target,tier,order,record=keep)
                r["book"]=name;cells.append(r)
                if keep:ledger=rows
                print("WL_PHYSICAL",tier,order,name,r.get("passed"),r.get("cagr"),
                      r.get("reason"),r.get("hour"),flush=True)
    failures=[];marginals={}
    for tier in TIERS:
        for order in ORDERS:
            group={x["book"]:x for x in cells if x["tier"]==tier and x["order"]==order}
            label=tier+"/"+order
            if not all(x["passed"] for x in group.values()):
                failures.append(label+":physical");continue
            full=group["WL_full"]
            marginals[label]={slot:full["log_growth"]-group[other]["log_growth"]
                for slot,other in (("Opportunity","WL_minus_opportunity"),
                                   ("Relative_Value","WL_minus_RV"),
                                   ("Stress_Recovery","WL_minus_stress"))}
            if tier in ("base","severe"):
                if full["cagr"]<=(.80 if tier=="base" else .60):failures.append(label+":cagr")
                if tier=="severe" and full["max_dd"]<=-.45:failures.append(label+":dd")
                if tier=="severe" and any(x<=0 for x in full["annual_returns"].values()):
                    failures.append(label+":annual")
                for slot,value in marginals[label].items():
                    if value<=0:failures.append(label+":"+slot+":marginal")
    receipt={"architecture":"WL","cells":cells,"sleeve_incidence":counts,
             "marginals":marginals,"failures":failures,
             "decision":"REJECT_WL_EXPOSED_TRAINING" if failures else "PASS_WL_EXPOSED_TRAINING_ONLY_NOT_VALIDATED",
             "independent_ledger_audit_pending":True,"account_costs_authenticated":False,
             "exact_exchange_marks_authenticated":False,"2026_accessed":False,
             "holdout_accessed":False,"benchmarks_accessed":False,
             "paper_live_authorized":False}
    (out/"wl_exposed_physical.json").write_text(json.dumps(receipt,indent=2,sort_keys=True,allow_nan=False)+"\n")
    if ledger:
        with (out/"wl_base_full_hourly_ledger.csv").open("w",newline="") as handle:
            w=csv.writer(handle,lineterminator="\n");w.writerow(HEADER)
            for row in ledger:
                w.writerow([json.dumps(v.tolist(),separators=(",",":")) if isinstance(v,np.ndarray)
                            else format(v,".16g") if isinstance(v,float) else v for v in row])
    print("WL_DECISION",receipt["decision"],"failed_gates",len(failures),flush=True)
    return receipt
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    for name in ("old-root","old-envelope","new-root","corrected-root","out-dir"):
        p.add_argument("--"+name)
    a=p.parse_args()
    if a.self_test:
        print(json.dumps(synthetic_test(),sort_keys=True))
    else:
        for k in ("old_root","old_envelope","new_root","corrected_root","out_dir"):
            if not getattr(a,k):p.error("--"+k.replace("_","-")+" required")
        run(load(a.old_root,a.old_envelope,a.new_root,a.corrected_root),a.out_dir)
