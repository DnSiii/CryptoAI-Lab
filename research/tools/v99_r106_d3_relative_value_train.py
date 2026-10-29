"""D3 one-shot preregistered BTC/ETH relative-value TRAIN; pre-funding only.

Research-only, no validation/holdout, no orders, no native fee/funding claims.
Preregistration commit: 3e5ddd2ab56381fa0ba88917757c7373c0daf3a9
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from research.verification.independent_d1_native_train_receipts import verify as verify_original

START = int(datetime(2021, 12, 9, tzinfo=timezone.utc).timestamp() * 1000)
END = int(datetime(2023, 10, 1, tzinfo=timezone.utc).timestamp() * 1000)
HOUR = 3600000
N = (END - START) // HOUR
WINDOW = 720
MAX_HOLD = 168
COOLDOWN = 168
RATES = {"severe": 0.0007, "supersevere": 0.0014}
FOLDS = [int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp()*1000) for s in
         ("2021-12-09T00:00:00", "2022-04-20T04:00:00",
          "2022-08-30T09:00:00", "2023-01-09T14:00:00",
          "2023-05-21T19:00:00", "2023-10-01T00:00:00")]
SCHEMA = "V99_R106_D3_RELATIVE_VALUE_COMPLETE_TRAIN_V1"
SAFETY = {key: False for key in (
    "native_fee_tier_authenticated", "settled_funding_cash_authenticated",
    "execution_fills_authenticated", "liquidation_margin_authenticated",
    "original_economic_train_certified", "freeze_authorized",
    "promotion_authorized", "validation_opened", "holdout_opened",
    "orders_enabled", "paper_publication_authorized")}

def load_original(root):
    root = Path(root)
    receipt = verify_original(root)
    if receipt.get("status") != "INDEPENDENT_FOUR_LEG_TRAIN_SOURCE_COMPLETE_NO_ECONOMICS":
        raise ValueError("D3_ORIGINAL_SOURCE_RECEIPT_FAILED")
    series = {}
    for asset in ("BTC-USDT", "ETH-USDT"):
        for suffix in ("", "-SWAP"):
            instrument = asset + suffix
            rows = json.loads((root / instrument / "train_opens.json").read_text())
            if len(rows) != N or any(row["ts"] != START + i*HOUR for i, row in enumerate(rows)):
                raise ValueError("D3_ORIGINAL_HOURLY_GRID_INCOMPLETE")
            vals = [float(row["open"]) for row in rows]
            if any(not math.isfinite(x) or x <= 0 for x in vals):
                raise ValueError("D3_ORIGINAL_OPEN_INVALID")
            series[instrument] = vals
    return series

def fold(ts):
    for k in range(5):
        if FOLDS[k] <= ts < FOLDS[k+1]:
            return k+1
    raise ValueError("D3_SEALED_OR_INVALID_TIMESTAMP")

def regime(btc, i):
    if i < 169:
        return "SIDEWAYS_LOW_VOL"
    trend = btc[i-1]/btc[i-169]-1
    state = "BULL" if trend > 0.05 else "BEAR" if trend < -0.05 else "SIDEWAYS"
    rets = [btc[k]/btc[k-1]-1 for k in range(i-168, i)]
    mu = sum(rets)/len(rets)
    sd = math.sqrt(sum((v-mu)**2 for v in rets)/len(rets))
    return state + ("_HIGH_VOL" if sd >= .01 else "_LOW_VOL")

def metrics(rows, scenario):
    capital_prev, peak, worst_dd = 1., 1., 0.
    folds = [1.]*5
    gain, loss, factors = [], [], []
    regimes = {a+"_"+b: 0 for a in ("BULL","BEAR","SIDEWAYS")
               for b in ("LOW_VOL","HIGH_VOL")}
    for row in rows:
        capital = row["nav"][scenario]
        if not math.isfinite(capital) or capital <= 0:
            raise ValueError("D3_CAPITAL_RUIN")
        change = capital-capital_prev
        if change > 0: gain.append(change)
        if change < 0: loss.append(-change)
        factor = capital/capital_prev
        factors.append(factor)
        folds[row["fold"]-1] *= factor
        peak = max(peak,capital)
        worst_dd = min(worst_dd,capital/peak-1)
        regimes[row["regime"]] += 1
        capital_prev = capital
    top = math.ceil(len(rows)/100)
    gain_share = sum(sorted(gain,reverse=True)[:top])/sum(gain) if gain else 1.
    loss_share = sum(sorted(loss,reverse=True)[:top])/sum(loss) if loss else 0.
    pf = sum(gain)/sum(loss) if loss else (float("inf") if gain else 0.)
    roi = capital_prev-1
    benchmark = rows[-1]["benchmark"]-1
    positive = sum(v>1 for v in folds)
    gates = {
        "positive_total": roi>0,
        "positive_folds": positive >= (4 if scenario=="severe" else 3),
        "profit_factor": pf>1,
        "max_drawdown": worst_dd>=-.35,
        "remove_best_hour_positive": capital_prev/max(factors)-1>0,
        "top_1pct_gain_share": gain_share<=.40,
        "worst_1pct_loss_share": loss_share<=.50,
        "beats_cash_and_spot_benchmark": roi>max(0.,benchmark),
        "six_regimes_present": all(regimes.values()),
        "completed_spread": any(e["kind"]=="EXIT" for row in rows for e in row["events"]),
    }
    return {"roi_pre_funding":roi, "fold_roi":[x-1 for x in folds],
            "positive_folds":positive,"max_drawdown":worst_dd,
            "profit_factor":pf if math.isfinite(pf) else "infinite",
            "remove_best_hour_roi":capital_prev/max(factors)-1,
            "gain_share_top_1pct":gain_share,"loss_share_worst_1pct":loss_share,
            "benchmark_50_50_spot_roi":benchmark,"regime_counts":regimes,
            "gates":gates,"numeric_pass":all(gates.values()),
            "funding_and_native_costs_certified":False}

def simulate(series, *, original_verified=False):
    expected={"BTC-USDT","ETH-USDT","BTC-USDT-SWAP","ETH-USDT-SWAP"}
    if set(series)!=expected or any(len(v)!=N or any(not math.isfinite(x) or x<=0 for x in v)
                                     for v in series.values()):
        raise ValueError("D3_FULL_FOUR_LEG_TRAIN_GRID_REQUIRED")
    btc,eth=series["BTC-USDT-SWAP"],series["ETH-USDT-SWAP"]
    ratio=[math.log(e/b) for e,b in zip(eth,btc)]
    nav={s:1. for s in RATES}
    active=None
    next_entry=WINDOW
    journal=[]
    event_count=0
    for i in range(N):
        ts=START+i*HOUR
        pnl=0.
        if i and active is not None:
            pnl=active["q_btc"]*(btc[i]-btc[i-1])+active["q_eth"]*(eth[i]-eth[i-1])
        z=None
        if i>=WINDOW:
            sample=ratio[i-WINDOW:i]
            mu=sum(sample)/WINDOW
            variance=sum((v-mu)**2 for v in sample)/WINDOW
            if variance>1e-24:
                z=(ratio[i-1]-mu)/math.sqrt(variance)
        terminal=i==N-1
        events=[]
        fees={s:0. for s in RATES}
        if active is not None and (terminal or i-active["entry_i"]>=MAX_HOLD
                                   or (z is not None and abs(z)<=.25)):
            for s,rate in RATES.items():
                fees[s]+=rate*(abs(active["q_btc"])*btc[i]+abs(active["q_eth"])*eth[i])
            events.append({"kind":"EXIT","q_btc":active["q_btc"],
                           "q_eth":active["q_eth"],"reason":"TERMINAL" if terminal else
                           ("MAX_HOLD" if i-active["entry_i"]>=MAX_HOLD else "RATIO_REVERSION")})
            active=None
            next_entry=i+COOLDOWN
        if active is None and not terminal and i>=next_entry and z is not None and abs(z)>=2:
            side=1 if z>=2 else -1
            # Rich ETH: short ETH / long BTC. Cheap ETH: reverse.
            q_btc=side*.20/btc[i]
            q_eth=-side*.20/eth[i]
            active={"q_btc":q_btc,"q_eth":q_eth,"entry_i":i}
            events.append({"kind":"OPEN","q_btc":q_btc,"q_eth":q_eth,
                           "reason":"RELATIVE_VALUE_DISLOCATION"})
            for s,rate in RATES.items():
                fees[s]+=rate*(abs(q_btc)*btc[i]+abs(q_eth)*eth[i])
        for s in RATES:
            nav[s]+=pnl-fees[s]
            if not math.isfinite(nav[s]) or nav[s]<=0:
                raise ValueError("D3_CAPITAL_RUIN")
        gross=(abs(active["q_btc"])*btc[i]+abs(active["q_eth"])*eth[i]) if active else 0.
        benchmark=.5*(series["BTC-USDT"][i]/series["BTC-USDT"][0]+
                      series["ETH-USDT"][i]/series["ETH-USDT"][0])
        journal.append({"ts_ms":ts,"fold":fold(ts),
                        "regime":regime(series["BTC-USDT"],i),
                        "z_lagged":z,"pnl":pnl,"fees":fees.copy(),
                        "nav":nav.copy(),"events":events,
                        "active":active.copy() if active else None,
                        "gross":gross,"benchmark":benchmark})
        event_count+=len(events)
    if active is not None: raise ValueError("D3_NOT_FLAT_AT_TRAIN_END")
    scores={s:metrics(journal,s) for s in RATES}
    return {"schema":SCHEMA,"status":"PRE_FUNDING_TRAIN_ONLY_NOT_EXCHANGE_CERTIFIED",
            "original_train_hours":N,"original_price_receipts_verified":original_verified,
            "event_count":event_count,"metrics":scores,
            "numeric_pass_both":all(m["numeric_pass"] for m in scores.values()),
            "full_hourly_journal":journal,**SAFETY}

def main(root,output):
    series=load_original(root)
    result=simulate(series,original_verified=True)
    dest=Path(output)
    dest.mkdir(parents=True,exist_ok=True)
    journal=result.pop("full_hourly_journal")
    (dest/"d3_hourly_journal.json").write_text(json.dumps(journal,allow_nan=False))
    (dest/"d3_train_report.json").write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False))
    print(json.dumps({"status":result["status"],"hours":N,"events":result["event_count"],
                      "metrics":result["metrics"],"numeric_pass_both":result["numeric_pass_both"],
                      "promotion_authorized":False},sort_keys=True))
    return result

if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("usage: python -m research.tools.v99_r106_d3_relative_value_train ORIGINAL_ROOT OUTPUT_DIR")
    main(*sys.argv[1:])
