#!/usr/bin/env python3
"""V99 Phase192 DATA_ONLY issuer-native impulse/rate coverage scout.

Preregistered broader TRAIN-only windows, selected from chain position only (no market
outcomes): +/-50,000 blocks around the prior 17M/18M/19M anchors. Queries only the
issuer-native event topics, so transfer/approval traffic cannot dominate transport.
No price, PnL, regime, benchmark, cost, direction, threshold, or holdout input exists.
"""
from __future__ import annotations
import argparse, hashlib, json, re, time, urllib.parse, urllib.request
from collections import Counter
from pathlib import Path

BASE="https://eth.blockscout.com/api"
USDC="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
USDT="0xdac17f958d2ee523a2206206994597c13d831ec7"
USDC_MINT="0xab8530f87dc9b59234c4623bf917212bb2536d647574c8e7e5da92c2ede0c9f8"
USDC_BURN="0xcc16f5dbb4873280815c1ee09dbd06736cffcc184412cf7a71a0fdb75d397ca5"
USDT_ISSUE="0xcb8241adb0c3fdb35b70c24ce35c5eb0c17af7431c99f827d44a445ca624176a"
USDT_REDEEM="0x702d5967f45f6513a38ffc42d6ba9bf230bd40e8f53b16363c7eb4fd2deb9a44"
WINDOWS=((16950000,17050000),(17950000,18050000),(18950000,19050000))
SPECS=(("USDC",USDC,"mint",USDC_MINT),("USDC",USDC,"burn",USDC_BURN),("USDT",USDT,"issue",USDT_ISSUE),("USDT",USDT,"redeem",USDT_REDEEM))
HEX64=re.compile(r"^0x[0-9a-fA-F]{64}$")
SNAP={}; MODE="live"; SNAPSHOT=None; LAST=0.0

def _bytes(): return json.dumps(SNAP,sort_keys=True,separators=(",",":")).encode()
def _save():
    if MODE=="live" and SNAPSHOT:
        p=Path(SNAPSHOT); t=p.with_suffix(p.suffix+".tmp"); t.write_bytes(_bytes()); t.replace(p)
def get(url):
    global LAST
    if url in SNAP:return SNAP[url]
    if MODE=="replay":raise RuntimeError("snapshot_miss")
    wait=5-(time.monotonic()-LAST)
    if wait>0:time.sleep(wait)
    LAST=time.monotonic()
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoAI-Lab-Phase192/1.0"})
    with urllib.request.urlopen(req,timeout=45) as r: obj=json.load(r)
    if not isinstance(obj,dict) or not isinstance(obj.get("result"),list):raise RuntimeError("source_not_log_list")
    SNAP[url]=obj;_save();return obj

def rows(addr,topic,lo,hi):
    out=[]
    for page in range(1,101):
        q=urllib.parse.urlencode({"module":"logs","action":"getLogs","address":addr,"topic0":topic,"fromBlock":lo,"toBlock":hi,"page":page,"offset":1000})
        b=get(BASE+"?"+q)["result"];out.extend(b)
        if len(b)<1000:return out
    if lo>=hi:raise RuntimeError("single_block_pagination_cap")
    mid=(lo+hi)//2
    return rows(addr,topic,lo,mid)+rows(addr,topic,mid+1,hi)

def audit():
    cells=[]; seen={}
    for lo,hi in WINDOWS:
        for token,addr,event,topic in SPECS:
            z=rows(addr,topic,lo,hi)
            ids=[]
            for r in z:
                if str(r.get("address","")).lower()!=addr:raise RuntimeError("emitter_mismatch")
                ts=r.get("topics") or []
                if not ts or str(ts[0]).lower()!=topic:raise RuntimeError("topic_mismatch")
                tx=str(r.get("transactionHash","")).lower(); li=int(str(r.get("logIndex")),16); bn=int(str(r.get("blockNumber")),16)
                if not HEX64.fullmatch(tx) or not lo<=bn<=hi:raise RuntimeError("identity_or_window_failure")
                ident=(tx,li); payload=json.dumps(r,sort_keys=True,separators=(",",":"))
                if ident in seen and seen[ident]!=payload:raise RuntimeError("conflicting_duplicate_identity")
                seen[ident]=payload;ids.append(ident)
            cells.append({"from":lo,"to":hi,"token":token,"event":event,"logs":len(set(ids)),"duplicate_appearances":len(ids)-len(set(ids))})
    grouped={}
    for c in cells:
        k=(c["from"],c["token"]);grouped[k]=grouped.get(k,0)+c["logs"]
    zero=[{"from":k[0],"token":k[1]} for k,n in sorted(grouped.items()) if n==0]
    return {"phase":192,"scope":"DATA_ONLY_NATIVE_IMPULSE_COVERAGE","economic_trials":0,"windows":[list(w) for w in WINDOWS],"cells":cells,"zero_native_token_windows":zero,"all_token_windows_have_native_events":not zero,"decision":"PASS_NATIVE_IMPULSE_COVERAGE" if not zero else "REJECT_BEFORE_ECONOMIC_TRIAL_INSUFFICIENT_NATIVE_COVERAGE","snapshot_entries":len(SNAP),"snapshot_sha256":hashlib.sha256(_bytes()).hexdigest()}

def self_test():
    assert len(WINDOWS)==3 and all(hi-lo==100000 for lo,hi in WINDOWS)
    assert len({x[3] for x in SPECS})==4 and all(HEX64.fullmatch(x[3]) for x in SPECS)

def main():
    global MODE,SNAP,SNAPSHOT
    ap=argparse.ArgumentParser();ap.add_argument("--snapshot");ap.add_argument("--replay");ap.add_argument("--self-test",action="store_true");a=ap.parse_args()
    if a.self_test:self_test();print("PASS: Phase192 preregistered native impulse coverage invariants");return
    if bool(a.snapshot)==bool(a.replay):raise SystemExit("choose exactly one of --snapshot/--replay")
    if a.replay:MODE="replay";SNAP=json.loads(Path(a.replay).read_text())
    else:
        SNAPSHOT=a.snapshot;p=Path(a.snapshot)
        if p.exists() and p.stat().st_size:SNAP=json.loads(p.read_text())
    out=audit();_save();print(json.dumps(out,sort_keys=True,separators=(",",":")))
if __name__=="__main__":main()
