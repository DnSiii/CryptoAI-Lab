#!/usr/bin/env python3
"""Phase195 read-only archival transport preflight, NOT coverage certification.
Fixed historical block 17,000,000 was selected by the earlier Phase191 source
protocol, never by a market outcome. No prices, PnL or holdout access.
"""
from __future__ import annotations
import hashlib
import json
import os
import urllib.request
from datetime import datetime, timezone

TRAIN_START=1638316800
TRAIN_END=1705536000
HEIGHT=17000000
USDC="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
TOPICS={
 "mint":"0xab8530f87dc9b59234c4623bf917212bb2536d647574c8e7e5da92c2ede0c9f8",
 "burn":"0xcc16f5dbb4873280815c1ee09dbd06736cffcc184412cf7a71a0fdb75d397ca5"
}
ENDPOINTS=[
 ("publicnode","https://ethereum-rpc.publicnode.com"),
 ("llamarpc","https://eth.llamarpc.com"),
 ("drpc","https://eth.drpc.org")
]

def rpc(endpoint, method, params):
    body=json.dumps({"jsonrpc":"2.0","id":195,"method":method,"params":params},
                    separators=(",",":")).encode()
    req=urllib.request.Request(endpoint,data=body,headers={
        "Content-Type":"application/json","User-Agent":"CryptoAI-Lab-Phase195-Preflight/1"})
    with urllib.request.urlopen(req,timeout=20) as f:
        response=json.load(f)
    if not isinstance(response,dict) or response.get("jsonrpc")!="2.0" or response.get("id")!=195 or "error" in response or "result" not in response:
        raise ValueError("rpc_invalid_response")
    return response["result"]

def hexnum(s):
    if not isinstance(s,str) or not s.startswith("0x"): raise ValueError("invalid_hex")
    return int(s,16)

def one(operator,endpoint):
    if hexnum(rpc(endpoint,"eth_chainId",[]))!=1: raise ValueError("wrong_chain")
    finalized=rpc(endpoint,"eth_getBlockByNumber",["finalized",False])
    if not isinstance(finalized,dict): raise ValueError("no_finalized_header")
    fh=hexnum(finalized["number"])
    if fh<HEIGHT: raise ValueError("historical_height_not_finalized")
    pinned=rpc(endpoint,"eth_getBlockByNumber",[hex(fh),False])
    if not isinstance(pinned,dict) or pinned.get("hash")!=finalized.get("hash"):
        raise ValueError("finalized_tag_equivocation")
    b=rpc(endpoint,"eth_getBlockByNumber",[hex(HEIGHT),False])
    if not isinstance(b,dict) or hexnum(b["number"])!=HEIGHT:
        raise ValueError("historical_header_missing")
    stamp=hexnum(b["timestamp"])
    if not TRAIN_START<=stamp<TRAIN_END:
        raise ValueError("train_firewall_header")
    bh=b["hash"].lower()
    if not (bh.startswith("0x") and len(bh)==66): raise ValueError("invalid_header_hash")
    events={}
    for name,topic in TOPICS.items():
        rows=rpc(endpoint,"eth_getLogs",[{"address":USDC,"topics":[topic],
                 "fromBlock":hex(HEIGHT),"toBlock":hex(HEIGHT)}])
        if not isinstance(rows,list) or len(rows)>=1000:
            raise ValueError("unproven_single_block_log_completeness")
        prev=-1
        sigs=[]
        for row in rows:
            idx=hexnum(row["logIndex"])
            if (hexnum(row["blockNumber"])!=HEIGHT or row["blockHash"].lower()!=bh
                or row["address"].lower()!=USDC or row["topics"][0].lower()!=topic
                or row.get("removed") is not False or idx<=prev):
                raise ValueError("log_provenance_or_order_mismatch")
            prev=idx
            sigs.append([row["blockHash"].lower(),row["transactionHash"].lower(),
                         idx,row["data"].lower(),[x.lower() for x in row["topics"]]])
        events[name]={"count":len(sigs),"sha256":hashlib.sha256(
            json.dumps(sigs,sort_keys=True,separators=(",",":")).encode()).hexdigest()}
    return {"operator_label":operator,"block":HEIGHT,"timestamp":stamp,
            "block_hash":bh,"events":events,"classification":"PROVISIONAL_TRANSPORT_ONLY"}

def main():
    if os.environ.get("PHASE195_NO_NETWORK")=="1":
        assert TRAIN_START<TRAIN_END and len(TOPICS)==2 and HEIGHT>0
        print("PASS: preflight static TRAIN firewall")
        return
    successes=[]
    failures=[]
    for label,url in ENDPOINTS:
        try:successes.append(one(label,url))
        except Exception as exc:
            failures.append({"operator_label":label,"error_class":type(exc).__name__,
                             "error_code":str(exc)[:100] if isinstance(exc,ValueError) else "transport_unavailable"})
    identical=len(successes)>=2 and all(
        (r["block_hash"],r["events"])==(successes[0]["block_hash"],successes[0]["events"])
        for r in successes[1:])
    result={"phase":195,"scope":"DATA_ONLY_ARCHIVE_PREFLIGHT","economic_trials":0,
            "fixed_train_height":HEIGHT,"successes":successes,"failures":failures,
            "matching_public_transport_probes":identical,
            "decision":"PROVISIONAL_TRANSPORT_MATCH_NO_COVERAGE_PROOF" if identical
            else "HOLD_TRANSPORT_OR_PROVENANCE",
            "no_historical_latency_or_operator_independence_proven":True,
            "no_complete_day_or_economic_trial_authorized":True}
    print(json.dumps(result,sort_keys=True,separators=(",",":")))

if __name__=="__main__":main()
