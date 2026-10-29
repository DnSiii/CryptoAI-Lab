"""D3 independent original-source -> lagged spread -> trades -> fee -> NAV oracle.

No imports from production D3 and no acceptance of reported PnL as source.
"""
from __future__ import annotations
import json
import math
import sys
from datetime import datetime,timezone
from pathlib import Path
from research.verification.independent_d1_native_train_receipts import verify as verify_original

T0=int(datetime(2021,12,9,tzinfo=timezone.utc).timestamp()*1000)
T1=int(datetime(2023,10,1,tzinfo=timezone.utc).timestamp()*1000)
N=(T1-T0)//3600000
EDGES=[int(datetime.fromisoformat(x).replace(tzinfo=timezone.utc).timestamp()*1000)
       for x in ("2021-12-09T00:00:00","2022-04-20T04:00:00",
                 "2022-08-30T09:00:00","2023-01-09T14:00:00",
                 "2023-05-21T19:00:00","2023-10-01T00:00:00")]
RATES={"severe":.0007,"supersevere":.0014}
FLAGS=("native_fee_tier_authenticated","settled_funding_cash_authenticated",
       "execution_fills_authenticated","liquidation_margin_authenticated",
       "original_economic_train_certified","freeze_authorized",
       "promotion_authorized","validation_opened","holdout_opened",
       "orders_enabled","paper_publication_authorized")

def same(a,b,tag):
    if not (math.isfinite(float(a)) and math.isfinite(float(b))
            and abs(float(a)-float(b))<=1e-9*max(1.,abs(float(a)),abs(float(b)))):
        raise AssertionError("D3_ORACLE_MISMATCH_"+tag)

def verify(root,out):
    root,out=Path(root),Path(out)
    original=verify_original(root)
    if original.get("status")!="INDEPENDENT_FOUR_LEG_TRAIN_SOURCE_COMPLETE_NO_ECONOMICS":
        raise AssertionError("D3_ORIGINAL_RAW_PAGE_PROOF_MISSING")
    report=json.loads((out/"d3_train_report.json").read_text())
    rows=json.loads((out/"d3_hourly_journal.json").read_text())
    if report.get("schema")!="V99_R106_D3_RELATIVE_VALUE_COMPLETE_TRAIN_V1" or len(rows)!=N:
        raise AssertionError("D3_SCHEMA_OR_GRID")
    if any(report.get(k) is not False for k in FLAGS):
        raise AssertionError("D3_FORGED_NATIVE_CERTIFICATION")
    prices={}
    for inst in ("BTC-USDT","ETH-USDT","BTC-USDT-SWAP","ETH-USDT-SWAP"):
        raw=json.loads((root/inst/"train_opens.json").read_text())
        if len(raw)!=N: raise AssertionError("D3_SOURCE_LENGTH")
        if any(r["ts"]!=T0+i*3600000 for i,r in enumerate(raw)):
            raise AssertionError("D3_SOURCE_TIMESTAMP")
        prices[inst]=[float(r["open"]) for r in raw]
        if any(not math.isfinite(x) or x<=0 for x in prices[inst]):
            raise AssertionError("D3_SOURCE_PRICE")
    btc,eth=prices["BTC-USDT-SWAP"],prices["ETH-USDT-SWAP"]
    logratio=[math.log(e/b) for e,b in zip(eth,btc)]
    capital={s:1. for s in RATES}
    prior={s:1. for s in RATES}
    peak={s:1. for s in RATES}
    worst={s:0. for s in RATES}
    factors={s:[] for s in RATES}
    gains={s:[] for s in RATES}
    losses={s:[] for s in RATES}
    folds={s:[1.]*5 for s in RATES}
    reg_counts={a+"_"+b:0 for a in ("BULL","BEAR","SIDEWAYS")
                for b in ("LOW_VOL","HIGH_VOL")}
    position=None
    ready=720
    total_events=0
    completed=0
    for i,row in enumerate(rows):
        ts=T0+i*3600000
        fold=next((j+1 for j in range(5) if EDGES[j]<=ts<EDGES[j+1]),None)
        if type(row.get("ts_ms")) is not int or row["ts_ms"]!=ts or row["fold"]!=fold:
            raise AssertionError("D3_SEALED_OR_FOLD_MISMATCH")
        if i<169:
            regime="SIDEWAYS_LOW_VOL"
        else:
            trend=prices["BTC-USDT"][i-1]/prices["BTC-USDT"][i-169]-1
            state="BULL" if trend>.05 else "BEAR" if trend<-.05 else "SIDEWAYS"
            changes=[prices["BTC-USDT"][k]/prices["BTC-USDT"][k-1]-1
                     for k in range(i-168,i)]
            mean=sum(changes)/168
            vol=math.sqrt(sum((v-mean)**2 for v in changes)/168)
            regime=state+("_HIGH_VOL" if vol>=.01 else "_LOW_VOL")
        if row["regime"]!=regime: raise AssertionError("D3_REGIME_MISMATCH")
        reg_counts[regime]+=1
        z=None
        if i>=720:
            window=logratio[i-720:i]
            center=sum(window)/720
            var=sum((x-center)**2 for x in window)/720
            if var>1e-24: z=(window[-1]-center)/math.sqrt(var)
        if z is None:
            if row["z_lagged"] is not None: raise AssertionError("D3_CAUSAL_Z_NULL")
        else: same(row["z_lagged"],z,"CAUSAL_Z")
        pnl=0.
        if i and position:
            pnl=position["btc"]*(btc[i]-btc[i-1])+position["eth"]*(eth[i]-eth[i-1])
        same(row["pnl"],pnl,"HOURLY_MARK")
        expected=[]
        fees={s:0. for s in RATES}
        terminal=i==N-1
        if position and (terminal or i-position["start"]>=168
                         or (z is not None and abs(z)<=.25)):
            expected.append(("EXIT",position["btc"],position["eth"]))
            for sc,rate in RATES.items():
                fees[sc]+=rate*(abs(position["btc"])*btc[i]+abs(position["eth"])*eth[i])
            position=None
            ready=i+168
            completed+=1
        if not position and not terminal and i>=ready and z is not None and abs(z)>=2:
            direction=1 if z>=2 else -1
            position={"btc":direction*.20/btc[i],
                      "eth":-direction*.20/eth[i],"start":i}
            expected.append(("OPEN",position["btc"],position["eth"]))
            for sc,rate in RATES.items():
                fees[sc]+=rate*(abs(position["btc"])*btc[i]+abs(position["eth"])*eth[i])
        if len(row["events"])!=len(expected):
            raise AssertionError("D3_EVENT_COUNT")
        for actual,(kind,qb,qe) in zip(row["events"],expected):
            if actual["kind"]!=kind: raise AssertionError("D3_SIGNAL_EVENT")
            same(actual["q_btc"],qb,"EVENT_BTC")
            same(actual["q_eth"],qe,"EVENT_ETH")
        total_events+=len(expected)
        active=row["active"]
        if bool(active)!=bool(position): raise AssertionError("D3_ACTIVE_MISMATCH")
        if position:
            same(active["q_btc"],position["btc"],"POSITION_BTC")
            same(active["q_eth"],position["eth"],"POSITION_ETH")
            if active["entry_i"]!=position["start"]: raise AssertionError("D3_ENTRY_CLOCK")
        gross=(abs(position["btc"])*btc[i]+abs(position["eth"])*eth[i]) if position else 0.
        same(row["gross"],gross,"GROSS")
        benchmark=.5*(prices["BTC-USDT"][i]/prices["BTC-USDT"][0]+
                      prices["ETH-USDT"][i]/prices["ETH-USDT"][0])
        same(row["benchmark"],benchmark,"BENCHMARK")
        for sc in RATES:
            same(row["fees"][sc],fees[sc],"FEES_"+sc)
            capital[sc]+=pnl-fees[sc]
            if capital[sc]<=0: raise AssertionError("D3_CAPITAL_RUIN")
            same(row["nav"][sc],capital[sc],"NAV_"+sc)
            diff=capital[sc]-prior[sc]
            if diff>0:gains[sc].append(diff)
            if diff<0:losses[sc].append(-diff)
            f=capital[sc]/prior[sc]
            factors[sc].append(f)
            folds[sc][fold-1]*=f
            peak[sc]=max(peak[sc],capital[sc])
            worst[sc]=min(worst[sc],capital[sc]/peak[sc]-1)
            prior[sc]=capital[sc]
    if position or report["event_count"]!=total_events:
        raise AssertionError("D3_NOT_FLAT_OR_EVENT_TOTAL")
    for sc in RATES:
        m=report["metrics"][sc]
        roi=capital[sc]-1
        positive=sum(x>1 for x in folds[sc])
        pf=sum(gains[sc])/sum(losses[sc]) if losses[sc] else (float("inf") if gains[sc] else 0.)
        tail=math.ceil(N/100)
        gainshare=sum(sorted(gains[sc],reverse=True)[:tail])/sum(gains[sc]) if gains[sc] else 1.
        lossshare=sum(sorted(losses[sc],reverse=True)[:tail])/sum(losses[sc]) if losses[sc] else 0.
        best=capital[sc]/max(factors[sc])-1
        same(m["roi_pre_funding"],roi,"ROI")
        same(m["max_drawdown"],worst[sc],"DD")
        same(m["remove_best_hour_roi"],best,"REMOVE_BEST")
        same(m["gain_share_top_1pct"],gainshare,"GAIN_TAIL")
        same(m["loss_share_worst_1pct"],lossshare,"LOSS_TAIL")
        same(m["benchmark_50_50_spot_roi"],benchmark-1,"BENCH")
        if pf==float("inf"):
            if m["profit_factor"]!="infinite": raise AssertionError("D3_PF")
        else: same(m["profit_factor"],pf,"PF")
        if m["positive_folds"]!=positive or m["regime_counts"]!=reg_counts:
            raise AssertionError("D3_FOLD_OR_REGIME")
        for x,y in zip(m["fold_roi"],folds[sc]): same(x,y-1,"FOLD_ROI")
        gates={
            "positive_total":roi>0,
            "positive_folds":positive>=(4 if sc=="severe" else 3),
            "profit_factor":pf>1,
            "max_drawdown":worst[sc]>=-.35,
            "remove_best_hour_positive":best>0,
            "top_1pct_gain_share":gainshare<=.40,
            "worst_1pct_loss_share":lossshare<=.50,
            "beats_cash_and_spot_benchmark":roi>max(0.,benchmark-1),
            "six_regimes_present":all(reg_counts.values()),
            "completed_spread":completed>0,
        }
        if m["gates"]!=gates or m["numeric_pass"]!=all(gates.values()):
            raise AssertionError("D3_GATE_MISMATCH")
    if report["numeric_pass_both"]!=all(report["metrics"][s]["numeric_pass"] for s in RATES):
        raise AssertionError("D3_COMBINED_GATE")
    return {"status":"INDEPENDENT_D3_FULL_ORIGINAL_TRAIN_HOURLY_REPLAY_PRE_FUNDING_ONLY",
            "hours_verified":N,"events_verified":total_events,"completed_spreads":completed,
            "severe_roi_pre_funding":capital["severe"]-1,
            "supersevere_roi_pre_funding":capital["supersevere"]-1,
            "numeric_pass_both":report["numeric_pass_both"],
            "native_funding_cash_certified":False,"native_fees_certified":False,
            "promotion_authorized":False,"validation_opened":False,
            "holdout_opened":False,"orders_enabled":False}

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: python -m research.verification.independent_v99_r106_d3_relative_value_oracle ORIGINAL_ROOT REPORT_DIR")
    print(json.dumps(verify(*sys.argv[1:]),sort_keys=True))
