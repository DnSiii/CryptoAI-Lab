#!/usr/bin/env python3
"""V98 Independent Phase051 feasibility probe: forced-liquidation archive only.

NO ALPHA / NO RETURNS. This script only checks whether Binance USD-M public
liquidationSnapshot files exist and whether their schema/timestamps are usable.
It deliberately samples training-era dates only (<=2025-12-31) and never reads
validation/final-holdout prices or V99 evidence.
"""
from __future__ import annotations
import csv, io, json, urllib.request, zipfile
from pathlib import Path

SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT"]
DATES = ["2023-01-15", "2023-07-15", "2024-01-15", "2024-07-15", "2025-01-15", "2025-07-15"]
BASE = "https://data.binance.vision/data/futures/um/daily/liquidationSnapshot/{s}/{s}-liquidationSnapshot-{d}.zip"
OUT = Path("reports/v98_independent_phase051_liquidation_probe.json")

def probe(symbol: str, day: str) -> dict:
    url = BASE.format(s=symbol, d=day)
    result = {"symbol": symbol, "date": day, "url": url, "ok": False}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CryptoAI-V98-Independent/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            payload = r.read()
        result["bytes"] = len(payload)
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            names = z.namelist()
            result["members"] = names
            if len(names) != 1:
                result["error"] = "unexpected_zip_members"
                return result
            text = z.read(names[0]).decode("utf-8-sig", errors="strict")
        rows = list(csv.reader(io.StringIO(text)))
        if not rows:
            result["error"] = "empty_csv"
            return result
        result["header"] = rows[0]
        result["rows"] = max(0, len(rows) - 1)
        result["first_row"] = rows[1] if len(rows) > 1 else None
        result["last_row"] = rows[-1] if len(rows) > 1 else None
        result["ok"] = len(rows) > 1
        return result
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"
        return result

def main() -> None:
    checks = [probe(s, d) for s in SYMBOLS for d in DATES]
    ok = sum(bool(x["ok"]) for x in checks)
    headers = sorted({tuple(x.get("header", [])) for x in checks if x.get("ok")})
    report = {
        "engine": "V98 Independent",
        "phase": "051-feasibility-only",
        "mechanism": "forced-liquidation event flow",
        "source": "Binance public USD-M daily liquidationSnapshot archive",
        "guardrails": {
            "alpha_scored": False,
            "returns_computed": False,
            "validation_accessed": False,
            "final_holdout_accessed": False,
            "v99_used": False,
            "latest_sample_date": max(DATES),
        },
        "symbols": SYMBOLS,
        "dates": DATES,
        "successful_checks": ok,
        "total_checks": len(checks),
        "success_rate": ok / len(checks),
        "distinct_headers": [list(h) for h in headers],
        "checks": checks,
        "decision_rule": "feasible only if files exist across multiple training years/assets with non-empty, stable parseable schema; feasibility does not authorize alpha until separately preregistered",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("phase", "successful_checks", "total_checks", "success_rate", "distinct_headers")}, indent=2))

if __name__ == "__main__":
    main()
