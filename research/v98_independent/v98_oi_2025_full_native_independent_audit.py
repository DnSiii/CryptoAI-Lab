#!/usr/bin/env python3
"""Independent artifact-only audit of V98 native OI 2025 exposed-training source.
Never downloads, computes PnL, inspects future holdout or uses benchmark signals.
"""
import argparse,csv,datetime as dt,hashlib,json,math,re,tempfile
from collections import Counter
from pathlib import Path

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
START=dt.date(2025,1,1)
END=dt.date(2025,12,31)
COLUMNS=("bar_open_utc","asset","oi_contracts","oi_value_usdt","taker_ratio","source_zip_sha256")

def audit(root):
    root=Path(root)
    report_path=root/"v98_oi_2025_native_source_report.json"
    csv_path=root/"v98_oi_2025_verified_hourly.csv"
    report=json.loads(report_path.read_text())
    if not (report.get("source_only") is True and
            report.get("2025_exposed_training_only") is True and
            report.get("2026_plus_accessed") is False and
            report.get("holdout_accessed") is False and
            report.get("pnl_computed") is False and
            report.get("paper_or_live_authorized") is False and
            report.get("external_benchmarks_used") is False):
        raise ValueError("V98_OI_2025_AUDIT_SCOPE_FIREWALL")
    if (report.get("date_start")!=str(START) or report.get("date_end")!=str(END)
        or report.get("assets")!=list(ASSETS)):
        raise ValueError("V98_OI_2025_AUDIT_DATE_ASSET_SCOPE")
    expected={(asset,str(START+dt.timedelta(days=i))) for asset in ASSETS
              for i in range((END-START).days+1)}
    manifest=report["manifest"]
    keyed={(x["asset"],x["date"]):x for x in manifest}
    if len(manifest)!=1460 or len(keyed)!=1460 or set(keyed)!=expected:
        raise ValueError("V98_OI_2025_AUDIT_MANIFEST_INVENTORY")
    good={k for k,v in keyed.items() if v["passed"] is True}
    bad=expected-good
    if (report["files_expected"]!=1460 or report["files_verified_complete"]!=len(good)
        or report["files_quarantined"]!=len(bad)):
        raise ValueError("V98_OI_2025_AUDIT_MANIFEST_COUNTS")
    for key in good:
        x=keyed[key]
        if (not re.fullmatch("[a-f0-9]{64}",x.get("sha256",""))
            or x.get("rows_5min")!=288 or x.get("hours")!=24
            or type(x.get("source_rows_reordered")) is not bool):
            raise ValueError("V98_OI_2025_AUDIT_VERIFIED_VENDOR_DAY")
    for key in bad:
        if not isinstance(keyed[key].get("first_fault"),str):
            raise ValueError("V98_OI_2025_AUDIT_QUARANTINE_REASON")
    if hashlib.sha256(csv_path.read_bytes()).hexdigest()!=report["hourly_csv_sha256"]:
        raise ValueError("V98_OI_2025_AUDIT_CSV_DIGEST")
    counts=Counter();seen=set();previous=None
    with csv_path.open(newline="") as handle:
        reader=csv.DictReader(handle)
        if tuple(reader.fieldnames or ())!=COLUMNS:
            raise ValueError("V98_OI_2025_AUDIT_COLUMNS")
        for row in reader:
            if row["asset"] not in ASSETS:
                raise ValueError("V98_OI_2025_AUDIT_UNKNOWN_ASSET")
            stamp=dt.datetime.fromisoformat(row["bar_open_utc"])
            if (stamp.tzinfo is None or stamp.utcoffset()!=dt.timedelta(0)
                or stamp.minute!=0 or stamp.second!=0 or stamp.microsecond!=0
                or not START<=stamp.date()<=END):
                raise ValueError("V98_OI_2025_AUDIT_TIMESTAMP")
            key=(row["asset"],str(stamp.date()))
            if key not in good:
                raise ValueError("V98_OI_2025_AUDIT_QUARANTINED_DAY_LEAK")
            if row["source_zip_sha256"]!=keyed[key]["sha256"]:
                raise ValueError("V98_OI_2025_AUDIT_VENDOR_SHA_REFERENCE")
            if not (math.isfinite(float(row["oi_contracts"])) and float(row["oi_contracts"])>0):
                raise ValueError("V98_OI_2025_AUDIT_NONPOSITIVE_OI")
            for name in ("oi_value_usdt","taker_ratio"):
                if row[name] and (not math.isfinite(float(row[name])) or float(row[name])<0):
                    raise ValueError("V98_OI_2025_AUDIT_INVALID_OPTIONAL_VALUE")
            identity=(row["asset"],row["bar_open_utc"])
            if identity in seen:raise ValueError("V98_OI_2025_AUDIT_DUPLICATE_HOUR")
            seen.add(identity);counts[key]+=1
            order=(row["bar_open_utc"],row["asset"])
            if previous is not None and order<=previous:
                raise ValueError("V98_OI_2025_AUDIT_CSV_ORDER")
            previous=order
    if any(counts[k]!=24 for k in good) or any(counts[k]!=0 for k in bad):
        raise ValueError("V98_OI_2025_AUDIT_HOURLY_DAY_GRID")
    if (len(seen)!=len(good)*24 or len(seen)!=report["verified_hourly_rows"]
        or report["expected_hourly_rows"]!=1460*24):
        raise ValueError("V98_OI_2025_AUDIT_HOURLY_COUNTS")
    expected_decision=("PASS_2025_NATIVE_OI_SOURCE_NO_GAPS_NOT_PNL" if not bad
                       else "QUARANTINE_2025_NATIVE_OI_GAPS_NOT_PNL")
    if report["decision"]!=expected_decision:
        raise ValueError("V98_OI_2025_AUDIT_DECISION")
    return {"decision":"PASS_2025_NATIVE_OI_INDEPENDENT_ARTIFACT_AUDIT_NOT_PNL",
            "verified_asset_days":len(good),"quarantined_asset_days":len(bad),
            "verified_hourly_asset_rows":len(seen),
            "vendor_sha_references_verified":len(seen),
            "csv_sha256":report["hourly_csv_sha256"],
            "2025_exposed_training_only":True,"holdout_accessed":False,
            "2026_plus_accessed":False,"pnl_computed":False,
            "source_origin_independently_downloaded":False,
            "paper_or_live_authorized":False}

def self_test():
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder)
        good=("BTCUSDT","2025-01-01")
        manifest=[]
        for asset in ASSETS:
            for i in range(365):
                date=str(START+dt.timedelta(days=i))
                if (asset,date)==good:
                    manifest.append({"asset":asset,"date":date,"passed":True,
                                     "sha256":"a"*64,"rows_5min":288,"hours":24,
                                     "source_rows_reordered":False})
                else:
                    manifest.append({"asset":asset,"date":date,"passed":False,
                                     "first_fault":"SYNTHETIC_MISSING"})
        csv_path=root/"v98_oi_2025_verified_hourly.csv"
        with csv_path.open("w",newline="") as handle:
            w=csv.writer(handle);w.writerow(COLUMNS)
            for h in range(24):
                w.writerow((f"2025-01-01T{h:02d}:00:00+00:00","BTCUSDT","1","2","0.5","a"*64))
        report={"source_only":True,"2025_exposed_training_only":True,
                "2026_plus_accessed":False,"holdout_accessed":False,
                "pnl_computed":False,"paper_or_live_authorized":False,
                "external_benchmarks_used":False,"date_start":str(START),"date_end":str(END),
                "assets":list(ASSETS),"files_expected":1460,
                "files_verified_complete":1,"files_quarantined":1459,
                "verified_hourly_rows":24,"expected_hourly_rows":35040,
                "hourly_csv_sha256":hashlib.sha256(csv_path.read_bytes()).hexdigest(),
                "decision":"QUARANTINE_2025_NATIVE_OI_GAPS_NOT_PNL","manifest":manifest}
        report_path=root/"v98_oi_2025_native_source_report.json"
        def save():report_path.write_text(json.dumps(report))
        save();assert audit(root)["verified_hourly_asset_rows"]==24
        cases=0
        for mutate in ("scope","sha","quarantine","year"):
            original=csv_path.read_bytes()
            if mutate=="scope":
                report["2026_plus_accessed"]=True
            elif mutate=="sha":
                csv_path.write_bytes(original.replace(b"a"*64,b"b"*64))
                report["hourly_csv_sha256"]=hashlib.sha256(csv_path.read_bytes()).hexdigest()
            elif mutate=="quarantine":
                report["manifest"][0]["passed"]=False
            else:
                csv_path.write_bytes(original.replace(b"2025-01-01T00",b"2026-01-01T00"))
                report["hourly_csv_sha256"]=hashlib.sha256(csv_path.read_bytes()).hexdigest()
            save()
            try:audit(root)
            except ValueError:cases+=1
            else:raise AssertionError("V98_OI_2025_AUDIT_TAMPER_NOT_BLOCKED_"+mutate)
            csv_path.write_bytes(original)
            report["hourly_csv_sha256"]=hashlib.sha256(original).hexdigest()
            report["2026_plus_accessed"]=False
            report["manifest"][0]["passed"]=True
            save()
        return {"decision":"PASS_V98_OI_2025_INDEPENDENT_SYNTHETIC_TAMPER_CONTRACT",
                "tamper_cases":cases,"official_data_downloaded":0,"pnl_computed":False}

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--root")
    parser.add_argument("--output")
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(),sort_keys=True))
    else:
        if not args.root or not args.output:parser.error("--root and --output required")
        receipt=audit(args.root)
        Path(args.output).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
        print(json.dumps(receipt,sort_keys=True))
