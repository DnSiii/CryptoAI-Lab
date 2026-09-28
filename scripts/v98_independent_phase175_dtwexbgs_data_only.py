#!/usr/bin/env python3
"""V98 Independent Phase175 DATA_ONLY checker for FRED DTWEXBGS.
No crypto data/PnL is read. Training era only; final holdout is outside acquisition.
"""
from __future__ import annotations
import csv, hashlib, io, json, math, sys, urllib.request
from collections import Counter
from datetime import date

SERIES = "DTWEXBGS"
START = date(2023,1,1)
END = date(2025,12,31)
URL = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={SERIES}&cosd={START.isoformat()}&coed={END.isoformat()}"


def acquire() -> bytes:
    req=urllib.request.Request(URL, headers={"User-Agent":"CryptoAI-Lab-V98-Independent/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def normalize(raw: bytes):
    text=raw.decode("utf-8-sig")
    rows=list(csv.DictReader(io.StringIO(text)))
    if not rows or "DATE" not in rows[0] or SERIES not in rows[0]:
        raise RuntimeError("unexpected FRED schema")
    seen=set(); valid=[]; missing=[]
    for row in rows:
        d=date.fromisoformat(row["DATE"])
        if not (START <= d <= END):
            raise RuntimeError(f"out-of-window observation: {d}")
        if d in seen: raise RuntimeError(f"duplicate date: {d}")
        seen.add(d)
        s=row[SERIES].strip()
        if s in ("", "."):
            missing.append(d); continue
        x=float(s)
        if not math.isfinite(x): raise RuntimeError(f"nonfinite: {d}")
        valid.append((d.isoformat(), format(x, ".10g")))
    payload=("DATE,"+SERIES+"\n"+"".join(f"{d},{x}\n" for d,x in valid)).encode()
    annual=Counter(d[:4] for d,_ in valid)
    return payload, valid, missing, dict(sorted(annual.items()))


def main():
    p1,v1,m1,a1=normalize(acquire())
    p2,v2,m2,a2=normalize(acquire())
    h1=hashlib.sha256(p1).hexdigest(); h2=hashlib.sha256(p2).hexdigest()
    if h1 != h2 or p1 != p2: raise RuntimeError("reacquisition mismatch")
    if not v1: raise RuntimeError("no valid observations")
    out={"phase":175,"series":SERIES,"window":[START.isoformat(),END.isoformat()],
         "valid_observations":len(v1),"explicit_missing_rows":len(m1),
         "first_valid":v1[0][0],"last_valid":v1[-1][0],"annual_valid":a1,
         "normalized_sha256":h1,"reacquisition_identical":True,
         "same_day_use_forbidden":True,"crypto_pnl_inspected":False,"holdout_inspected":False}
    print(json.dumps(out, sort_keys=True, indent=2))

if __name__ == "__main__": main()
