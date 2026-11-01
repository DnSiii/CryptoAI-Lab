#!/usr/bin/env python3
"""Independent audit of V98 premium-index source artifact; never imports capture."""
import csv,datetime as dt,hashlib,json,math,sys
from collections import defaultdict
from pathlib import Path

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
FIRST=dt.datetime(2022,12,1,tzinfo=dt.timezone.utc)
LAST=dt.datetime(2026,1,1,tzinfo=dt.timezone.utc)

def audit(folder):
    folder=Path(folder)
    p=folder/"v98_premium_2022_2025_source_report.json"
    c=folder/"v98_premium_2022_2025_verified_hourly.csv"
    j=json.loads(p.read_text())
    assert j["decision"]=="PASS_PREMIUM_FULL_SOURCE_ONLY_NOT_PNL"
    assert j["pnl_computed"] is False and j["2026_plus_accessed"] is False
    assert j["holdout_accessed"] is False and j["exact_event_mark_attested"] is False
    assert j["assets"]==list(ASSETS) and j["months"]==148
    assert j["passed_months"]==148 and j["quarantined_months"]==0
    assert j["verified_asset_hours"]==108192 and j["expected_asset_hours"]==108192
    assert hashlib.sha256(c.read_bytes()).hexdigest()==j["hourly_csv_sha256"]
    manifest={(x["asset"],x["month"]):x for x in j["manifest"]}
    assert len(manifest)==148 and all("error" not in x for x in manifest.values())
    counts=defaultdict(int)
    clocks={a:FIRST for a in ASSETS}
    with c.open(newline="") as f:
        reader=csv.DictReader(f)
        assert reader.fieldnames==["asset","bar_open_utc","premium_open","premium_high","premium_low","premium_close","source_zip_sha256"]
        for row in reader:
            a=row["asset"];assert a in ASSETS
            t=dt.datetime.fromisoformat(row["bar_open_utc"])
            assert t.tzinfo is not None and t.utcoffset()==dt.timedelta(0)
            assert t==clocks[a] and t<LAST
            clocks[a]+=dt.timedelta(hours=1)
            key=(a,t.strftime("%Y-%m"))
            assert key in manifest and row["source_zip_sha256"]==manifest[key]["zip_sha256"]
            vals=[float(row[k]) for k in ("premium_open","premium_high","premium_low","premium_close")]
            assert all(math.isfinite(v) and abs(v)<1 for v in vals)
            o,h,l,cl=vals
            assert l<=min(o,cl)+1e-10 and h>=max(o,cl)-1e-10
            counts[key]+=1
    assert all(t==LAST for t in clocks.values())
    assert len(counts)==148
    assert all(counts[k]==v["rows"] for k,v in manifest.items())
    result={"decision":"PASS_INDEPENDENT_PREMIUM_FULL_SOURCE_INTEGRITY_NOT_PNL",
            "months_verified":len(counts),"asset_hours_verified":sum(counts.values()),
            "csv_sha256":j["hourly_csv_sha256"],"no_2026":True,
            "no_holdout":True,"no_pnl":True,"exact_event_mark_attested":False}
    return result

if __name__=="__main__":
    print(json.dumps(audit(sys.argv[1]),sort_keys=True))
