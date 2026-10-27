#!/usr/bin/env python3
"""Source-only Binance native OI vendor ZIP timestamp and invalid-value forensics."""
from __future__ import annotations
import collections,csv,hashlib,io,json,math,zipfile
from pathlib import Path
from v98_oi_native_source_probe_20261027 import ROOT,get,timestamp
CASES=(("BTCUSDT","2024-04-01"),("BTCUSDT","2024-04-10"),
       ("BTCUSDT","2024-05-10"),("BTCUSDT","2024-05-11"),
       ("BNBUSDT","2023-11-16"),("BTCUSDT","2024-02-16"),
       ("BTCUSDT","2023-04-10"))
OUT=Path(__file__).resolve().parent/"v98_oi_anomaly_forensics_20261027.json"
def inspect(asset,date):
    url=f"{ROOT}/{asset}/{asset}-metrics-{date}.zip"
    payload=get(url);side=get(url+".CHECKSUM").decode("utf-8-sig")
    sha=hashlib.sha256(payload).hexdigest()
    if sha not in side.lower():raise ValueError("OI_FORENSIC_VENDOR_SHA")
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        names=[n for n in z.namelist() if n.endswith(".csv")]
        assert len(names)==1
        rows=list(csv.DictReader(io.StringIO(z.read(names[0]).decode("utf-8-sig"))))
    key=next(x for x in ("create_time","timestamp","time") if x in rows[0])
    oi_key=next(x for x in ("sum_open_interest","sumOpenInterest") if x in rows[0])
    ts=[timestamp(row[key]) for row in rows]
    by_day=dict(collections.Counter(x.date().isoformat() for x in ts))
    diffs=[(b-a).total_seconds()/60 for a,b in zip(ts,ts[1:])]
    bad_values=[{"index":i,"timestamp":row[key],"value":row[oi_key]}
                for i,row in enumerate(rows) if not
                (math.isfinite(float(row[oi_key])) and float(row[oi_key])>0)]
    return {"asset":asset,"archive_day":date,"zip_sha256":sha,"checksum_pass":True,
            "rows":len(rows),"first_raw":rows[0][key],"last_raw":rows[-1][key],
            "first_utc":ts[0].isoformat(),"last_utc":ts[-1].isoformat(),
            "utc_day_distribution":by_day,"monotonic":ts==sorted(ts),
            "duplicates":len(ts)-len(set(ts)),
            "gap_minutes_distribution":dict(collections.Counter(diffs)),
            "invalid_oi_count":len(bad_values),"invalid_oi_first":bad_values[:5]}
if __name__=="__main__":
    results=[]
    for a,d in CASES:
        try:r=inspect(a,d)
        except Exception as exc:r={"asset":a,"archive_day":d,"error":str(exc)[:250]}
        results.append(r)
        print("V98_OI_RAW_FORENSIC",json.dumps(r,sort_keys=True),flush=True)
    OUT.write_text(json.dumps({"source_only":True,"pnl_computed":False,
        "holdout_2025_read":False,"results":results},indent=2,sort_keys=True)+"\n")
