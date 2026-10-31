#!/usr/bin/env python3
"""V98-only correction of 2025 first funding envelope; source-only, no PnL."""
import argparse,csv,hashlib,io,json,math,urllib.request,zipfile
from pathlib import Path
from datetime import datetime,timezone
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
BASE="https://data.binance.vision/data/futures/um/monthly/markPriceKlines"
PIN="7ce4ec7e2a6980838fa0179729b3cc6da8f131806b03e070590146d6d6ca046b"
START=1735689600000
HOUR=3600000
def sha(x):return hashlib.sha256(x).hexdigest()
def read_csv(path):
    with open(path,newline="") as f:
        r=csv.DictReader(f)
        return list(r),tuple(r.fieldnames or ())
def official(asset,dest):
    name=f"{asset}-1h-2024-12.zip"
    base=f"{BASE}/{asset}/1h/{name}"
    raw=[]
    for suffix in (".CHECKSUM",""):
        url=base+suffix
        req=urllib.request.Request(url,headers={"User-Agent":"V98-Independent-Crossyear-Source/1.0"})
        with urllib.request.urlopen(req,timeout=60) as response:
            if response.status!=200 or response.geturl()!=url:raise ValueError("V98_VENDOR_REDIRECT")
            b=response.read(15000001)
        if len(b)>15000000:raise ValueError("V98_VENDOR_OVERSIZE")
        raw.append(b)
        (dest/(name+suffix)).write_bytes(b)
    declaration=raw[0].decode("utf-8-sig").strip().split()
    if len(declaration)!=2 or declaration[1].lstrip("*./")!=name or sha(raw[1])!=declaration[0].lower():
        raise ValueError("V98_VENDOR_CHECKSUM_"+asset)
    with zipfile.ZipFile(io.BytesIO(raw[1])) as z:
        if z.namelist()!=[name[:-4]+".csv"]:raise ValueError("V98_VENDOR_MEMBER_"+asset)
        lines=list(csv.reader(io.StringIO(z.read(z.namelist()[0]).decode("utf-8-sig"))))
    if lines and lines[0] and lines[0][0].lower()=="open_time":lines.pop(0)
    first=int(datetime(2024,12,1,tzinfo=timezone.utc).timestamp()*1000)
    if len(lines)!=744:raise ValueError("V98_VENDOR_MONTH_HOURS_"+asset)
    for i,row in enumerate(lines):
        if len(row)!=12 or int(row[0])!=first+i*HOUR or int(row[6])!=int(row[0])+HOUR-1:
            raise ValueError("V98_VENDOR_MONTH_CHRONOLOGY_"+asset)
    row=lines[-1]
    if int(row[0])!=START-HOUR:raise ValueError("V98_VENDOR_PREVIOUS_HOUR_"+asset)
    o,h,l,c=map(float,row[1:5])
    if not all(math.isfinite(x) and x>0 for x in (o,h,l,c)) or l>min(o,c) or h<max(o,c):
        raise ValueError("V98_VENDOR_PRICE_GEOMETRY_"+asset)
    return l,h,sha(raw[1]),base
def run(src,dest):
    src=Path(src);dest=Path(dest)
    if src.resolve()==dest.resolve() or (dest.exists() and any(dest.iterdir())):
        raise ValueError("V98_IMMUTABLE_SOURCE_OR_NONEMPTY_OUTPUT")
    receipt_raw=(src/"nh_2025_official_source_receipt.json").read_bytes()
    if sha(receipt_raw)!=PIN:raise ValueError("V98_PINNED_2025_RECEIPT_MISMATCH")
    receipt=json.loads(receipt_raw)
    if (receipt.get("decision")!="PASS_NH_2025_OFFICIAL_SOURCE_ONLY_NOT_VALIDATION"
        or receipt.get("official_archives_verified")!=144 or receipt.get("vendor_sha_verified") is not True
        or receipt.get("pnl_computed") is not False or receipt.get("exact_funding_tick_mark_attested") is not False
        or set(receipt["assets"])!=set(ASSETS)):
        raise ValueError("V98_SOURCE_RECEIPT_INVALID")
    dest.mkdir(parents=True,exist_ok=True)
    vendor=dest/"official_2024_dec_vendor";vendor.mkdir()
    details={}
    for asset in ASSETS:
        info=receipt["assets"][asset]
        opath=src/f"{asset}_1h_2025.csv";fpath=src/f"{asset}_funding_2025.csv"
        if sha(opath.read_bytes())!=info["ohlc_csv_sha256"] or sha(fpath.read_bytes())!=info["funding_envelope_csv_sha256"]:
            raise ValueError("V98_SOURCE_SHA_"+asset)
        candles,cols=read_csv(opath)
        if cols!=("open_time_ms","open","high","low","close","quote_volume") or len(candles)!=8760:
            raise ValueError("V98_2025_OHLC_SCHEMA_"+asset)
        for i,row in enumerate(candles):
            if int(row["open_time_ms"])!=START+i*HOUR:raise ValueError("V98_2025_OHLC_CHRONOLOGY_"+asset)
            o,h,l,c,q=(float(row[k]) for k in ("open","high","low","close","quote_volume"))
            if not all(math.isfinite(v) for v in (o,h,l,c,q)) or l<=0 or l>min(o,c) or h<max(o,c) or q<0:
                raise ValueError("V98_2025_OHLC_GEOMETRY_"+asset)
        funding,cols=read_csv(fpath)
        if cols!=("funding_slot_ms","funding_rate","exchange_offset_ms","mark_lower_bound","mark_upper_bound") or len(funding)!=1095:
            raise ValueError("V98_2025_FUNDING_SCHEMA_"+asset)
        for i,row in enumerate(funding):
            if int(row["funding_slot_ms"])!=START+i*8*HOUR or not 0<=int(row["exchange_offset_ms"])<=60000:
                raise ValueError("V98_2025_FUNDING_CHRONOLOGY_"+asset)
            rate,lo,hi=(float(row[k]) for k in ("funding_rate","mark_lower_bound","mark_upper_bound"))
            if not all(math.isfinite(v) for v in (rate,lo,hi)) or lo<=0 or hi<lo:
                raise ValueError("V98_2025_FUNDING_GEOMETRY_"+asset)
        previous_low,previous_high,vendor_sha,url=official(asset,vendor)
        old=[float(funding[0]["mark_lower_bound"]),float(funding[0]["mark_upper_bound"])]
        corrected=[min(old[0],previous_low),max(old[1],previous_high)]
        funding[0]["mark_lower_bound"]=format(corrected[0],".12g")
        funding[0]["mark_upper_bound"]=format(corrected[1],".12g")
        output=io.StringIO(newline="")
        w=csv.DictWriter(output,fieldnames=cols,lineterminator="\n")
        w.writeheader();w.writerows(funding)
        blob=output.getvalue().encode()
        (dest/f"{asset}_funding_2025_boundary_corrected.csv").write_bytes(blob)
        details[asset]={"original_funding_sha256":info["funding_envelope_csv_sha256"],
                        "corrected_funding_sha256":sha(blob),
                        "official_2024_12_mark_zip_sha256":vendor_sha,
                        "official_vendor_url":url,"previous_mark_bounds":[previous_low,previous_high],
                        "old_first_bounds":old,"corrected_first_bounds":corrected,
                        "other_events_unchanged":1094}
    result={"decision":"PASS_V98_2025_TRAINING_SOURCE_CROSSYEAR_BOUNDARY_NOT_VALIDATION",
            "original_artifact_id":12987237544,"original_artifact_zip_sha256":"0787b6a832e322dfab9c2724c006691228e9f162cb46cf1a16e26d7f06debfab",
            "original_receipt_sha256":PIN,"assets":details,
            "source_only":True,"pnl_computed":False,"2025_exposed_training_only":True,
            "2026_data_accessed":False,"exact_event_mark_attested":False,
            "holdout_accessed":False,"benchmarks_accessed":False}
    (dest/"v98_2025_boundary_receipt.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return result
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--source-dir",required=True);p.add_argument("--output-dir",required=True)
    a=p.parse_args();r=run(a.source_dir,a.output_dir)
    print(json.dumps({"decision":r["decision"],"assets":len(r["assets"]),
                      "first_events_changed":sum(x["old_first_bounds"]!=x["corrected_first_bounds"] for x in r["assets"].values())}))
