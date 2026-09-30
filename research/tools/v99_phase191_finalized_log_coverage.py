#!/usr/bin/env python3
"""DATA_ONLY real-log coverage collector for Phase191.

Queries finalized Ethereum logs only. No price/PnL/holdout inputs. Windows are
fixed historical TRAIN-era probes, separated in time, and results contain only
chain provenance/coverage diagnostics. Transport chunking never changes the
pre-registered scientific windows.
"""
import json, os, urllib.request, urllib.error

PUBLIC_RPCS=[
    "https://ethereum-rpc.publicnode.com","https://eth.llamarpc.com",
    "https://rpc.ankr.com/eth","https://eth.drpc.org","https://1rpc.io/eth",
    "https://eth.merkle.io","https://cloudflare-eth.com",
]
RPCS=[x for x in [os.environ.get("ETH_RPC_URL"),*PUBLIC_RPCS] if x]
USDC="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
USDT="0xdAC17F958D2ee523a2206206994597C13D831ec7"
WINDOWS=[(17000000,17000199),(18000000,18000199),(19000000,19000199)]
CHUNK=50  # transport-only; one audited public RPC explicitly caps eth_getLogs at 50 blocks

class RPCUnavailable(RuntimeError): pass

def call(endpoint, method, params):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params},separators=(",",":")).encode()
    req=urllib.request.Request(endpoint,data=body,headers={"Content-Type":"application/json","User-Agent":"CryptoAI-Lab-Phase191/3.0"})
    with urllib.request.urlopen(req,timeout=30) as r: out=json.load(r)
    if "error" in out: raise RuntimeError(out["error"])
    if "result" not in out: raise RuntimeError("missing result")
    return out["result"]

def rpc(method, params):
    errors=[]
    for endpoint in RPCS:
        try: return call(endpoint,method,params)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, RuntimeError, ValueError, json.JSONDecodeError) as e:
            errors.append(type(e).__name__+":"+str(e)[:120])
    raise RPCUnavailable(method+" unavailable on every configured transport: "+" | ".join(errors))

def get_logs(token,lo,hi):
    out=[]
    for a in range(lo,hi+1,CHUNK):
        b=min(a+CHUNK-1,hi)
        out.extend(rpc("eth_getLogs",[{"address":token,"fromBlock":hex(a),"toBlock":hex(b)}]))
    return out

def main():
    finalized_obj=rpc("eth_getBlockByNumber",["finalized",False])
    if not finalized_obj or "number" not in finalized_obj: raise RuntimeError("invalid finalized block response")
    finalized=int(finalized_obj["number"],16)
    rows=[]
    for lo,hi in WINDOWS:
        if hi>=finalized: raise RuntimeError("probe window is not finalized")
        for token in (USDC,USDT):
            logs=get_logs(token,lo,hi)
            ids=set(); by_height={}
            for x in logs:
                required=("blockHash","transactionHash","logIndex","blockNumber")
                if any(k not in x for k in required): raise RuntimeError("log missing provenance field")
                bh=x["blockHash"].lower(); th=x["transactionHash"].lower(); li=int(x["logIndex"],16); bn=int(x["blockNumber"],16)
                if len(bh)!=66 or len(th)!=66: raise RuntimeError("malformed provenance hash")
                if not (lo<=bn<=hi): raise RuntimeError("log outside fixed probe window")
                ident=(bh,th,li)
                if ident in ids: raise RuntimeError("duplicate log identity")
                ids.add(ident)
                old=by_height.setdefault(bn,bh)
                if old!=bh: raise RuntimeError("conflicting block hash")
            rows.append({"from":lo,"to":hi,"contract":token.lower(),"logs":len(logs),"blocks_with_logs":len(by_height)})
    if any(r["logs"]==0 for r in rows): raise RuntimeError("empty contract/window coverage")
    print(json.dumps({"schema":"phase191-coverage-v4","windows":rows},sort_keys=True,separators=(",",":")))
if __name__=="__main__": main()
