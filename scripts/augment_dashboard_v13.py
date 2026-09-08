from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact_fast
from paper_once_v13 import apply_funding_quarantine, cap_targets
from run_final_candidate import build_candidate

DASHBOARD = PROJECT / "dashboard" / "dashboard_data.json"
REPORTS = PROJECT / "reports"
CONFIG = PROJECT / "config"
DASHBOARD_TIMEZONE = "America/Sao_Paulo"
META = {
    "label": "V13",
    "name": "PIT Carry Core",
    "role": "Core",
    "description": "Núcleo causal point-in-time com carry e circuit breaker.",
}


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def pct(value: float) -> float:
    return round(float(value) * 100.0, 6)


def dashboard_local_equity(equity: pd.Series) -> pd.Series:
    series = equity.dropna().copy()
    if not isinstance(series.index, pd.DatetimeIndex):
        raise TypeError("equity index must be a DatetimeIndex")
    if series.index.tz is None:
        series.index = series.index.tz_localize("UTC")
    return series.tz_convert(DASHBOARD_TIMEZONE)


def daily_close(equity: pd.Series) -> pd.Series:
    return dashboard_local_equity(equity).resample("1D").last().dropna()


def summary(equity: pd.Series) -> dict:
    equity = equity.dropna()
    daily = daily_close(equity)
    daily_returns = daily.pct_change(fill_method=None).dropna()
    dd = equity.div(equity.cummax()).sub(1.0)
    return {
        "returnPct": pct(equity.iloc[-1] / equity.iloc[0] - 1.0) if len(equity) > 1 else 0.0,
        "maxDrawdownPct": pct(dd.min()) if len(dd) else 0.0,
        "bestDayPct": pct(daily_returns.max()) if len(daily_returns) else 0.0,
        "worstDayPct": pct(daily_returns.min()) if len(daily_returns) else 0.0,
    }


def daily_curve(equity: pd.Series) -> list[dict]:
    daily = daily_close(equity)
    return [
        {"time": ts.isoformat(), "equity": round(float(value), 10)}
        for ts, value in daily.items()
    ]


def build_history() -> pd.Series:
    finalist = load_json(CONFIG / "candidate_v13_circuit_breaker.json")
    base_config = load_json(CONFIG / finalist["base_candidate_config"])
    data, targets, _, _ = build_candidate(base_config)
    targets = cap_targets(targets, finalist["target_cap"])
    data, targets, _ = apply_funding_quarantine(data, targets)
    execution = base_config["execution"]
    guard = finalist["circuit_breaker"]
    result = exact_fast(
        data,
        targets,
        execution["base_cost_per_side"],
        execution["maintenance_equity_fraction"],
        gross_guard_cap=finalist["gross_guard_cap"],
        drawdown_guard_threshold=guard["drawdown_threshold"],
        drawdown_guard_multiplier=guard["exposure_multiplier"],
        drawdown_guard_cooldown_hours=guard["cooldown_hours"],
    )
    return result.equity


def paper_payload() -> dict:
    snapshot = load_json(REPORTS / "paper_v13_snapshot.json", {}) or {}
    ledger = load_json(REPORTS / "paper_v13_ledger.json", {}) or {}
    base = float(ledger.get("base_capital_brl", 10000.0))
    ledger_summary = ledger.get("summary", {})
    current = float(
        ledger_summary.get(
            "current_capital_brl",
            base * float(snapshot.get("forward_equity_multiple", 1.0)),
        )
    )
    curve = [
        {
            "time": row.get("timestamp"),
            "capital": row.get(
                "capital_brl", base * float(row.get("equity_multiple", 1.0))
            ),
        }
        for row in ledger.get("equity_curve", [])
        if row.get("timestamp")
    ]
    assets = ledger.get("assets", {})
    positions = sorted(
        [
            {
                "symbol": symbol,
                "direction": item.get("direction", "none"),
                "weightPct": round(float(item.get("current_weight", 0.0)) * 100.0, 4),
                "valueBrl": round(float(item.get("position_value_brl", 0.0)), 2),
            }
            for symbol, item in assets.items()
            if abs(float(item.get("current_weight", 0.0))) > 1e-8
        ],
        key=lambda item: abs(item["weightPct"]),
        reverse=True,
    )[:8]
    return {
        **META,
        "track": "v13",
        "candidate": snapshot.get("candidate", ledger.get("candidate", META["name"])),
        "status": snapshot.get("status", "pending"),
        "paperStart": snapshot.get(
            "paper_start_after_timestamp", ledger.get("paper_start_after_timestamp")
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
            snapshot.get("new_forward_hours", max(0, len(curve) - 1))
        ),
        "positions": positions,
        "curve": curve,
        "strictResearchGate": None,
        "forwardValidation": None,
        "satelliteWeightPct": None,
        "satelliteTargetPct": None,
        "consensusPct": None,
    }


def main() -> None:
    payload = load_json(DASHBOARD)
    if not payload:
        raise RuntimeError("dashboard_data.json must exist before V13 augmentation")
    equity = build_history()
    payload.setdefault("backtest", {}).setdefault("engines", {})["v13"] = {
        **META,
        "track": "v13",
        "summary": summary(equity),
        "curve": daily_curve(equity),
    }
    payload.setdefault("paper", {}).setdefault("engines", {})["v13"] = paper_payload()
    payload["timezone"] = DASHBOARD_TIMEZONE
    payload["paper"]["timezone"] = DASHBOARD_TIMEZONE
    payload["backtest"]["timezone"] = DASHBOARD_TIMEZONE
    times = [
        pd.Timestamp(point["time"])
        for engine in payload["backtest"]["engines"].values()
        for point in engine.get("curve", [])
        if point.get("time")
    ]
    if times:
        payload["backtest"]["availableFrom"] = min(times).isoformat()
        payload["backtest"]["through"] = max(times).isoformat()
    payload["schemaVersion"] = max(3, int(payload.get("schemaVersion", 2)))
    DASHBOARD.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "augmented": "v13",
                "timezone": DASHBOARD_TIMEZONE,
                "history_days": len(
                    payload["backtest"]["engines"]["v13"]["curve"]
                ),
                "paper_points": len(payload["paper"]["engines"]["v13"]["curve"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
