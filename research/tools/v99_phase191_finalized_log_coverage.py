#!/usr/bin/env python3
"""DATA_ONLY real-log coverage collector for Phase191.

Queries finalized Ethereum logs only. No price/PnL/holdout inputs. Windows are
fixed historical TRAIN-era probes, separated in time, and results contain only
chain provenance/coverage diagnostics. Public RPC endpoints are transport-only
fallbacks; chain responses must agree on block identity where independently
queried.
"""
import json, os, urllib.request, urllib.error
from collections import Counter

RPCS=[x for x in [os.environ.get("ETH_RPC_URL"),"https://ethereum-rpc.publicnode.com","https://eth.llamarpc.com","https://rpc.ankr.com/eth"] if x]
USDC="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
USDT="0xdAC17F958D2ee523a2206206994597C13D831ec7"
WINDOWS=[(17000000,17000199),(18000000,18000199),(19000000,19000199)]

def rpc(method, params):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    errors=[]
    for endpoint in RPCS:
        try:
            req=urllib.request.Request(endpoint,data=body,headers={"Content-Type":"application/json","User-Agent":"CryptoAI-Lab-Phase191/1.0"})
            with urllib.request.urlopen(req,timeout=30) as r: out=json.load(r)
            if "error" in out: raise RuntimeError(out["error"])
            if "result" not in out: raise RuntimeError("missing result")
            return out["result"]
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, RuntimeError) as e:
            errors.append(type(e).__name__+":"+str(e)[:120])
    raise RuntimeError("all RPC transports failed: "+" | ".join(errors))

def main():
    finalized=int(rpc("eth_getBlockByNumber",["finalized",False])["number"],16)
    rows=[]
    for lo,hi in WINDOWS:
        if hi>=finalized: raise RuntimeError("probe window is not finalized")
        for token in (USDC,USDT):
            logs=rpc("eth_getLogs",[{"address":token,"fromBlock":hex(lo),"toBlock":hex(hi)}])
            ids=set(); by_height={}
            for x in logs:
                bh=x["blockHash"].lower(); th=x["transactionHash"].lower(); li=int(x["logIndex"],16); bn=int(x["blockNumber"],16)
                ident=(bh,th,li)
                if ident in ids: raise RuntimeError("duplicate log identity")
                ids.add(ident)
                old=by_height.setdefault(bn,bh)
                if old!=bh: raise RuntimeError("conflicting block hash")
            rows.append({"from":lo,"to":hi,"contract":token.lower(),"logs":len(logs),"blocks_with_logs":len(by_height)})
    if any(r["logs"]==0 for r in rows): raise RuntimeError("empty contract/window coverage")
    # Exclude moving finalized tip from deterministic payload; only its gate effect matters.
    print(json.dumps({"schema":"phase191-coverage-v2","windows":rows},sort_keys=True,separators=(",",":")))
if __name__=="__main__": main()
