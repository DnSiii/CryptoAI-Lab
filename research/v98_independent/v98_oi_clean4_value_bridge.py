#!/usr/bin/env python3
"""V98-only source bridge: independently audited native OI numerical values, no PnL."""
import argparse,csv,datetime as dt,hashlib,json,math
from pathlib import Path
import numpy as np
from v98_oi_2022_2025_causal_mask import source_only_mask,find_one

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=27048
CLOCK=tuple(range(744,HOURS,168))
START=dt.datetime(2022,12,1,tzinfo=dt.timezone.utc)
FIELDS=["bar_open_utc","asset","oi_contracts","oi_value_usdt","taker_ratio","source_zip_sha256"]
SOURCES=(
 ("v98_oi_full_history_v2_verified_hourly_20261027.csv",
  "68ecdb3827b1540f94fb50ee053adf4af356a27260fd930853fadf0d942c7c6e"),
 ("v98_oi_2025_verified_hourly.csv",
  "890c01a719d825a799484779a97b227f34d46f00aaff280fd0d950c67f858943")
)

def load(old_root,new_root):
    # Independent original daily-manifest and hourly-source auditors run first.
    audit=source_only_mask(old_root,new_root)
    if audit["decision"]!="PASS_V98_2022_25_OI_CAUSAL_SOURCE_MASK_NOT_PNL":
        raise ValueError("V98_OI_BRIDGE_UPSTREAM_AUDIT")
    oi=np.full((HOURS,4),np.nan,dtype=float)
    observed=np.zeros((HOURS,4),bool)
    source_roots=(old_root,new_root)
    count=0
    for root,(name,pin) in zip(source_roots,SOURCES):
        path=find_one(root,name)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=pin:
            raise ValueError("V98_OI_BRIDGE_SOURCE_SHA")
        with path.open(newline="") as handle:
            reader=csv.DictReader(handle)
            if reader.fieldnames!=FIELDS:raise ValueError("V98_OI_BRIDGE_SCHEMA")
            for row in reader:
                if row["asset"] not in ASSETS:raise ValueError("V98_OI_BRIDGE_ASSET")
                stamp=dt.datetime.fromisoformat(row["bar_open_utc"])
                if (stamp.tzinfo is None or stamp.utcoffset()!=dt.timedelta(0)
                    or stamp.minute or stamp.second or stamp.microsecond):
                    raise ValueError("V98_OI_BRIDGE_TIMESTAMP")
                delta=(stamp-START).total_seconds()
                if delta<0 or delta>=HOURS*3600 or delta%3600:
                    raise ValueError("V98_OI_BRIDGE_TIME_SCOPE")
                t=int(delta//3600);j=ASSETS.index(row["asset"])
                if observed[t,j]:raise ValueError("V98_OI_BRIDGE_DUPLICATE")
                v=float(row["oi_contracts"])
                if not math.isfinite(v) or v<=0:raise ValueError("V98_OI_BRIDGE_NONFINITE_OI")
                if len(row["source_zip_sha256"])!=64 or any(
                    ch not in "0123456789abcdefABCDEF" for ch in row["source_zip_sha256"]):
                    raise ValueError("V98_OI_BRIDGE_VENDOR_SHA")
                # No substitute for unavailable upstream value/taker fields.
                for field in ("oi_value_usdt","taker_ratio"):
                    if row[field]:
                        x=float(row[field])
                        if not math.isfinite(x) or x<0:
                            raise ValueError("V98_OI_BRIDGE_OPTIONAL_FIELD")
                oi[t,j]=v;observed[t,j]=True;count+=1
    if count!=106920 or int(observed.sum())!=106920 or int((~observed).sum())!=1272:
        raise ValueError("V98_OI_BRIDGE_ROW_COUNT")
    if not np.array_equal(observed,np.isfinite(oi)):
        raise ValueError("V98_OI_BRIDGE_MISSING_VALUE_MASK")
    eligible={t:bool(observed[t-167:t+1].all()) for t in CLOCK}
    if len(eligible)!=157 or sum(eligible.values())!=143:
        raise ValueError("V98_OI_BRIDGE_168H_MASK")
    if audit["summary"]["168"]["eligible_decisions"]!=143:
        raise ValueError("V98_OI_BRIDGE_ORIGINAL_MASK_DISAGREES")
    return {"oi":oi,"observed":observed,"eligible":eligible,
            "source_audit":audit,"training_only":True,"2026_plus_accessed":False,
            "pnl_computed":False}

def self_test():
    observed=np.ones((HOURS,4),bool)
    for t in CLOCK:
        assert observed[t-167:t+1].all()
        mutated=observed.copy()
        if t+1<HOURS:
            mutated[t+1,0]=False
            assert mutated[t-167:t+1].all()
        mutated=observed.copy()
        mutated[t,2]=False
        assert not mutated[t-167:t+1].all()
        mutated=observed.copy()
        mutated[t-168,1]=False
        assert mutated[t-167:t+1].all()
    return {"decision":"PASS_V98_OI_VALUE_BRIDGE_SYNTHETIC_CAUSALITY_NOT_PNL",
            "weekly_decisions":len(CLOCK),"future_mutation_excluded":True,
            "in_window_quarantine_fail_closed":True,"pnl_computed":False}

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--old-root")
    parser.add_argument("--new-root")
    parser.add_argument("--output")
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(),sort_keys=True))
    else:
        if not args.old_root or not args.new_root or not args.output:
            parser.error("--old-root, --new-root and --output required")
        data=load(args.old_root,args.new_root)
        receipt={"decision":"PASS_V98_OI_NUMERICAL_VALUE_BRIDGE_SOURCE_ONLY_NOT_PNL",
                 "verified_asset_hours":int(data["observed"].sum()),
                 "quarantined_asset_hours":int((~data["observed"]).sum()),
                 "eligible_weekly_decisions":sum(data["eligible"].values()),
                 "total_weekly_decisions":len(data["eligible"]),
                 "source_sha256":[pin for _,pin in SOURCES],
                 "original_mask_receipt_sha256":data["source_audit"]["receipts_sha256"],
                 "2025_exposed_training_only":True,"2026_plus_accessed":False,
                 "holdout_accessed":False,"pnl_computed":False,
                 "paper_or_live_authorized":False}
        Path(args.output).write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
        print(json.dumps(receipt,sort_keys=True))
