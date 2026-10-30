#!/usr/bin/env python3
"""V98 Phase264 CFTC Bitcoin CME positioning DATA_ONLY acquisition."""
from __future__ import annotations
import argparse,csv,datetime as dt,hashlib,io,json,time,urllib.request,zipfile
from pathlib import Path

YEARS=(2023,2024,2025)
URLS={y:f"https://www.cftc.gov/files/dea/history/deacot{y}.zip" for y in YEARS}
CONTRACT_CODE="133741"
MARKET_NEEDLES=("BITCOIN","CHICAGO MERCANTILE EXCHANGE")
UA="CryptoAI-Lab-V98-Phase264/1.0 (https://github.com/DnSiii/CryptoAI-Lab)"
NUMERIC_FIELDS={
 "open_interest":"openinterestall",
 "noncommercial_long":"noncommercialpositionslongall",
 "noncommercial_short":"noncommercialpositionsshortall",
 "noncommercial_spreading":"noncommercialpositionsspreadingall",
 "commercial_long":"commercialpositionslongall",
 "commercial_short":"commercialpositionsshortall",
 "nonreportable_long":"nonreportablepositionslongall",
 "nonreportable_short":"nonreportablepositionsshortall",
}
DATE_KEYS=("asofdateinformyymmdd","asofdateinformyyyymmdd","reportdateasyyyymmdd")

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def fetch(url,attempts=3,timeout=60):
    err=None
    for i in range(attempts):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/zip"})
            with urllib.request.urlopen(req,timeout=timeout) as r:return r.read()
        except Exception as e:
            err=e
            if i+1<attempts:time.sleep(1+i)
    raise err

def clean(v):return str(v or "").strip().strip('"').strip()

def canon(v):
    return "".join(ch.lower() for ch in str(v or "") if ch.isalnum())

def parse_date(row):
    for key in DATE_KEYS:
        v=clean(row.get(key))
        if not v:continue
        for fmt in ("%y%m%d","%Y%m%d","%m/%d/%Y","%Y-%m-%d"):
            try:return dt.datetime.strptime(v[:10],fmt).date()
            except ValueError:pass
    raise ValueError("no supported report-date field")

def parse_zip(raw:bytes,year:int):
    z=zipfile.ZipFile(io.BytesIO(raw))
    members=sorted(n for n in z.namelist() if not n.endswith("/") and n.lower().endswith((".txt",".csv")))
    if len(members)!=1:
        raise ValueError(f"expected exactly one text/csv member, got {members}")
    member=members[0]
    body=z.read(member)
    text=body.decode("utf-8-sig",errors="strict")
    reader=csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("legacy COT header missing")
    header_map={canon(h):h for h in reader.fieldnames if h is not None}
    required={"marketandexchangenames","cftccontractmarketcode",*NUMERIC_FIELDS.values()}
    if not required.issubset(set(header_map)):
        raise ValueError(f"legacy COT required headers missing: {sorted(set(required)-set(header_map))}")
    rows=[];invalid=0
    for raw_row in reader:
        row={canon(k):v for k,v in raw_row.items() if k is not None}
        if clean(row.get("cftccontractmarketcode"))!=CONTRACT_CODE:continue
        try:
            market=clean(row["marketandexchangenames"])
            day=parse_date(row)
            vals={k:int(float(clean(row[v]))) for k,v in NUMERIC_FIELDS.items()}
            if day.year!=year:raise ValueError("row year mismatch")
        except Exception:
            invalid+=1;continue
        rows.append({"report_date":day.isoformat(),"market_name":market,"contract_code":CONTRACT_CODE,**vals})
    return rows,member,sha(body),invalid

def csv_bytes(rows):
    from io import StringIO
    fields=["report_date","market_name","contract_code",*NUMERIC_FIELDS.keys()]
    s=StringIO(newline="");w=csv.DictWriter(s,fieldnames=fields,lineterminator="\n");w.writeheader()
    for r in sorted(rows,key=lambda x:x["report_date"]):w.writerow(r)
    return s.getvalue().encode()

def build(attempts=3):
    rows=[];archives={};errors={}
    for y in YEARS:
        try:
            raw=fetch(URLS[y],attempts=attempts)
            yr,member,member_sha,invalid=parse_zip(raw,y)
            rows.extend(yr)
            archives[str(y)]={"url":URLS[y],"zip_sha256":sha(raw),"zip_bytes":len(raw),
                              "member":member,"member_sha256":member_sha,"bitcoin_rows":len(yr),
                              "invalid_bitcoin_rows":invalid}
        except Exception as e:
            errors[str(y)]=f"{type(e).__name__}: {e}"
    rows=sorted(rows,key=lambda x:x["report_date"])
    dates=[dt.date.fromisoformat(r["report_date"]) for r in rows]
    dup=len(dates)-len(set(dates))
    gaps=[(b-a).days for a,b in zip(dates,dates[1:])]
    per_year={str(y):sum(d.year==y for d in dates) for y in YEARS}
    nums=[k for k in NUMERIC_FIELDS]
    market_ok=all(all(n in r["market_name"].upper() for n in MARKET_NEEDLES) for r in rows)
    values_ok=bool(rows) and all(all(isinstance(r[k],int) and r[k]>=0 for k in nums) for r in rows)
    oi_ok=bool(rows) and all(r["open_interest"]>0 for r in rows)
    sanity=bool(rows) and all(all(r[k]<=2*r["open_interest"] for k in nums if k!="open_interest") for r in rows)
    boundary=bool(rows) and all(dt.date(2023,1,1)<=d<=dt.date(2025,12,31) for d in dates)
    normalized=csv_bytes(rows)
    gates={
      "all_three_archives_succeeded":not errors and len(archives)==3,
      "one_member_each":len(archives)==3 and all(v["member"] for v in archives.values()),
      "at_least_50_rows_each_year":all(per_year[str(y)]>=50 for y in YEARS),
      "at_least_150_rows_total":len(rows)>=150,
      "no_duplicate_report_date":dup==0,
      "position_values_nonnegative_integer":values_ok,
      "open_interest_positive":oi_ok,
      "position_accounting_sanity":sanity,
      "contract_code_exact":bool(rows) and all(r["contract_code"]==CONTRACT_CODE for r in rows),
      "market_name_exact_family":bool(rows) and market_ok,
      "training_boundary_enforced":boundary,
      "max_report_gap_le_14_days":bool(gaps) and max(gaps)<=14,
      "normalized_hash_recorded":bool(normalized),
      "archive_member_hash_ledger_complete":len(archives)==3 and all(v["zip_sha256"] and v["member_sha256"] for v in archives.values()),
    }
    decision="PASS_DATA_ONLY" if all(gates.values()) else "FAIL_DATA_NO_ALPHA"
    manifest={
      "engine":"V98 Independent","phase":264,"kind":"DATA_ONLY_CFTC_BTC_POSITIONING",
      "decision":decision,"source":"CFTC Historical Compressed Legacy Futures Only",
      "contract_code":CONTRACT_CODE,"market_identity":"BITCOIN - CHICAGO MERCANTILE EXCHANGE",
      "period_report_dates":["2023-01-01","2025-12-31"],"archives":archives,
      "request_errors":errors,"rows":len(rows),"rows_per_year":per_year,
      "first_report_date":dates[0].isoformat() if dates else None,"last_report_date":dates[-1].isoformat() if dates else None,
      "max_report_gap_days":max(gaps,default=0),"duplicate_report_dates":dup,
      "normalized_csv_sha256":sha(normalized),"gates":gates,
      "alpha_executed":False,"pnl_executed":False,"crypto_price_join":False,
      "direction_selected":False,"parameter_search":False,"validation_accessed":False,"holdout_accessed":False,
      "phase083_selection_use":False,"v14_used":False,"v15_used":False,"v99_used":False,
      "preregistration":"research/v98_independent/phase264_cftc_btc_positioning_prereg.md"
    }
    return normalized,manifest

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out-dir",type=Path,default=Path("research/v98_independent/data/phase264_cftc_btc_positioning"))
    ap.add_argument("--manifest",type=Path,default=Path("research/v98_independent/phase264_cftc_btc_positioning_manifest.json"))
    ap.add_argument("--attempts",type=int,default=3);a=ap.parse_args()
    data,m=build(a.attempts)
    a.out_dir.mkdir(parents=True,exist_ok=True);(a.out_dir/"cftc_btc_weekly.csv").write_bytes(data)
    a.manifest.parent.mkdir(parents=True,exist_ok=True);a.manifest.write_text(json.dumps(m,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"phase":264,"decision":m["decision"],"rows":m["rows"],"rows_per_year":m["rows_per_year"],
      "first_report_date":m["first_report_date"],"last_report_date":m["last_report_date"],
      "max_report_gap_days":m["max_report_gap_days"],"errors":m["request_errors"],"gates":m["gates"],
      "normalized_csv_sha256":m["normalized_csv_sha256"]},indent=2,sort_keys=True))
if __name__=="__main__":main()
