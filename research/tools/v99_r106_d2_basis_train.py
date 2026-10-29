"""D2 preregistered BTC/ETH spot-perp basis-convergence TRAIN; pre-funding only.

Never reads validation/holdout. No orders, native fee claims or promotion.
See V99_R106_D2_BASIS_CONVERGENCE_COMPLETE_TRAIN_PREREG_20261029.md.
"""
from __future__ import annotations
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from research.verification.independent_d1_native_train_receipts import verify as verify_original

START = int(datetime(2021, 12, 9, tzinfo=timezone.utc).timestamp()*1000)
END = int(datetime(2023, 10, 1, tzinfo=timezone.utc).timestamp()*1000)
HOUR = 3600000
HOURS = (END-START)//HOUR
ASSETS = ("BTC", "ETH")
SCENARIOS = {"severe": .0007, "supersevere": .0014}
EDGES = [int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp()*1000) for s in
         ("2021-12-09T00:00:00", "2022-04-20T04:00:00",
          "2022-08-30T09:00:00", "2023-01-09T14:00:00",
          "2023-05-21T19:00:00", "2023-10-01T00:00:00")]
SCHEMA = "V99_R106_D2_BASIS_COMPLETE_TRAIN_V1"
NO_PROMOTION = dict(native_fee_tier_authenticated=False,
    settled_funding_cash_authenticated=False, execution_fills_authenticated=False,
    liquidation_margin_authenticated=False, original_economic_train_certified=False,
    independent_original_accounting_verified=False, freeze_authorized=False,
    promotion_authorized=False, validation_opened=False, holdout_opened=False,
    orders_enabled=False, paper_publication_authorized=False)

def load_original(root):
    root = Path(root)
    proof = verify_original(root)
    if proof["status"] != "INDEPENDENT_FOUR_LEG_TRAIN_SOURCE_COMPLETE_NO_ECONOMICS":
        raise ValueError("D2_ORIGINAL_TRAIN_PRICE_RECEIPTS_INCOMPLETE")
    series = {}
    for asset in ASSETS:
        for suffix in ("", "-SWAP"):
            inst = asset + "-USDT" + suffix
            rows = json.loads((root/inst/"train_opens.json").read_text())
            if len(rows) != HOURS or [x["ts"] for x in rows] != list(range(START, END, HOUR)):
                raise ValueError("D2_ORIGINAL_TRAIN_GRID_INCOMPLETE")
            values = [float(x["open"]) for x in rows]
            if any(not math.isfinite(x) or x <= 0 for x in values):
                raise ValueError("D2_INVALID_SOURCE_OPEN")
            series[inst] = values
    return series, proof

def _zscore(values):
    mean = sum(values)/len(values)
    variance = sum((v-mean)**2 for v in values)/len(values)
    return (values[-1]-mean)/math.sqrt(variance) if variance > 1e-24 else None

def _fold(ts):
    for i in range(5):
        if EDGES[i] <= ts < EDGES[i+1]:
            return i+1
    raise ValueError("D2_SEALED_OR_INVALID_FOLD_TIMESTAMP")

def _regime(series, i):
    if i < 169:
        return "SIDEWAYS_LOW_VOL"
    btc = series["BTC-USDT"]
    move = btc[i-1]/btc[i-169]-1
    state = "BULL" if move > .05 else "BEAR" if move < -.05 else "SIDEWAYS"
    ret = [btc[k]/btc[k-1]-1 for k in range(i-168, i)]
    avg = sum(ret)/168
    vol = math.sqrt(sum((x-avg)**2 for x in ret)/168)
    return state + ("_HIGH_VOL" if vol >= .01 else "_LOW_VOL")

def _metrics(rows, scenario, source_verified):
    prev = 1.
    peak = 1.
    worst_dd = 0.
    fold_factors = [1.]*5
    gains, losses, factors = [], [], []
    regime_counts = {s+"_"+v: 0 for s in ("BULL", "BEAR", "SIDEWAYS")
                     for v in ("LOW_VOL", "HIGH_VOL")}
    for row in rows:
        nav = row["nav"][scenario]
        if not math.isfinite(nav) or nav <= 0:
            raise ValueError("D2_CAPITAL_RUIN_OR_NONFINITE_NAV")
        delta = nav-prev
        if delta > 0: gains.append(delta)
        elif delta < 0: losses.append(-delta)
        factor = nav/prev
        factors.append(factor)
        fold_factors[row["fold"]-1] *= factor
        regime_counts[row["regime"]] += 1
        peak = max(peak, nav)
        worst_dd = min(worst_dd, nav/peak-1)
        prev = nav
    total = prev-1
    best_hour_removed = prev/max(factors)-1
    top = math.ceil(len(rows)/100)
    gain_share = sum(sorted(gains, reverse=True)[:top])/sum(gains) if gains else 1.
    loss_share = sum(sorted(losses, reverse=True)[:top])/sum(losses) if losses else 0.
    pf = sum(gains)/sum(losses) if losses else (float("inf") if gains else 0.)
    benchmark = rows[-1]["benchmark"]-1
    positives = sum(x > 1 for x in fold_factors)
    gates = dict(positive_total=total>0,
        positive_folds=positives >= (4 if scenario=="severe" else 3),
        profit_factor=pf>1, remove_best_hour_positive=best_hour_removed>0,
        max_drawdown=worst_dd>=-.35, top_1pct_gain_share=gain_share<=.40,
        worst_1pct_loss_share=loss_share<=.50,
        beats_cash_and_50_50_spot=total>max(0., benchmark),
        six_regimes_present=all(regime_counts.values()),
        executed_trades=any(row["events"] for row in rows))
    return dict(roi_pre_funding=total, positive_folds=positives,
        fold_roi=[x-1 for x in fold_factors], max_drawdown=worst_dd,
        profit_factor=pf if math.isfinite(pf) else "infinite",
        remove_best_hour_roi=best_hour_removed, gain_share_top_1pct=gain_share,
        loss_share_worst_1pct=loss_share, benchmark_50_50_spot_roi=benchmark,
        regime_counts=regime_counts, gates=gates, numeric_pass=all(gates.values()),
        original_source_verified=source_verified, funding_and_native_costs_certified=False)

def simulate(series, *, source_verified=False):
    if set(series) != {a+"-USDT"+s for a in ASSETS for s in ("", "-SWAP")}:
        raise ValueError("D2_FOUR_ORIGINAL_LEGS_REQUIRED")
    if any(len(v)!=HOURS or any(not math.isfinite(x) or x<=0 for x in v)
           for v in series.values()):
        raise ValueError("D2_FULL_TRAIN_PRICE_GRID_REQUIRED")
    basis = {a: [p/s-1 for s,p in zip(series[a+"-USDT"], series[a+"-USDT-SWAP"])]
             for a in ASSETS}
    nav = {s:1. for s in SCENARIOS}
    active = {}
    rows = []
    total_events = 0
    for i in range(HOURS):
        ts = START+i*HOUR
        pnl = 0.
        if i:
            for asset, pos in active.items():
                q = pos["qty"]
                spot = series[asset+"-USDT"]
                perp = series[asset+"-USDT-SWAP"]
                pnl += q*((spot[i]-spot[i-1])-(perp[i]-perp[i-1]))
        events = []
        fees = {s:0. for s in SCENARIOS}
        for asset in ASSETS:
            spot = series[asset+"-USDT"][i]
            perp = series[asset+"-USDT-SWAP"][i]
            z = _zscore(basis[asset][i-168:i]) if i>=168 else None
            old = active.get(asset)
            terminal = i == HOURS-1
            exit_due = old is not None and (terminal or i-old["entry_i"]>=168
                                           or (z is not None and z<=.5))
            if exit_due:
                qty = old["qty"]
                events.append(dict(kind="EXIT", asset=asset, qty=qty,
                    reason="TRAIN_TERMINAL" if terminal else
                    ("MAX_HOLD" if i-old["entry_i"]>=168 else "BASIS_CONVERGENCE")))
                for s, rate in SCENARIOS.items():
                    fees[s] += rate*qty*(spot+perp)
                del active[asset]
            if (not terminal and asset not in active and i>=168 and
                    z is not None and z>=2. and basis[asset][i-1]>0):
                qty = .25/max(spot,perp)
                active[asset] = dict(qty=qty, entry_i=i)
                events.append(dict(kind="OPEN", asset=asset, qty=qty,
                                   reason="POSITIVE_BASIS_EXTREME"))
                for s, rate in SCENARIOS.items():
                    fees[s] += rate*qty*(spot+perp)
        for s in SCENARIOS:
            nav[s] += pnl-fees[s]
            if not math.isfinite(nav[s]) or nav[s]<=0:
                raise ValueError("D2_CAPITAL_RUIN_OR_NONFINITE_NAV")
        gross = sum(p["qty"]*(series[a+"-USDT"][i]+series[a+"-USDT-SWAP"][i])
                    for a,p in active.items())
        if gross > 1.50:  # mark-to-market can exceed initial 1.0, never new leverage.
            raise ValueError("D2_EXCESSIVE_MARKED_GROSS_RISK")
        benchmark = .5*(series["BTC-USDT"][i]/series["BTC-USDT"][0]+
                        series["ETH-USDT"][i]/series["ETH-USDT"][0])
        rows.append(dict(ts_ms=ts, fold=_fold(ts), regime=_regime(series,i),
            benchmark=benchmark, pnl=pnl, fees=fees.copy(), nav=nav.copy(),
            events=events, active={a:p.copy() for a,p in active.items()},
            gross=gross))
        total_events += len(events)
    if active:
        raise ValueError("D2_TRAIN_NOT_FLAT_AT_END")
    metrics = {s:_metrics(rows,s,source_verified) for s in SCENARIOS}
    return dict(schema=SCHEMA, status="PRE_FUNDING_TRAIN_ONLY_NOT_EXCHANGE_CERTIFIED",
        original_train_hours=HOURS, event_count=total_events,
        full_hourly_journal=rows, metrics=metrics,
        numeric_pass_both=all(m["numeric_pass"] for m in metrics.values()),
        source_verified=source_verified, no_orders=True, **NO_PROMOTION)

def main(root, output):
    series, proof = load_original(root)
    report = simulate(series, source_verified=True)
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    journal = report.pop("full_hourly_journal")
    (out/"d2_hourly_journal.json").write_text(json.dumps(journal, allow_nan=False))
    (out/"d2_train_report.json").write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    print(json.dumps({k:report[k] for k in ("status","original_train_hours","event_count",
        "numeric_pass_both","metrics","promotion_authorized")},sort_keys=True))
    return report

if __name__=="__main__":
    if len(sys.argv)!=3:
        raise SystemExit("usage: python -m research.tools.v99_r106_d2_basis_train ORIGINAL_FOUR_LEG_ROOT OUTPUT_DIR")
    main(*sys.argv[1:])
