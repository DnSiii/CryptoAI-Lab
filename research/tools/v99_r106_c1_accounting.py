"""C1 transparent preliminary accounting; hourly PF is NOT trade PF."""
import math,csv,hashlib
from pathlib import Path
from research.tools import v99_r106_c1_core as c

def summary(hourly):
    if not hourly:raise ValueError("empty_train")
    ret=[row["net"] for row in hourly]
    eq=peak=1.;dd=0.
    for r in ret:
        if not math.isfinite(r) or r<=-1:raise ValueError("bad_return")
        eq*=1+r;peak=max(peak,eq);dd=min(dd,eq/peak-1)
    folds=[]
    for k in range(5):
        q=1.
        for r in ret[k*len(ret)//5:(k+1)*len(ret)//5]:q*=1+r
        folds.append(q-1)
    days=[];day=None;daily=1.
    for row in hourly:
        d=row["time"].date()
        if day is not None and d!=day:
            days.append(daily-1);daily=1.
        day=d;daily*=1+row["net"]
    days.append(daily-1)
    best=max(range(len(days)),key=days.__getitem__)
    no_best=1.
    for j,r in enumerate(days):
        if j!=best:no_best*=1+r
    gains=sum(max(0.,r) for r in ret)
    losses=-sum(min(0.,r) for r in ret)
    matrix={}
    for d in ("BULL","BEAR","SIDEWAYS"):
        for v in ("HIGH_VOLATILITY","LOW_VOLATILITY"):
            state=d+"__"+v
            rows=[x for x in hourly if x["regime"]==state]
            q=1.
            for x in rows:q*=1+x["net"]
            matrix[state]={"hours":len(rows),"roi":q-1,
                           "active_hours":sum(x["active"] for x in rows),
                           "positive_hours":sum(x["net"]>0 for x in rows),
                           "worst_hour":min((x["net"] for x in rows),default=None)}
    return {"roi":eq-1,"max_drawdown":dd,"worst_day":min(days),
            "hourly_profit_factor":gains/losses if losses>0 else None,
            "fold_returns":folds,"positive_folds":sum(x>0 for x in folds),
            "remove_best_day_roi":no_best-1,"hours":len(ret),
            "active_hours":sum(x["active"] for x in hourly),
            "turnover":sum(x["turnover"] for x in hourly),
            "modeled_transaction_cost_sum":sum(x["fee"] for x in hourly),
            "regime_matrix":matrix}

def benchmark(b,e,indices,cost,weights):
    # Same-period fixed-exposure proxy, no authenticated execution.
    q=1.
    for j,i in enumerate(indices):
        rb=b[i+1][1]/b[i][1]-1
        re=e[i+1][1]/e[i][1]-1
        q*=1+weights[0]*rb+weights[1]*re-(cost*sum(weights) if j==0 else 0)
    return q-1

def simulate(b,e,cost,journal_path=None):
    if cost not in (c.SEVERE,c.SUPERSEVERE):raise ValueError("unfrozen_cost")
    if len(b)!=len(e) or any(x[0]!=y[0] for x,y in zip(b,e)):
        raise ValueError("unaligned_train_hours")
    if b[-1][0]>=c.END:raise ValueError("train_boundary")
    fb=c.features(b);fe=c.features(e)
    indices=[i for i in fb if b[i][0]>=c.START]
    if not indices:raise ValueError("no_train_evaluation")
    eq=peak=1.;lock=0;armed=True;desired=(0.,0.);prior=(0.,0.);hourly=[]
    for i in indices:
        t=b[i][0]
        if t.hour==0:
            desired=(c.signal(fb[i]),c.signal(fe[i]))
        state=c.regime(fb[i])
        weights,lock,armed=c.governor(desired,state,eq/peak-1,lock,armed)
        turnover=sum(abs(x-y) for x,y in zip(weights,prior))
        fee=cost*turnover
        rb=b[i+1][1]/b[i][1]-1
        re=e[i+1][1]/e[i][1]-1
        net=weights[0]*rb+weights[1]*re-fee
        if not math.isfinite(net) or net<=-1:raise ValueError("bad_net_return")
        eq*=1+net;peak=max(eq,peak)
        hourly.append({"time":t,"net":net,"fee":fee,"turnover":turnover,
                       "regime":state,"active":int(any(abs(x)>0 for x in weights)),
                       "btc_weight":weights[0],"eth_weight":weights[1],
                       "equity":eq,"peak":peak,"lock_remaining":lock})
        prior=weights
    report=summary(hourly)
    report["cost_per_side"]=cost
    if journal_path is not None:
        path=Path(journal_path);path.parent.mkdir(parents=True,exist_ok=True)
        fields=("time","regime","btc_weight","eth_weight","turnover","fee",
                "net","equity","peak","lock_remaining")
        with path.open("w",newline="",encoding="utf-8") as file:
            writer=csv.writer(file);writer.writerow(fields)
            for row in hourly:
                writer.writerow([row[k].isoformat() if k=="time" else row[k] for k in fields])
        report["simulated_journal_sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
        report["simulated_journal_rows"]=len(hourly)
        report["simulated_journal_type"]="ASSUMED_COST_PRE_FUNDING_NOT_EXCHANGE_FILLS"
    report["benchmark_proxies"]={
        "btc_100pct":benchmark(b,e,indices,cost,(1.,0.)),
        "btc_eth_equal":benchmark(b,e,indices,cost,(.5,.5))}
    return report
