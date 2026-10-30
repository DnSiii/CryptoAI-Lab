#!/usr/bin/env python3
"""V98 Independent Phase052 feasibility probe: spot-vs-USD-M perp price data.

NO ALPHA / NO RETURNS. Checks matched Binance public spot and USD-M 1h kline
archives on training-era dates only. This establishes whether a genuinely new
cross-market basis/dislocation mechanism can later be preregistered. It does
not compute basis, returns, ranks, thresholds, or access validation/holdout.
"""
from __future__ import annotations
import csv, io, json, urllib.request, zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT"]
DATES = ["2023-01-15", "2023-07-15", "2024-01-15", "2024-07-15", "2025-01-15", "2025-07-15"]
OUT = Path("reports/v98_independent_phase052_spot_perp_basis_probe.json")

def url(market: str, symbol: str, day: str) -> str:
    if market == "spot":
        return f"https://data.binance.vision/data/spot/daily/klines/{symbol}/1h/{symbol}-1h-{day}.zip"
    return f"https://data.binance.vision/data/futures/um/daily/klines/{symbol}/1h/{symbol}-1h-{day}.zip"

def fetch_one(args: tuple[str,str,str]) -> dict:
    market, symbol, day = args
    u = url(market, symbol, day)
    out = {"market": market, "symbol": symbol, "date": day, "url": u, "ok": False}
    try:
        req=urllib.request.Request(u, headers={"User-Agent":"CryptoAI-V98-Independent/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r: payload=r.read()
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            names=z.namelist()
            if len(names)!=1:
                out["error"]="unexpected_zip_members"; return out
            rows=list(csv.reader(io.StringIO(z.read(names[0]).decode("utf-8-sig"))))
        out["bytes"]=len(payload); out["rows"]=len(rows)
        out["first_row_width"]=len(rows[0]) if rows else 0
        out["first_row_prefix"]=rows[0][:4] if rows else None
        out["last_row_prefix"]=rows[-1][:4] if rows else None
        out["ok"]=len(rows)>=23
        return out
    except Exception as e:
        out["error"]=f"{type(e).__name__}: {e}"; return out

def main() -> None:
    tasks=[(m,s,d) for s in SYMBOLS for d in DATES for m in ("spot","um_perp")]
    with ThreadPoolExecutor(max_workers=16) as ex: checks=list(ex.map(fetch_one,tasks))
    lookup={(x["market"],x["symbol"],x["date"]):x for x in checks}
    matched=[]
    for s in SYMBOLS:
        for d in DATES:
            matched.append({"symbol":s,"date":d,"spot_ok":lookup[("spot",s,d)]["ok"],"perp_ok":lookup[("um_perp",s,d)]["ok"]})
    matched_ok=sum(x["spot_ok"] and x["perp_ok"] for x in matched)
    report={
      "engine":"V98 Independent","phase":"052-feasibility-only",
      "mechanism":"cross-market spot-vs-USD-M perpetual basis/dislocation",
      "source":"Binance public spot + USD-M daily 1h kline archives",
      "guardrails":{"alpha_scored":False,"basis_computed":False,"returns_computed":False,"validation_accessed":False,"final_holdout_accessed":False,"v99_used":False,"latest_sample_date":max(DATES)},
      "symbols":SYMBOLS,"dates":DATES,"matched_pairs_ok":matched_ok,"matched_pairs_total":len(matched),
      "matched_pair_success_rate":matched_ok/len(matched),"matched":matched,"checks":checks,
      "decision_rule":"feasible only if matched spot/perp archives are broadly available across all three training years and multiple assets; feasibility alone does not authorize alpha until separately preregistered"
    }
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:report[k] for k in ("phase","matched_pairs_ok","matched_pairs_total","matched_pair_success_rate")},indent=2))
if __name__=="__main__": main()
