from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

import build_cryptoai_dashboard as base
from cryptoai_v13.backtest import exact_fast

PROJECT = Path(__file__).resolve().parents[1]
DASHBOARD = PROJECT / "dashboard"
CONFIG = PROJECT / "config"
REPORTS = PROJECT / "reports"

V13_META = {
    "label": "V13",
    "name": "PIT Carry Core",
    "role": "Core",
    "description": "Núcleo point-in-time com carry, controle de exposição e circuit breaker.",
}


def build_v13_history():
    finalist = base.load_json(CONFIG / "candidate_v13_circuit_breaker.json")
    base_config = base.load_json(CONFIG / finalist["base_candidate_config"])
    data, targets, _, _ = base.build_candidate(base_config)
    targets = base.cap_targets(targets, finalist["target_cap"])
    data, targets, _ = base.apply_funding_quarantine(data, targets)
    execution = base_config["execution"]
    guard = finalist["circuit_breaker"]
    result = exact_fast(
        data,
        targets,
        cost_per_side=execution["base_cost_per_side"],
        maintenance_equity_fraction=execution["maintenance_equity_fraction"],
        gross_guard_cap=finalist["gross_guard_cap"],
        drawdown_guard_threshold=guard["drawdown_threshold"],
        drawdown_guard_multiplier=guard["exposure_multiplier"],
        drawdown_guard_cooldown_hours=guard["cooldown_hours"],
    )
    return result.equity


def main() -> None:
    # Extend the existing validated dashboard builder instead of duplicating the
    # engine implementations.  V13 becomes a first-class engine for both paper
    # and historical views.
    base.ENGINE_META = {"v13": V13_META, **base.ENGINE_META}
    base.prepare_v15_runtime_from_published_state()

    v13_equity = build_v13_history()
    v14_equity = base.build_v14_history()
    _, _, _, v15_result, _, _, _ = base.build_v15()
    v16_candidate = base.load_json(
        CONFIG / "candidate_v16_experimental_balanced_relaxed.json"
    )
    _, _, v16_result, _, _ = base.build_v16(v16_candidate)
    v99_candidate = base.load_json(CONFIG / "candidate_v99_asymmetric.json")
    _, v99_frozen, _, _ = base.build_v99(v99_candidate)

    histories = {
        "v13": v13_equity,
        "v14": v14_equity,
        "v15": v15_result.equity,
        "v16": v16_result.equity,
        "v99": v99_frozen.equity,
    }

    backtest = {}
    for engine, equity in histories.items():
        backtest[engine] = {
            **base.ENGINE_META[engine],
            "track": engine,
            "summary": base.summary(equity),
            "curve": base.daily_curve(equity),
        }

    papers = {engine: base.paper_payload(engine) for engine in base.ENGINE_META}
    runtime = base.load_json(REPORTS / "paper_runtime_status.json", {}) or {}
    all_times = [
        pd.Timestamp(point["time"])
        for item in backtest.values()
        for point in item["curve"]
        if point.get("time")
    ]

    payload = {
        "schemaVersion": 3,
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
    print(json.dumps({
        "generatedAt": payload["generatedAt"],
        "engines": list(backtest),
        "schemaVersion": payload["schemaVersion"],
    }, indent=2))


if __name__ == "__main__":
    main()
