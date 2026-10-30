"""Independent S1 per-hour market/decision/fee/cash/unit oracle.
Does NOT import strategy simulate/features/rebalance or accept self-declared PnL.
Read-only original OKX TRAIN; NEVER opens validation, final holdout or orders.
"""
import hashlib
import json
import math
import statistics
import sys
from datetime import datetime,timezone
from pathlib import Path

from research.verification.independent_d1_native_train_receipts import verify

START=int(datetime(2021,12,9,tzinfo=timezone.utc).timestamp()*1000)
END=int(datetime(2023,10,1,tzinfo=timezone.utc).timestamp()*1000)
HOUR=3600000
N=(END-START)//HOUR
EDGES=[int(datetime.fromisoformat(x).replace(tzinfo=timezone.utc).timestamp()*1000) for x in (
    "2021-12-09T00:00:00","2022-04-20T04:00:00","2022-08-30T09:00:00",
    "2023-01-09T14:00:00","2023-05-21T19:00:00","2023-10-01T00:00:00")]
RATES={"severe_model_only":.0025,"supersevere_model_only":.006}
ASSETS=("BTC","ETH")

def load(root):
    root=Path(root)
    v=verify(root)
    if v["status"]!="INDEPENDENT_FOUR_LEG_TRAIN_SOURCE_COMPLETE_NO_ECONOMICS":
        raise ValueError("S1_INDEPENDENT_ORIGINAL_SOURCE_VETO")
    prices={}
    for a in ASSETS:
        raw=json.loads((root/(a+"-USDT")/"train_opens.json").read_bytes())
        if len(raw)!=N:raise ValueError("S1_ORACLE_LENGTH")
        if any(type(x["ts"])!=int or x["ts"]!=START+i*HOUR for i,x in enumerate(raw)):
            raise ValueError("S1_ORACLE_SEALED_OR_MISSING_HOUR")
        p=[float(x["open"]) for x in raw]
        if any(not math.isfinite(x) or x<=0 for x in p):raise ValueError("S1_ORACLE_BAD_PRICE")
        prices[a]=p
    return prices

def signal(p,t):
    if t<720:return (None,None)
    b,e=p["BTC"],p["ETH"]
    spread=(b[t-1]/b[t-73]-1)-(e[t-1]/e[t-73]-1)
    trend=b[t-1]/b[t-720]-1
    def vol(q):
        diffs=[math.log(q[j]/q[j-1]) for j in range(t-72,t)]
        return statistics.pstdev(diffs)*math.sqrt(24)
    vb,ve=vol(b),vol(e)
    regime=("bull" if trend>.05 else "bear" if trend<-.05 else "sideways")+(
        "_high" if vb>=.04 else "_low")
    wanted="ETH" if spread>=.08 else "BTC" if spread<=-.08 else None
    if trend<-.25 or max(vb,ve)>.08:wanted=None
    return wanted,regime

def replay(p,fee):
    cash=1.
    units={"BTC":0.,"ETH":0.}
    previous=1.
    high=1.
    dd=0.
    fold_logs=[0.]*5
    regime_logs={x+"_"+y:[0,0.] for x in ("bull","bear","sideways") for y in ("low","high")}
    day_logs={}
    trade_count=0; volume_total=0.; cost_total=0.
    decisions=[]
    h=hashlib.sha256()
    for t in range(N):
        px={a:p[a][t] for a in ASSETS}
        nav_before=cash+sum(units[a]*px[a] for a in ASSETS)
        decision,regime=signal(p,t)
        if t>=720 and t%24==0:
            weights={a:(.65 if decision==a else 0.) for a in ASSETS}
            original={a:units[a]*px[a] for a in ASSETS}
            # Alternative fixed-point iteration, not production bisection.
            after=nav_before
            for _ in range(80):
                after=nav_before-fee*sum(abs(weights[a]*after-original[a]) for a in ASSETS)
            new_units={a:weights[a]*after/px[a] for a in ASSETS}
            turn=sum(abs(new_units[a]*px[a]-original[a]) for a in ASSETS)
            paid=fee*turn
            cash-=sum((new_units[a]-units[a])*px[a] for a in ASSETS)+paid
            units=new_units
            if turn>1e-10:trade_count+=1
            volume_total+=turn;cost_total+=paid
            decisions.append((t,decision))
        # Independent terminal spot liquidation, preserving full fee accounting.
        if t==N-1 and any(units.values()):
            before={a:units[a]*px[a] for a in ASSETS}
            turn=sum(before.values())
            paid=fee*turn
            cash+=turn-paid
            units={a:0. for a in ASSETS}
            trade_count+=1
            volume_total+=turn;cost_total+=paid
        nav=cash+sum(units[a]*px[a] for a in ASSETS)
        if cash < -1e-8 or min(units.values()) < -1e-12 or nav<=0 or not math.isfinite(nav):
            raise ValueError("S1_ORACLE_ACCOUNT_NOT_SELF_FINANCING")
        lr=math.log(nav/previous)
        timestamp=START+t*HOUR
        fold=next((i for i,(a,b) in enumerate(zip(EDGES,EDGES[1:])) if a<=timestamp<b),None)
        if fold is None:raise ValueError("S1_ORACLE_SEALED_HOUR")
        fold_logs[fold]+=lr
        if regime is not None:
            regime_logs[regime][0]+=1
            regime_logs[regime][1]+=lr
            day_logs[t//24]=day_logs.get(t//24,0.)+lr
        high=max(high,nav);dd=min(dd,nav/high-1)
        h.update(f"{t},{nav:.12f},{cash:.12f},{units['BTC']:.12f},{units['ETH']:.12f}\n".encode())
        previous=nav
    total=math.exp(sum(fold_logs))-1
    return dict(roi=total,fold_rois=[math.exp(x)-1 for x in fold_logs],
        worst_fold=min(math.exp(x)-1 for x in fold_logs),
        positive_folds=sum(x>0 for x in fold_logs),
        max_drawdown=dd,trades=trade_count,turnover=volume_total,
        modeled_cost=cost_total,final_nav=previous,decision_count=len(decisions),
        decisions_sha256=hashlib.sha256(json.dumps(decisions,separators=(",",":")).encode()).hexdigest(),
        hourly_nav_sha256=h.hexdigest(),
        regimes={k:dict(hours=v[0],roi=math.exp(v[1])-1) for k,v in regime_logs.items()},
        best_day_removed_roi=math.exp(sum(fold_logs)-max(day_logs.values(),default=0.))-1)

def verify_report(root,report_file):
    data=json.loads(Path(report_file).read_text())
    if data["schema"]!="V99_R106_S1_ONE_SHOT_SPOT_TRAIN_V1" or data["original_train_hours"]!=N:
        raise ValueError("S1_ORACLE_REPORT_SCOPE")
    if any(data.get(k) is not False for k in (
        "historical_native_fills_authenticated","historical_native_fee_tier_authenticated",
        "promotion_authorized","validation_opened","final_holdout_opened",
        "orders_enabled","paper_publication_authorized")):
        raise ValueError("S1_ORACLE_UNAUTHORIZED_PROMOTION")
    p=load(root)
    for scenario,rate in RATES.items():
        independent=replay(p,rate)
        published=data['severe' if scenario=='severe_model_only' else 'supersevere']
        for key,value in independent.items():
            other=published[key]
            if isinstance(value,(float,int)) and type(value)!=bool:
                if not math.isclose(value,other,rel_tol=1e-9,abs_tol=1e-9):
                    raise ValueError(f"S1_ORACLE_ACCOUNT_MISMATCH_{scenario}_{key}")
            elif isinstance(value,list):
                if len(value)!=len(other) or any(not math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-9) for a,b in zip(value,other)):
                    raise ValueError(f"S1_ORACLE_FOLD_MISMATCH_{scenario}_{key}")
            elif isinstance(value,dict):
                if set(value)!=set(other):raise ValueError("S1_ORACLE_REGIME_KEYS")
                for regime,stats in value.items():
                    if stats["hours"]!=other[regime]["hours"] or not math.isclose(stats["roi"],other[regime]["roi"],rel_tol=1e-9,abs_tol=1e-9):
                        raise ValueError("S1_ORACLE_REGIME_PNL")
            elif value!=other:
                raise ValueError(f"S1_ORACLE_TRACE_MISMATCH_{scenario}_{key}")
    if data["severe"]["decisions_sha256"]!=data["supersevere"]["decisions_sha256"]:
        raise ValueError("S1_ORACLE_SCENARIO_SIGNAL_DIVERGENCE")
    print(json.dumps({"status":"INDEPENDENT_ORIGINAL_PRICE_AND_PER_HOUR_ACCOUNT_REPLAY_PASS",
        "train_hours":N,"cost_scenarios":2,
        "model_status":data["status"],"promotion_authorized":False}))
    return True

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: python -m research.verification.independent_v99_r106_s1_spot_train PRICE_ROOT REPORT_JSON")
    verify_report(sys.argv[1],sys.argv[2])
