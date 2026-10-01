#!/usr/bin/env python3
"""Phase191 DATA_ONLY audit over preregistered TRAIN windows.
No price/PnL/regime/benchmark/holdout access. No provenance repair/inference.
Live mode records an immutable source snapshot; replay mode performs zero network I/O.
Live snapshots are checkpointed after every successful response so transport failures
cannot erase already captured immutable historical evidence.
"""
from __future__ import annotations
import argparse,json,re,time,urllib.error,urllib.parse,urllib.request
from pathlib import Path
BASE="https://eth.blockscout.com/api"; V2="https://eth.blockscout.com/api/v2"
USDC="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"; USDT="0xdac17f958d2ee523a2206206994597c13d831ec7"
WINDOWS=((17000000,17000199),(18000000,18000199),(19000000,19000199)); OFFSET=1000
HEX64=re.compile(r"^0x[0-9a-fA-F]{64}$"); HEXDATA=re.compile(r"^0x(?:[0-9a-fA-F]{2})*$")
SNAP={}; MODE="live"; LAST_REQUEST=0.0; SNAPSHOT_PATH=None
MIN_REQUEST_GAP=12.0

def checkpoint():
    if MODE!="live" or SNAPSHOT_PATH is None:return
    tmp=SNAPSHOT_PATH.with_suffix(SNAPSHOT_PATH.suffix+".tmp")
    tmp.write_text(json.dumps(SNAP,sort_keys=True,separators=(",",":")))
    tmp.replace(SNAPSHOT_PATH)

def get(url):
    global SNAP,LAST_REQUEST
    # A restored checkpoint is immutable evidence for an exact URL. Reuse it rather
    # than refetching and creating needless anonymous-source load.
    if url in SNAP:return SNAP[url]
    if MODE=="replay":raise RuntimeError("snapshot_miss")
    for attempt in range(10):
        wait=MIN_REQUEST_GAP-(time.monotonic()-LAST_REQUEST)
        if wait>0:time.sleep(wait)
        req=urllib.request.Request(url,headers={"User-Agent":"CryptoAI-Lab-Phase191/2.6"})
        LAST_REQUEST=time.monotonic()
        try:
            with urllib.request.urlopen(req,timeout=30) as r:obj=json.load(r)
            SNAP[url]=obj;checkpoint();return obj
        except urllib.error.HTTPError as e:
            if e.code!=429 or attempt==9:raise
            retry_after=e.headers.get("Retry-After") if e.headers else None
            try:server_wait=float(retry_after) if retry_after is not None else 0.0
            except ValueError:server_wait=0.0
            time.sleep(max(server_wait,min(240.0,30.0*(2**attempt))))
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
        obj=get(BASE+"?"+qs);batch=obj.get("result") if isinstance(obj,dict) else None
        if not isinstance(batch,list):raise RuntimeError("source_not_log_list")
        rows.extend(batch)
        if len(batch)<OFFSET:return rows
    raise RuntimeError("pagination_safety_cap")

def collect(addr,lo,hi):
    rows=fetch_rows(addr,lo,hi)
    if not rows:raise RuntimeError("empty_contract_window")
    ids=set();heights={};topic0=set()
    for x in rows:
        for k in ("blockHash","transactionHash","logIndex","blockNumber","address","topics","data"):
            if k not in x:raise RuntimeError("missing_"+k)
        if str(x["address"]).lower()!=addr:raise RuntimeError("emitter_mismatch")
        bh=str(x["blockHash"]).lower();th=str(x["transactionHash"]).lower()
        if not HEX64.fullmatch(bh) or not HEX64.fullmatch(th):raise RuntimeError("bad_hash")
        bn=qint(x["blockNumber"]);li=qint(x["logIndex"])
        if not lo<=bn<=hi:raise RuntimeError("outside_frozen_window")
        ts=x["topics"]
        if not isinstance(ts,list) or not ts or any(not HEX64.fullmatch(str(t)) for t in ts):raise RuntimeError("bad_topics")
        if not isinstance(x["data"],str) or not HEXDATA.fullmatch(x["data"]):raise RuntimeError("bad_data")
        ident=(bh,th,li)
        if ident in ids:raise RuntimeError("duplicate_identity")
        ids.add(ident);topic0.add(str(ts[0]).lower())
        old=heights.setdefault(bn,bh)
        if old!=bh:raise RuntimeError("conflicting_block_hash")
    sample=sorted(heights);sample=sample[::max(1,len(sample)//3)][:3]
    for bn in sample:
        b=get(V2+f"/blocks/{bn}");canonical=str(b.get("hash") or "").lower()
        if canonical!=heights[bn]:raise RuntimeError("block_identity_mismatch")
    return {"address":addr,"from":lo,"to":hi,"logs":len(rows),"heights":len(heights),"finality_identity_samples":len(sample),"topic0":sorted(topic0)}

def main():
    global MODE,SNAP,SNAPSHOT_PATH
    ap=argparse.ArgumentParser();ap.add_argument("--snapshot");ap.add_argument("--replay");a=ap.parse_args()
    if bool(a.snapshot)==bool(a.replay):raise SystemExit("choose exactly one of --snapshot/--replay")
    if a.replay:
        MODE="replay";SNAP=json.loads(Path(a.replay).read_text())
    else:
        SNAPSHOT_PATH=Path(a.snapshot)
        if SNAPSHOT_PATH.exists() and SNAPSHOT_PATH.stat().st_size:
            SNAP=json.loads(SNAPSHOT_PATH.read_text())
            if not isinstance(SNAP,dict):raise RuntimeError("bad_checkpoint_snapshot")
    out=[collect(addr,lo,hi) for lo,hi in WINDOWS for addr in (USDC,USDT)]
    checkpoint()
    print(json.dumps({"phase":191,"scope":"DATA_ONLY","economic_trials":0,"source_mode":"snapshot_replay_v2_checkpointed","snapshot_entries":len(SNAP),"windows":out},sort_keys=True,separators=(",",":")))
if __name__=="__main__":main()
