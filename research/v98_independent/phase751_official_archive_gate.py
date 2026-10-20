#!/usr/bin/env python3
"""V98 Independent Phase751: attest 100 official pre-2025 funding archives only.
No 2025/2026 reads, external benchmarks, signals, PnL or promotion.
"""
import csv,hashlib,json,sys
from decimal import Decimal
from pathlib import Path
from phase206_acquire_funding_archive import fetch,checksum_expected,parse_archive,BASE
ROOT=Path(__file__).resolve().parent
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
PINS={
"BTCUSDT":(183855,"4f48e2b2c2354bb81e13d68760ea83b83a161f4e50a8a93d20c5673186537751",3289),
"ETHUSDT":(183970,"dc637df1aeae3a3cec56cbf19b39aa18fd3a6c2359866be59e8c75010beb1113",3289),
"BNBUSDT":(174861,"6e8e6e6e01bc527680cc590a61653a4fd47928d952c34e6fd6a3dfee6164f570",3289),
"SOLUSDT":(188710,"0d64741989844c96d8aa3e349ae7c2d305bc1d56fc2a0f6cfed85d7b715f9999",3364)}
MONTHS=tuple(f"{y}-{m:02d}" for y in (2022,2023,2024) for m in range(1,13) if (y,m)>=(2022,12))
START=1669852800000;END=1735689600000;STEP=28800000
def native(a):
 raw=(ROOT/"data/phase751_training_only_funding"/f"{a}_funding.csv").read_bytes()
 n,digest,lines=PINS[a]
 if len(raw)!=n or raw.count(b"\n")!=lines or hashlib.sha256(raw).hexdigest()!=digest or b"2025-" in raw:
  raise ValueError(a+": prefix digest/boundary mismatch")
 rows=list(csv.DictReader(raw.decode().splitlines()))
 expected={}
 for row in rows:
  t=int(row["fundingTime_ms"])
  if t>=END:raise ValueError("validation-year funding present")
  if t>=START:
   slot=START+len(expected)*STEP
   rate=Decimal(row["fundingRate"])
   if not slot<=t<=slot+29 or Decimal(row["fundingIntervalHours"])!=8 or not rate.is_finite():
    raise ValueError("native funding schedule mismatch")
   expected[slot]=(t,rate)
 if len(expected)!=2286:raise ValueError("training native coverage mismatch")
 return expected
def audit(a,expected):
 seen={};digests={}
 for month in MONTHS:
  filename=f"{a}-fundingRate-{month}.zip"
  url=f"{BASE}/{a}/{filename}"
  checksum=checksum_expected(fetch(url+".CHECKSUM"),filename)
  raw=fetch(url)
  digest=hashlib.sha256(raw).hexdigest()
  if digest!=checksum:raise ValueError(filename+": official SHA mismatch")
  rows=parse_archive(raw,filename)
  for t,interval,rate in rows:
   slot=(t//STEP)*STEP
   if not START<=slot<END or slot in seen or not slot<=t<=slot+29 or Decimal(interval)!=8 or expected.get(slot)!=(t,Decimal(rate)):
    raise ValueError(filename+": archive/native discrepancy")
   seen[slot]=(t,Decimal(rate))
  digests[month]=digest
 if seen!=expected:raise ValueError(a+": official archive coverage mismatch")
 return {"settlements":len(seen),"archives":len(digests),
  "zip_manifest_sha256":hashlib.sha256(json.dumps(digests,sort_keys=True).encode()).hexdigest()}
def main():
 out={"phase":751,"decision":"BLOCKED_OFFICIAL_SOURCE","mode":"SOURCE_ONLY",
 "validation_2025_read":False,"historical_pnl_computed":False,"promotion_eligible":False,
 "vendor_origin_attested":False,"assets":{}}
 try:
  for a in ASSETS:out["assets"][a]=audit(a,native(a))
  if sum(x["archives"] for x in out["assets"].values())!=100 or sum(x["settlements"] for x in out["assets"].values())!=9144:
   raise ValueError("source count mismatch")
  out["decision"]="PASS_OFFICIAL_100_TRAINING_ARCHIVES_NATIVE_ONLY"
  out["vendor_origin_attested"]=False # API mark verification still required
 except Exception as e:out["reason"]=type(e).__name__+": "+str(e)[:300]
 (ROOT/"phase751_official_archive_result.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"decision":out["decision"],"reason":out.get("reason"),"assets":len(out["assets"])}))
 return 0 if out["decision"].startswith("PASS_") else 2
if __name__=="__main__":sys.exit(main())
