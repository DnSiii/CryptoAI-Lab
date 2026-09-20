#!/usr/bin/env python3
"""V98 Independent Phase063: frozen derivatives-positioning DATA feasibility only.

No price bars, crypto returns, alpha, sign, threshold, lookback, exposure or holdout access.
"""
from __future__ import annotations

import csv
import io
import json
import math
import urllib.error
import urllib.request
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path

ENGINE = "V98 Independent"
PHASE = "063"
PREREG = "reports/v98_independent_phase063_positioning_metrics_preregistration.md"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT")
CHECK_DATES = ("2023-03-15", "2023-09-15", "2024-03-15", "2024-09-16", "2025-03-17", "2025-09-15")
FIELDS = (
    "sum_open_interest",
    "sum_open_interest_value",
    "count_toptrader_long_short_ratio",
    "sum_toptrader_long_short_ratio",
    "count_long_short_ratio",
    "sum_taker_long_short_vol_ratio",
)
URL = "https://data.binance.vision/data/futures/um/daily/metrics/{symbol}/{symbol}-metrics-{day}.zip"
OUT = Path("reports/v98_independent_phase063_positioning_metrics_feasibility.json")


def parse_ts(raw: str) -> datetime | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        # Binance metrics commonly use millisecond epoch create_time.
        if raw.replace(".", "", 1).isdigit():
            x = float(raw)
            if x > 1e12:
                x /= 1000.0
            return datetime.fromtimestamp(x, tz=timezone.utc)
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc)
    except (ValueError, OverflowError, OSError):
        return None


def fetch_archive(symbol: str, day: str) -> tuple[list[dict[str, str]], str]:
    url = URL.format(symbol=symbol, day=day)
    req = urllib.request.Request(url, headers={"User-Agent": "CryptoAI-Lab-V98-Independent/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            payload = r.read()
    except (TimeoutError, urllib.error.URLError, OSError) as exc:
        raise RuntimeError(f"frozen Binance metrics archive unavailable: {symbol} {day}") from exc
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as zf:
            names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if len(names) != 1:
                raise RuntimeError(f"expected exactly one CSV in {symbol} {day}, got {len(names)}")
            text = zf.read(names[0]).decode("utf-8-sig")
    except (zipfile.BadZipFile, UnicodeDecodeError, KeyError) as exc:
        raise RuntimeError(f"invalid frozen Binance metrics archive: {symbol} {day}") from exc
    rows = list(csv.DictReader(io.StringIO(text)))
    return rows, url


def main() -> None:
    archive_checks = []
    field_checks = []
    for symbol in SYMBOLS:
        for day in CHECK_DATES:
            rows, url = fetch_archive(symbol, day)
            cutoff = date.fromisoformat(day)
            causal_rows = []
            for row in rows:
                raw_ts = row.get("create_time") or row.get("timestamp") or row.get("time")
                ts = parse_ts(raw_ts or "")
                if ts is not None and ts.date() <= cutoff:
                    causal_rows.append(row)
            archive_ok = bool(causal_rows)
            archive_checks.append({"symbol": symbol, "check_date": day, "url": url, "rows": len(rows), "causal_rows": len(causal_rows), "available_and_causal": archive_ok})
            for field in FIELDS:
                vals = []
                for row in causal_rows:
                    try:
                        v = float(row.get(field, ""))
                    except (ValueError, TypeError):
                        continue
                    if math.isfinite(v):
                        vals.append(v)
                field_checks.append({"symbol": symbol, "check_date": day, "field": field, "finite_count": len(vals), "finite": bool(vals)})
    passed = len(archive_checks) == 30 and all(x["available_and_causal"] for x in archive_checks) and len(field_checks) == 180 and all(x["finite"] for x in field_checks)
    report = {
        "engine": ENGINE,
        "phase": PHASE,
        "purpose": "DATA_FEASIBILITY_ONLY",
        "preregistration": PREREG,
        "source": "Binance public data archive USD-M daily metrics",
        "symbols": list(SYMBOLS),
        "check_dates": list(CHECK_DATES),
        "required_fields": list(FIELDS),
        "archive_checks": archive_checks,
        "field_checks": field_checks,
        "archives_passed": sum(bool(x["available_and_causal"]) for x in archive_checks),
        "archives_total": len(archive_checks),
        "fields_passed": sum(bool(x["finite"]) for x in field_checks),
        "fields_total": len(field_checks),
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
    print(json.dumps({"decision": report["decision"], "archives": f"{report['archives_passed']}/{report['archives_total']}", "fields": f"{report['fields_passed']}/{report['fields_total']}"}))
    if not passed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
