#!/usr/bin/env python3
"""V98 Independent Phase184 — WALCL DATA_ONLY integrity audit. No crypto/PnL access."""
from __future__ import annotations
import csv, hashlib, io, json, math, urllib.request
from datetime import date

URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=WALCL&cosd=2023-01-01&coed=2025-12-31"
START, END = date(2023,1,1), date(2025,12,31)

def acquire():
    req=urllib.request.Request(URL, headers={"User-Agent":"CryptoAI-Lab-V98-Phase184/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw=r.read().decode("utf-8")
    reader=csv.DictReader(io.StringIO(raw))
    fields=reader.fieldnames or []
    date_col="observation_date" if "observation_date" in fields else ("DATE" if "DATE" in fields else None)
    if date_col is None or "WALCL" not in fields:
        raise AssertionError(f"unexpected FRED schema: {fields}")
    rows=[]
    for x in reader:
        d=date.fromisoformat(x[date_col])
        if not START <= d <= END: continue
        s=x["WALCL"].strip()
        if s in ("", "."): raise AssertionError(f"missing WALCL at {d}")
        v=float(s)
        if not math.isfinite(v): raise AssertionError(f"nonfinite WALCL at {d}")
        rows.append((d,v))
    norm="".join(f"{d.isoformat()},{v:.12g}\n" for d,v in rows).encode()
    return rows, hashlib.sha256(norm).hexdigest(), fields

def main():
    a,h1,f1=acquire(); b,h2,f2=acquire()
    if not a: raise AssertionError("empty WALCL acquisition")
    dates=[d for d,_ in a]; vals=[v for _,v in a]
    counts={str(y):sum(d.year==y for d in dates) for y in (2023,2024,2025)}
    gaps=[(dates[i]-dates[i-1]).days for i in range(1,len(dates))]
    sv=sorted(vals)
    def q(p):
        i=(len(sv)-1)*p; lo=int(i); hi=min(lo+1,len(sv)-1); f=i-lo
        return sv[lo]*(1-f)+sv[hi]*f
    gates={
      "schema_repeat_match": f1==f2,
      "nonempty_each_year": all(counts[str(y)]>0 for y in (2023,2024,2025)),
      "at_least_50_each_year": all(counts[str(y)]>=50 for y in (2023,2024,2025)),
      "monotonic": dates==sorted(dates), "unique_dates": len(dates)==len(set(dates)),
      "max_gap_le_10": bool(gaps) and max(gaps)<=10,
      "duplicate_sha_match": h1==h2,
      "no_2026_access": all(d<date(2026,1,1) for d in dates),
    }
    out={"phase":184,"mode":"DATA_ONLY","series":"WALCL","source":URL,"schema":f1,
      "first":dates[0].isoformat(),"last":dates[-1].isoformat(),"counts":counts,"n":len(a),
      "max_calendar_gap_days":max(gaps) if gaps else None,"sha256_acq1":h1,"sha256_acq2":h2,
      "quantiles":{"min":min(vals),"p25":q(.25),"median":q(.5),"p75":q(.75),"max":max(vals)},
      "causal_policy":"Wednesday observation no earlier than next UTC day; later economic prereg must honor any stricter documented release timing",
      "gates":gates,"decision":"PASS_DATA_ONLY" if all(gates.values()) else "REJECT_DATA_AVAILABILITY_NO_RESCUE"}
    print(json.dumps(out,indent=2,sort_keys=True))
    if out["decision"]!="PASS_DATA_ONLY": raise SystemExit(2)
if __name__=="__main__": main()
