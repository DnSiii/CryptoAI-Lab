#!/usr/bin/env python3
"""V98 Independent Phase062: frozen cross-asset liquidity DATA feasibility only.

No crypto prices, returns, alpha, sign, threshold, exposure or holdout access.
"""
from __future__ import annotations

import csv
import io
import json
import math
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

ENGINE = "V98 Independent"
PHASE = "062"
PREREG = "reports/v98_independent_phase062_cross_asset_liquidity_preregistration.md"
SERIES = ("WALCL", "RRPONTSYD", "WTREGEN")
CHECK_DATES = (
    "2023-03-15", "2023-09-15", "2024-03-15", "2024-09-16", "2025-03-17", "2025-09-15"
)
URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
OUT = Path("reports/v98_independent_phase062_cross_asset_liquidity_feasibility.json")


def fetch_series(series: str) -> list[tuple[date, float]]:
    req = urllib.request.Request(URL.format(series=series), headers={"User-Agent": "CryptoAI-Lab-V98-Independent/1.0"})
    text = None
    last_error: Exception | None = None
    # Transport-only hardening: retry the identical frozen source/query; never change series/dates/source.
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                text = r.read().decode("utf-8")
            break
        except (TimeoutError, urllib.error.URLError, OSError) as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(5 * attempt)
    if text is None:
        raise RuntimeError(f"FRED transport failed for frozen series {series} after 3 identical attempts") from last_error
    rows: list[tuple[date, float]] = []
    for row in csv.DictReader(io.StringIO(text)):
        raw_date = row.get("DATE") or row.get("observation_date")
        raw_value = row.get(series)
        if not raw_date or raw_value in (None, "", "."):
            continue
        try:
            d = date.fromisoformat(raw_date)
            v = float(raw_value)
        except (ValueError, TypeError):
            continue
        if math.isfinite(v):
            rows.append((d, v))
    rows.sort(key=lambda x: x[0])
    if not rows:
        raise RuntimeError(f"no finite observations for {series}")
    return rows


def latest_not_after(rows: list[tuple[date, float]], cutoff: date) -> tuple[date, float] | None:
    eligible = [x for x in rows if x[0] <= cutoff]
    return eligible[-1] if eligible else None


def main() -> None:
    checks = []
    source_counts = {}
    for series in SERIES:
        rows = fetch_series(series)
        source_counts[series] = len(rows)
        for cutoff_s in CHECK_DATES:
            cutoff = date.fromisoformat(cutoff_s)
            obs = latest_not_after(rows, cutoff)
            ok = obs is not None and obs[0] <= cutoff and math.isfinite(obs[1])
            checks.append({
                "series": series,
                "check_date": cutoff_s,
                "observation_date": obs[0].isoformat() if obs else None,
                "value": obs[1] if obs else None,
                "finite": bool(ok),
                "causal_not_after_check_date": bool(ok),
            })
    passed = len(checks) == 18 and all(c["finite"] and c["causal_not_after_check_date"] for c in checks)
    report = {
        "engine": ENGINE,
        "phase": PHASE,
        "purpose": "DATA_FEASIBILITY_ONLY",
        "preregistration": PREREG,
        "source": "FRED public CSV",
        "series": list(SERIES),
        "check_dates": list(CHECK_DATES),
        "checks": checks,
        "checks_passed": sum(bool(c["finite"] and c["causal_not_after_check_date"]) for c in checks),
        "checks_total": len(checks),
        "source_observation_counts": source_counts,
        "decision": "PASS_DATA_ONLY" if passed else "FAIL_DATA_NO_ALPHA",
        "crypto_prices_used": False,
        "crypto_returns_used": False,
        "alpha_or_pnl_computed": False,
        "parameter_search": False,
        "validation": None,
        "final_holdout": None,
        "final_holdout_untouched": True,
        "v99_used": False,
        "v16_used": False,
        "no_future_observation_rule": True,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": report["decision"], "checks": f"{report['checks_passed']}/{report['checks_total']}"}))
    if not passed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
