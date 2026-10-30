"""V98 Independent Phase058 — FRED macro-risk feasibility only. ZERO alpha/returns."""
from __future__ import annotations
import csv, io, json, math, urllib.request
from pathlib import Path
SERIES=["VIXCLS","DGS10","DFF"]
DATES=["2023-01-17","2023-07-17","2024-01-16","2024-07-15","2025-01-15","2025-07-15"]
OUT=Path("reports/v98_independent_phase058_macro_risk_probe.json")

def finite(x):
    try:return math.isfinite(float(x))
    except (TypeError,ValueError):return False

def fetch_series(s):
    url=f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={s}&cosd=2023-01-01&coed=2025-12-31"
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 CryptoAI-Lab-V98-Independent/1.0","Accept":"text/csv,*/*"})
        with urllib.request.urlopen(req,timeout=120) as r:text=r.read().decode("utf-8");status=getattr(r,"status",200)
        rows=list(csv.DictReader(io.StringIO(text))); vals={row.get("observation_date"):row.get(s) for row in rows}
        checks={d:{"finite":finite(vals.get(d)),"present":d in vals} for d in DATES}
        return {"ok":status==200 and all(v["finite"] for v in checks.values()),"http_status":status,"rows":len(rows),"checks":checks}
    except Exception as e:return {"ok":False,"error":type(e).__name__+":"+str(e)[:180]}

def main():
    checks={s:fetch_series(s) for s in SERIES}; passed=all(v["ok"] for v in checks.values())
    report={"engine":"V98 Independent","phase":"058","purpose":"exogenous macro-risk data feasibility only; ZERO ALPHA/ZERO RETURNS","source":"FRED public CSV","training_probe_only":True,"training_years":[2023,2024,2025],"validation_accessed":False,"final_holdout_accessed":False,"v99_used":False,"alpha_computed":False,"returns_computed":False,"parameter_search":False,"series":SERIES,"dates":DATES,"checks":checks,"feasibility_pass":passed,"decision_rule":"PASS_DATA_ONLY iff all frozen series are finite on all frozen training-era dates; otherwise FAIL_DATA_NO_ALPHA."}
    OUT.write_text(json.dumps(report,indent=2),encoding="utf-8");print(json.dumps({"phase":"058","feasibility_pass":passed,"series_ok":{s:v["ok"] for s,v in checks.items()}},indent=2))
if __name__=="__main__":main()
