"""Read-only market input, exact V16 research, no paper publication.

This command never calls a paper runner's main() or a market synchronizer.
Outputs are research evidence only. Existing engine/config/paper files are
hashed before and after. Historical data already researched is NOT a holdout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(PROJECT / "src"), str(PROJECT / "scripts")]
from cryptoai_v13.data import FuturesData, load_data, point_in_time_liquid_view
from cryptoai_v13.backtest import exact_fast, screen
from cryptoai_v13.allocator import convex_equity_overlay, multihorizon_two_sleeve_targets
from cryptoai_v13.opportunity import OpportunityBudget, additive_opportunity_targets
from cryptoai_v13.signals import StrategySpec, build_targets
from cryptoai_v13.v16 import trailing_profit_lock_targets
import run_final_candidate
from paper_once_v13 import cap_targets


def hashes(root: Path) -> dict:
    result = {}
    for folder in ("src", "config", "state", "reports", "scripts"):
        for path in sorted((root / folder).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                result[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def subset(data: FuturesData, start=None, end=None) -> FuturesData:
    if start is not None:
        start = pd.Timestamp(start)
        start = start.tz_localize("UTC") if start.tzinfo is None else start.tz_convert("UTC")
    if end is not None:
        end = pd.Timestamp(end)
        end = end.tz_localize("UTC") if end.tzinfo is None else end.tz_convert("UTC")
    return FuturesData({k: v.loc[start:end].copy() for k, v in data.frames.items()},
                       data.funding.loc[start:end].copy(), data.symbols)


def metrics(equity: pd.Series, start, end) -> dict:
    """Include the boundary equity and every daily return (incl. first day)."""
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    before = equity.loc[equity.index < start].dropna()
    sel = equity.loc[start:end].dropna()
    if before.empty or sel.empty:
        raise ValueError("missing pre-period equity or evaluation data")
    base = float(before.iloc[-1])
    curve = pd.concat([before.iloc[-1:], sel]) / base
    daily_equity = curve.resample("D").last().dropna()
    daily = daily_equity.pct_change(fill_method=None).iloc[1:]
    total = float(curve.iloc[-1] - 1)
    dd = float((curve / curve.cummax() - 1).min())
    month = daily.groupby(daily.index.strftime("%Y-%m")).apply(lambda x: float((1+x).prod()-1))
    return {
        "start": start.isoformat(), "end": end.isoformat(), "days": len(daily),
        "return": total, "max_drawdown": dd,
        "return_over_drawdown": total / abs(dd) if dd else None,
        "best_day": float(daily.max()), "worst_day": float(daily.min()),
        "positive_days": int((daily > 0).sum()), "negative_days": int((daily < 0).sum()),
        "without_best_day": float((1 + daily.drop(daily.idxmax())).prod()-1),
        "without_best_3_days": float((1+daily.drop(daily.nlargest(min(3,len(daily))).index)).prod()-1),
        "monthly": month.to_dict(),
        "worst_7d": float((daily_equity / daily_equity.shift(7) - 1).min()) if len(daily)>=7 else None,
        "worst_30d": float((daily_equity / daily_equity.shift(30) - 1).min()) if len(daily)>=30 else None,
        "positive_rolling_30d": float(((daily_equity / daily_equity.shift(30)-1).dropna()>0).mean()) if len(daily)>=30 else None,
        "sharpe_daily": float(daily.mean()/daily.std()*np.sqrt(365)) if daily.std()>0 else None,
    }


def windows(equity: pd.Series, end: pd.Timestamp) -> dict:
    next_day = end.floor("D") + pd.Timedelta(days=1)
    starts = {"1Y": next_day-pd.DateOffset(years=1),
              "6M": next_day-pd.DateOffset(months=6),
              "3M": next_day-pd.DateOffset(months=3),
              "30D": next_day-pd.Timedelta(days=30),
              "7D": next_day-pd.Timedelta(days=7)}
    return {name: metrics(equity, start, end) for name,start in starts.items()}


def build_baselines(market: Path, end: pd.Timestamp):
    # Only redirect read paths in this process. No source file mutation.
    run_final_candidate.PROJECT = market
    core_config = json.loads((PROJECT/"config/candidate_v13_circuit_breaker.json").read_text())
    base_config = json.loads((PROJECT/"config"/core_config["base_candidate_config"]).read_text())
    data, core, _, _ = run_final_candidate.build_candidate(base_config)
    data = subset(data, "2025-01-01", end)
    core = cap_targets(core.reindex_like(data.close).fillna(0), core_config["target_cap"])
    signal, _ = point_in_time_liquid_view(data, 20, 720, 720)
    attack_config = json.loads((PROJECT/"config/candidate_v14_max_capture.json").read_text())
    raw = build_targets(signal, StrategySpec(**attack_config["opportunity"]["spec"]))
    a = attack_config["allocation"]
    attack, _ = additive_opportunity_targets(core, raw, OpportunityBudget(a["maximum_overlay_gross"], a["maximum_portfolio_gross"]))
    v16 = json.loads((PROJECT/"config/candidate_v16_experimental_balanced_relaxed.json").read_text())
    alloc = v16["allocator"]
    core_ret = screen(data, core).equity.pct_change(fill_method=None).fillna(0)
    attack_ret = screen(data, attack).equity.pct_change(fill_method=None).fillna(0)
    mixed = multihorizon_two_sleeve_targets(core, attack, core_ret, attack_ret,
        windows_days=tuple(alloc["windows_days"]),
        funding_weight_when_leading=alloc["core_weight_when_leading"],
        funding_weight_when_lagging=alloc["core_weight_when_lagging"],
        rebalance_hours=alloc["rebalance_hours"])
    convex = convex_equity_overlay(mixed, screen(data, mixed).equity, **v16["convex_overlay"])
    locked, _ = trailing_profit_lock_targets(convex, screen(data, convex).equity, **v16["profit_lock"])
    return data, {"v13": (core, core_config), "v14": (attack, attack_config), "v16_previous": (locked, v16)}


def audit_market(data: FuturesData) -> dict:
    report = {}
    for symbol in data.symbols:
        p = data.close[symbol].dropna()
        if p.empty:
            report[symbol] = {"rows":0}
            continue
        expected = pd.date_range(p.index[0], p.index[-1], freq="h")
        holes = expected.difference(p.index)
        report[symbol] = {"first":p.index[0].isoformat(), "last":p.index[-1].isoformat(),
            "rows":len(p), "internal_missing_hours":len(holes),
            "funding_events":int((data.funding[symbol]!=0).sum()),
            "largest_abs_hour_move":float(p.pct_change(fill_method=None).abs().max())}
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--market-root", type=Path, required=True)
    parser.add_argument("--end", default="2026-08-31")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(args.market_root.resolve()):
        raise ValueError("refuse writing in read-only input root")
    before = hashes(args.market_root)
    end = pd.Timestamp(args.end, tz="UTC") + pd.Timedelta(hours=23)
    print("Building native baseline targets", flush=True)
    data, models = build_baselines(args.market_root, end)
    execution_start = pd.Timestamp("2025-09-01",tz="UTC")-pd.Timedelta(days=240)
    execution = subset(data, execution_start)
    results = {}
    for name, (target, config) in models.items():
        guard = config["circuit_breaker"]
        result = exact_fast(execution, target.loc[execution_start:],
            gross_guard_cap=config.get("gross_guard_cap",config.get("allocation",guard).get("gross_drift_guard_cap",2.0)),
            drawdown_guard_threshold=guard["drawdown_threshold"],
            drawdown_guard_multiplier=guard["exposure_multiplier"],
            drawdown_guard_cooldown_hours=guard["cooldown_hours"])
        results[name] = {"windows":windows(result.equity,end), "ruin":result.ruin}
        start = end.floor("D")+pd.Timedelta(days=1)-pd.DateOffset(years=1)
        results[name]["attribution"] = {
            "gross": result.asset_gross.loc[start:end].sum().to_dict(),
            "fees": result.asset_fees.loc[start:end].sum().to_dict(),
            "funding_cost": result.asset_funding.loc[start:end].sum().to_dict(),
        }
        print(name, {k:round(v["return"]*100,3) for k,v in results[name]["windows"].items()}, flush=True)
    after=hashes(args.market_root)
    if before != after:
        raise RuntimeError("read-only source integrity changed during research")
    output={"status":"BASELINE_NOT_APPROVAL", "end":end.isoformat(),
        "history_is_previously_researched":True,"read_only_input_preserved":True,
        "market_root":str(args.market_root),"market_audit":audit_market(data),"results":results}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(output,indent=2,allow_nan=False)+"\n")

if __name__=="__main__":
    main()
