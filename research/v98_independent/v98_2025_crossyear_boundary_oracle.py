#!/usr/bin/env python3
"""V98 independent read-only source oracle; no signals or PnL."""
import argparse,csv,hashlib,io,json,zipfile
from pathlib import Path
def sha(b):return hashlib.sha256(b).hexdigest()
def rows(p):
    with open(p,newline="") as f:return list(csv.DictReader(f))
def run(original,derived):
    original=Path(original);derived=Path(derived)
    r=json.loads((derived/"v98_2025_boundary_receipt.json").read_text())
    if r.get("decision")!="PASS_V98_2025_TRAINING_SOURCE_CROSSYEAR_BOUNDARY_NOT_VALIDATION" or r.get("pnl_computed") is not False:
        raise ValueError("ORACLE_INVALID_RECEIPT")
    names=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
    if set(r["assets"])!=set(names):raise ValueError("ORACLE_SCOPE")
    changed=0
    for a in names:
        old=rows(original/f"{a}_funding_2025.csv")
        target=derived/f"{a}_funding_2025_boundary_corrected.csv"
        new=rows(target)
        if len(old)!=1095 or len(new)!=1095 or new[1:]!=old[1:]:
            raise ValueError("ORACLE_NONBOUNDARY_MUTATION_"+a)
        for field in ("funding_slot_ms","funding_rate","exchange_offset_ms"):
            if old[0][field]!=new[0][field]:raise ValueError("ORACLE_RATE_OR_SLOT_MUTATION_"+a)
        name=f"{a}-1h-2024-12.zip";vendor=derived/"official_2024_dec_vendor"
        raw=(vendor/name).read_bytes();check=(vendor/(name+".CHECKSUM")).read_text().split()
        if len(check)!=2 or check[1].lstrip("*./")!=name or sha(raw)!=check[0].lower():
            raise ValueError("ORACLE_VENDOR_CHECKSUM_"+a)
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            if z.namelist()!=[name[:-4]+".csv"]:raise ValueError("ORACLE_VENDOR_ZIP_MEMBER")
            data=list(csv.reader(io.StringIO(z.read(z.namelist()[0]).decode("utf-8-sig"))))
        if data[0][0].lower()=="open_time":data.pop(0)
        if len(data)!=744 or int(data[-1][0])!=1735686000000:
            raise ValueError("ORACLE_PREVIOUS_BAR_"+a)
        low=min(float(old[0]["mark_lower_bound"]),float(data[-1][3]))
        high=max(float(old[0]["mark_upper_bound"]),float(data[-1][2]))
        if float(new[0]["mark_lower_bound"])!=low or float(new[0]["mark_upper_bound"])!=high:
            raise ValueError("ORACLE_BOUNDARY_ARITHMETIC_"+a)
        if sha(target.read_bytes())!=r["assets"][a]["corrected_funding_sha256"] or sha(raw)!=r["assets"][a]["official_2024_12_mark_zip_sha256"]:
            raise ValueError("ORACLE_OUTPUT_SHA_"+a)
        changed+=int(old[0]!=new[0])
    return {"decision":"PASS_INDEPENDENT_V98_BOUNDARY_SOURCE_ORACLE_NOT_PNL",
            "reconciled_funding_rows":4380,"unchanged_nonboundary_rows":4376,
            "first_events_modified":changed,"exact_event_mark_proven":False}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--source-dir",required=True);p.add_argument("--corrected-dir",required=True)
    a=p.parse_args();print(json.dumps(run(a.source_dir,a.corrected_dir),sort_keys=True))
