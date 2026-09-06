from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import point_in_time_liquid_view
from cryptoai_v13.opportunity import OpportunityBudget, additive_opportunity_targets
from cryptoai_v13.signals import StrategySpec, build_targets
from paper_once_v13 import apply_funding_quarantine, cap_targets
from paper_once_v15 import build_v15
from paper_once_v16 import build_v16
from paper_once_v99 import build_v99
from run_final_candidate import build_candidate

DASHBOARD = PROJECT / "dashboard"
REPORTS = PROJECT / "reports"
CONFIG = PROJECT / "config"
STATE = PROJECT / "state"
CANONICAL = PROJECT / "data" / "canonical"

ENGINE_META = {
    "v14": {
        "label": "V14",
        "name": "Maximum Capture",
        "role": "Agressivo",
        "description": "Captura de movimentos com overlay de oportunidade.",
    },
    "v15": {
        "label": "V15",
        "name": "Adaptive Capture",
        "role": "Adaptativo",
        "description": "Direção e universo adaptativos derivados do V14.",
    },
    "v16": {
        "label": "V16",
        "name": "Balanced Relaxed",
        "role": "Controle",
        "description": "Núcleo histórico usado como referência do V99 Frozen.",
    },
    "v99": {
        "label": "V99",
        "name": "Frozen Core + Alpha",
        "role": "Forward candidate",
        "description": "V16 core + satélite persistente ativado por consenso multihorizonte.",
    },
}


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def prepare_v15_runtime_from_published_state() -> None:
    """Recreate V15's ephemeral runtime config without rediscovering symbols.

    The dynamic universe state is a published paper artifact.  The dashboard
    must replay exactly that known universe instead of performing a fresh
    discovery that could leak today's membership into historical simulation.
    """
    runtime_path = CONFIG / "research_v15_runtime.json"
    universe_state = load_json(STATE / "paper_v15_universe.json", {}) or {}
    symbols = {}
    for symbol, item in universe_state.get("symbols", {}).items():
        price = CANONICAL / f"{symbol}_1h.csv"
        funding = CANONICAL / f"{symbol}_funding.csv"
        if price.exists() and price.stat().st_size and funding.exists():
            start_month = item.get("start_month")
            if start_month:
                symbols[str(symbol)] = str(start_month)
    if not symbols:
        raise RuntimeError(
            "V15 published universe has no symbols available in the canonical cache"
        )
    sync = load_json(REPORTS / "paper_data_sync_v15.json", {}) or {}
    latest_raw = sync.get("expected_latest_closed_hour")
    latest = pd.Timestamp(latest_raw) if latest_raw else pd.Timestamp.now(tz="UTC")
    payload = {
        "cutoff_month": latest.strftime("%Y-%m"),
        "interval": "1h",
        "market": "Binance USD-M perpetual futures",
        "source": "published V15 paper universe + canonical market cache",
        "universe_rule": "frozen published discovery state; no dashboard rediscovery",
        "symbols": symbols,
    }
    runtime_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def pct(value: float) -> float:
    return round(float(value) * 100.0, 6)


def summary(equity: pd.Series) -> dict:
    equity = equity.dropna()
    if len(equity) < 2:
        return {
            "returnPct": 0.0,
            "maxDrawdownPct": 0.0,
            "bestDayPct": 0.0,
            "worstDayPct": 0.0,
        }
    daily = equity.resample("1D").last().dropna()
    daily_returns = daily.pct_change(fill_method=None).dropna()
    drawdown = equity.div(equity.cummax()).sub(1.0)
    return {
        "returnPct": pct(equity.iloc[-1] / equity.iloc[0] - 1.0),
        "maxDrawdownPct": pct(drawdown.min()),
        "bestDayPct": pct(daily_returns.max()) if len(daily_returns) else 0.0,
        "worstDayPct": pct(daily_returns.min()) if len(daily_returns) else 0.0,
    }


def daily_curve(equity: pd.Series) -> list[dict]:
    daily = equity.resample("1D").last().dropna()
    if not len(daily):
        return []
    return [
        {"time": timestamp.isoformat(), "equity": round(float(value), 10)}
        for timestamp, value in daily.items()
    ]


def build_v14_history():
    candidate = load_json(CONFIG / "candidate_v14_max_capture.json")
    finalist = load_json(CONFIG / candidate["frozen_core_config"])
    base_config = load_json(CONFIG / finalist["base_candidate_config"])
    data, core_targets, _, _ = build_candidate(base_config)
    core_targets = cap_targets(core_targets, finalist["target_cap"])
    universe = base_config["point_in_time_universe"]
    signal_data, _ = point_in_time_liquid_view(
        data,
        top_n=universe["top_n"],
        lookback_hours=universe["quote_volume_lookback_hours"],
        minimum_history_hours=universe["minimum_history_hours"],
    )
    raw = build_targets(
        signal_data, StrategySpec(**candidate["opportunity"]["spec"])
    )
    allocation = candidate["allocation"]
    targets, _ = additive_opportunity_targets(
        core_targets,
        raw,
        OpportunityBudget(
            allocation["maximum_overlay_gross"],
            allocation["maximum_portfolio_gross"],
        ),
    )
    data, targets, _ = apply_funding_quarantine(data, targets)
    execution = base_config["execution"]
    guard = candidate["circuit_breaker"]
    result = exact_fast(
        data,
        targets,
        cost_per_side=execution["base_cost_per_side"],
        maintenance_equity_fraction=execution["maintenance_equity_fraction"],
        gross_guard_cap=allocation["gross_drift_guard_cap"],
        drawdown_guard_threshold=guard["drawdown_threshold"],
        drawdown_guard_multiplier=guard["exposure_multiplier"],
        drawdown_guard_cooldown_hours=guard["cooldown_hours"],
    )
    return result.equity


def paper_payload(engine: str) -> dict:
    meta = ENGINE_META[engine]
    snapshot = load_json(REPORTS / f"paper_{engine}_snapshot.json", {}) or {}
    ledger = load_json(REPORTS / f"paper_{engine}_ledger.json", {}) or {}
    base = float(ledger.get("base_capital_brl", 10000.0))
    ledger_summary = ledger.get("summary", {})
    current = float(
        ledger_summary.get(
            "current_capital_brl",
            base * float(snapshot.get("forward_equity_multiple", 1.0)),
        )
    )
    curve = ledger.get("equity_curve", [])
    compact_curve = [
        {
            "time": row.get("timestamp"),
            "capital": row.get(
                "capital_brl",
                base * float(row.get("equity_multiple", 1.0)),
            ),
        }
        for row in curve
        if row.get("timestamp")
    ]
    assets = ledger.get("assets", {})
    positions = sorted(
        [
            {
                "symbol": symbol,
                "direction": item.get("direction", "none"),
                "weightPct": round(
                    float(item.get("current_weight", 0.0)) * 100.0, 4
                ),
                "valueBrl": round(
                    float(item.get("position_value_brl", 0.0)), 2
                ),
            }
            for symbol, item in assets.items()
            if abs(float(item.get("current_weight", 0.0))) > 1e-8
        ],
        key=lambda item: abs(item["weightPct"]),
        reverse=True,
    )[:8]
    return {
        **meta,
        "track": engine,
        "candidate": snapshot.get(
            "candidate", ledger.get("candidate", meta["name"])
        ),
        "status": snapshot.get("status", "pending"),
        "paperStart": snapshot.get(
            "paper_start_after_timestamp",
            ledger.get("paper_start_after_timestamp"),
        ),
        "latest": snapshot.get(
            "latest_data_timestamp", ledger.get("latest_data_timestamp")
        ),
        "baseCapitalBrl": round(base, 2),
        "currentCapitalBrl": round(current, 2),
        "roiPct": round((current / base - 1.0) * 100.0, 4) if base else 0.0,
        "grossExposurePct": round(
            float(snapshot.get("gross_exposure", 0.0)) * 100.0, 4
        ),
        "newForwardHours": int(
            snapshot.get(
                "new_forward_hours",
                ledger_summary.get(
                    "new_forward_hours", max(0, len(compact_curve) - 1)
                ),
            )
        ),
        "positions": positions,
        "curve": compact_curve,
        "strictResearchGate": snapshot.get("strict_research_gate"),
        "forwardValidation": snapshot.get("forward_validation"),
        "satelliteWeightPct": round(
            float(snapshot.get("satellite_realized_weight", 0.0)) * 100.0, 3
        )
        if engine == "v99"
        else None,
        "satelliteTargetPct": round(
            float(snapshot.get("satellite_target_weight", 0.0)) * 100.0, 3
        )
        if engine == "v99"
        else None,
        "consensusPct": round(
            float(snapshot.get("consensus_vote_fraction", 0.0)) * 100.0, 2
        )
        if engine == "v99"
        else None,
    }


def main() -> None:
    prepare_v15_runtime_from_published_state()
    v14_equity = build_v14_history()
    _, _, _, v15_result, _, _, _ = build_v15()
    v16_candidate = load_json(
        CONFIG / "candidate_v16_experimental_balanced_relaxed.json"
    )
    _, _, v16_result, _, _ = build_v16(v16_candidate)
    v99_candidate = load_json(CONFIG / "candidate_v99_asymmetric.json")
    _, v99_frozen, _, _ = build_v99(v99_candidate)

    histories = {
        "v14": v14_equity,
        "v15": v15_result.equity,
        "v16": v16_result.equity,
        "v99": v99_frozen.equity,
    }
    backtest = {}
    for engine, equity in histories.items():
        backtest[engine] = {
            **ENGINE_META[engine],
            "track": engine,
            "summary": summary(equity),
            "curve": daily_curve(equity),
        }

    papers = {engine: paper_payload(engine) for engine in ENGINE_META}
    runtime = load_json(REPORTS / "paper_runtime_status.json", {}) or {}
    all_times = [
        pd.Timestamp(point["time"])
        for item in backtest.values()
        for point in item["curve"]
        if point.get("time")
    ]
    payload = {
        "schemaVersion": 2,
        "generatedAt": pd.Timestamp.now(tz="UTC").isoformat(),
        "mode": "PAPER_ONLY",
        "realOrders": False,
        "runtime": runtime,
        "paper": {
            "baseCapitalBrl": 10000,
            "engines": papers,
        },
        "backtest": {
            "availableFrom": min(all_times).isoformat() if all_times else None,
            "through": max(all_times).isoformat() if all_times else None,
            "presetsDays": [7, 30, 90, 180, 365],
            "engines": backtest,
            "disclosure": "Backtest usa replay histórico causal e custos modelados. Não é lucro real nem garantia de retorno futuro.",
        },
        "v99": {
            "architecture": v99_candidate["frozen_composite"],
            "status": v99_candidate["strict_research_gate"],
            "disclosure": v99_candidate["disclosure"],
        },
    }
    DASHBOARD.mkdir(exist_ok=True)
    (DASHBOARD / "dashboard_data.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {"generatedAt": payload["generatedAt"], "engines": list(backtest)},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
