#!/usr/bin/env python3
"""Offline integrity audit for Phase192 partial DATA_ONLY snapshots.

This tool never accesses the network and never consumes market outcomes. It verifies
that every cached request/result remains inside the preregistered TRAIN-only native
issuer-event envelope before a partial checkpoint may be trusted for continuation.
"""
from __future__ import annotations
import argparse, hashlib, json, urllib.parse
from pathlib import Path

BASE_HOST="eth.blockscout.com"
BASE_PATH="/api"
USDC="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
USDT="0xdac17f958d2ee523a2206206994597c13d831ec7"
SPECS={
 (USDC,"0xab8530f87dc9b59234c4623bf917212bb2536d647574c8e7e5da92c2ede0c9f8"),
 (USDC,"0xcc16f5dbb4873280815c1ee09dbd06736cffcc184412cf7a71a0fdb75d397ca5"),
 (USDT,"0xcb8241adb0c3fdb35b70c24ce35c5eb0c17af7431c99f827d44a445ca624176a"),
 (USDT,"0x702d5967f45f6513a38ffc42d6ba9bf230bd40e8f53b16363c7eb4fd2deb9a44"),
}
WINDOWS=((16950000,17050000),(17950000,18050000),(18950000,19050000))
ALLOWED={"module","action","address","topic0","fromBlock","toBlock","page","offset"}

def _window(lo:int,hi:int):
    matches=[w for w in WINDOWS if w[0]<=lo<=hi<=w[1]]
    if len(matches)!=1: raise RuntimeError("request_outside_preregistered_train_window")
    return matches[0]

def audit(snapshot:dict)->dict:
    if not isinstance(snapshot,dict): raise RuntimeError("snapshot_not_object")
    touched=set(); rows=0; identities=set(); duplicate_appearances=0
    for url,obj in snapshot.items():
        u=urllib.parse.urlparse(url)
        if u.scheme!="https" or u.netloc!=BASE_HOST or u.path!=BASE_PATH: raise RuntimeError("unexpected_source_endpoint")
        q=urllib.parse.parse_qs(u.query,strict_parsing=True)
        if set(q)!=ALLOWED or any(len(v)!=1 for v in q.values()): raise RuntimeError("unexpected_query_shape")
        one={k:v[0] for k,v in q.items()}
        if one["module"]!="logs" or one["action"]!="getLogs" or one["offset"]!="1000": raise RuntimeError("unexpected_query_contract")
        addr=one["address"].lower(); topic=one["topic0"].lower()
        if (addr,topic) not in SPECS: raise RuntimeError("non_native_event_request")
        lo,hi,page=int(one["fromBlock"]),int(one["toBlock"]),int(one["page"])
        w=_window(lo,hi)
        if not 1<=page<=100: raise RuntimeError("page_out_of_bounds")
        if not isinstance(obj,dict) or not isinstance(obj.get("result"),list): raise RuntimeError("cached_response_not_log_list")
        touched.add((w[0],addr,topic)); result=obj["result"]
        if len(result)>1000: raise RuntimeError("response_exceeds_requested_offset")
        for r in result:
            if str(r.get("address","")).lower()!=addr: raise RuntimeError("cached_emitter_mismatch")
            topics=r.get("topics") or []
            if not topics or str(topics[0]).lower()!=topic: raise RuntimeError("cached_topic_mismatch")
            bn=int(str(r.get("blockNumber")),16)
            if not lo<=bn<=hi: raise RuntimeError("cached_log_outside_request_window")
            ident=(str(r.get("transactionHash","")).lower(),str(r.get("logIndex","")).lower())
            if ident in identities: duplicate_appearances+=1
            identities.add(ident); rows+=1
    raw=json.dumps(snapshot,sort_keys=True,separators=(",",":")).encode()
    return {"phase":192,"scope":"DATA_ONLY_PARTIAL_SNAPSHOT_INTEGRITY","economic_trials":0,
            "cached_requests":len(snapshot),"cached_rows":rows,"unique_log_identities":len(identities),
            "duplicate_appearances":duplicate_appearances,"native_cells_touched":len(touched),
            "max_native_cells":len(WINDOWS)*len(SPECS),"snapshot_sha256":hashlib.sha256(raw).hexdigest(),
            "decision":"PASS_PARTIAL_SNAPSHOT_INTEGRITY"}

def self_test():
    addr,topic=next(iter(SPECS)); lo,hi=WINDOWS[0]
    q=urllib.parse.urlencode({"module":"logs","action":"getLogs","address":addr,"topic0":topic,"fromBlock":lo,"toBlock":hi,"page":1,"offset":1000})
    out=audit({f"https://{BASE_HOST}{BASE_PATH}?{q}":{"result":[]}})
    assert out["economic_trials"]==0 and out["cached_requests"]==1 and out["native_cells_touched"]==1
    try: audit({"https://example.com/api?"+q:{"result":[]}})
    except RuntimeError: pass
    else: raise AssertionError("endpoint guard failed")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("snapshot",nargs="?"); ap.add_argument("--self-test",action="store_true"); a=ap.parse_args()
    if a.self_test: self_test(); print("PASS: Phase192 offline snapshot integrity invariants"); return
    if not a.snapshot: raise SystemExit("snapshot path required")
    snap=json.loads(Path(a.snapshot).read_text()); print(json.dumps(audit(snap),sort_keys=True,separators=(",",":")))
if __name__=="__main__": main()
