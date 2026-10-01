#!/usr/bin/env python3
"""Phase191 DATA_ONLY audit over preregistered TRAIN windows.
No price/PnL/regime/benchmark/holdout access. No provenance repair/inference.
Live mode records an immutable source snapshot; replay mode performs zero network I/O.
"""
from __future__ import annotations
import argparse,json,re,time,urllib.error,urllib.parse,urllib.request
from pathlib import Path
BASE="https://eth.blockscout.com/api"; V2="https://eth.blockscout.com/api/v2"
USDC="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"; USDT="0xdac17f958d2ee523a2206206994597c13d831ec7"
WINDOWS=((17000000,17000199),(18000000,18000199),(19000000,19000199)); OFFSET=1000
HEX64=re.compile(r"^0x[0-9a-fA-F]{64}$"); HEXDATA=re.compile(r"^0x(?:[0-9a-fA-F]{2})*$")
SNAP={}; MODE="live"
def get(url):
    global SNAP
    if MODE=="replay":
        if url not in SNAP: raise RuntimeError("snapshot_miss")
        return SNAP[url]
    for attempt in range(8):
        req=urllib.request.Request(url,headers={"User-Agent":"CryptoAI-Lab-Phase191/2.3"})
        try:
            with urllib.request.urlopen(req,timeout=30) as r: obj=json.load(r)
            SNAP[url]=obj; time.sleep(1.05); return obj
        except urllib.error.HTTPError as e:
            if e.code!=429 or attempt==7: raise
            time.sleep(min(60,3*(2**attempt)))
    raise RuntimeError("unreachable")
def qint(v):
    if isinstance(v,int) and not isinstance(v,bool) and v>=0:return v
    if isinstance(v,str) and v.startswith("0x") and len(v)>2:return int(v,16)
    if isinstance(v,str) and v.isdigit():return int(v)
    raise ValueError("noncanonical_integer")
def fetch_rows(addr,lo,hi):
    rows=[]
    for page in range(1,101):
        qs=urllib.parse.urlencode({"module":"logs","action":"getLogs","address":addr,"fromBlock":lo,"toBlock":hi,"page":page,"offset":OFFSET})
        obj=get(BASE+"?"+qs); batch=obj.get("result") if isinstance(obj,dict) else None
        if not isinstance(batch,list):raise RuntimeError("source_not_log_list")
        rows.extend(batch)
        if len(batch)<OFFSET:return rows
    raise RuntimeError("pagination_safety_cap")
def collect(addr,lo,hi):
    rows=fetch_rows(addr,lo,hi)
    if not rows:raise RuntimeError("empty_contract_window")
    ids=set(); heights={}; topic0=set()
    for x in rows:
        for k in ("blockHash","transactionHash","logIndex","blockNumber","address","topics","data"):
            if k not in x:raise RuntimeError("missing_"+k)
        if str(x["address"]).lower()!=addr:raise RuntimeError("emitter_mismatch")
        bh=str(x["blockHash"]).lower(); th=str(x["transactionHash"]).lower()
        if not HEX64.fullmatch(bh) or not HEX64.fullmatch(th):raise RuntimeError("bad_hash")
        bn=qint(x["blockNumber"]); li=qint(x["logIndex"])
        if not lo<=bn<=hi:raise RuntimeError("outside_frozen_window")
        ts=x["topics"]
        if not isinstance(ts,list) or not ts or any(not HEX64.fullmatch(str(t)) for t in ts):raise RuntimeError("bad_topics")
        if not isinstance(x["data"],str) or not HEXDATA.fullmatch(x["data"]):raise RuntimeError("bad_data")
        ident=(bh,th,li)
        if ident in ids:raise RuntimeError("duplicate_identity")
        ids.add(ident); topic0.add(str(ts[0]).lower())
        old=heights.setdefault(bn,bh)
        if old!=bh:raise RuntimeError("conflicting_block_hash")
    sample=sorted(heights); sample=sample[::max(1,len(sample)//3)][:3]
    for bn in sample:
        b=get(V2+f"/blocks/{bn}"); canonical=str(b.get("hash") or "").lower()
        if canonical!=heights[bn]:raise RuntimeError("block_identity_mismatch")
    return {"address":addr,"from":lo,"to":hi,"logs":len(rows),"heights":len(heights),"finality_identity_samples":len(sample),"topic0":sorted(topic0)}
def main():
    global MODE,SNAP
    ap=argparse.ArgumentParser(); ap.add_argument("--snapshot"); ap.add_argument("--replay"); a=ap.parse_args()
    if bool(a.snapshot)==bool(a.replay): raise SystemExit("choose exactly one of --snapshot/--replay")
    if a.replay:
        MODE="replay"; SNAP=json.loads(Path(a.replay).read_text())
    out=[collect(addr,lo,hi) for lo,hi in WINDOWS for addr in (USDC,USDT)]
    if a.snapshot: Path(a.snapshot).write_text(json.dumps(SNAP,sort_keys=True,separators=(",",":")))
    print(json.dumps({"phase":191,"scope":"DATA_ONLY","economic_trials":0,"source_mode":"snapshot_replay_v1","windows":out},sort_keys=True,separators=(",",":")))
if __name__=="__main__":main()
