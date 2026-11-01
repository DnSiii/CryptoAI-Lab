#!/usr/bin/env python3
"""Independent V98 spot 2025 masked-source receipt/CSV oracle, never computes trading PnL."""
import argparse,csv,datetime as dt,hashlib,io,json,math
from pathlib import Path

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
FIELDS=["asset","open_time_ms","open","high","low","close","quote_volume","source_zip_sha256"]
HOUR=3600000
START=1735689600000
END=1767225600000

def audit(raw,receipt):
    if receipt["decision"]!="PASS_MASKED_SPOT_2025_SOURCE_ONLY_NOT_ECONOMIC":
        raise ValueError("SPOT_2025_DECISION")
    if hashlib.sha256(raw).hexdigest()!=receipt["canonical_sha256"]:
        raise ValueError("SPOT_2025_CANONICAL_HASH")
    if receipt["archive_count"]!=48 or receipt["provider_sha256_verified"]!=48:
        raise ValueError("SPOT_2025_ARCHIVE_COUNT")
    if any(receipt[k] is not False for k in
           ("pnl_computed","holdout_accessed","data_2026_accessed",
            "external_benchmarks_accessed","trading_authorized")):
        raise ValueError("SPOT_2025_RESEARCH_FIREWALL")
    if receipt["complete_grid_2022_2024_source_rejection_still_active"] is not True:
        raise ValueError("SPOT_2022_2024_REJECTED_SOURCE_REHABILITATED")
    archive={}
    for item in receipt["archives"]:
        name=item["archive"]
        if not name.endswith(".zip") or name in archive:raise ValueError("SPOT_ARCHIVE_DUPLICATE")
        archive[name]=item
    if len(archive)!=48:raise ValueError("SPOT_ARCHIVE_GEOMETRY")
    stream=io.StringIO(raw.decode("utf-8"),newline="")
    reader=csv.DictReader(stream)
    if reader.fieldnames!=FIELDS:raise ValueError("SPOT_CANONICAL_SCHEMA")
    observed={a:set() for a in ASSETS};counts={a:0 for a in ASSETS}
    previous=None
    for row in reader:
        asset=row["asset"]
        if asset not in ASSETS:raise ValueError("SPOT_BAD_ASSET")
        ts=int(row["open_time_ms"])
        if ts<START or ts>=END or (ts-START)%HOUR:
            raise ValueError("SPOT_OFF_GRID")
        key=(ASSETS.index(asset),ts)
        if previous is not None and key<=previous:raise ValueError("SPOT_UNSORTED_OR_DUPLICATE")
        previous=key
        month=dt.datetime.fromtimestamp(ts/1000,dt.timezone.utc).month
        filename=f"{asset}-1h-2025-{month:02d}.zip"
        if filename not in archive or row["source_zip_sha256"]!=archive[filename]["sha256"]:
            raise ValueError("SPOT_ARCHIVE_ROW_PROVENANCE")
        o,h,l,c,q=(float(row[x]) for x in ("open","high","low","close","quote_volume"))
        if not all(math.isfinite(x) for x in (o,h,l,c,q)) or min(o,h,l,c)<=0 or q<0 or l>min(o,c) or h<max(o,c):
            raise ValueError("SPOT_ROW_OHLC")
        observed[asset].add(ts);counts[asset]+=1
    missing_total=0
    for asset in ASSETS:
        expected=set(range(START,END,HOUR))
        absent=sorted(expected-observed[asset])
        missing_total+=len(absent)
        stated=[dt.datetime.fromtimestamp(t/1000,dt.timezone.utc).isoformat() for t in absent]
        if stated!=receipt["missing_utc"][asset]:
            raise ValueError("SPOT_MISSING_MASK_MISMATCH")
        if counts[asset]!=receipt["per_asset_observed_hours"][asset]:
            raise ValueError("SPOT_ASSET_COUNT_MISMATCH")
    if sum(counts.values())!=receipt["observed_asset_hours"] or missing_total!=receipt["missing_asset_hours"]:
        raise ValueError("SPOT_GLOBAL_COVERAGE_MISMATCH")
    if sum(counts.values())+missing_total!=35040 or receipt["expected_asset_hours"]!=35040:
        raise ValueError("SPOT_EXPECTED_CALENDAR_MISMATCH")
    return {"decision":"PASS_INDEPENDENT_SPOT_2025_MASKED_SOURCE_ORACLE_NOT_PNL",
            "observed_asset_hours":sum(counts.values()),
            "missing_asset_hours":missing_total,
            "archives":len(archive),"assets":list(ASSETS),
            "pnl_computed":False,"holdout_accessed":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--csv",required=True);p.add_argument("--receipt",required=True)
    args=p.parse_args()
    raw=Path(args.csv).read_bytes()
    receipt=json.loads(Path(args.receipt).read_text())
    out=audit(raw,receipt)
    # Independent negative controls; do not mutate canonical data or write back.
    altered=dict(receipt);altered["canonical_sha256"]="0"*64
    try:audit(raw,altered)
    except ValueError as e:assert str(e)=="SPOT_2025_CANONICAL_HASH"
    else:raise AssertionError("SPOT_HASH_TAMPER_ACCEPTED")
    altered=dict(receipt);altered["data_2026_accessed"]=True
    try:audit(raw,altered)
    except ValueError as e:assert str(e)=="SPOT_2025_RESEARCH_FIREWALL"
    else:raise AssertionError("SPOT_FUTURE_ACCESS_TAMPER_ACCEPTED")
    out["tamper_cases_rejected"]=2
    print(json.dumps(out,sort_keys=True))

if __name__=="__main__":main()
