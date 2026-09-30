#!/usr/bin/env python3
"""Phase191 DATA_ONLY Blockscout receipt provenance probe.
No price/PnL/holdout access. Fails closed on missing canonical log identity.
"""
from __future__ import annotations
import json, re, sys, urllib.parse, urllib.request

BASE = "https://eth.blockscout.com/api/v2"
USDC = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
USDT = "0xdac17f958d2ee523a2206206994597c13d831ec7"
HEX64 = re.compile(r"^0x[0-9a-fA-F]{64}$")


def get_json(path: str):
    req = urllib.request.Request(BASE + path, headers={"User-Agent":"CryptoAI-Lab-Phase191/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def as_int(v):
    if isinstance(v, int): return v
    if isinstance(v, str) and v.startswith("0x") and len(v) > 2: return int(v, 16)
    if isinstance(v, str) and v.isdigit(): return int(v)
    raise ValueError(f"noncanonical integer: {v!r}")


def validate_log(log, expected_addr):
    addr = str(log.get("address") or {}).lower()
    if isinstance(log.get("address"), dict): addr = str(log["address"].get("hash", "")).lower()
    if addr != expected_addr: raise ValueError("emitter_mismatch")
    bh = str(log.get("block_hash") or log.get("blockHash") or "")
    th = str(log.get("transaction_hash") or log.get("transactionHash") or "")
    li = log.get("index", log.get("log_index", log.get("logIndex")))
    if not HEX64.match(bh): raise ValueError("bad_block_hash")
    if not HEX64.match(th): raise ValueError("bad_tx_hash")
    li = as_int(li)
    topics = log.get("topics") or []
    if not topics or not all(isinstance(x, str) and x.startswith("0x") for x in topics): raise ValueError("bad_topics")
    data = log.get("data", "")
    if not isinstance(data, str) or not data.startswith("0x"): raise ValueError("bad_data")
    return (bh.lower(), th.lower(), li)


def probe_contract(address):
    # Source-schema probe only: request first page of contract logs and validate canonical identity.
    payload = get_json(f"/addresses/{address}/logs")
    items = payload.get("items", []) if isinstance(payload, dict) else []
    if not items: raise RuntimeError("empty_source_probe")
    ids=[]
    for log in items[:25]: ids.append(validate_log(log, address))
    if len(ids) != len(set(ids)): raise RuntimeError("duplicate_identity")
    return {"address":address,"validated":len(ids),"first_identity":ids[0]}


def main():
    out={"phase":191,"scope":"DATA_ONLY","economic_trials":0,"source":"blockscout","contracts":[]}
    for a in (USDC, USDT): out["contracts"].append(probe_contract(a))
    print(json.dumps(out, sort_keys=True, separators=(",",":")))

if __name__ == "__main__": main()
