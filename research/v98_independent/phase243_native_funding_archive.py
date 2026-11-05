#!/usr/bin/env python3
"""V98-only Binance USD-M native funding audit. Source evidence, NOT PnL."""
import argparse, csv, hashlib, io, json, re, zipfile
from datetime import datetime, timezone
from pathlib import Path
from phase243_clean4_official_archive_acquire import ASSETS, MONTHS, _fetch
BASE="https://data.binance.vision/data/futures/um/monthly/fundingRate"
def audit(blob, asset, month):
    name=f"{asset}-fundingRate-{month}.csv"
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        members=z.infolist()
        if len(members)!=1 or members[0].filename!=name or members[0].file_size>20_000_000:
            raise ValueError("INVALID_FUNDING_ZIP_MEMBER")
        reader=csv.DictReader(io.StringIO(z.read(name).decode("utf-8-sig")))
        columns=set(reader.fieldnames or [])
        if {"calc_time","funding_interval_hours","last_funding_rate"}.issubset(columns):
            time_col, rate_col = "calc_time", "last_funding_rate"
            interval_col = "funding_interval_hours"
        elif {"fundingTime","fundingRate"}.issubset(columns):
            time_col, rate_col = "fundingTime", "fundingRate"
            interval_col = None
        else:
            raise ValueError(f"INVALID_FUNDING_COLUMNS:{sorted(columns)}")
        year,mo=map(int,month.split("-"))
        lo=int(datetime(year,mo,1,tzinfo=timezone.utc).timestamp()*1000)
        hi=int(datetime(year+(mo==12),mo%12+1,1,tzinfo=timezone.utc).timestamp()*1000)
        times=[]
        for row in reader:
            t=int(row[time_col]); r=float(row[rate_col])
            if interval_col is not None:
                interval=float(row[interval_col])
                if not 0 < interval <= 24:
                    raise ValueError("INVALID_FUNDING_INTERVAL")
            if not lo<=t<hi or not -1<r<1: raise ValueError("INVALID_FUNDING_EVENT")
            times.append(t)
        if not times or times!=sorted(set(times)): raise ValueError("FUNDING_DUPLICATE_OR_ORDER")
        if times[0] - lo > 24*3600*1000 or hi - times[-1] > 24*3600*1000:
            raise ValueError("FUNDING_MONTH_BOUNDARY_GAP")
        if any(b-a > 24*3600*1000 for a,b in zip(times,times[1:])):
            raise ValueError("FUNDING_EVENT_GAP")
        return {"events":len(times),"first_ms":times[0],"last_ms":times[-1]}
def acquire(root, limit=None):
    root=Path(root)
    if "v98_independent" not in root.absolute().parts: raise ValueError("V98_NAMESPACE_REQUIRED")
    jobs=[(a,m) for a in ASSETS for m in MONTHS]
    if limit is not None:
        if limit<1: raise ValueError("INVALID_LIMIT")
        jobs=jobs[:limit]
    receipts={}
    for asset,month in jobs:
        name=f"{asset}-fundingRate-{month}.zip"
        url=f"{BASE}/{asset}/{name}"
        checksum=_fetch(url+".CHECKSUM",4096).decode("ascii").strip()
        tokens=checksum.split()
        if len(tokens)!=2 or not re.fullmatch("[0-9a-fA-F]{64}",tokens[0]) or tokens[1].lstrip("*")!=name:
            raise ValueError("INVALID_PROVIDER_FUNDING_CHECKSUM")
        blob=_fetch(url,5_000_000)
        sha=hashlib.sha256(blob).hexdigest()
        if sha!=tokens[0].lower(): raise ValueError("FUNDING_HASH_MISMATCH")
        evidence=audit(blob,asset,month)
        dest=root/"fundingRate"/asset/name
        dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.is_symlink() or dest.with_name(name+".CHECKSUM").is_symlink():
            raise ValueError("SYMLINKED_FUNDING_OUTPUT")
        if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest()!=sha:
            raise ValueError("EXISTING_FUNDING_CONFLICT")
        dest.write_bytes(blob)
        dest.with_name(name+".CHECKSUM").write_text(checksum+"\n")
        receipts[f"{asset}/{month}"]={"sha256":sha,"url":url,"checksum_url":url+".CHECKSUM",**evidence}
    return {"mode":"V98_NATIVE_FUNDING_SOURCE_ONLY","verified_archives":len(receipts),
            "expected_archives":148,"complete":len(receipts)==148,"holdout_accessed":False,
            "economic_validation":False,"funding_reconciled":False,"receipts":receipts}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,required=True)
    p.add_argument("--limit",type=int);args=p.parse_args()
    print(json.dumps(acquire(args.root,args.limit),sort_keys=True))
