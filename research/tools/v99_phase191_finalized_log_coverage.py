#!/usr/bin/env python3
"""DATA_ONLY real-log coverage collector for Phase191.

Queries finalized Ethereum logs only. No price/PnL/holdout inputs. Windows are
fixed historical TRAIN-era probes, separated in time, and results contain only
chain provenance/coverage diagnostics.
"""
import json, os, urllib.request
from collections import Counter

RPC=os.environ.get("ETH_RPC_URL", "https://ethereum-rpc.publicnode.com")
USDC="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
USDT="0xdAC17F958D2ee523a2206206994597C13D831ec7"
# Fixed block windows chosen ex ante, well before current chain tip.
WINDOWS=[(17000000,17000199),(18000000,18000199),(19000000,19000199)]

def rpc(method, params):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req=urllib.request.Request(RPC,data=body,headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=30) as r: out=json.load(r)
    if "error" in out: raise RuntimeError(out["error"])
    return out["result"]

def main():
    finalized=int(rpc("eth_getBlockByNumber",["finalized",False])["number"],16)
    rows=[]
    for lo,hi in WINDOWS:
        if hi>=finalized: raise RuntimeError("probe window is not finalized")
        for token in (USDC,USDT):
            logs=rpc("eth_getLogs",[{"address":token,"fromBlock":hex(lo),"toBlock":hex(hi)}])
            ids=set(); blocks=set()
            for x in logs:
                ident=(x["blockHash"].lower(),x["transactionHash"].lower(),int(x["logIndex"],16))
                if ident in ids: raise RuntimeError("duplicate log identity")
                ids.add(ident); blocks.add((int(x["blockNumber"],16),x["blockHash"].lower()))
            # conflicting hashes at a height fail closed
            c=Counter(n for n,_ in blocks)
            if any(v>1 for v in c.values()): raise RuntimeError("conflicting block hash")
            rows.append({"from":lo,"to":hi,"contract":token.lower(),"logs":len(logs),"blocks_with_logs":len(blocks)})
    if any(r["logs"]==0 for r in rows): raise RuntimeError("empty contract/window coverage")
    print(json.dumps({"schema":"phase191-coverage-v1","finalized_tip":finalized,"windows":rows},sort_keys=True,separators=(",",":")))
if __name__=="__main__": main()
