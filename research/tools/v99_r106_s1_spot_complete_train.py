"""V99 S1 preregistered one-shot SPOT-ONLY historical TRAIN; NO orders/validation.
Original OKX source independently verified before any modeled economics.
Model-only severe/supersevere execution, NOT exchange-certified fills.
"""
from __future__ import annotations
import hashlib
import json
import math
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

from research.tools.v99_r106_d1_real_train_source_join import (
    START, END, HOURS, HOUR, FOLD_EDGES, strict_json,
)
from research.verification.independent_d1_native_train_receipts import verify

ASSETS = ("BTC", "ETH")
INST = {"BTC": "BTC-USDT", "ETH": "ETH-USDT"}
COSTS = {"severe_model_only": .0025, "supersevere_model_only": .006}
NO_PROMOTION = dict(historical_native_fills_authenticated=False,
    historical_native_fee_tier_authenticated=False, promotion_authorized=False,
    validation_opened=False, final_holdout_opened=False, orders_enabled=False,
    paper_publication_authorized=False)
PREREG = "research/V99_R106_S1_SPOT_OVERREACTION_PREREG_20261029.md"
WARMUP = 720

def source(price_root):
    if verify(Path(price_root))["status"] != "INDEPENDENT_FOUR_LEG_TRAIN_SOURCE_COMPLETE_NO_ECONOMICS":
        raise ValueError("S1_ORIGINAL_SOURCE_NOT_VERIFIED")
    expected = list(range(START, END, HOUR))
    prices = {}
    for a in ASSETS:
        rows = strict_json(Path(price_root) / INST[a] / "train_opens.json")
        if len(rows) != HOURS or [r["ts"] for r in rows] != expected:
            raise ValueError("S1_ORIGINAL_TRAIN_GRID_INVALID")
        vals = [float(r["open"]) for r in rows]
        if not all(math.isfinite(v) and v > 0 for v in vals):
            raise ValueError("S1_NONPOSITIVE_OR_NONFINITE_PRICE")
        prices[a] = vals
    return prices

def features(prices, t):
    if t < WARMUP:
        return None
    btc, eth = prices["BTC"], prices["ETH"]
    rb = btc[t-1]/btc[t-73]-1
    re = eth[t-1]/eth[t-73]-1
    def sigma(p):
        r = [math.log(p[k]/p[k-1]) for k in range(t-72, t)]
        return statistics.pstdev(r) * math.sqrt(24)
    sb, se = sigma(btc), sigma(eth)
    trend = btc[t-1]/btc[t-720]-1
    regime = ("bull" if trend > .05 else "bear" if trend < -.05 else "sideways") + (
        "_high" if sb >= .04 else "_low")
    veto = trend < -.25 or max(sb, se) > .08
    laggard = "ETH" if rb-re >= .08 else "BTC" if rb-re <= -.08 else None
    target = laggard if laggard and not veto else None
    return dict(target=target, regime=regime)

def fold(t_ms):
    for i,(a,b) in enumerate(zip(FOLD_EDGES,FOLD_EDGES[1:])):
        if a <= t_ms < b:
            return i
    raise ValueError("S1_SEALED_TIME_ACCESS_ATTEMPT")

def rebalance(cash, units, px, target, fee):
    nav = cash + sum(units[a]*px[a] for a in ASSETS)
    weights = {a: .65 if target == a else 0. for a in ASSETS}
    before = {a: units[a]*px[a] for a in ASSETS}
    # Solve NAV_after = NAV_before - fee*sum(abs(target_weight*NAV_after - current_value)).
    lo, hi = max(0., nav*(1-2*fee)), nav
    for _ in range(65):
        mid = (lo+hi)/2
        residual = mid + fee*sum(abs(weights[a]*mid-before[a]) for a in ASSETS)-nav
        if residual > 0: hi=mid
        else: lo=mid
    after = (lo+hi)/2
    next_units = {a: weights[a]*after/px[a] for a in ASSETS}
    turnover = sum(abs(next_units[a]*px[a]-before[a]) for a in ASSETS)
    fee_paid = fee*turnover
    next_cash = cash - sum((next_units[a]-units[a])*px[a] for a in ASSETS) - fee_paid
    if next_cash < -1e-9 or min(next_units.values()) < -1e-12:
        raise ValueError("S1_NEGATIVE_CASH_OR_SPOT")
    if abs(next_cash+sum(next_units[a]*px[a] for a in ASSETS)-(nav-fee_paid)) > 1e-8:
        raise ValueError("S1_SELF_FINANCING_VIOLATION")
    return max(0.,next_cash), next_units, turnover, fee_paid

def simulate(prices, scenario, emit_trace=False):
    fee = COSTS[scenario]
    cash, units = 1., {a:0. for a in ASSETS}
    prev_nav = 1.
    logs = [0.]*5
    regimes = {f"{tr}_{v}": dict(hours=0, log_return=0.)
               for tr in ("bull","bear","sideways") for v in ("low","high")}
    day_logs = {}
    trades=0; turnover=0.; fees=0.; min_nav=1.; max_nav=1.; max_dd=0.
    decisions=[]; nav_trace=[]; hourly_hash=hashlib.sha256()
    for t in range(HOURS):
        px={a:prices[a][t] for a in ASSETS}
        f=features(prices,t) if t>=WARMUP else None
        if f and t%24 == 0:
            cash,units,volume,paid=rebalance(cash,units,px,f["target"],fee)
            turnover+=volume; fees+=paid
            if volume>1e-10: trades+=1
            decisions.append((t,f["target"]))
        nav=cash+sum(units[a]*px[a] for a in ASSETS)
        if not math.isfinite(nav) or nav<=0:
            raise ValueError("S1_NONPOSITIVE_NAV")
        hourly=math.log(nav/prev_nav)
        logs[fold(START+t*HOUR)]+=hourly
        if f:
            regimes[f["regime"]]["hours"]+=1
            regimes[f["regime"]]["log_return"]+=hourly
            day_logs[t//24]=day_logs.get(t//24,0.)+hourly
        max_nav=max(max_nav,nav); min_nav=min(min_nav,nav)
        max_dd=min(max_dd,nav/max_nav-1)
        # Fixed canonical trace digest, not independent evidence by itself.
        hourly_hash.update(f"{t},{nav:.12f},{cash:.12f},{units['BTC']:.12f},{units['ETH']:.12f}\n".encode())
        if emit_trace: nav_trace.append(nav)
        prev_nav=nav
    total=math.exp(sum(logs))-1
    return dict(scenario=scenario,roi=total,fold_rois=[math.exp(x)-1 for x in logs],
        worst_fold=min(math.exp(x)-1 for x in logs),positive_folds=sum(x>0 for x in logs),
        max_drawdown=max_dd,trades=trades,turnover=turnover,modeled_cost=fees,
        final_nav=prev_nav,decision_count=len(decisions),
        decisions_sha256=hashlib.sha256(json.dumps(decisions,separators=(",",":")).encode()).hexdigest(),
        hourly_nav_sha256=hourly_hash.hexdigest(),
        regimes={k:dict(hours=v["hours"],roi=math.exp(v["log_return"])-1) for k,v in regimes.items()},
        best_day_removed_roi=math.exp(sum(logs)-max(day_logs.values(),default=0.))-1,
        **({"nav_trace":nav_trace,"decisions":decisions} if emit_trace else {}))

def benchmark(prices,fee):
    # Invest at first executable open after warmup, liquidate at last TRAIN open.
    t=WARMUP
    p0={a:prices[a][t] for a in ASSETS}
    pend={a:prices[a][-1] for a in ASSETS}
    out={"cash":0.}
    for label,weights in (("BTC",{"BTC":1.}),("ETH",{"ETH":1.}),
                          ("BTC_ETH_50_50",{"BTC":.5,"ETH":.5})):
        # Entry and exit costs; initial all-in NAV is 1/(1+fee).
        gross=sum(w*pend[a]/p0[a] for a,w in weights.items())/(1+fee)
        out[label]=gross*(1-fee)-1
    return out

def report(price_root,output):
    prices=source(price_root)
    severe=simulate(prices,"severe_model_only")
    supersevere=simulate(prices,"supersevere_model_only")
    if severe["decisions_sha256"]!=supersevere["decisions_sha256"]:
        raise ValueError("S1_COST_SCENARIO_CHANGED_SIGNAL")
    b=benchmark(prices,COSTS["severe_model_only"])
    tests={
        "positive_both": severe["roi"]>0 and supersevere["roi"]>0,
        "four_of_five_both": min(severe["positive_folds"],supersevere["positive_folds"])>=4,
        "worst_fold_both": min(severe["worst_fold"],supersevere["worst_fold"])>=-.05,
        "maxdd_both": min(severe["max_drawdown"],supersevere["max_drawdown"])>=-.25,
        "severe_beats_passive_envelope":severe["roi"]>max(b.values()),
        "four_of_six_regimes":sum(x["hours"]>=48 and x["roi"]>0 for x in severe["regimes"].values())>=4,
        "best_day_removed_positive":severe["best_day_removed_roi"]>0,
        "source_and_accounting":True,
        "native_fee_fill_provenance":False,
    }
    status="MODEL_ONLY_HOLD_NATIVE_PROVENANCE" if all(v for k,v in tests.items() if k!="native_fee_fill_provenance") else "S1_REJECTED_NO_RETUNE"
    result=dict(schema="V99_R106_S1_ONE_SHOT_SPOT_TRAIN_V1",status=status,
        original_train_hours=HOURS,preregistered_spec=PREREG,
        original_source_verified=True,original_first_party_open_not_executable_fill=True,
        severe=severe,supersevere=supersevere,passive_benchmarks=b,
        fixed_gates=tests,**NO_PROMOTION)
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    (output/"s1_train_model_only.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(dict(status=status,severe_roi=severe["roi"],
        supersevere_roi=supersevere["roi"],folds=[severe["positive_folds"],supersevere["positive_folds"]],
        maxdd=[severe["max_drawdown"],supersevere["max_drawdown"]],
        gates=tests,NO_PROMOTION=True),sort_keys=True))
    return result

if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("usage: python -m research.tools.v99_r106_s1_spot_complete_train PRICE_ROOT OUTPUT")
    report(sys.argv[1],sys.argv[2])
