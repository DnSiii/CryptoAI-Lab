from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import FuturesData
from paper_once_v15 import build_v15

REPORT_PATH = PROJECT / "reports" / "candidate_v99_r21_segregated_alpha.json"
HORIZONS = (7, 30, 90, 180, 365)


def stats(equity: pd.Series) -> dict:
    e = equity.dropna().astype(float)
    if len(e) < 2:
        return {"return": 0.0, "max_drawdown": 0.0, "best_day": 0.0,
                "worst_day": 0.0, "positive_days": 0.0}
    n = e / float(e.iloc[0])
    dd = n.div(n.cummax()).sub(1.0)
    daily = n.resample("1D").last().pct_change(fill_method=None).dropna()
    return {
        "return": float(n.iloc[-1] - 1.0),
        "max_drawdown": float(dd.min()),
        "best_day": float(daily.max()) if len(daily) else 0.0,
        "worst_day": float(daily.min()) if len(daily) else 0.0,
        "positive_days": float((daily > 0.0).mean()) if len(daily) else 0.0,
    }


def slice_data(data: FuturesData, start: pd.Timestamp, end: pd.Timestamp) -> FuturesData:
    return FuturesData(
        frames={k: v.loc[start:end].copy() for k, v in data.frames.items()},
        funding=data.funding.loc[start:end].copy(),
        symbols=data.symbols,
    )


def cap_gross(targets: pd.DataFrame, cap: float) -> pd.DataFrame:
    gross = targets.abs().sum(axis=1)
    factor = (cap / gross.replace(0.0, np.nan)).clip(upper=1.0).fillna(1.0)
    return targets.mul(factor, axis=0)


def run_exact(data, targets, execution, *, gross_cap, cost,
              dd_threshold=None, dd_multiplier=1.0, cooldown=None):
    return exact_fast(
        data,
        targets,
        cost_per_side=cost,
        maintenance_equity_fraction=execution["maintenance_equity_fraction"],
        gross_guard_cap=gross_cap,
        drawdown_guard_threshold=dd_threshold,
        drawdown_guard_multiplier=dd_multiplier,
        drawdown_guard_cooldown_hours=cooldown,
    )


def attack_mask(v15_equity: pd.Series, btc: pd.Series, strength: int) -> pd.Series:
    e = v15_equity.astype(float)
    e7 = e.div(e.shift(24 * 7)).sub(1.0)
    e30 = e.div(e.shift(24 * 30)).sub(1.0)
    e90 = e.div(e.shift(24 * 90)).sub(1.0)
    edd = e.div(e.cummax()).sub(1.0)
    b7 = btc.div(btc.shift(24 * 7)).sub(1.0)
    b30 = btc.div(btc.shift(24 * 30)).sub(1.0)
    ema = btc.ewm(span=336, adjust=False, min_periods=336).mean()
    vol7 = btc.pct_change(fill_method=None).rolling(24 * 7, min_periods=48).std()
    vol30 = btc.pct_change(fill_method=None).rolling(24 * 30, min_periods=168).std()

    if strength == 1:
        mask = (e7 > 0.015) & (e30 > 0.04) & (edd > -0.05) & (btc > ema)
    elif strength == 2:
        mask = (e7 > 0.025) & (e30 > 0.06) & (e90 > 0.08) & (edd > -0.04) & (btc > ema) & (b30 > 0.0)
    else:
        mask = (e7 > 0.04) & (e30 > 0.08) & (e90 > 0.12) & (edd > -0.03) & (btc > ema) & (b7 > 0.0) & (b30 > 0.02) & ((vol7 < 1.35 * vol30) | vol30.isna())
    return mask.fillna(False)


def satellite_targets(v15_targets: pd.DataFrame, mask: pd.Series, scale: float, cap: float) -> pd.DataFrame:
    # mask at close t determines target that exact_fast executes at open t+1.
    t = v15_targets.mul(mask.astype(float), axis=0).mul(float(scale))
    return cap_gross(t, cap)


def combine_rebalanced(core: pd.Series, sat: pd.Series, sat_weight: float,
                       rebalance_hours: int, transfer_cost: float = 0.0010) -> pd.Series:
    idx = core.index.intersection(sat.index)
    rc = core.reindex(idx).pct_change(fill_method=None).fillna(0.0)
    rs = sat.reindex(idx).pct_change(fill_method=None).fillna(0.0)
    total = 1.0
    core_cap = total * (1.0 - sat_weight)
    sat_cap = total * sat_weight
    out = pd.Series(index=idx, dtype=float)
    if len(idx):
        out.iloc[0] = 1.0
    for i in range(1, len(idx)):
        core_cap *= max(0.0, 1.0 + float(rc.iloc[i]))
        sat_cap *= max(0.0, 1.0 + float(rs.iloc[i]))
        total = core_cap + sat_cap
        if total <= 0.0:
            out.iloc[i:] = 0.0
            break
        if rebalance_hours > 0 and i % rebalance_hours == 0:
            desired_sat = total * sat_weight
            moved = abs(desired_sat - sat_cap)
            total -= moved * transfer_cost
            sat_cap = total * sat_weight
            core_cap = total - sat_cap
        out.iloc[i] = core_cap + sat_cap
    return out.ffill().fillna(1.0)


def normalize_window(e: pd.Series, start, end):
    s = e.loc[start:end]
    return s / float(s.iloc[0]) if len(s) else s


def portfolio_on_slice(data, v15_targets, sat_targets, execution, base_guard, base_gross,
                       sat_params, portfolio_params, start, end, cost):
    d = slice_data(data, start, end)
    core_t = v15_targets.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    sat_t = sat_targets.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    core = run_exact(
        d, core_t, execution,
        gross_cap=base_gross, cost=cost,
        dd_threshold=base_guard["drawdown_threshold"],
        dd_multiplier=base_guard["exposure_multiplier"],
        cooldown=base_guard["cooldown_hours"],
    ).equity
    sat = run_exact(
        d, sat_t, execution,
        gross_cap=sat_params["gross_cap"], cost=cost,
        dd_threshold=sat_params["dd_threshold"],
        dd_multiplier=sat_params["dd_multiplier"],
        cooldown=sat_params["cooldown"],
    ).equity
    return combine_rebalanced(
        core, sat,
        portfolio_params["sat_weight"],
        portfolio_params["rebalance_hours"],
        portfolio_params["transfer_cost"],
    )


def main() -> None:
    candidate, data, v15_targets, _, _, quarantined, metadata = build_v15()
    v14 = json.loads((PROJECT / "config" / candidate["parent_candidate_config"]).read_text())
    finalist = json.loads((PROJECT / "config" / v14["frozen_core_config"]).read_text())
    base = json.loads((PROJECT / "config" / finalist["base_candidate_config"]).read_text())
    execution = base["execution"]
    guard = v14["circuit_breaker"]
    base_gross = float(v14["allocation"]["gross_drift_guard_cap"])
    base_cost = float(execution["base_cost_per_side"])
    severe_cost = float(execution["severe_cost_per_side"])

    core = run_exact(
        data, v15_targets, execution, gross_cap=base_gross, cost=base_cost,
        dd_threshold=guard["drawdown_threshold"], dd_multiplier=guard["exposure_multiplier"],
        cooldown=guard["cooldown_hours"],
    ).equity
    core_severe = run_exact(
        data, v15_targets, execution, gross_cap=base_gross, cost=severe_cost,
        dd_threshold=guard["drawdown_threshold"], dd_multiplier=guard["exposure_multiplier"],
        cooldown=guard["cooldown_hours"],
    ).equity
    core_stats = stats(core)
    core_severe_stats = stats(core_severe)

    btc = data.close["BTCUSDT"]
    masks = {s: attack_mask(core.reindex(v15_targets.index).ffill(), btc, s) for s in (1, 2, 3)}

    satellite_defs = []
    for strength, scale, cap, dd_threshold, dd_multiplier, cooldown in itertools.product(
        (1, 2, 3), (1.5, 2.0, 2.5), (1.8, 2.2, 2.6), (0.08, 0.12), (0.0, 0.25), (24, 72)
    ):
        if cap + 1e-12 < scale * 0.7:
            continue
        key = f"s{strength}_x{scale:.1f}_c{cap:.1f}_dd{dd_threshold:.2f}_m{dd_multiplier:.2f}_p{cooldown}"
        satellite_defs.append((key, strength, scale, cap, dd_threshold, dd_multiplier, cooldown))

    # Limit the expensive exact sweep using diverse definitions; all are causal.
    satellite_defs = satellite_defs[::2]
    sat_cache = {}
    rows = []
    split = int(len(data.close.index) * 0.60)
    train_end = data.close.index[split]
    hold_start = data.close.index[min(split + 1, len(data.close.index) - 1)]

    for key, strength, scale, cap, dd_threshold, dd_multiplier, cooldown in satellite_defs:
        t = satellite_targets(v15_targets, masks[strength], scale, cap)
        sat = run_exact(
            data, t, execution, gross_cap=cap + 0.10, cost=base_cost,
            dd_threshold=dd_threshold, dd_multiplier=dd_multiplier, cooldown=cooldown,
        ).equity
        sat_cache[key] = (t, sat, {
            "gross_cap": cap + 0.10,
            "dd_threshold": dd_threshold,
            "dd_multiplier": dd_multiplier,
            "cooldown": cooldown,
            "strength": strength,
            "scale": scale,
            "target_cap": cap,
        })
        for sat_weight, rebalance_hours in itertools.product((0.10, 0.15, 0.20, 0.25), (24 * 7, 24 * 30)):
            p = combine_rebalanced(core, sat, sat_weight, rebalance_hours)
            train = stats(normalize_window(p, p.index[0], train_end))
            hold = stats(normalize_window(p, hold_start, p.index[-1]))
            train_core = stats(normalize_window(core, core.index[0], train_end))
            hold_core = stats(normalize_window(core, hold_start, core.index[-1]))
            wealth_train = (1 + train["return"]) / max(1e-12, 1 + train_core["return"])
            wealth_hold = (1 + hold["return"]) / max(1e-12, 1 + hold_core["return"])
            dd_hold = abs(hold["max_drawdown"]) / max(1e-12, abs(hold_core["max_drawdown"]))
            worst_hold = abs(hold["worst_day"]) / max(1e-12, abs(hold_core["worst_day"]))
            score = (
                2.5 * np.log(max(wealth_train, 1e-12))
                + 4.0 * np.log(max(wealth_hold, 1e-12))
                + 1.5 * max(0.0, 1.0 - dd_hold)
                - 3.0 * max(0.0, dd_hold - 1.0)
                - 1.5 * max(0.0, worst_hold - 1.0)
            )
            rows.append({
                "key": f"{key}_w{sat_weight:.2f}_r{rebalance_hours}",
                "satellite_key": key,
                "sat_weight": sat_weight,
                "rebalance_hours": rebalance_hours,
                "train": train,
                "holdout": hold,
                "train_wealth_ratio_to_v15": float(wealth_train),
                "holdout_wealth_ratio_to_v15": float(wealth_hold),
                "holdout_drawdown_ratio_to_v15": float(dd_hold),
                "holdout_worst_day_ratio_to_v15": float(worst_hold),
                "score": float(score),
            })

    ranking = sorted(rows, key=lambda x: x["score"], reverse=True)
    finalists = []
    for row in ranking[:8]:
        t, sat, sp = sat_cache[row["satellite_key"]]
        pp = {"sat_weight": row["sat_weight"], "rebalance_hours": row["rebalance_hours"], "transfer_cost": 0.0010}
        full = combine_rebalanced(core, sat, pp["sat_weight"], pp["rebalance_hours"], pp["transfer_cost"])
        full_stats = stats(full)
        full_wealth = (1 + full_stats["return"]) / max(1e-12, 1 + core_stats["return"])
        full_dd = abs(full_stats["max_drawdown"]) / max(1e-12, abs(core_stats["max_drawdown"]))
        full_worst = abs(full_stats["worst_day"]) / max(1e-12, abs(core_stats["worst_day"]))

        iso = {}
        iso_core = {}
        iso_wins = {}
        iso_dd = {}
        end = data.close.index[-1]
        for days in HORIZONS:
            start = end - pd.Timedelta(days=int(days))
            peq = portfolio_on_slice(data, v15_targets, t, execution, guard, base_gross, sp, pp, start, end, base_cost)
            ceq = run_exact(
                slice_data(data, start, end),
                v15_targets.loc[start:end], execution,
                gross_cap=base_gross, cost=base_cost,
                dd_threshold=guard["drawdown_threshold"], dd_multiplier=guard["exposure_multiplier"],
                cooldown=guard["cooldown_hours"],
            ).equity
            iso[str(days)] = stats(peq)
            iso_core[str(days)] = stats(ceq)
            iso_wins[str(days)] = iso[str(days)]["return"] >= iso_core[str(days)]["return"]
            iso_dd[str(days)] = abs(iso[str(days)]["max_drawdown"]) <= abs(iso_core[str(days)]["max_drawdown"])

        sat_severe = run_exact(
            data, t, execution, gross_cap=sp["gross_cap"], cost=severe_cost,
            dd_threshold=sp["dd_threshold"], dd_multiplier=sp["dd_multiplier"], cooldown=sp["cooldown"],
        ).equity
        severe = combine_rebalanced(core_severe, sat_severe, pp["sat_weight"], pp["rebalance_hours"], pp["transfer_cost"])
        severe_stats = stats(severe)
        severe_ratio = (1 + severe_stats["return"]) / max(1e-12, 1 + core_severe_stats["return"])

        gate = bool(
            all(iso_wins.values())
            and full_wealth >= 1.20
            and full_dd <= 0.85
            and full_worst <= 0.90
            and row["holdout_wealth_ratio_to_v15"] >= 1.10
            and row["holdout_drawdown_ratio_to_v15"] <= 0.90
            and severe_ratio >= 1.10
        )
        finalists.append({
            **row,
            "satellite_params": sp,
            "portfolio_params": pp,
            "summary": full_stats,
            "wealth_ratio_to_v15": float(full_wealth),
            "drawdown_ratio_to_v15": float(full_dd),
            "worst_day_ratio_to_v15": float(full_worst),
            "isolated": iso,
            "isolated_v15": iso_core,
            "isolated_return_wins_vs_v15": iso_wins,
            "isolated_drawdown_wins_vs_v15": iso_dd,
            "severe_cost": severe_stats,
            "severe_wealth_ratio_to_v15": float(severe_ratio),
            "superior_gate_passed": gate,
        })

    finalists.sort(key=lambda x: (
        x["superior_gate_passed"],
        sum(x["isolated_return_wins_vs_v15"].values()),
        x["holdout_wealth_ratio_to_v15"],
        x["wealth_ratio_to_v15"],
        -x["drawdown_ratio_to_v15"],
    ), reverse=True)
    selected = finalists[0] if finalists else None
    report = {
        "study": "V99 R21 segregated alpha capital architecture",
        "status": "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective": "preserve V15 compounding while a separately risk-governed alpha sleeve attacks only strong causal regimes",
        "architecture": "core and satellite have separate exact replays and separate circuit-breaker state; capital is periodically rebalanced with transfer friction, preventing satellite losses from tripping the core guard",
        "selection_disclosure": "Parameters are historical research. A successful gate is not a profit guarantee and still requires freezing plus an independent forward boundary.",
        "satellite_count": len(satellite_defs),
        "portfolio_screen_count": len(rows),
        "v15": {"summary": core_stats, "severe_cost": core_severe_stats},
        "selected": selected,
        "finalists": finalists,
        "top_screen": ranking[:30],
        "promotion_rule": {
            "beat_v15_isolated_all_horizons": True,
            "full_wealth_ratio_minimum": 1.20,
            "full_drawdown_ratio_maximum": 0.85,
            "full_worst_day_ratio_maximum": 0.90,
            "holdout_wealth_ratio_minimum": 1.10,
            "holdout_drawdown_ratio_maximum": 0.90,
            "severe_cost_wealth_ratio_minimum": 1.10,
        },
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "study": report["study"],
        "satellite_count": report["satellite_count"],
        "portfolio_screen_count": report["portfolio_screen_count"],
        "v15": report["v15"],
        "selected": selected,
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
