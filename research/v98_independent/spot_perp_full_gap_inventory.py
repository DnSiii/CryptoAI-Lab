#!/usr/bin/env python3
"""V98 Independent read-only 100-archive spot source discrepancy inventory.
Does NOT repair, fill, select alpha, calculate PnL or access 2025.
"""
from __future__ import annotations
import csv,datetime as dt,hashlib,io,json,zipfile
from pathlib import Path
from spot_perp_source_only import ASSETS,MONTHS,SOURCE,get,month_hours
OUT=Path(__file__).resolve().parent/"spot_perp_full_gap_inventory.json"
def iso(ms):
    return dt.datetime.fromtimestamp(ms/1000,dt.timezone.utc).isoformat()
def run():
    errors=[];archives=[];total=0
    for asset in ASSETS:
        for year,month in MONTHS:
            filename=f"{asset}-1h-{year}-{month:02d}.zip"
            url=f"{SOURCE}/{asset}/1h/{filename}"
            raw=get(url)
            provider=get(url+".CHECKSUM").decode("ascii").strip().split()[0].lower()
            digest=hashlib.sha256(raw).hexdigest()
            if digest!=provider:raise ValueError("INVENTORY_PROVIDER_SHA_MISMATCH "+filename)
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                names=[n for n in z.namelist() if not n.endswith("/")]
                if names!=[filename.replace(".zip",".csv")]:
                    raise ValueError("INVENTORY_ZIP_MEMBER "+filename)
                with z.open(names[0]) as f:
                    rows=list(csv.reader(io.TextIOWrapper(f,encoding="utf-8",newline="")))
            expected=month_hours(year,month)
            got=[int(row[0]) for row in rows]
            missing=sorted(set(expected)-set(got))
            extras=sorted(set(got)-set(expected))
            dup=len(got)-len(set(got))
            wrong=(len(got)!=len(expected) or bool(missing) or bool(extras) or dup!=0 or got!=sorted(got))
            item={"archive":filename,"provider_sha256":provider,"rows":len(rows),
                "expected_rows":len(expected),"missing_utc":[iso(x) for x in missing],
                "unexpected_utc":[iso(x) for x in extras],"duplicate_timestamps":dup,
                "strictly_increasing":all(x<y for x,y in zip(got,got[1:]))}
            archives.append(item);total+=len(rows)
            if wrong:
                errors.append(item)
                print("SPOT_OFFICIAL_SOURCE_GAP",json.dumps(item,sort_keys=True),flush=True)
    out={"decision":"READ_ONLY_100_ARCHIVE_SOURCE_GAP_INVENTORY_NOT_SOURCE_RESCUE",
         "archive_count":len(archives),"provider_sha256_verified":len(archives),
         "observed_asset_hours":total,"expected_asset_hours":73152,
         "defective_archives":len(errors),"errors":errors,"archives":archives,
         "holdout_2025_read":False,"historical_system_pnl_computed":False,
         "trading_authorized":False}
    OUT.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print("SPOT_GAP_INVENTORY",len(archives),len(errors),total,flush=True)
if __name__=="__main__":
    # Preserve the rejected complete-grid inventory unchanged. HQ is a
    # separately preregistered masked-source protocol; its success does NOT
    # rehabilitate that source or authorize any alpha/PNL.
    run()
    from hq_gap_aware_spot_source import run as run_hq
    run_hq()
    receipt_path = OUT.parent / "hq_gap_aware_spot_source_only" / "hq_masked_source_receipt.json"
    hq = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (hq.get("decision") != "PASS_HQ_MASKED_SOURCE_ONLY_NOT_ECONOMIC"
            or hq.get("complete_grid_source_rejection_still_active") is not True
            or hq.get("validation_2025_read") is not False
            or hq.get("historical_system_pnl_computed") is not False):
        raise ValueError("HQ_INDEPENDENT_RECEIPT_FIREWALL")
    inventory = json.loads(OUT.read_text(encoding="utf-8"))
    if inventory.get("decision") != "READ_ONLY_100_ARCHIVE_SOURCE_GAP_INVENTORY_NOT_SOURCE_RESCUE":
        raise ValueError("HQ_REJECTED_INVENTORY_DECISION_CHANGED")
    from hq_independent_receipt_reconcile import reconcile
    independent = reconcile(inventory, hq)
    inventory["separate_hq_masked_source_only_receipt"] = hq
    inventory["separate_hq_independent_source_reconciliation"] = independent
    OUT.write_text(json.dumps(inventory, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("HQ_OFFICIAL_100_SOURCE_ONLY_PASS", hq["canonical_sha256"], flush=True)
    print("HQ_INDEPENDENT_RECONCILE_PASS", independent["archive_pairs"],
          independent["eligible_full_hour_asset_hours"], flush=True)

