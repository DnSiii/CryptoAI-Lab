from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data
from cryptoai_v13.metrics import slice_summary
from run_canonical_risk_stress import cap_targets
from search_dynamic_circuit_breaker import circuit_breaker_bootstrap


START = "2021-01-01"
END = "2026-07-31 23:00"
REPORT_PATH = PROJECT / "reports" / "candidate_v13_circuit_breaker_validation.json"
EQUITY_PATH = PROJECT / "reports" / "candidate_v13_circuit_breaker_equity.csv"


def metric(result) -> dict:
    return slice_summary(
        result.equity, result.turnover, result.gross_exposure, START, END
    )


def checkpoint(report: dict) -> None:
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n")


def main() -> None:
    finalist = json.loads(
        (PROJECT / "config" / "candidate_v13_circuit_breaker.json").read_text()
    )
    base_config = json.loads(
        (PROJECT / "config" / finalist["base_candidate_config"]).read_text()
    )
    data = load_data(PROJECT, base_config["data_config"])
    raw_targets = pd.read_csv(
        PROJECT / "reports" / "candidate_v13_pit_carry_core_targets.csv",
        index_col=0,
        parse_dates=True,
    )
    raw_targets.index = pd.to_datetime(raw_targets.index, utc=True)
    raw_targets = raw_targets.reindex(
        index=data.close.index, columns=data.close.columns
    ).fillna(0.0)
    targets = cap_targets(raw_targets, finalist["target_cap"])
    execution = base_config["execution"]
    guard = finalist["circuit_breaker"]
    guard_kwargs = {
        "drawdown_guard_threshold": guard["drawdown_threshold"],
        "drawdown_guard_multiplier": guard["exposure_multiplier"],
        "drawdown_guard_cooldown_hours": guard["cooldown_hours"],
    }
    report = {
        "status": "in_progress",
        "candidate": finalist,
        "historical_disclosure": (
            "All available historical data participated in iterative research. "
            "This is adversarial evidence, not a pristine untouched holdout. "
            "Forward paper trading remains mandatory."
        ),
        "scenarios": {},
        "bootstrap": {"status": "pending", "designs": {}},
    }
    checkpoint(report)

    unguarded_base = exact_fast(
        data,
        targets,
        execution["base_cost_per_side"],
        execution["maintenance_equity_fraction"],
        gross_guard_cap=finalist["gross_guard_cap"],
    )
    scenarios = (
        ("base", execution["base_cost_per_side"], 0, 1.0, 1.0),
        ("severe_cost", execution["severe_cost_per_side"], 0, 1.0, 1.0),
        ("extreme_cost_20bps", 0.0020, 0, 1.0, 1.0),
        ("delay_3h", execution["base_cost_per_side"], 2, 1.0, 1.0),
        ("delay_6h", execution["base_cost_per_side"], 5, 1.0, 1.0),
        ("adverse_funding", execution["base_cost_per_side"], 0, 2.0, 0.5),
        ("harsh_funding", execution["base_cost_per_side"], 0, 3.0, 0.0),
        ("severe_cost_and_adverse_funding", execution["severe_cost_per_side"], 0, 2.0, 0.5),
    )
    base_result = None
    for name, cost, delay, debit, credit in scenarios:
        print(f"starting {name}", flush=True)
        result = exact_fast(
            data,
            targets.shift(delay).fillna(0.0),
            cost,
            execution["maintenance_equity_fraction"],
            gross_guard_cap=finalist["gross_guard_cap"],
            funding_debit_multiplier=debit,
            funding_credit_multiplier=credit,
            **guard_kwargs,
        )
        if name == "base":
            base_result = result
            result.equity.rename("equity").rename_axis("timestamp").to_csv(
                EQUITY_PATH
            )
        report["scenarios"][name] = metric(result)
        checkpoint(report)
        print(
            f"completed {name}: CAGR={report['scenarios'][name]['cagr']:.4f} "
            f"DD={report['scenarios'][name]['max_drawdown']:.4f}",
            flush=True,
        )
    assert base_result is not None

    report["bootstrap"]["status"] = "in_progress"
    checkpoint(report)
    for block_days in (7, 14, 30):
        for horizon_years in (3, 5):
            name = f"block_{block_days}d_horizon_{horizon_years}y"
            print(f"starting bootstrap {name}", flush=True)
            risk = circuit_breaker_bootstrap(
                unguarded_base.equity,
                guard["drawdown_threshold"],
                guard["exposure_multiplier"],
                guard["cooldown_hours"] // 24,
                paths=30_000,
                block_days=block_days,
                horizon_years=horizon_years,
            )
            report["bootstrap"]["designs"][name] = risk
            checkpoint(report)
            print(
                f"completed bootstrap {name}: "
                f"ruin={risk['estimated_ruin_probability']:.6f}",
                flush=True,
            )
    report["bootstrap"]["worst_estimated_ruin_probability"] = max(
        item["estimated_ruin_probability"]
        for item in report["bootstrap"]["designs"].values()
    )
    report["bootstrap"]["status"] = "completed"
    base = report["scenarios"]["base"]
    severe = report["scenarios"]["severe_cost"]
    delay = report["scenarios"]["delay_3h"]
    adverse = report["scenarios"]["adverse_funding"]
    combined = report["scenarios"]["severe_cost_and_adverse_funding"]
    report["gate_snapshot"] = {
        "base_cagr_at_least_50pct": base["cagr"] >= 0.50,
        "base_drawdown_no_worse_than_35pct": base["max_drawdown"] >= -0.35,
        "all_base_years_positive": min(base["annual_returns"].values()) > 0.0,
        "severe_cost_cagr_at_least_35pct": severe["cagr"] >= 0.35,
        "delay_3h_cagr_at_least_40pct": delay["cagr"] >= 0.40,
        "adverse_funding_cagr_at_least_35pct": adverse["cagr"] >= 0.35,
        "combined_stress_cagr_at_least_25pct": combined["cagr"] >= 0.25,
        "bootstrap_ruin_below_1pct": (
            report["bootstrap"]["worst_estimated_ruin_probability"] < 0.01
        ),
        "no_exact_ruin": all(
            not scenario["ruin"] for scenario in report["scenarios"].values()
        ),
        "gross_exposure_within_1_5x": base["max_gross_exposure"] <= 1.505,
    }
    report["status"] = "completed"
    checkpoint(report)
    print(json.dumps({
        "scenarios": report["scenarios"],
        "bootstrap_worst": report["bootstrap"]["worst_estimated_ruin_probability"],
        "gates": report["gate_snapshot"],
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
