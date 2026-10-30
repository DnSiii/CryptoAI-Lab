"""V98 Independent Phase695: source-only Phase206 metadata completeness audit.
No vendor-origin claim, no strategy PnL, no external engines.
"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
MONTHS=tuple(f"{y}-{m:02d}" for y in range(2022,2026) for m in range(1,13) if (y,m)>=(2022,12))
def audit():
    m=json.loads((ROOT/"data/phase206_funding/manifest.json").read_text())
    c=json.loads((ROOT/"phase243_clean4_source_manifest.json").read_text())
    if str(m.get("phase"))!="206" or c.get("universe")!=list(ASSETS):
        raise ValueError("V98 Clean-4 source contract")
    result={}
    for a in ASSETS:
        records={x["file"]:x for x in m["symbols"][a]["source_files"]}
        expected=[f"{a}-fundingRate-{month}.zip" for month in MONTHS]
        if any(x not in records for x in expected):
            raise ValueError(a+" missing official monthly manifest")
        selected=[records[x] for x in expected]
        if sum(x["rows"] for x in selected)!=3381:
            raise ValueError(a+" funding event count")
        if m["symbols"][a]["canonical_csv_sha256"]!=c["funding"][a]["raw_sha256"]:
            raise ValueError(a+" cross-manifest SHA mismatch")
        result[a]={"months":len(selected),"events":sum(x["rows"] for x in selected)}
    return {"phase":695,"decision":"PASS_PINNED_METADATA_ONLY_VENDOR_UNVERIFIED",
            "assets":result,"historical_pnl_computed":False,
            "vendor_origin_attested":False,"promotion_eligible":False}
if __name__=="__main__":
    print(json.dumps(audit(),sort_keys=True))
