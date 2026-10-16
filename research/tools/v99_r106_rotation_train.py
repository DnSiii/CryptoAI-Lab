"""One precommitted cross-sectional weekly momentum long/cash test. TRAIN-only."""
import csv,datetime,hashlib,json,math
from pathlib import Path
UTC=datetime.timezone.utc
END=datetime.datetime(2024,1,18,tzinfo=UTC)
START=datetime.datetime(2021,12,1,tzinfo=UTC)
N=720
SEVERE=.0007
SUPERSEVERE=.0014
MONDAY=0

def parse_utc(s):
    if not isinstance(s,str):raise ValueError("timestamp_missing")
    t=datetime.datetime.fromisoformat(s.replace("Z","+00:00"))
    if t.tzinfo is None or t.utcoffset()!=datetime.timedelta(0):raise ValueError("explicit_utc_required")
    return t.astimezone(UTC)

def load_train(path):
    vals=[];sha=hashlib.sha256();prev=None
    with open(path,encoding="utf-8",newline="") as f:
        rd=csv.DictReader(f)
        cols=("timestamp","open","high","low","close","volume")
        if rd.fieldnames is None or any(n not in rd.fieldnames for n in cols):
            raise ValueError("required_canonical_ohlcv_fields")
        for row in rd:
            t=parse_utc(row["timestamp"])
            if t>=END:break  # Do not even parse future OHLCV
            if prev is not None and t-prev!=datetime.timedelta(hours=1):raise ValueError("hourly_gap_or_repeat")
            o,h,l,c,v=[float(row[n]) for n in cols[1:]]
            if (not all(math.isfinite(x) for x in (o,h,l,c,v))
                 or min(o,h,l,c)<=0 or v<0 or h<max(o,c) or l>min(o,c) or l>h):
                raise ValueError("invalid_train_ohlcv")
            vals.append((t,o,h,l,c,v))
            sha.update(("|".join(row[n] for n in cols)+"\n").encode())
            prev=t
    if len(vals)<N+240:raise ValueError("insufficient_train_data")
    return vals,sha.hexdigest()

def signals(b,e):
    if len(b)!=len(e) or [x[0] for x in b]!=[x[0] for x in e]:
        raise ValueError("unaligned_market_hours")
    if b[-1][0]>=END or e[-1][0]>=END:raise ValueError("TRAIN_only")
    target=(0.,0.);out=[]
    for i in range(N+1,len(b)-1):
        t=b[i][0]
        if t<START:continue
        if t.weekday()==MONDAY and t.hour==0:
            # At time t, last close is t-1; baseline close is t-721.
            rb=b[i-1][4]/b[i-N-1][4]-1.
            re=e[i-1][4]/e[i-N-1][4]-1.
            if rb<=0. or max(rb,re)<=0.:
                target=(0.,0.)
            elif rb>=re:
                target=(1.,0.)
            else:
                target=(0.,1.)
        if sum(abs(x) for x in target)>1.+1e-12 or min(target)<0:
            raise ValueError("long_only_no_leverage_guard")
        out.append((i,t,*target))
    if not out:raise ValueError("empty_train")
    return out

def measure(b,e,series,cost):
    if cost not in (SEVERE,SUPERSEVERE):raise ValueError("nonfrozen_cost")
    returns=[];weights=[];turnover=0.;active=0
    pb=pe=0.
    for i,t,wb,we in series:
        br=b[i+1][1]/b[i][1]-1.
        er=e[i+1][1]/e[i][1]-1.
        traded=abs(wb-pb)+abs(we-pe)
        r=wb*br+we*er-cost*traded
        if not math.isfinite(r) or r<=-1:raise ValueError("invalid_portfolio_hour_return")
        returns.append(r);weights.append((wb,we));turnover+=traded
        active+=int(wb+we>0)
        pb,pe=wb,we
    equity=peak=1.;maxdd=0.
    for r in returns:
        equity*=1+r;peak=max(equity,peak);maxdd=min(maxdd,equity/peak-1)
    folds=[]
    for k in range(5):
        eq=1.
        for r in returns[k*len(returns)//5:(k+1)*len(returns)//5]:
            eq*=1+r
        folds.append(eq-1)
    best=max(range(len(returns)),key=returns.__getitem__)
    without=1.
    for i,r in enumerate(returns):
        if i!=best:without*=1+r
    gains=sum(r for r in returns if r>0)
    losses=-sum(r for r in returns if r<0)
    return {"return":equity-1,"max_drawdown":maxdd,"fold_returns":folds,
            "healthy_folds":sum(x>0 for x in folds),
            "remove_best_hour_return":without-1,
            "profit_factor":gains/losses if losses else None,
            "active_hours":active,"hours":len(returns),
            "worst_hour":min(returns),"total_turnover":turnover,
            "cost_per_side":cost}

def evaluate(b,e):
    selected=signals(b,e)
    severe=measure(b,e,selected,SEVERE)
    supersevere=measure(b,e,selected,SUPERSEVERE)
    static_btc=[(i,t,1.,0.) for i,t,*_ in selected]
    static_equal=[(i,t,.5,.5) for i,t,*_ in selected]
    benchmarks={
        "btc_100pct":measure(b,e,static_btc,SEVERE),
        "btc_eth_equal":measure(b,e,static_equal,SEVERE),
    }
    # Strictly frozen gate; no optimizer; no comparison to final holdout.
    passed=(severe["return"]>0 and supersevere["return"]>0
        and severe["healthy_folds"]>=4 and supersevere["healthy_folds"]>=3
        and severe["remove_best_hour_return"]>0
        and supersevere["remove_best_hour_return"]>0
        and (severe["profit_factor"] or 0)>1 and (supersevere["profit_factor"] or 0)>1
        and severe["active_hours"]>=720 and supersevere["max_drawdown"]>=-.35
        and all(severe["return"]>v["return"] for v in benchmarks.values()))
    return {
      "study":"V99 R106 fixed weekly two-asset long/cash strength rotation",
      "status":"TRAIN_RESEARCH_PRELIMINARY_PASS_NOT_PROMOTED" if passed else "TRAIN_REJECT_PERMANENT_NO_RETUNE",
      "rules":{"momentum_hours":N,"weekly_utc_weekday":MONDAY,"weekly_utc_hour":0,
               "no_short":True,"portfolio_max_gross":1.0,"end_exclusive":END.isoformat()},
      "severe":severe,"supersevere":supersevere,"benchmark_severe":benchmarks,
      "passed_all_preregistered_pre_funding_gates":passed,
      "holdout_market_values_parsed":False,"final_holdout_accessed":False,
      "native_fee_tier_authenticated":False,"settled_funding_authenticated":False,
      "actual_fills_authenticated":False,"promotion_authorized":False,
      "paper_publication_authorized":False,"real_orders_enabled":False,
      "economic_trials":1}

def main(btc="data/canonical/BTCUSDT_1h.csv",eth="data/canonical/ETHUSDT_1h.csv",
         output="reports/candidate_v99_r106_rotation_train.json"):
    b,bh=load_train(btc);e,eh=load_train(eth)
    result=evaluate(b,e)
    result["btc_train_sha256"]=bh;result["eth_train_sha256"]=eh
    p=Path(output);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"status":result["status"],"severe_roi":result["severe"]["return"],
         "supersevere_roi":result["supersevere"]["return"],
         "severe_folds":result["severe"]["healthy_folds"],
         "supersevere_folds":result["supersevere"]["healthy_folds"],
         "benchmark_btc_roi":result["benchmark_severe"]["btc_100pct"]["return"],
         "benchmark_equal_roi":result["benchmark_severe"]["btc_eth_equal"]["return"],
         "promotion_authorized":False},sort_keys=True))
    return result
if __name__=="__main__":main()
