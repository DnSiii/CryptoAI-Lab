#!/usr/bin/env python3
"""Phase191 DATA_ONLY audit over the three preregistered TRAIN windows.
No price/PnL/regime/benchmark/holdout access. No provenance repair/inference.
"""
from __future__ import annotations
import json,re,urllib.parse,urllib.request
BASE="https://eth.blockscout.com/api"
V2="https://eth.blockscout.com/api/v2"
USDC="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
USDT="0xdac17f958d2ee523a2206206994597c13d831ec7"
WINDOWS=((17000000,17000199),(18000000,18000199),(19000000,19000199))
HEX64=re.compile(r"^0x[0-9a-fA-F]{64}$")
HEXDATA=re.compile(r"^0x(?:[0-9a-fA-F]{2})*$")

def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoAI-Lab-Phase191/2.0"})
    with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)

def qint(v):
    if isinstance(v,int) and not isinstance(v,bool) and v>=0:return v
    if isinstance(v,str) and v.startswith("0x") and len(v)>2:return int(v,16)
    if isinstance(v,str) and v.isdigit():return int(v)
    raise ValueError("noncanonical_integer")

def collect(addr,lo,hi):
    qs=urllib.parse.urlencode({"module":"logs","action":"getLogs","address":addr,"fromBlock":lo,"toBlock":hi,"page":1,"offset":1000})
    obj=get(BASE+"?"+qs); rows=obj.get("result") if isinstance(obj,dict) else None
    if not isinstance(rows,list):raise RuntimeError("source_not_log_list")
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
    # Independent endpoint check: sampled heights must resolve to the same canonical block hash.
    for bn in sorted(heights)[::max(1,len(heights)//5)]:
        b=get(V2+f"/blocks/{bn}"); canonical=str(b.get("hash") or "").lower()
        if canonical!=heights[bn]:raise RuntimeError("block_identity_mismatch")
    return {"address":addr,"from":lo,"to":hi,"logs":len(rows),"heights":len(heights),"topic0":sorted(topic0)}

def main():
    out=[]
    for lo,hi in WINDOWS:
        for addr in (USDC,USDT):out.append(collect(addr,lo,hi))
    print(json.dumps({"phase":191,"scope":"DATA_ONLY","economic_trials":0,"windows":out},sort_keys=True,separators=(",",":")))
if __name__=="__main__":main()
