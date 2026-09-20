"""V98 Independent Phase056 — options-implied-volatility data feasibility only.
Orthogonal source family: Binance options EOHSummary/BVOLIndex.
ZERO alpha, ZERO returns, training-era samples only; validation/final holdout inaccessible.
"""
from __future__ import annotations
import io, json, urllib.request, zipfile
from pathlib import Path

# Fixed before any Phase056 PnL. Sparse dates deliberately span all training folds.
DATES = ["2023-07-10", "2023-10-10", "2024-01-10", "2024-07-10", "2025-01-10", "2025-07-10"]
SERIES = {
    "btc_eoh": ("EOHSummary", "BTCUSDT"),
    "eth_eoh": ("EOHSummary", "ETHUSDT"),
    "btc_bvol": ("BVOLIndex", "BTCBVOLUSDT"),
}
OUT = Path("reports/v98_independent_phase056_options_volatility_probe.json")
BASE = "https://data.binance.vision/data/option/daily"

def probe(dtype: str, symbol: str, day: str) -> dict:
    url = f"{BASE}/{dtype}/{symbol}/{symbol}-{dtype}-{day}.zip"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            raw = r.read()
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            names = z.namelist()
            text = z.read(names[0]).decode("utf-8", errors="replace").splitlines()
        header = text[0].split(",") if text else []
        return {"ok": True, "rows": max(0, len(text)-1), "columns": len(header), "header": header, "member": names[0], "bytes": len(raw)}
    except Exception as e:
        return {"ok": False, "error": type(e).__name__ + ":" + str(e)[:180]}

def main() -> None:
    checks = {}
    for name, (dtype, symbol) in SERIES.items():
        checks[name] = {d: probe(dtype, symbol, d) for d in DATES}
    ok = sum(x["ok"] for by_date in checks.values() for x in by_date.values())
    total = len(SERIES) * len(DATES)
    by_series = {name: sum(v["ok"] for v in by_date.values()) for name, by_date in checks.items()}
    report = {
        "engine": "V98 Independent", "phase": "056",
        "purpose": "options implied-volatility/source feasibility only; ZERO ALPHA/ZERO RETURNS",
        "mechanism_family": "options-implied-volatility / volatility-risk-premium",
        "training_probe_only": True, "training_years": [2023, 2024, 2025],
        "validation_accessed": False, "final_holdout_accessed": False, "v99_used": False,
        "alpha_computed": False, "returns_computed": False, "parameter_search": False,
        "dates": DATES, "series": SERIES, "ok": ok, "total": total, "by_series_ok": by_series,
        "checks": checks,
        "decision_rule": "Feasibility only. No alpha may be specified from values in this report. A later Phase057 mechanism requires separate preregistration before any PnL."
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["phase","ok","total","by_series_ok","alpha_computed","returns_computed"]}, indent=2))

if __name__ == "__main__":
    main()
