"""Strict append-only storage of contemporaneous V99 OKX source receipts.

This stores first-party source evidence on a SEPARATE receipt branch. It does
not publish paper, change any model/holdout, or grant execution permission.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import datetime,timedelta,timezone
from pathlib import Path

INSTRUMENTS=("BTC-USDT-SWAP","ETH-USDT-SWAP","SOL-USDT-SWAP","XRP-USDT-SWAP","DOGE-USDT-SWAP")
EXPECTED=("manifest.json","clock_before.raw.json","clock_after.raw.json",
          *(f"{x}.raw.json" for x in INSTRUMENTS))

def strict(raw):
    def unique(pairs):
        obj={}
        for key,value in pairs:
            if key in obj: raise ValueError("duplicate JSON property")
            obj[key]=value
        return obj
    def invalid(x):
        raise ValueError("nonfinite JSON value")
    data=json.loads(raw,parse_constant=invalid,object_pairs_hook=unique)
    if not isinstance(data,dict):raise ValueError("JSON object required")
    return data

def utc(value):
    if not isinstance(value,str):raise ValueError("UTC timestamp required")
    v=datetime.fromisoformat(value.replace("Z","+00:00"))
    if v.tzinfo is None or v.utcoffset()!=timedelta(0):
        raise ValueError("explicit UTC required")
    return v.astimezone(timezone.utc)

def verify_source(directory:Path):
    if not directory.is_dir():raise ValueError("source receipt directory missing")
    files={x.name for x in directory.iterdir()}
    if files!=set(EXPECTED):
        raise ValueError("source files incomplete or contain unapproved files")
    manifest=strict((directory/"manifest.json").read_bytes())
    if manifest.get("schema")!="V99_R106_OKX_PROSPECTIVE_ASOF_V1" or manifest.get("mode")!="DATA_ONLY":
        raise ValueError("wrong source/version")
    if (manifest.get("paper_publication_authorized") is not False or
        manifest.get("promotion_authorized") is not False or
        manifest.get("original_r106_binance_fee_and_funding_model_transfer_authorized") is not False or
        manifest.get("real_orders_enabled") is not False):
        raise ValueError("source cannot authorize trading")
    if set(manifest.get("instruments",{}))!=set(INSTRUMENTS):
        raise ValueError("five frozen OKX instruments required")
    before=manifest.get("clock_receipts")
    if not isinstance(before,list) or len(before)!=2:
        raise ValueError("clock corroboration missing")
    hashes={"clock_before.raw.json":before[0]["sha256"],
            "clock_after.raw.json":before[1]["sha256"]}
    for inst,item in manifest["instruments"].items():
        hashes[f"{inst}.raw.json"]=item["source_raw_sha256"]
        if item.get("latest_confirmed_close_utc") is None:
            raise ValueError("missing confirmed close")
        if utc(item["latest_confirmed_close_utc"])>utc(item["received_utc"]):
            raise ValueError("reported confirmed bar is not closed")
    for filename,expected in hashes.items():
        if not isinstance(expected,str) or not re.fullmatch(r"[a-f0-9]{64}",expected):
            raise ValueError("invalid source hash")
        real=hashlib.sha256((directory/filename).read_bytes()).hexdigest()
        if real!=expected:
            raise ValueError("source raw evidence tampered: "+filename)
    acquired=utc(manifest["last_received_utc"])
    earliest=utc(manifest["earliest_candidate_decision_utc"])
    if earliest!=acquired.replace(minute=0,second=0,microsecond=0)+timedelta(hours=2):
        raise ValueError("conservative next-hour t-1 violation")
    clock=manifest.get("server_clock_corrob")
    if not isinstance(clock,dict) or type(clock.get("before_ms")) is not int or type(clock.get("after_ms")) is not int:
        raise ValueError("source clock not corroborated")
    if clock["before_ms"]>clock["after_ms"]:
        raise ValueError("source clock regressed")
    return manifest

def append(source:Path,root:Path,run_id:str):
    manifest=verify_source(source)
    if not isinstance(run_id,str) or not re.fullmatch(r"\d{8,15}",run_id):
        raise ValueError("real GitHub Actions run ID required")
    acquired=utc(manifest["last_received_utc"])
    bucket=acquired.strftime("%Y-%m-%dT%H")
    target=root/bucket
    root.mkdir(parents=True,exist_ok=True)
    if target.exists():
        # No update/overwrite on this branch, even if the source changed.
        return {"status":"ALREADY_PRESENT_UNCHANGED","bucket":bucket,"destination":str(target)}
    temp=Path(tempfile.mkdtemp(prefix=".pending-",dir=root))
    try:
        for name in EXPECTED:
            shutil.copyfile(source/name,temp/name)
        digest=hashlib.sha256((temp/"manifest.json").read_bytes()).hexdigest()
        (temp/"receipt_commit_provenance.json").write_text(json.dumps({
            "run_id":run_id,
            "manifest_sha256":digest,
            "acquired_utc":manifest["last_received_utc"],
            "immutable_bucket_utc":bucket,
            "paper_or_model_changes_allowed":False,
        },sort_keys=True,indent=2)+"\n")
        if target.exists():
            raise ValueError("receipt race: target appeared; do not overwrite")
        temp.rename(target)
    finally:
        if temp.exists():shutil.rmtree(temp)
    return {"status":"APPENDED_NEW_FIRST_PARTY_RECEIPT","bucket":bucket,
            "destination":str(target),"manifest_sha256":digest,
            "paper_publication_authorized":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--run-id",required=True)
    args=p.parse_args()
    result=append(args.source,args.root,args.run_id)
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":
    main()
