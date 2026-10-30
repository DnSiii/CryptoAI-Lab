"""V98 Independent Phase057 — Coin Metrics on-chain feasibility only.
ZERO alpha, ZERO returns, fixed training-era samples only.
"""
from __future__ import annotations
import json, math, urllib.parse, urllib.request
from pathlib import Path

ASSETS = ["btc", "eth"]
METRICS = ["AdrActCnt", "TxCnt", "FeeTotUSD"]
DATES = ["2023-01-15", "2023-07-15", "2024-01-15", "2024-07-15", "2025-01-15", "2025-07-15"]
BASE = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
OUT = Path("reports/v98_independent_phase057_onchain_activity_probe.json")
HEADERS = {"User-Agent": "CryptoAI-Lab-V98-Independent/1.0", "Accept": "application/json"}

def finite_value(x):
    try: return math.isfinite(float(x))
    except (TypeError, ValueError): return False

def one_metric(asset: str, metric: str, day: str) -> dict:
    q = urllib.parse.urlencode({"assets": asset, "metrics": metric, "frequency": "1d", "start_time": day, "end_time": day, "page_size": 10})
    req = urllib.request.Request(BASE + "?" + q, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            payload = json.loads(r.read().decode("utf-8")); status = getattr(r, "status", 200)
        rows = payload.get("data", []); row = rows[0] if rows else {}
        return {"ok": status == 200 and bool(rows) and finite_value(row.get(metric)), "http_status": status, "rows": len(rows), "time": row.get("time"), "finite": finite_value(row.get(metric))}
    except Exception as e:
        return {"ok": False, "error": type(e).__name__ + ":" + str(e)[:180]}

def probe(asset: str, day: str) -> dict:
    metric_checks = {m: one_metric(asset, m, day) for m in METRICS}
    return {"ok": all(v["ok"] for v in metric_checks.values()), "metrics": metric_checks}

def main():
    checks = {a: {d: probe(a, d) for d in DATES} for a in ASSETS}
    total = len(ASSETS) * len(DATES); ok = sum(v["ok"] for a in checks.values() for v in a.values())
    years = {str(y): {a: sum(v["ok"] for d, v in checks[a].items() if d.startswith(str(y))) for a in ASSETS} for y in [2023, 2024, 2025]}
    report = {
        "engine":"V98 Independent","phase":"057","purpose":"on-chain network-activity feasibility only; ZERO ALPHA/ZERO RETURNS",
        "source":"Coin Metrics Community API","training_probe_only":True,"training_years":[2023,2024,2025],
        "validation_accessed":False,"final_holdout_accessed":False,"v99_used":False,"alpha_computed":False,"returns_computed":False,"parameter_search":False,
        "assets":ASSETS,"metrics":METRICS,"dates":DATES,"ok":ok,"total":total,"by_training_year_ok":years,"checks":checks,
        "feasibility_pass": all(years[str(y)][a] == 2 for y in [2023,2024,2025] for a in ASSETS),
        "decision_rule":"PASS_DATA_ONLY only if every frozen BTC/ETH metric is finite on both sampled dates in every training year; otherwise FAIL_DATA_NO_ALPHA."
    }
    OUT.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({k:report[k] for k in ["phase","ok","total","by_training_year_ok","feasibility_pass","alpha_computed","returns_computed"]},indent=2))
if __name__ == "__main__": main()
