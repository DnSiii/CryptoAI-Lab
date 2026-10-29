"""Independent source-to-signal-to-position-to-fee-to-NAV D2 TRAIN oracle.

Does not import production D2 implementation or accept reported PnL as input.
Only original OKX first-party 2021-12-09..2023-10-01 opens; NO FUNDING CERTIFICATION.
"""
from __future__ import annotations
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from research.verification.independent_d1_native_train_receipts import verify as verify_original

START=int(datetime(2021,12,9,tzinfo=timezone.utc).timestamp()*1000)
END=int(datetime(2023,10,1,tzinfo=timezone.utc).timestamp()*1000)
HOUR=3600000
N=(END-START)//HOUR
EDGES=[int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp()*1000)
       for s in ("2021-12-09T00:00:00","2022-04-20T04:00:00",
                 "2022-08-30T09:00:00","2023-01-09T14:00:00",
                 "2023-05-21T19:00:00","2023-10-01T00:00:00")]
COSTS={"severe":.0007,"supersevere":.0014}

def close(a,b,*,tag):
    if not (math.isfinite(a) and math.isfinite(b) and
            abs(a-b)<=1e-9*max(1.,abs(a),abs(b))):
        raise AssertionError("D2_INDEPENDENT_MISMATCH:"+tag)

def verify(root, out):
    root,out=Path(root),Path(out)
    proof=verify_original(root)
    if proof["status"]!="INDEPENDENT_FOUR_LEG_TRAIN_SOURCE_COMPLETE_NO_ECONOMICS":
        raise AssertionError("D2_ORIGINAL_SOURCE_NOT_INDEPENDENTLY_VERIFIED")
    report=json.loads((out/"d2_train_report.json").read_text())
    journal=json.loads((out/"d2_hourly_journal.json").read_text())
    if report.get("schema")!="V99_R106_D2_BASIS_COMPLETE_TRAIN_V1" or len(journal)!=N:
        raise AssertionError("D2_REPORT_OR_HOURLY_GRID_INVALID")
    for flag in ("native_fee_tier_authenticated","settled_funding_cash_authenticated",
                 "execution_fills_authenticated","liquidation_margin_authenticated",
                 "original_economic_train_certified","independent_original_accounting_verified",
                 "freeze_authorized","promotion_authorized","validation_opened",
                 "holdout_opened","orders_enabled","paper_publication_authorized"):
        if report.get(flag) is not False:
            raise AssertionError("D2_UNAUTHORIZED_CERTIFICATION:"+flag)
    opens={}
    for asset in ("BTC","ETH"):
        for suffix in ("","-SWAP"):
            key=asset+"-USDT"+suffix
            data=json.loads((root/key/"train_opens.json").read_text())
            if len(data)!=N or any(row["ts"]!=START+i*HOUR for i,row in enumerate(data)):
                raise AssertionError("D2_INVALID_ORIGINAL_HOUR")
            opens[key]=[float(row["open"]) for row in data]
    basis={asset:[opens[asset+"-USDT-SWAP"][i]/opens[asset+"-USDT"][i]-1
                  for i in range(N)] for asset in ("BTC","ETH")}
    positions={}
    capital={"severe":1.,"supersevere":1.}
    previous_capital={s:1. for s in COSTS}
    peak={s:1. for s in COSTS}
    dd={s:0. for s in COSTS}
    fold_returns={s:[1.]*5 for s in COSTS}
    gain={s:[] for s in COSTS}
    loss={s:[] for s in COSTS}
    factors={s:[] for s in COSTS}
    regime_counts={s+"_"+v:0 for s in ("BULL","BEAR","SIDEWAYS")
                   for v in ("LOW_VOL","HIGH_VOL")}
    events_total=0
    for i,row in enumerate(journal):
        now=START+i*HOUR
        fold=next((k+1 for k in range(5) if EDGES[k]<=now<EDGES[k+1]),None)
        if type(row.get("ts_ms")) is not int or row["ts_ms"]!=now or row["fold"]!=fold:
            raise AssertionError("D2_TIMESTAMP_FOLD_OR_SEALED_MISMATCH")
        pnl=0.
        if i:
            for asset,pos in positions.items():
                s=opens[asset+"-USDT"]
                p=opens[asset+"-USDT-SWAP"]
                pnl+=pos["qty"]*((s[i]-s[i-1])-(p[i]-p[i-1]))
        fees={s:0. for s in COSTS}
        expected=[]
        for asset in ("BTC","ETH"):
            spot=opens[asset+"-USDT"][i]
            perp=opens[asset+"-USDT-SWAP"][i]
            values=basis[asset][i-168:i] if i>=168 else []
            if values:
                avg=sum(values)/len(values)
                var=sum((x-avg)**2 for x in values)/len(values)
                z=(values[-1]-avg)/math.sqrt(var) if var>1e-24 else None
            else: z=None
            old=positions.get(asset)
            end=i==N-1
            if old is not None and (end or i-old["start"]>=168 or
                                     (z is not None and z<=.5)):
                q=old["qty"]
                expected.append(("EXIT",asset,q))
                for sc,rate in COSTS.items(): fees[sc]+=rate*q*(spot+perp)
                del positions[asset]
            if (not end and asset not in positions and i>=168 and
                    z is not None and z>=2 and basis[asset][i-1]>0):
                q=.25/max(spot,perp)
                expected.append(("OPEN",asset,q))
                for sc,rate in COSTS.items(): fees[sc]+=rate*q*(spot+perp)
                positions[asset]={"qty":q,"start":i}
        actual=row.get("events")
        if not isinstance(actual,list) or len(actual)!=len(expected):
            raise AssertionError("D2_INDEPENDENT_SIGNAL_EVENT_COUNT_MISMATCH")
        for event,(kind,asset,q) in zip(actual,expected):
            if event.get("kind")!=kind or event.get("asset")!=asset:
                raise AssertionError("D2_INDEPENDENT_SIGNAL_OR_EVENT_MISMATCH")
            close(float(event["qty"]),q,tag="EVENT_QUANTITY")
        events_total+=len(expected)
        close(row["pnl"],pnl,tag="HOURLY_MARK_PNL")
        if set(row["active"])!=set(positions):
            raise AssertionError("D2_INDEPENDENT_ACTIVE_POSITIONS_MISMATCH")
        for asset,pos in positions.items():
            close(float(row["active"][asset]["qty"]),pos["qty"],tag="POSITION_QTY")
            if row["active"][asset]["entry_i"]!=pos["start"]:
                raise AssertionError("D2_INDEPENDENT_ENTRY_TIMESTAMP_MISMATCH")
        gross=sum(pos["qty"]*(opens[asset+"-USDT"][i]+
                              opens[asset+"-USDT-SWAP"][i])
                  for asset,pos in positions.items())
        close(row["gross"],gross,tag="GROSS")
        bench=.5*(opens["BTC-USDT"][i]/opens["BTC-USDT"][0]+
                  opens["ETH-USDT"][i]/opens["ETH-USDT"][0])
        close(row["benchmark"],bench,tag="BENCHMARK")
        if i<169:
            regime="SIDEWAYS_LOW_VOL"
        else:
            btc=opens["BTC-USDT"]
            trend=btc[i-1]/btc[i-169]-1
            state="BULL" if trend>.05 else "BEAR" if trend<-.05 else "SIDEWAYS"
            returns=[btc[k]/btc[k-1]-1 for k in range(i-168,i)]
            mean=sum(returns)/len(returns)
            vol=math.sqrt(sum((x-mean)**2 for x in returns)/len(returns))
            regime=state+("_HIGH_VOL" if vol>=.01 else "_LOW_VOL")
        if row["regime"]!=regime:
            raise AssertionError("D2_INDEPENDENT_CAUSAL_REGIME_MISMATCH")
        regime_counts[regime]+=1
        for sc in COSTS:
            close(row["fees"][sc],fees[sc],tag="FEE_"+sc)
            capital[sc]+=pnl-fees[sc]
            close(row["nav"][sc],capital[sc],tag="CAPITAL_"+sc)
            if capital[sc]<=0:
                raise AssertionError("D2_RUIN")
            diff=capital[sc]-previous_capital[sc]
            if diff>0:gain[sc].append(diff)
            if diff<0:loss[sc].append(-diff)
            factor=capital[sc]/previous_capital[sc]
            factors[sc].append(factor)
            fold_returns[sc][fold-1]*=factor
            peak[sc]=max(peak[sc],capital[sc])
            dd[sc]=min(dd[sc],capital[sc]/peak[sc]-1)
            previous_capital[sc]=capital[sc]
    if positions or report["event_count"]!=events_total:
        raise AssertionError("D2_TERMINAL_POSITIONS_OR_EVENT_TOTAL")
    top=math.ceil(N/100)
    for sc in COSTS:
        result=report["metrics"][sc]
        close(result["roi_pre_funding"],capital[sc]-1,tag="ROI_"+sc)
        close(result["max_drawdown"],dd[sc],tag="DRAWDOWN_"+sc)
        for x,y in zip(result["fold_roi"],fold_returns[sc]):
            close(x,y-1,tag="FOLD_"+sc)
        best=capital[sc]/max(factors[sc])-1
        close(result["remove_best_hour_roi"],best,tag="REMOVE_BEST_"+sc)
        gains=sum(gain[sc]); losses=sum(loss[sc])
        share=sum(sorted(gain[sc],reverse=True)[:top])/gains if gains else 1.
        tail=sum(sorted(loss[sc],reverse=True)[:top])/losses if losses else 0.
        close(result["gain_share_top_1pct"],share,tag="GAIN_TAIL_"+sc)
        close(result["loss_share_worst_1pct"],tail,tag="LOSS_TAIL_"+sc)
        if result["regime_counts"]!=regime_counts:
            raise AssertionError("D2_INDEPENDENT_REGIME_COUNTS")
        if result["positive_folds"]!=sum(x>1 for x in fold_returns[sc]):
            raise AssertionError("D2_INDEPENDENT_FOLD_COUNTS")
    return dict(status="INDEPENDENT_FULL_ORIGINAL_HOURLY_ACCOUNTING_REPLAY_PRE_FUNDING_ONLY",
        hours_verified=N, events_verified=events_total,
        severe_roi_pre_funding=capital["severe"]-1,
        supersevere_roi_pre_funding=capital["supersevere"]-1,
        original_source_price_receipts_verified=True,
        original_settled_funding_and_historical_fees_verified=False,
        original_economic_train_certified=False, promotion_authorized=False,
        validation_opened=False,holdout_opened=False,orders_enabled=False)

if __name__=="__main__":
    if len(sys.argv)!=3:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_d2_basis_oracle ORIGINAL_ROOT REPORT_DIR")
    print(json.dumps(verify(*sys.argv[1:]),sort_keys=True))
