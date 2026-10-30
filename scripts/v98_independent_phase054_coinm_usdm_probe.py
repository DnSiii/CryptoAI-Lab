"""V98 Independent Phase054 — COIN-M vs USD-M feasibility only.
No alpha, ranks, thresholds, returns, validation, or holdout access.
"""
from __future__ import annotations
import io,json,urllib.request,zipfile
from pathlib import Path

ASSETS={"BTC":"BTCUSD_PERP","ETH":"ETHUSD_PERP","BNB":"BNBUSD_PERP","XRP":"XRPUSD_PERP","SOL":"SOLUSD_PERP"}
DATES=["2023-01-15","2023-07-15","2024-01-15","2024-07-15","2025-01-15","2025-07-15"]
OUT=Path("reports/v98_independent_phase054_coinm_usdm_probe.json")

def probe(url):
    try:
        with urllib.request.urlopen(url,timeout=25) as r: raw=r.read()
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            names=z.namelist(); data=z.read(names[0]).decode("utf-8",errors="replace").splitlines()
        return {"ok":True,"rows":max(0,len(data)-1),"member":names[0],"bytes":len(raw)}
    except Exception as e:
        return {"ok":False,"error":type(e).__name__+":"+str(e)[:160]}

def main():
    checks={}
    for asset,cm in ASSETS.items():
        um=asset+"USDT"
        for d in DATES:
            cu=f"https://data.binance.vision/data/futures/cm/daily/klines/{cm}/1h/{cm}-1h-{d}.zip"
            uu=f"https://data.binance.vision/data/futures/um/daily/klines/{um}/1h/{um}-1h-{d}.zip"
            checks[f"{asset}:{d}"]={"coinm":probe(cu),"usdm":probe(uu)}
    paired=sum(v["coinm"]["ok"] and v["usdm"]["ok"] for v in checks.values())
    report={"engine":"V98 Independent","phase":"054","purpose":"COIN-M vs USD-M paired data feasibility only; ZERO ALPHA","training_probe_only":True,"validation_accessed":False,"final_holdout_accessed":False,"v99_used":False,"alpha_computed":False,"returns_computed":False,"assets":list(ASSETS),"dates":DATES,"paired_ok":paired,"paired_total":len(checks),"checks":checks}
    OUT.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({k:report[k] for k in ["phase","paired_ok","paired_total","alpha_computed","returns_computed"]},indent=2))
if __name__=="__main__": main()
