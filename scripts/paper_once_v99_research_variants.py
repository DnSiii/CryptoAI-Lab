from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r105_all_regime_structural_audit as audit
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase2_bear_native_alpha as p2
import run_v99_r106_phase3_dispersion_breakout as p3
import run_v99_r106_phase4_bear_subregimes as p4
import run_v99_r106_phase7_train_validated_bhv_short_veto as p7

STATE_PATH = PROJECT / "state" / "paper_v99_research_state.json"
SNAPSHOT_PATH = PROJECT / "reports" / "paper_v99_research_snapshot.json"
LEDGER_PATH = PROJECT / "reports" / "paper_v99_research_ledger.json"
VERSION = "v99-research-five-v1"
BASE_CAPITAL_BRL = 10000.0

VARIANT_META = {
    "r98": {
        "label": "R98",
        "name": "Friction-Aware Hybrid",
        "status": "reference",
        "description": "Baseline estrutural forte anterior ao R106.",
    },
    "f1": {
        "label": "R106 F1",
        "name": "Native All-Regime Hybrid",
        "status": "research_rejected",
        "description": "Primeira integração nativa all-regime do R106.",
    },
    "f3": {
        "label": "R106 F3",
        "name": "Dispersion + Breakout Hybrid",
        "status": "research_rejected",
        "description": "Maior potência histórica entre os cinco acompanhados.",
    },
    "f7": {
        "label": "R106 F7/F9",
        "name": "Train-Validated BHV Short Veto",
        "status": "research_leader",
        "description": "Atual líder de pesquisa; F9 preservou exatamente o core F7.",
    },
    "f12": {
        "label": "R106 F12",
        "name": "BHV Crash State Gate",
        "status": "research_rejected",
        "description": "Experimento de veto no estado CRASH_CONTINUATION; reprovado no gate de treino.",
    },
}

# Snapshot dos resultados já validados. Estes números não são recalibrados pelo paper.
REFERENCE_BACKTEST = {
    "r98": {
        "historicalRoiPct": 33579.0,
        "holdoutRoiPct": 1069.86,
        "maxDrawdownPct": -32.18,
        "profitFactor": 1.696,
        "winRatePct": 26.68,
        "positiveDaysPct": 48.77,
        "payoff": 4.66,
        "severeRoiPct": None,
        "researchGate": "REFERENCE",
    },
    "f1": {
        "historicalRoiPct": 60523.0,
        "holdoutRoiPct": 882.95,
        "maxDrawdownPct": -41.26,
        "profitFactor": 1.585,
        "winRatePct": None,
        "positiveDaysPct": None,
        "payoff": None,
        "severeRoiPct": None,
        "researchGate": "REJECTED",
    },
    "f3": {
        "historicalRoiPct": 66782.0,
        "holdoutRoiPct": 1116.15,
        "maxDrawdownPct": -33.18,
        "profitFactor": 1.572,
        "winRatePct": 42.41,
        "positiveDaysPct": 47.91,
        "payoff": 2.13,
        "severeRoiPct": 18663.0,
        "researchGate": "REJECTED",
    },
    "f7": {
        "historicalRoiPct": 45928.2253,
        "holdoutRoiPct": 1185.1963,
        "maxDrawdownPct": -32.18494,
        "profitFactor": 1.720088,
        "winRatePct": 29.59262,
        "positiveDaysPct": 47.95585,
        "payoff": 4.09247,
        "severeRoiPct": 18968.0819,
        "researchGate": "CURRENT_RESEARCH_LEADER",
    },
    "f12": {
        "historicalRoiPct": 43382.08,
        "holdoutRoiPct": 1197.737,
        "maxDrawdownPct": -32.371,
        "profitFactor": 1.68865,
        "winRatePct": 30.62,
        "positiveDaysPct": 47.016,
        "payoff": 3.826,
        "severeRoiPct": 16844.0,
        "researchGate": "REJECTED_TRAIN_PARETO",
    },
}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_state() -> dict | None:
    if not STATE_PATH.exists():
        return None
    payload = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return payload if payload.get("version") == VERSION else None


def build_variants():
    cfg, data, raw, ex, guard, gross, quarantined, metadata = p1.r98.r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    direction, vol, _ = audit.classify_regimes(data.close)

    # R98: exact validated target stream.
    r98_targets, r98_result, _ = p1.build_r98_targets(
        data, raw, ex, guard, gross, base_cost
    )

    # F1: reproduce phase-1 train router and its side-aware controller.
    fixed = p1.fixed_sleeves(data)
    fixed_results = {
        name: p1.run_targets(data, targets, ex, guard, base_cost, p1.NATIVE_GROSS_CAP)
        for name, targets in fixed.items()
    }
    train_end = min(p1.TRAIN_END, data.close.index[-1])
    train_analyses = {
        name: audit.analyze_result(
            result, data, direction, vol, data.close.index[0], train_end
        )
        for name, result in fixed_results.items()
    }
    f1_routing, _ = p1.train_router(train_analyses)
    f1_native = p1.route_native(fixed, direction, vol, f1_routing)
    f1_native, _ = p1.side_aware_quality_controller(
        f1_native, data.close, direction, vol
    )
    f1_targets = p1.cap(
        r98_targets.add(f1_native * p1.HYBRID_ALPHA_SCALE, fill_value=0.0),
        p1.GROSS_CAP,
    )
    f1_targets, _ = p1.side_aware_quality_controller(
        f1_targets, data.close, direction, vol
    )
    f1_result = p1.run_targets(data, f1_targets, ex, guard, base_cost, p1.GROSS_CAP)

    # F3: reproduce its chronological stability router. TRAIN_END is fixed, so
    # future paper observations cannot alter the training decision.
    dispersion, _ = p3.bear_dispersion_targets(data, direction)
    breakout, _ = p3.breakout_targets(data)
    f3_sleeves = {**fixed, "bear_dispersion": dispersion, "breakout": breakout}
    f3_sleeve_results = {
        name: p1.run_targets(data, targets, ex, guard, base_cost, p1.NATIVE_GROSS_CAP)
        for name, targets in f3_sleeves.items()
    }
    f3_routing, _ = p2.stability_router(
        f3_sleeve_results,
        data,
        direction,
        vol,
        data.close.index[0],
        train_end,
    )
    f3_native = p1.route_native(f3_sleeves, direction, vol, f3_routing)
    f3_targets = p1.cap(
        r98_targets.add(f3_native * p1.HYBRID_ALPHA_SCALE, fill_value=0.0),
        p1.GROSS_CAP,
    )
    f3_result = p1.run_targets(data, f3_targets, ex, guard, base_cost, p1.GROSS_CAP)

    # F7/F9: the validated BHV short veto is frozen ON. F9 selected no extra
    # marginal native cells, so its candidate is exactly this F7 core.
    bhv = p7.bhv_mask(data.close.index, direction, vol)
    f7_targets = p7.short_veto_targets(r98_targets, bhv)
    f7_result = p1.run_targets(data, f7_targets, ex, guard, base_cost, p1.GROSS_CAP)

    # F12: reproduce the tested candidate, not a new optimized version. Its
    # train-selected state was CRASH_CONTINUATION; paper data never reselects it.
    substates = p4.bear_high_vol_substates(data.close, direction, vol)
    crash = substates["CRASH_CONTINUATION"].reindex(f7_targets.index).fillna(False)
    f12_targets = f7_targets.copy()
    f12_targets.loc[crash, :] = 0.0
    f12_result = p1.run_targets(data, f12_targets, ex, guard, base_cost, p1.GROSS_CAP)

    return data, {
        "r98": (r98_targets, r98_result),
        "f1": (f1_targets, f1_result),
        "f3": (f3_targets, f3_result),
        "f7": (f7_targets, f7_result),
        "f12": (f12_targets, f12_result),
    }, quarantined, metadata


def position_payload(row: pd.Series, capital: float) -> dict[str, dict]:
    payload: dict[str, dict] = {}
    for symbol, raw_weight in row.items():
        weight = float(raw_weight)
        if abs(weight) <= 1e-8:
            continue
        payload[str(symbol)] = {
            "direction": "buy" if weight > 0 else "sell",
            "current_weight": round(weight, 8),
            "position_value_brl": round(abs(weight) * capital, 2),
        }
    return payload


def variant_ledger(
    key: str,
    targets: pd.DataFrame,
    result,
    paper_start: pd.Timestamp,
    latest: pd.Timestamp,
) -> dict:
    equity = result.equity.dropna()
    if paper_start not in equity.index:
        eligible = equity.index[equity.index <= paper_start]
        if not len(eligible):
            raise RuntimeError(f"{key}: paper boundary precedes available equity")
        base_ts = eligible[-1]
    else:
        base_ts = paper_start
    effective_latest = min(latest, equity.index[-1])
    window = equity.loc[base_ts:effective_latest]
    if not len(window):
        raise RuntimeError(f"{key}: empty forward window")
    normalized = window / float(window.iloc[0])
    curve = []
    prior = BASE_CAPITAL_BRL
    for timestamp, multiple in normalized.items():
        capital = BASE_CAPITAL_BRL * float(multiple)
        curve.append(
            {
                "timestamp": timestamp.isoformat(),
                "equity_multiple": round(float(multiple), 10),
                "capital_brl": round(capital, 2),
                "hour_result_brl": round(capital - prior, 2) if curve else 0.0,
            }
        )
        prior = capital
    current = BASE_CAPITAL_BRL * float(normalized.iloc[-1])
    target_ts = targets.index[targets.index <= effective_latest][-1]
    assets = position_payload(targets.loc[target_ts], current)
    meta = VARIANT_META[key]
    return {
        "track": key,
        **meta,
        "base_capital_brl": BASE_CAPITAL_BRL,
        "paper_start_after_timestamp": paper_start.isoformat(),
        "effective_base_timestamp": base_ts.isoformat(),
        "latest_data_timestamp": effective_latest.isoformat(),
        "summary": {
            "new_forward_hours": max(0, len(window) - 1),
            "net_result_brl": round(current - BASE_CAPITAL_BRL, 2),
            "current_capital_brl": round(current, 2),
            "highest_capital_brl": round(BASE_CAPITAL_BRL * float(normalized.max()), 2),
            "lowest_capital_brl": round(BASE_CAPITAL_BRL * float(normalized.min()), 2),
            "forward_return_pct": round((float(normalized.iloc[-1]) - 1.0) * 100.0, 6),
            "gross_exposure_pct": round(sum(abs(float(x["current_weight"])) for x in assets.values()) * 100.0, 6),
        },
        "assets": assets,
        "equity_curve": curve,
        "real_orders_enabled": False,
    }


def main() -> None:
    data, variants, quarantined, metadata = build_variants()
    latest = data.close.index[-1]
    previous = load_state()
    initialized_at = (
        pd.Timestamp(previous["initialized_at_utc"])
        if previous
        else pd.Timestamp.now(tz="UTC")
    )
    paper_start = (
        pd.Timestamp(previous["paper_start_after_timestamp"])
        if previous
        else latest
    )
    if paper_start > latest:
        raise RuntimeError("paper boundary is newer than canonical market data")

    variant_ledgers = {
        key: variant_ledger(key, targets, result, paper_start, latest)
        for key, (targets, result) in variants.items()
    }
    state_variants = {
        key: {
            "label": item["label"],
            "status": "tracking" if latest > paper_start else "initialized",
            "current_capital_brl": item["summary"]["current_capital_brl"],
            "forward_return_pct": item["summary"]["forward_return_pct"],
            "gross_exposure_pct": item["summary"]["gross_exposure_pct"],
            "open_positions": len(item["assets"]),
        }
        for key, item in variant_ledgers.items()
    }
    state = {
        "schema_version": 1,
        "version": VERSION,
        "mode": "PAPER_ONLY",
        "real_orders_enabled": False,
        "initialized_at_utc": initialized_at.isoformat(),
        "paper_start_after_timestamp": paper_start.isoformat(),
        "latest_data_timestamp": latest.isoformat(),
        "same_boundary_for_all_variants": True,
        "selection_frozen_before_paper": True,
        "variants": state_variants,
        "funding_quarantined_symbols": quarantined,
        "metadata": metadata,
        "disclosure": "Forward-only simulated paper comparison. No real orders and no paper-data retuning.",
    }
    ledger = {
        "schema_version": 1,
        "version": VERSION,
        "mode": "PAPER_ONLY",
        "real_orders_enabled": False,
        "base_capital_brl": BASE_CAPITAL_BRL,
        "paper_start_after_timestamp": paper_start.isoformat(),
        "latest_data_timestamp": latest.isoformat(),
        "same_boundary_for_all_variants": True,
        "variants": variant_ledgers,
        "backtest_reference": {
            key: {**VARIANT_META[key], **REFERENCE_BACKTEST[key]}
            for key in VARIANT_META
        },
        "disclosure": "Backtest reference is frozen from the validated research reports; paper curves contain only observations after the shared boundary.",
    }
    write_json(STATE_PATH, state)
    write_json(SNAPSHOT_PATH, state)
    write_json(LEDGER_PATH, ledger)
    print(json.dumps(state, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
