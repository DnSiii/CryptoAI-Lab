from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
DASHBOARD_DATA = PROJECT / "dashboard" / "dashboard_data.json"
LEDGER = PROJECT / "reports" / "paper_v99_research_ledger.json"
SNAPSHOT = PROJECT / "reports" / "paper_v99_research_snapshot.json"

ORDER = ["r98", "f1", "f3", "f7", "f12"]


def load(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def paper_variant(item: dict) -> dict:
    summary = item.get("summary", {})
    base = float(item.get("base_capital_brl", 10000.0))
    current = float(summary.get("current_capital_brl", base))
    assets = item.get("assets", {})
    positions = sorted(
        [
            {
                "symbol": symbol,
                "direction": value.get("direction", "none"),
                "weightPct": round(float(value.get("current_weight", 0.0)) * 100.0, 5),
                "valueBrl": round(float(value.get("position_value_brl", 0.0)), 2),
            }
            for symbol, value in assets.items()
            if abs(float(value.get("current_weight", 0.0))) > 1e-8
        ],
        key=lambda row: abs(row["weightPct"]),
        reverse=True,
    )
    curve = [
        {
            "time": row.get("timestamp"),
            "capital": float(row.get("capital_brl", base)),
            "hourResultBrl": float(row.get("hour_result_brl", 0.0)),
        }
        for row in item.get("equity_curve", [])
        if row.get("timestamp")
    ]
    return {
        "track": item.get("track"),
        "label": item.get("label"),
        "name": item.get("name"),
        "researchStatus": item.get("status"),
        "description": item.get("description"),
        "paperStart": item.get("paper_start_after_timestamp"),
        "latest": item.get("latest_data_timestamp"),
        "baseCapitalBrl": round(base, 2),
        "currentCapitalBrl": round(current, 2),
        "netResultBrl": round(float(summary.get("net_result_brl", current - base)), 2),
        "roiPct": round(float(summary.get("forward_return_pct", 0.0)), 6),
        "highestCapitalBrl": round(float(summary.get("highest_capital_brl", base)), 2),
        "lowestCapitalBrl": round(float(summary.get("lowest_capital_brl", base)), 2),
        "grossExposurePct": round(float(summary.get("gross_exposure_pct", 0.0)), 5),
        "newForwardHours": int(summary.get("new_forward_hours", max(0, len(curve) - 1))),
        "positions": positions,
        "curve": curve,
    }


def main() -> None:
    payload = load(DASHBOARD_DATA)
    if not payload:
        raise RuntimeError("dashboard/dashboard_data.json must exist before V99 augmentation")

    ledger = load(LEDGER)
    snapshot = load(SNAPSHOT, {}) or {}
    if ledger:
        variants = ledger.get("variants", {})
        backtest = ledger.get("backtest_reference", {})
        payload["v99Research"] = {
            "available": True,
            "mode": "PAPER_ONLY",
            "realOrders": False,
            "title": "V99 Research Lab",
            "subtitle": "Cinco versões do V99 acompanhadas no mesmo boundary forward.",
            "order": [key for key in ORDER if key in variants or key in backtest],
            "paperStart": ledger.get("paper_start_after_timestamp"),
            "latest": ledger.get("latest_data_timestamp"),
            "sameBoundary": bool(ledger.get("same_boundary_for_all_variants", False)),
            "selectionFrozenBeforePaper": bool(snapshot.get("selection_frozen_before_paper", True)),
            "backtest": backtest,
            "paper": {
                key: paper_variant(variants[key])
                for key in ORDER
                if key in variants
            },
            "disclosure": ledger.get("disclosure"),
        }
    else:
        payload["v99Research"] = {
            "available": False,
            "mode": "PAPER_ONLY",
            "realOrders": False,
            "title": "V99 Research Lab",
            "subtitle": "Aguardando o primeiro ciclo forward das cinco versões.",
            "order": ORDER,
            "paperStart": None,
            "latest": None,
            "sameBoundary": True,
            "selectionFrozenBeforePaper": True,
            "backtest": {},
            "paper": {},
            "disclosure": "O paper das cinco versões ainda não publicou o primeiro snapshot.",
        }

    DASHBOARD_DATA.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "v99ResearchAvailable": payload["v99Research"]["available"],
        "variants": payload["v99Research"]["order"],
        "paperStart": payload["v99Research"]["paperStart"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
