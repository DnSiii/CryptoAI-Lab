"""Preregistered C2 structural-beta + contrarian inventory integrated engine.
TRAIN-only, causal t-1, fixed targets across cost scenarios. NO ORDERS.
"""
import argparse,csv,hashlib,json,math
from datetime import datetime,timedelta,timezone
from pathlib import Path
UTC=timezone.utc
START=datetime(2021,12,1,tzinfo=UTC)
END=datetime(2023,10,1,tzinfo=UTC)
FINAL_HOLDOUT=datetime(2024,1,18,tzinfo=UTC)
SEVERE=0.0007
SUPERSEVERE=0.0014
FIELDS=("timestamp","open","high","low","close","volume")
JOURNAL_FIELDS=("time","regime","btc_weight","eth_weight","turnover","fee","net","equity","peak","cooldown")
SPEC=Path("research/V99_R106_C2_STRUCTURAL_BETA_RELATIVE_INVENTORY_PREREG_20261016.md")

def load_train(path):
    rows=[];h=hashlib.sha256();previous=None
    with open(path,newline="",encoding="utf-8") as f:
        rd=csv.DictReader(f)
        if rd.fieldnames is None or any(k not in rd.fieldnames for k in FIELDS):
            raise ValueError("canonical_fields_missing")
        for row in rd:
            t=datetime.fromisoformat(row["timestamp"].replace("Z","+00:00"))
            if t.tzinfo is None or t.utcoffset()!=timedelta(0):raise ValueError("utc_required")
            if t>=END:break
            if previous is not None and t-previous!=timedelta(hours=1):raise ValueError("hourly_gap_or_duplicate")
            o,hi,lo,cl,v=(float(row[k]) for k in FIELDS[1:])
            if (not all(map(math.isfinite,(o,hi,lo,cl,v))) or min(o,hi,lo,cl)<=0
                or v<0 or hi<max(o,cl) or lo>min(o,cl)):
                raise ValueError("invalid_ohlcv")
            rows.append((t,o,hi,lo,cl,v))
            h.update(("|".join(row[k] for k in FIELDS)+"\n").encode())
            previous=t
    if not rows or rows[0][0]>START-timedelta(hours=721) or rows[0][0]>=START:
        raise ValueError("missing_preregistered_warmup")
    if rows[-1][0]!=END-timedelta(hours=1):raise ValueError("incomplete_train_end")
    return rows,h.hexdigest()

def make_features(b,e):
    """Each entry at index i uses close <= i-1; never close(i) or open(i+1)."""
    out={}
    bc=[r[4] for r in b];ec=[r[4] for r in e]
    br=[0.]+[math.log(bc[i]/bc[i-1]) for i in range(1,len(b))]
    er=[0.]+[math.log(ec[i]/ec[i-1]) for i in range(1,len(e))]
    for i in range(721,len(b)-1):
        rb=br[i-168:i];re=er[i-168:i]
        def vol(x):
            mean=sum(x)/len(x)
            return math.sqrt(max(0.,sum((r-mean)**2 for r in x)/167)*8760)
        vb=vol(rb);ve=vol(re)
        mom=math.log(bc[i-1]/bc[i-169]);relative=math.log(bc[i-1]/bc[i-73])-math.log(ec[i-1]/ec[i-73])
        out[i]=(vb,ve,mom,relative,br[i-1],er[i-1])
    return out

def regime(f):
    vb,_,mom,*_=f
    direction="BULL" if mom>.04 else "BEAR" if mom<-.04 else "SIDEWAYS"
    return direction+"__"+("HIGH_VOLATILITY" if vb>.85 else "LOW_VOLATILITY")

def weekly_target(f):
    vb,ve,mom,rel,*_=f
    if not all(math.isfinite(x) for x in (vb,ve,mom,rel)) or min(vb,ve)<=1e-12:
        return (0.,0.)
    gross=.25 if mom<0 and vb>1. else .45 if mom<0 or vb>1. else .70
    invb,inve=1/vb,1/ve
    wb=gross*invb/(invb+inve);we=gross*inve/(invb+inve)
    if rel>=.05:wb-=.10;we+=.10
    elif rel<=-.05:wb+=.10;we-=.10
    if abs(wb)+abs(we)>.90+1e-10 or max(abs(wb),abs(we))>.80+1e-10:
        raise ValueError("gross_or_asset_limit")
    return wb,we

def path_targets(b,e):
    if len(b)!=len(e) or any(x[0]!=y[0] for x,y in zip(b,e)):
        raise ValueError("unaligned_train_pairs")
    if b[-1][0]>=END:raise ValueError("future_source")
    f=make_features(b,e)
    indices=[i for i in f if b[i][0]>=START]
    if not indices:raise ValueError("no_train_hours")
    target=(0.,0.);cooldown=0;output=[]
    for i in indices:
        t=b[i][0];feat=f[i]
        if t.weekday()==0 and t.hour==0:target=weekly_target(feat)
        if cooldown==0 and min(feat[4],feat[5])<=math.log(.90):cooldown=24
        w=(0.,0.) if cooldown else target
        output.append((i,t,regime(feat),w,cooldown))
        if cooldown:cooldown-=1
    return output

def summarise(rows):
    returns=[x["net"] for x in rows]
    if not returns:raise ValueError("empty_evaluation")
    equity=peak=1.;maxdd=0.
    for r in returns:
        equity*=1+r;peak=max(peak,equity);maxdd=min(maxdd,equity/peak-1)
    folds=[]
    for k in range(5):
        q=1.
        for r in returns[k*len(rows)//5:(k+1)*len(rows)//5]:q*=1+r
        folds.append(q-1)
    daily=[];day=None;prod=1.
    for row in rows:
        d=row["time"].date()
        if day is not None and d!=day:daily.append(prod-1);prod=1.
        day=d;prod*=1+row["net"]
    daily.append(prod-1)
    best=max(range(len(daily)),key=daily.__getitem__)
    without=1.
    for i,r in enumerate(daily):
        if i!=best:without*=1+r
    gains=sum(max(0.,x) for x in returns)
    losses=-sum(min(0.,x) for x in returns)
    negative=sorted([-x for x in returns if x<0],reverse=True)
    n=max(1,math.ceil(len(rows)*.01))
    tail_share=sum(negative[:n])/sum(negative) if negative else None
    matrix={}
    for d in ("BULL","BEAR","SIDEWAYS"):
        for v in ("HIGH_VOLATILITY","LOW_VOLATILITY"):
            key=d+"__"+v;subset=[x for x in rows if x["regime"]==key]
            eq=1.
            for x in subset:eq*=1+x["net"]
            matrix[key]={"hours":len(subset),"roi":eq-1,
                         "active_hours":sum(x["active"] for x in subset),
                         "worst_hour":min((x["net"] for x in subset),default=None)}
    return {"roi":equity-1,"max_drawdown":maxdd,"fold_returns":folds,
            "positive_folds":sum(x>0 for x in folds),"hourly_profit_factor":gains/losses if losses else None,
            "remove_best_day_roi":without-1,"worst_day":min(daily),
            "tail_loss_top_1pct_hour_share":tail_share,"hours":len(rows),
            "active_hours":sum(x["active"] for x in rows),"cooldown_hours":sum(x["cooldown"]>0 for x in rows),
            "turnover":sum(x["turnover"] for x in rows),
            "modeled_transaction_cost_sum":sum(x["fee"] for x in rows),
            "regime_matrix":matrix}

def benchmark(b,e,indices,cost,weights):
    equity=1.
    for k,i in enumerate(indices):
        rb=b[i+1][1]/b[i][1]-1;re=e[i+1][1]/e[i][1]-1
        equity*=1+weights[0]*rb+weights[1]*re-(cost*sum(map(abs,weights)) if k==0 else 0)
    return equity-1

def simulate(b,e,targets,cost,journal_path):
    if cost not in (SEVERE,SUPERSEVERE):raise ValueError("unfrozen_cost")
    rows=[];equity=peak=1.;prior=(0.,0.)
    journal_path.parent.mkdir(parents=True,exist_ok=True)
    with journal_path.open("w",newline="",encoding="utf-8") as file:
        writer=csv.DictWriter(file,fieldnames=JOURNAL_FIELDS);writer.writeheader()
        for i,t,state,w,cooldown in targets:
            turnover=sum(abs(x-y) for x,y in zip(w,prior));fee=cost*turnover
            gross=w[0]*(b[i+1][1]/b[i][1]-1)+w[1]*(e[i+1][1]/e[i][1]-1)
            net=gross-fee
            if not math.isfinite(net) or net<=-1:raise ValueError("nonfinite_or_liquidated")
            equity*=1+net;peak=max(peak,equity)
            row={"time":t,"regime":state,"btc_weight":w[0],"eth_weight":w[1],
                 "turnover":turnover,"fee":fee,"net":net,"equity":equity,
                 "peak":peak,"cooldown":cooldown,"active":int(any(abs(x)>0 for x in w))}
            writer.writerow({k:(v.isoformat() if k=="time" else v) for k,v in row.items() if k in JOURNAL_FIELDS})
            rows.append(row);prior=w
    report=summarise(rows)
    report["cost_per_side"]=cost
    report["journal_sha256"]=hashlib.sha256(journal_path.read_bytes()).hexdigest()
    report["journal_rows"]=len(rows)
    report["benchmark_proxies"]={"btc_100pct":benchmark(b,e,[x[0] for x in targets],cost,(1.,0.)),
                                 "btc_eth_equal":benchmark(b,e,[x[0] for x in targets],cost,(.5,.5))}
    return report

def gates(s,v,identical_targets):
    return {"positive_severe":s["roi"]>0,"positive_supersevere":v["roi"]>0,
            "severe_at_least_4_5_folds":s["positive_folds"]>=4,
            "supersevere_at_least_3_5_folds":v["positive_folds"]>=3,
            "both_hourly_profit_factors_gt_1":all((x["hourly_profit_factor"] or 0)>1 for x in (s,v)),
            "both_remove_best_day_positive":all(x["remove_best_day_roi"]>0 for x in (s,v)),
            "supersevere_drawdown_within_35pct":v["max_drawdown"]>=-.35,
            "at_least_720_active_hours":s["active_hours"]>=720,
            "beats_train_btc_passive":s["roi"]>s["benchmark_proxies"]["btc_100pct"],
            "beats_train_equal_passive":s["roi"]>s["benchmark_proxies"]["btc_eth_equal"],
            "exactly_five_folds":len(s["fold_returns"])==len(v["fold_returns"])==5,
            "six_regimes":len(s["regime_matrix"])==len(v["regime_matrix"])==6,
            "identical_scenario_target_paths":identical_targets,
            "cost_monotone_fixed_path":v["roi"]<=s["roi"]+1e-10}

def run(btc,eth,out,prefix):
    if not SPEC.is_file() or not SPEC.read_text().strip():raise ValueError("prereg_missing")
    b,bsha=load_train(btc);e,esha=load_train(eth)
    targets=path_targets(b,e)
    s=simulate(b,e,targets,SEVERE,Path(str(prefix)+"_severe.csv"))
    v=simulate(b,e,targets,SUPERSEVERE,Path(str(prefix)+"_supersevere.csv"))
    identical=(s["active_hours"]==v["active_hours"] and s["turnover"]==v["turnover"])
    checks=gates(s,v,identical)
    report={"study":"V99_R106_C2_PREREGISTERED_COMPLETE_ENGINE_TRAIN",
            "status":"TRAIN_PASS_PENDING_INDEPENDENT_VALIDATION" if all(checks.values()) else "TRAIN_REJECT_NO_RETUNE",
            "economic_trials":1,"gates":checks,"passed_all_train_gates":all(checks.values()),
            "btc_train_sha256":bsha,"eth_train_sha256":esha,
            "train_start":START.isoformat(),"train_end_exclusive":END.isoformat(),
            "sealed_validation_start":END.isoformat(),"final_holdout_start":FINAL_HOLDOUT.isoformat(),
            "severe":s,"supersevere":v,"preliminary_pre_funding":True,
            "native_fee_tier_authenticated":False,"settled_funding_authenticated":False,
            "real_fills_authenticated":False,"validation_market_values_parsed":False,
            "holdout_market_values_parsed":False,"promotion_authorized":False,
            "paper_publication_authorized":False,"real_orders_enabled":False}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--btc",type=Path,default=Path("data/canonical/BTCUSDT_1h.csv"))
    p.add_argument("--eth",type=Path,default=Path("data/canonical/ETHUSDT_1h.csv"))
    p.add_argument("--out",type=Path,default=Path("reports/candidate_v99_r106_c2_complete_train.json"))
    p.add_argument("--prefix",type=Path,default=Path("research_evidence/v99_r106_c2"))
    a=p.parse_args();r=run(a.btc,a.eth,a.out,a.prefix)
    print(json.dumps({"status":r["status"],"severe_roi":r["severe"]["roi"],
                      "supersevere_roi":r["supersevere"]["roi"],
                      "severe_folds":r["severe"]["fold_returns"],
                      "supersevere_folds":r["supersevere"]["fold_returns"],
                      "failed_gates":[k for k,v in r["gates"].items() if not v],
                      "promotion_authorized":False},sort_keys=True))
if __name__=="__main__":main()
