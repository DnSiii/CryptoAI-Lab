#!/usr/bin/env python3
"""Phase191 DATA_ONLY Blockscout receipt provenance probe.
No price/PnL/holdout access. Fails closed on missing canonical log identity.
"""
from __future__ import annotations
import json, re, urllib.request

BASE = "https://eth.blockscout.com/api/v2"
USDC = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
USDT = "0xdac17f958d2ee523a2206206994597c13d831ec7"
HEX64 = re.compile(r"^0x[0-9a-fA-F]{64}$")
HEXDATA = re.compile(r"^0x(?:[0-9a-fA-F]{2})*$")


def get_json(path: str):
    req = urllib.request.Request(BASE + path, headers={"User-Agent":"CryptoAI-Lab-Phase191/1.1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def as_int(v):
    if isinstance(v, int) and not isinstance(v, bool) and v >= 0: return v
    if isinstance(v, str) and v.startswith("0x") and len(v) > 2: return int(v, 16)
    if isinstance(v, str) and v.isdigit(): return int(v)
    raise ValueError(f"noncanonical integer: {v!r}")


def topic_hash(v):
    # Blockscout v2 may encode a topic as a hash string or as {hash: 0x...}.
    if isinstance(v, dict): v = v.get("hash")
    if not isinstance(v, str) or not HEX64.fullmatch(v):
        raise ValueError("bad_topic")
    return v.lower()


def validate_log(log, expected_addr):
    raw_addr = log.get("address")
    addr = str(raw_addr.get("hash", "") if isinstance(raw_addr, dict) else raw_addr or "").lower()
    if addr != expected_addr: raise ValueError("emitter_mismatch")
    bh = str(log.get("block_hash") or log.get("blockHash") or "")
    th = str(log.get("transaction_hash") or log.get("transactionHash") or "")
    li = log.get("index", log.get("log_index", log.get("logIndex")))
    if not HEX64.fullmatch(bh): raise ValueError("bad_block_hash")
    if not HEX64.fullmatch(th): raise ValueError("bad_tx_hash")
    li = as_int(li)
    topics = log.get("topics") or []
    if not isinstance(topics, list) or not topics: raise ValueError("bad_topics")
    norm_topics = tuple(topic_hash(x) for x in topics)
    data = log.get("data", "")
    if not isinstance(data, str) or not HEXDATA.fullmatch(data): raise ValueError("bad_data")
    return (bh.lower(), th.lower(), li), norm_topics


def probe_contract(address):
    payload = get_json(f"/addresses/{address}/logs")
    items = payload.get("items", []) if isinstance(payload, dict) else []
    if not items: raise RuntimeError("empty_source_probe")
    ids=[]
    topic0=set()
    for log in items[:25]:
        ident, topics = validate_log(log, address)
        ids.append(ident); topic0.add(topics[0])
    if len(ids) != len(set(ids)): raise RuntimeError("duplicate_identity")
    return {"address":address,"validated":len(ids),"first_identity":ids[0],"topic0_count":len(topic0)}


def main():
    out={"phase":191,"scope":"DATA_ONLY","economic_trials":0,"source":"blockscout","contracts":[]}
    for a in (USDC, USDT): out["contracts"].append(probe_contract(a))
    print(json.dumps(out, sort_keys=True, separators=(",",":")))

if __name__ == "__main__": main()
