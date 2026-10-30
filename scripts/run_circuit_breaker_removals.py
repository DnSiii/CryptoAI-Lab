from __future__ import annotations

import copy
import json
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.metrics import slice_summary
from run_canonical_risk_stress import cap_targets
from run_final_candidate import build_candidate


START = "2021-01-01"
END = "2026-07-31 23:00"
REPORT_PATH = PROJECT / "reports" / "candidate_v13_circuit_breaker_removals.json"


def metric(result) -> dict:
    return slice_summary(
        result.equity, result.turnover, result.gross_exposure, START, END
    )


def checkpoint(report: dict) -> None:
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n")


def main() -> None:
    config = json.loads(
        (PROJECT / "config" / "candidate_v13_pit_carry_core.json").read_text()
    )
    finalist = json.loads(
        (PROJECT / "config" / "candidate_v13_circuit_breaker.json").read_text()
    )
    guard = finalist["circuit_breaker"]
    execution = config["execution"]
    guard_kwargs = {
        "drawdown_guard_threshold": guard["drawdown_threshold"],
        "drawdown_guard_multiplier": guard["exposure_multiplier"],
        "drawdown_guard_cooldown_hours": guard["cooldown_hours"],
    }
    report = {
        "status": "in_progress",
        "method": (
            "Full target recomputation where the removed sleeve/component changes "
            "the strategy; exact causal replay with the finalist circuit breaker."
        ),
        "cases": {},
    }
    checkpoint(report)

    variants: list[tuple[str, dict, int, str | None]] = []
    variants.append(("base", config, 0, None))
    variants.append(("remove_asset_BTCUSDT", config, 0, "BTCUSDT"))
    variants.append(("remove_asset_ETHUSDT", config, 0, "ETHUSDT"))

    no_funding = copy.deepcopy(config)
    no_funding["core"]["weight"] = 1.0
    no_funding["funding_carry"]["weight"] = 0.0
    variants.append(("remove_funding_sleeve", no_funding, 0, None))

    no_core = copy.deepcopy(config)
    no_core["core"]["weight"] = 0.0
    no_core["funding_carry"]["weight"] = 1.0
    variants.append(("remove_core_sleeve", no_core, 0, None))

    for component_id in config["core"]["component_ids"]:
        variant = copy.deepcopy(config)
        variant["core"]["component_ids"] = [
            item
            for item in config["core"]["component_ids"]
            if item != component_id
        ]
        variants.append(
            (f"remove_core_component_{component_id}", variant, 0, None)
        )

    variants.append(("phase_5", config, 5, None))
    variants.append(("phase_22", config, 22, None))

    for name, variant, phase, removed_asset in variants:
        print(f"starting {name}", flush=True)
        data, targets, _, _ = build_candidate(variant, phase)
        targets = cap_targets(targets, finalist["target_cap"])
        if removed_asset is not None:
            targets[removed_asset] = 0.0
        result = exact_fast(
            data,
            targets,
            execution["base_cost_per_side"],
            execution["maintenance_equity_fraction"],
            gross_guard_cap=finalist["gross_guard_cap"],
            **guard_kwargs,
        )
        report["cases"][name] = metric(result)
        checkpoint(report)
        print(
            f"completed {name}: CAGR={report['cases'][name]['cagr']:.4f} "
            f"DD={report['cases'][name]['max_drawdown']:.4f}",
            flush=True,
        )

    base_cagr = report["cases"]["base"]["cagr"]
    report["diagnostic"] = {
        "base_cagr": base_cagr,
        "largest_cagr_dependency": min(
            (
                {
                    "case": name,
                    "cagr_change": value["cagr"] - base_cagr,
                    "remaining_cagr": value["cagr"],
                }
                for name, value in report["cases"].items()
                if name != "base"
            ),
            key=lambda row: row["cagr_change"],
        ),
        "any_exact_ruin": any(
            value["ruin"] for value in report["cases"].values()
        ),
    }
    report["status"] = "completed"
    checkpoint(report)
    print(json.dumps(report["diagnostic"], indent=2), flush=True)


if __name__ == "__main__":
    main()
