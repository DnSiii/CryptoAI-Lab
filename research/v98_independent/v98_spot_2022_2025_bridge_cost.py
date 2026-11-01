#!/usr/bin/env python3
"""V98 Independent source-only 2022-25 spot mask bridge + conditional 2025 two-leg fee diagnostic.
No PnL, no trading signals, no validation holdout, no V99 access.
"""
from __future__ import annotations
import argparse,csv,datetime as dt,hashlib,io,json,math
from pathlib import Path

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOUR=3600000
START=1669852800000  # 2022-12-01 00:00 UTC
SPLIT=1735689600000  # 2025-01-01 00:00 UTC
END=1767225600000    # 2026-01-01 00:00 UTC, exclusive
HQ_MANIFEST="02f1eef3fb3bd5a8a4f7ab7e60379474f091c961f9be98217b8b9792f75ef3a9"
SPOT25_SHA="069bec10906e476e19470b042d40ce3fa7d654228de9cff50bd53ad91ed74156"
NH_RECEIPT_SHA="7ce4ec7e2a6980838fa0179729b3cc6da8f131806b03e070590146d6d6ca046b"
OUT_FIELDS=("asset","open_time_ms","spot_close","quote_volume","observed","full_hour","source_era","provider_zip_sha256")
HQ_FIELDS=["asset","open_time_ms","observed","full_hour","open","high","low","close","quote_volume"]
NEW_FIELDS=["asset","open_time_ms","open","high","low","close","quote_volume","source_zip_sha256"]
PERP_FIELDS=["open_time_ms","open","high","low","close","quote_volume"]
GAP=int(dt.datetime(2023,3,24,13,tzinfo=dt.timezone.utc).timestamp()*1000)
def sha(b):return hashlib.sha256(b).hexdigest()
def read_csv(raw,fields):
    stream=io.StringIO(raw.decode("utf-8"),newline="")
    reader=csv.DictReader(stream)
    if reader.fieldnames!=fields:raise ValueError("SOURCE_SCHEMA")
    return list(reader)
def valid_price(row):
    o,h,l,c,q=[float(row[k]) for k in ("open","high","low","close","quote_volume")]
    if not all(map(math.isfinite,(o,h,l,c,q))) or min(o,h,l,c)<=0 or q<0 or l>min(o,c) or h<max(o,c):
        raise ValueError("SOURCE_PRICE_GEOMETRY")
    return c,q
def month_key(ts):
    return dt.datetime.fromtimestamp(ts/1000,dt.timezone.utc).strftime("%Y-%m")
def source_bridge(hq_raw,hq_receipt,new_raw,new_receipt):
    if hq_receipt.get("decision")!="PASS_HQ_MASKED_SOURCE_ONLY_NOT_ECONOMIC" or hq_receipt.get("publisher_manifest_sha256")!=HQ_MANIFEST:
        raise ValueError("HQ_PUBLISHER_CUSTODY")
    if sha(hq_raw)!=hq_receipt.get("canonical_sha256") or hq_receipt.get("eligible_full_hour_asset_hours")!=73144:
        raise ValueError("HQ_SOURCE_HASH_OR_MASK")
    if hq_receipt.get("complete_grid_source_rejection_still_active") is not True or hq_receipt.get("historical_system_pnl_computed") is not False:
        raise ValueError("HQ_REJECTED_SOURCE_FIREWALL")
    if new_receipt.get("decision")!="PASS_MASKED_SPOT_2025_SOURCE_ONLY_NOT_ECONOMIC" or sha(new_raw)!=SPOT25_SHA or new_receipt.get("canonical_sha256")!=SPOT25_SHA:
        raise ValueError("SPOT25_SOURCE_CUSTODY")
    if any(new_receipt.get(k) is not False for k in ("pnl_computed","holdout_accessed","data_2026_accessed","external_benchmarks_accessed","trading_authorized")):
        raise ValueError("SPOT25_FIREWALL")
    if new_receipt.get("complete_grid_2022_2024_source_rejection_still_active") is not True:
        raise ValueError("SPOT25_REJECTED_SOURCE_FIREWALL")
    hq_archives={(a["asset"],a["month"]):a["sha256"] for a in hq_receipt["archives"]}
    new_archives={a["archive"]:a["sha256"] for a in new_receipt["archives"]}
    if len(hq_archives)!=100 or len(new_archives)!=48:raise ValueError("ARCHIVE_COVERAGE")
    old=read_csv(hq_raw,HQ_FIELDS);new=read_csv(new_raw,NEW_FIELDS)
    if len(old)!=73152 or len(new)!=35040:raise ValueError("SPOT_ROWS_COUNT")
    output=io.StringIO(newline="");w=csv.writer(output,lineterminator="\n");w.writerow(OUT_FIELDS)
    counts={"calendar":0,"observed":0,"eligible":0,"missing":0,"partial":0}
    for j,asset in enumerate(ASSETS):
        old_asset=old[j*18288:(j+1)*18288]
        new_asset=new[j*8760:(j+1)*8760]
        for k,ts in enumerate(range(START,END,HOUR)):
            is_old=ts<SPLIT
            row=old_asset[k] if is_old else new_asset[k-18288]
            if row["asset"]!=asset or int(row["open_time_ms"])!=ts:raise ValueError("SPOT_CALENDAR_OR_ORDER")
            ym=month_key(ts)
            if is_old:
                digest=hq_archives.get((asset,ym))
                if not digest:raise ValueError("HQ_ARCHIVE_MISSING")
                observed=row["observed"]=="1";full=row["full_hour"]=="1"
                if row["observed"] not in ("0","1") or row["full_hour"] not in ("0","1") or (full and not observed):
                    raise ValueError("HQ_MASK_SCHEMA")
                if observed:
                    c,q=valid_price(row)
                else:
                    if any(row[z] for z in ("open","high","low","close","quote_volume")):raise ValueError("HQ_GAP_PRICE_NOT_EMPTY")
                    c=q=None
                # 12:00 is a real, early-closed publisher bar; 13:00 is absent.
                expected_gap=ts==GAP;expected_partial=ts==GAP-HOUR
                if expected_gap!=(not observed) or expected_partial!=(observed and not full):
                    raise ValueError("HQ_UNEXPECTED_GAP_OR_PARTIAL")
            else:
                name=f"{asset}-1h-{ym}.zip"
                digest=new_archives.get(name)
                if not digest or row["source_zip_sha256"]!=digest:raise ValueError("SPOT25_ARCHIVE_ROW_PROVENANCE")
                c,q=valid_price(row);observed=full=True
            counts["calendar"]+=1;counts["observed"]+=int(observed);counts["eligible"]+=int(full)
            counts["missing"]+=int(not observed);counts["partial"]+=int(observed and not full)
            w.writerow((asset,ts,("" if c is None else row["close"]),
                        ("" if q is None else row["quote_volume"]),int(observed),int(full),
                        ("HQ_MASKED_2022_2024" if is_old else "OFFICIAL_2025"),digest))
    if counts!={"calendar":108192,"observed":108188,"eligible":108184,"missing":4,"partial":4}:
        raise ValueError("SPOT_FULL_MASK_COUNTS")
    canonical=output.getvalue().encode("utf-8")
    return canonical,counts

def fee_diagnostic(new_raw,new_receipt,nh_dir):
    if sha(new_raw)!=SPOT25_SHA or new_receipt["canonical_sha256"]!=SPOT25_SHA:
        raise ValueError("DIAGNOSTIC_SPOT_SHA")
    nh_dir=Path(nh_dir)
    rbytes=(nh_dir/"nh_2025_official_source_receipt.json").read_bytes()
    if sha(rbytes)!=NH_RECEIPT_SHA:raise ValueError("DIAGNOSTIC_PERP_RECEIPT_SHA")
    receipt=json.loads(rbytes)
    if receipt.get("decision")!="PASS_NH_2025_OFFICIAL_SOURCE_ONLY_NOT_VALIDATION":
        raise ValueError("DIAGNOSTIC_PERP_SOURCE_STATUS")
    spot=read_csv(new_raw,NEW_FIELDS)
    result={}
    for j,asset in enumerate(ASSETS):
        path=nh_dir/f"{asset}_1h_2025.csv"
        if sha(path.read_bytes())!=receipt["assets"][asset]["ohlc_csv_sha256"]:
            raise ValueError("DIAGNOSTIC_PERP_CSV_SHA")
        perp=read_csv(path.read_bytes(),PERP_FIELDS)
        if len(perp)!=8760:raise ValueError("DIAGNOSTIC_PERP_COUNT")
        diffs=[]
        for k,row in enumerate(perp):
            s=spot[j*8760+k]
            ts=SPLIT+k*HOUR
            if s["asset"]!=asset or int(s["open_time_ms"])!=ts or int(row["open_time_ms"])!=ts:
                raise ValueError("DIAGNOSTIC_JOIN_TIMESTAMP")
            cspot,_=valid_price(s);cperp,_=valid_price(row)
            diffs.append(abs(cperp/cspot-1)*10000)
        ordered=sorted(diffs)
        result[asset]={"hours":8760,
            "median_abs_basis_bps":round(ordered[len(ordered)//2],6),
            "p99_abs_basis_bps":round(ordered[int(.99*(len(ordered)-1))],6),
            "max_abs_basis_bps":round(ordered[-1],6),
            "hours_abs_basis_above_illustrative_four_fill_fee_budgets":{
                str(b):sum(x>b for x in diffs) for b in (8,16,24,30)}}
    return {"decision":"PASS_DESCRIPTIVE_TWO_LEG_FEE_FEASIBILITY_NOT_PNL",
            "scenario_fee_bps_per_fill":[2,4,6],"four_fills_assumed":True,
            "fee_budgets_bps":[8,16,24,30],"published_regular_spot_taker_bps":10,
            "published_regular_perp_taker_bps":5,"published_regular_two_leg_taker_roundtrip_bps":30,
            "published_fee_schedule_current_not_historical":True,
            "funding_borrow_spread_slippage_excluded":True,
            "actual_account_fees_verified":False,"tradeable_edge_proven":False,
            "pnl_computed":False,"2025_exposed_training_only":True,"assets":result}

def main():
    p=argparse.ArgumentParser()
    for k in ("hq-dir","spot25-dir","nh-dir","output-dir"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    h=Path(a.hq_dir);s=Path(a.spot25_dir);out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True)
    hr=json.loads((h/"hq_masked_source_receipt.json").read_text())
    sr=json.loads((s/"v98_spot_2025_masked_source_receipt.json").read_text())
    hb=(h/"hq_spot_calendar_masked.csv").read_bytes()
    sb=(s/"v98_spot_2025_observed_only.csv").read_bytes()
    raw,counts=source_bridge(hb,hr,sb,sr)
    # Exact deterministic replay without re-reading remote sources.
    repeat,_=source_bridge(hb,hr,sb,sr)
    if raw!=repeat:raise ValueError("SPOT_BRIDGE_NONDETERMINISM")
    (out/"v98_spot_2022_2025_masked_calendar.csv").write_bytes(raw)
    diag=fee_diagnostic(sb,sr,a.nh_dir)
    result={"decision":"PASS_AUTHENTICATED_SPOT_2022_2025_MASKED_BRIDGE_NOT_PNL",
            "counts":counts,"canonical_sha256":sha(raw),
            "hq_canonical_sha256":sha(hb),"spot25_canonical_sha256":sha(sb),
            "hq_publisher_manifest_sha256":HQ_MANIFEST,
            "nh_receipt_sha256":NH_RECEIPT_SHA,"two_pass_byte_identical":True,
            "rejected_strict_complete_grid_source_stays_rejected":True,
            "2025_exposed_training_only":True,"holdout_accessed":False,
            "data_2026_accessed":False,"external_benchmarks_accessed":False,
            "pnl_computed":False,"trading_authorized":False,
            "two_leg_fee_diagnostic":diag}
    (out/"v98_spot_bridge_cost_receipt.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"decision":result["decision"],"counts":counts,"sha256":sha(raw),
                      "fee_diagnostic":diag},sort_keys=True))
if __name__=="__main__":main()
