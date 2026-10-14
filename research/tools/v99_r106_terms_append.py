"""Append-only raw OKX native contract/funding notices to source-evidence branch.

Standalone DATA_ONLY source artifact. Funding notice != realized cashflow.
Never overwrite old receipts or the published V99 research paper.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
import tempfile
from pathlib import Path
from datetime import timedelta

from research.tools.v99_r106_receipt_append import strict,utc,INSTRUMENTS

FILES=("manifest.json","clock_before.raw.json","clock_after.raw.json",
       *(f"{kind}_{inst}.raw.json" for inst in INSTRUMENTS
         for kind in ("metadata","funding")))

def validate(source:Path):
    if not source.is_dir() or {p.name for p in source.iterdir()}!=set(FILES):
        raise ValueError("incomplete/mismatched native terms receipt")
    manifest=strict((source/"manifest.json").read_bytes())
    if (manifest.get("schema")!="V99_R106_OKX_NATIVE_TERMS_ASOF_V1" or
        manifest.get("mode")!="DATA_ONLY" or
        set(manifest.get("contracts",{}))!=set(INSTRUMENTS)):
        raise ValueError("unexpected as-of term schema or instruments")
    for flag in ("fee_schedule_independently_proven",
                 "funding_cashflows_settled_and_pit_authenticated",
                 "binance_r106_parameters_crossvenue_transfer_authorized",
                 "paper_publication_authorized",
                 "promotion_authorized",
                 "real_orders_enabled",
                 "holdout_accessed"):
        if manifest.get(flag) is not False:
            raise ValueError("source cannot confer funding, economic or trading validity: "+flag)
    clock=manifest.get("first_party_clock_receipts")
    if not isinstance(clock,list) or len(clock)!=2:
        raise ValueError("missing OKX clock receipt references")
    expected={"clock_before.raw.json":clock[0],
              "clock_after.raw.json":clock[1]}
    observed=utc(manifest.get("acquisition_last_utc"))
    earliest=utc(manifest.get("earliest_safe_decision_utc"))
    if earliest!=observed.replace(minute=0,second=0,microsecond=0)+timedelta(hours=2):
        raise ValueError("receipt t-1 eligibility is inconsistent")
    for inst,entry in manifest["contracts"].items():
        contract=entry.get("contract") or {}
        funding=entry.get("funding_notice") or {}
        if (contract.get("instId")!=inst or contract.get("state")!="live" or
            contract.get("ctType")!="linear" or contract.get("settleCcy")!="USDT" or
            funding.get("instId")!=inst or funding.get("settled_cashflow_authenticated") is not False):
            raise ValueError("wrong native contract/funding semantics")
        for key,original in (("metadata","contract"),("funding","funding")):
            expected[f"{key}_{inst}.raw.json"]=entry[original+"_raw_sha256"]
            if utc(entry[key if key=="funding" else "contract"+"_received_utc"])>observed:
                raise ValueError("native term observation after manifest final clock")
    for path,digest in expected.items():
        if not isinstance(digest,str) or not re.fullmatch("[a-f0-9]{64}",digest):
            raise ValueError("invalid first-party source digest")
        if hashlib.sha256((source/path).read_bytes()).hexdigest()!=digest:
            raise ValueError("native-term source bytes failed SHA256: "+path)
    return manifest

def append(source:Path,root:Path,run_id:str):
    manifest=validate(source)
    if not re.fullmatch(r"\d{8,15}",run_id):
        raise ValueError("GitHub Actions run ID required")
    bucket=utc(manifest["acquisition_last_utc"]).strftime("%Y-%m-%dT%H")
    target=root/bucket
    root.mkdir(parents=True,exist_ok=True)
    if target.exists():
        return {"status":"ALREADY_PRESENT_IMMUTABLE","bucket":bucket}
    work=Path(tempfile.mkdtemp(dir=root,prefix=".pending-"))
    try:
        for name in FILES:
            shutil.copyfile(source/name,work/name)
        (work/"receipt_commit_provenance.json").write_text(json.dumps({
            "run_id":run_id,
            "observed_utc":manifest["acquisition_last_utc"],
            "bucket":bucket,
            "sha256_manifest":hashlib.sha256((work/"manifest.json").read_bytes()).hexdigest(),
            "native_fee_and_settled_funding_verified":False,
            "paper_or_model_changes_allowed":False,
        },sort_keys=True,indent=2)+"\n")
        if target.exists():
            raise ValueError("receipt appeared during staging; no overwrite allowed")
        work.rename(target)
    finally:
        if work.exists():shutil.rmtree(work)
    return {"status":"APPENDED_FIRST_PARTY_NATIVE_TERMS_ONLY","bucket":bucket,
            "paper_publication_authorized":False}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",required=True,type=Path)
    ap.add_argument("--root",required=True,type=Path)
    ap.add_argument("--run-id",required=True)
    args=ap.parse_args()
    print(json.dumps(append(args.source,args.root,args.run_id),sort_keys=True))

if __name__=="__main__":
    main()
