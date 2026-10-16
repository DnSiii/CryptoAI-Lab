"""One-shot V99 TRAIN-only two-asset high-growth breakout. No holdout parse, no orders."""
import csv
import hashlib
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

CUTOFF=datetime(2024,1,18,tzinfo=timezone.utc)
START=datetime(2021,12,1,tzinfo=timezone.utc)
BREAKOUT=168
EXIT=72
VOL=168
TARGET_HOURLY_VOL_BUDGET=0.35
ASSET_GROSS_CAP=0.625
GROSS_CAP=1.25
SEVERE=0.0007
SUPERSEVERE=0.0014
KEYS=("BTCUSDT","ETHUSDT")

def utc(text):
    if not isinstance(text,str):raise ValueError("missing_utc_timestamp")
    v=datetime.fromisoformat(text.replace("Z","+00:00"))
    if v.tzinfo is None or v.utcoffset()!=timedelta(0):raise ValueError("explicit_utc_required")
    return v.astimezone(timezone.utc)

def load_train(path):
    values=[];digest=hashlib.sha256()
    with open(path,newline="",encoding="utf-8") as file:
        reader=csv.DictReader(file)
        fields=("timestamp","open","high","low","close","volume")
        if reader.fieldnames is None or any(x not in reader.fieldnames for x in fields):
            raise ValueError("missing_canonical_market_fields")
        prior=None
        for row in reader:
            timestamp=utc(row["timestamp"])
            # Break BEFORE parsing any market values from final holdout / 2024+.
            if timestamp>=CUTOFF:break
            if prior is not None and timestamp-prior!=timedelta(hours=1):
                raise ValueError("gapped_repeated_or_out_of_order_train_hour")
            vals=tuple(float(row[x]) for x in ("open","high","low","close","volume"))
            if (not all(math.isfinite(q) for q in vals)
                    or min(vals[0:4])<=0 or vals[4]<vals[2] or vals[4]>vals[1]
                    or vals[2]>min(vals[0],vals[3]) or vals[1]<max(vals[0],vals[3])
                    or vals[4]<0):
                raise ValueError("invalid_canonical_train_ohlcv")
            values.append((timestamp,*vals))
            digest.update(("|".join(row[x] for x in fields)+"\n").encode())
            prior=timestamp
    if len(values)<500:raise ValueError("insufficient_train_history")
    return values,digest.hexdigest()

def direction(history,t,previous):
    """Decide hour t using only bars [0..t-1]. Midrange/trend rules frozen."""
    last=history[t-1][4]
    old=history[t-BREAKOUT-1:t-1]
    breakout_high=max(x[2] for x in old)
    breakout_low=min(x[3] for x in old)
    if last>breakout_high:return 1
    if last<breakout_low:return -1
    recent=history[t-EXIT:t]
    midpoint=(max(x[2] for x in recent)+min(x[3] for x in recent))/2
    if previous>0 and last<midpoint:return 0
    if previous<0 and last>midpoint:return 0
    return previous

def position(history,t,previous):
    # Zero volatility isn't proof of tradable zero risk: stay flat.
    d=direction(history,t,previous)
    ret=[math.log(history[i][4]/history[i-1][4])
         for i in range(t-VOL,t)]
    mean=sum(ret)/VOL
    variance=sum((x-mean)*(x-mean) for x in ret)/(VOL-1)
    annual=math.sqrt(variance)*math.sqrt(8760)
    scale=min(ASSET_GROSS_CAP,TARGET_HOURLY_VOL_BUDGET/annual) if annual>1e-12 else 0.
    return d*scale

def targets(b,e):
    if [x[0] for x in b]!=[x[0] for x in e]:raise ValueError("canonical_hourly_timestamp_mismatch")
    if not b or b[-1][0]>=CUTOFF or e[-1][0]>=CUTOFF:raise ValueError("train_cutoff_violation")
    out=[];pb=pe=0.
    for i in range(BREAKOUT+1,len(b)-1):
        if b[i][0]<START:continue
        if b[i][0].hour==0:
            pb=position(b,i,1 if pb>0 else -1 if pb<0 else 0)
            pe=position(e,i,1 if pe>0 else -1 if pe<0 else 0)
        if abs(pb)+abs(pe)>GROSS_CAP+1e-12:raise ValueError("gross_cap")
        out.append((i,b[i][0],pb,pe))
    if not out:raise ValueError("no_eligible_train_trades")
    return out

def assess(b,e,cost,signals=None):
    if cost not in (SEVERE,SUPERSEVERE):raise ValueError("cost_not_preregistered")
    signals=targets(b,e) if signals is None else signals
    returns=[];active=0;prevb=preve=0.
    for i,t,pb,pe in signals:
        rb=b[i+1][1]/b[i][1]-1
        re=e[i+1][1]/e[i][1]-1
        turnover=abs(pb-prevb)+abs(pe-preve)
        net=pb*rb+pe*re-cost*turnover
        if not math.isfinite(net) or net<=-1:raise ValueError("invalid_compounded_train_return")
        returns.append(net)
        active+=int(abs(pb)+abs(pe)>0)
        prevb,preve=pb,pe
    eq=peak=1.;dd=0.
    for ret in returns:
        eq*=1+ret;peak=max(peak,eq);dd=min(dd,eq/peak-1)
    folds=[]
    for k in range(5):
        q=1.
        for r in returns[k*len(returns)//5:(k+1)*len(returns)//5]:q*=1+r
        folds.append(q-1)
    best=max(range(len(returns)),key=lambda i:returns[i]);no_best=1.
    for i,r in enumerate(returns):
        if i!=best:no_best*=1+r
    gains=sum(x for x in returns if x>0)
    losses=-sum(x for x in returns if x<0)
    return {"return":eq-1,"max_drawdown":dd,
            "profit_factor":gains/losses if losses>0 else None,
            "fold_returns":folds,"healthy_folds":sum(x>0 for x in folds),
            "worst_hour":min(returns),"remove_best_hour_return":no_best-1,
            "hours":len(returns),"active_hours":active,"cost_per_side":cost,
            "funding_settlement_authenticated":False,"real_fills_authenticated":False}

def evaluate(b,e):
    sig=targets(b,e)
    severe=assess(b,e,SEVERE,sig)
    supersevere=assess(b,e,SUPERSEVERE,sig)
    passed=(severe["return"]>0 and supersevere["return"]>0
            and severe["healthy_folds"]>=4 and supersevere["healthy_folds"]>=3
            and severe["remove_best_hour_return"]>0
            and supersevere["remove_best_hour_return"]>0
            and (severe["profit_factor"] or 0)>1
            and (supersevere["profit_factor"] or 0)>1
            and severe["active_hours"]>=720)
    return {"status":"TRAIN_ALPHA_PRELIMINARY_PASS_NO_FUNDING_NOT_PROMOTED" if passed else "TRAIN_ALPHA_REJECT_NO_RETUNE",
            "study":"V99 R106 isolated Donchian growth sleeve one-shot",
            "mode":"TRAIN_ONLY_PRE_FUNDING",
            "preregistered_parameters":{"breakout_hours":BREAKOUT,"exit_midrange_hours":EXIT,
                "volatility_hours":VOL,"annualized_single_asset_vol_budget":TARGET_HOURLY_VOL_BUDGET,
                "per_asset_max_gross":ASSET_GROSS_CAP,"max_portfolio_gross":GROSS_CAP,
                "rebalance_utc_hour":0,"training_end_exclusive":CUTOFF.isoformat()},
            "severe":severe,"supersevere":supersevere,"passed_pre_funding_train_gate":passed,
            "holdout_market_values_parsed":False,"final_holdout_accessed":False,
            "fee_tier_independently_authenticated":False,"realized_funding_authenticated":False,
            "promotion_authorized":False,"paper_publication_authorized":False,
            "real_orders_enabled":False,"economic_trials":1}

def main(btc="data/canonical/BTCUSDT_1h.csv",eth="data/canonical/ETHUSDT_1h.csv",
         output="reports/candidate_v99_r106_growth_breakout_train.json"):
    b,bs=load_train(btc);e,es=load_train(eth)
    r=evaluate(b,e)
    r["btc_train_stream_sha256"]=bs;r["eth_train_stream_sha256"]=es
    path=Path(output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":r["status"],"severe_return":r["severe"]["return"],
          "supersevere_return":r["supersevere"]["return"],
          "severe_folds":r["severe"]["healthy_folds"],
          "supersevere_folds":r["supersevere"]["healthy_folds"],
          "holdout_accessed":False,"promotion_authorized":False},sort_keys=True))
    return r
if __name__=="__main__":main()
