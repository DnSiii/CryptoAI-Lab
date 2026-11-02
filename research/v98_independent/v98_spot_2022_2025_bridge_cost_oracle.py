#!/usr/bin/env python3
"""Independent read-only audit of V98 2022-25 masked spot bridge receipt. Never PnL."""
import argparse,csv,datetime as dt,hashlib,io,json,math
from pathlib import Path
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
FIELDS=["asset","open_time_ms","spot_close","quote_volume","observed","full_hour","source_era","provider_zip_sha256"]
START=1669852800000;SPLIT=1735689600000;END=1767225600000;HOUR=3600000
GAP=1679662800000
def audit(raw,receipt):
    if receipt.get("decision")!="PASS_AUTHENTICATED_SPOT_2022_2025_MASKED_BRIDGE_NOT_PNL":
        raise ValueError("AUDIT_DECISION")
    if hashlib.sha256(raw).hexdigest()!=receipt.get("canonical_sha256"):
        raise ValueError("AUDIT_CANONICAL_SHA")
    if any(receipt.get(k) is not False for k in ("holdout_accessed","data_2026_accessed",
                                                "external_benchmarks_accessed","pnl_computed","trading_authorized")):
        raise ValueError("AUDIT_RESEARCH_FIREWALL")
    if receipt.get("rejected_strict_complete_grid_source_stays_rejected") is not True or receipt.get("2025_exposed_training_only") is not True:
        raise ValueError("AUDIT_REJECTED_SOURCE_FIREWALL")
    d=receipt.get("two_leg_fee_diagnostic",{})
    if (d.get("decision")!="PASS_DESCRIPTIVE_TWO_LEG_FEE_FEASIBILITY_NOT_PNL" or
        d.get("fee_budgets_bps")!=[8,16,24,30] or
        d.get("actual_account_fees_verified") is not False or
        d.get("tradeable_edge_proven") is not False or d.get("pnl_computed") is not False or
        d.get("published_regular_spot_taker_bps")!=10 or
        d.get("published_regular_perp_taker_bps")!=5 or
        d.get("published_regular_two_leg_taker_roundtrip_bps")!=30 or
        d.get("published_fee_schedule_current_not_historical") is not True):
        raise ValueError("AUDIT_COST_IS_NOT_EXECUTABLE")
    rows=csv.DictReader(io.StringIO(raw.decode("utf-8"),newline=""))
    if rows.fieldnames!=FIELDS:raise ValueError("AUDIT_FIELDS")
    counts=dict(calendar=0,observed=0,eligible=0,missing=0,partial=0)
    perasset={a:0 for a in ASSETS}
    for row in rows:
        a=row["asset"]
        if a not in perasset:raise ValueError("AUDIT_ASSET")
        t=START+perasset[a]*HOUR
        if perasset[a]>=27048 or int(row["open_time_ms"])!=t:
            raise ValueError("AUDIT_CALENDAR")
        if any(perasset[b] and ASSETS.index(b)>ASSETS.index(a) for b in ASSETS):
            raise ValueError("AUDIT_ASSET_ORDER")
        era="HQ_MASKED_2022_2024" if t<SPLIT else "OFFICIAL_2025"
        if row["source_era"]!=era:raise ValueError("AUDIT_ERA")
        digest=row["provider_zip_sha256"]
        if len(digest)!=64 or any(x not in "0123456789abcdef" for x in digest):
            raise ValueError("AUDIT_PROVIDER_SHA_FORMAT")
        if row["observed"] not in ("0","1") or row["full_hour"] not in ("0","1"):
            raise ValueError("AUDIT_MASK_FORMAT")
        observed=row["observed"]=="1";full=row["full_hour"]=="1"
        if full and not observed:raise ValueError("AUDIT_MASK_CONFLICT")
        if not observed:
            if row["spot_close"] or row["quote_volume"]:raise ValueError("AUDIT_GAP_FILLED")
        else:
            price=float(row["spot_close"]);quote=float(row["quote_volume"])
            if not math.isfinite(price) or price<=0 or not math.isfinite(quote) or quote<0:
                raise ValueError("AUDIT_PRICE")
        if (not observed)!=(t==GAP) or (observed and not full)!=(t==GAP-HOUR):
            raise ValueError("AUDIT_UNEXPECTED_SOURCE_GAP")
        if t>=SPLIT and not full:raise ValueError("AUDIT_2025_MASK")
        perasset[a]+=1;counts["calendar"]+=1;counts["observed"]+=int(observed)
        counts["eligible"]+=int(full);counts["missing"]+=int(not observed)
        counts["partial"]+=int(observed and not full)
    if perasset!={a:27048 for a in ASSETS} or counts!={"calendar":108192,"observed":108188,
        "eligible":108184,"missing":4,"partial":4} or receipt.get("counts")!=counts:
        raise ValueError("AUDIT_COVERAGE")
    for a,stats in d["assets"].items():
        if a not in ASSETS or stats["hours"]!=8760:raise ValueError("AUDIT_COST_HOURS")
        previous=8761
        for budget in ("8","16","24","30"):
            n=stats["hours_abs_basis_above_illustrative_four_fill_fee_budgets"][budget]
            if not isinstance(n,int) or not 0<=n<=previous:
                raise ValueError("AUDIT_COST_MONOTONIC")
            previous=n
        if not 0<=stats["median_abs_basis_bps"]<=stats["p99_abs_basis_bps"]<=stats["max_abs_basis_bps"]:
            raise ValueError("AUDIT_COST_QUANTILES")
    return {"decision":"PASS_INDEPENDENT_SPOT_BRIDGE_AND_COST_DESCRIPTIVE_AUDIT_NOT_PNL",
            "counts":counts,"assets":perasset,"source_sha256":hashlib.sha256(raw).hexdigest(),
            "trading_authorized":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--csv",required=True);p.add_argument("--receipt",required=True)
    a=p.parse_args();raw=Path(a.csv).read_bytes();r=json.loads(Path(a.receipt).read_text())
    result=audit(raw,r)
    # Independently replay every native funding event and all 48 signed monthly sums.
    from v98_funding_carry_source_oracle import audit as audit_carry, tamper as tamper_carry
    carry=r["native_signed_funding_carry_diagnostic"]
    carry_raw=(Path(a.receipt).parent/carry["canonical_event_csv"]).read_bytes()
    result["native_signed_funding_carry"]=audit_carry(carry_raw,carry)
    result["native_funding_tamper_cases_rejected"]=tamper_carry(carry_raw,carry)
    controls=0
    for key,value,error in (("canonical_sha256","0"*64,"AUDIT_CANONICAL_SHA"),
                            ("trading_authorized",True,"AUDIT_RESEARCH_FIREWALL")):
        altered=dict(r);altered[key]=value
        try:audit(raw,altered)
        except ValueError as e:
            if str(e)!=error:raise
            controls+=1
        else:raise AssertionError("TAMPER_ACCEPTED "+key)
    result["tamper_cases_rejected"]=controls
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
