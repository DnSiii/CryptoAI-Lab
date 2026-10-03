#!/usr/bin/env python3
"""Phase191 DATA_ONLY raw-snapshot coverage audit.

Reads only the immutable Blockscout source snapshot. No price/PnL/regime/benchmark/
holdout inputs. Deduplicates overlapping/sharded responses by immutable log identity
and reports issuer-native event coverage before any economic trial is allowed.
"""
from __future__ import annotations
import argparse,json,re
from collections import Counter
from pathlib import Path

USDC="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
USDT="0xdac17f958d2ee523a2206206994597c13d831ec7"
TRANSFER="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
APPROVAL="0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"
USDC_MINT="0xab8530f87dc9b59234c4623bf917212bb2536d647574c8e7e5da92c2ede0c9f8"
USDC_BURN="0xcc16f5dbb4873280815c1ee09dbd06736cffcc184412cf7a71a0fdb75d397ca5"
WINDOWS=((17000000,17000199),(18000000,18000199),(19000000,19000199))

def _logs(snapshot):
    seen={}; appearances=0
    for value in snapshot.values():
        if not isinstance(value,dict) or not isinstance(value.get("result"),list): continue
        for row in value["result"]:
            if not isinstance(row,dict) or "transactionHash" not in row or "logIndex" not in row: continue
            appearances+=1
            ident=(row["transactionHash"].lower(),int(row["logIndex"],16))
            old=seen.setdefault(ident,row)
            if old != row: raise ValueError(f"conflicting duplicate log payload: {ident}")
    return list(seen.values()),appearances

def audit(snapshot):
    logs,appearances=_logs(snapshot); windows=[]
    for lo,hi in WINDOWS:
        rows=[r for r in logs if lo<=int(r["blockNumber"],16)<=hi]
        cells=[]
        for token in (USDC,USDT):
            z=[r for r in rows if r["address"].lower()==token]
            topics=Counter(r["topics"][0].lower() for r in z)
            native=(topics[USDC_MINT]+topics[USDC_BURN]) if token==USDC else sum(n for t,n in topics.items() if t not in (TRANSFER,APPROVAL))
            cells.append({"token":token,"logs":len(z),"native_event_logs":native,"topic0_counts":dict(sorted(topics.items()))})
        windows.append({"from":lo,"to":hi,"blocks":hi-lo+1,"cells":cells})
    native_cells=[c for w in windows for c in w["cells"]]
    zero_native=[{"from":w["from"],"token":c["token"]} for w in windows for c in w["cells"] if c["native_event_logs"]==0]
    return {"phase":191,"scope":"DATA_ONLY_COVERAGE_AUDIT","economic_trials":0,
            "unique_logs":len(logs),"raw_log_appearances":appearances,"windows":windows,
            "all_token_windows_have_native_events":not zero_native,"zero_native_cells":zero_native,
            "decision":"PASS_FEATURE_COVERAGE" if not zero_native else "REJECT_BEFORE_ECONOMIC_TRIAL_INSUFFICIENT_NATIVE_COVERAGE"}

def self_test():
    row=lambda token,topic,b,tx,li:{"address":token,"blockNumber":hex(b),"transactionHash":"0x"+tx*64,"logIndex":hex(li),"topics":[topic,None,None,None],"data":"0x1"}
    s={"a":{"result":[row(USDC,USDC_MINT,17000000,"1",0),row(USDT,TRANSFER,17000000,"2",0)]}}
    o=audit(s); assert o["economic_trials"]==0 and not o["all_token_windows_have_native_events"]
    assert o["decision"].startswith("REJECT_BEFORE_ECONOMIC_TRIAL")

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--snapshot");ap.add_argument("--self-test",action="store_true");a=ap.parse_args()
    if a.self_test:self_test();print("PASS: Phase191 immutable snapshot coverage audit");return
    if not a.snapshot:raise SystemExit("--snapshot required unless --self-test")
    print(json.dumps(audit(json.loads(Path(a.snapshot).read_text())),sort_keys=True,separators=(",",":")))
if __name__=="__main__":main()
