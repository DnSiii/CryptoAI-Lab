#!/usr/bin/env python3
"""Phase191 DATA_ONLY orthogonal transport probe: Routescan keyless indexed logs.

No price/PnL/holdout inputs. This does NOT authorize an economic trial. It only
checks whether an independent indexed source can serve the already-fixed TRAIN-era
Ethereum windows with immutable log provenance. Finality remains a separate gate.
"""
import json, urllib.parse, urllib.request

BASE="https://api.routescan.io/v2/network/mainnet/evm/1/etherscan/api"
USDC="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
USDT="0xdAC17F958D2ee523a2206206994597C13D831ec7"
WINDOWS=[(17000000,17000199),(18000000,18000199),(19000000,19000199)]
OFFSET=1000

def hexword(v,nbytes):
    return isinstance(v,str) and v.startswith("0x") and len(v)==2+2*nbytes and all(c in "0123456789abcdefABCDEF" for c in v[2:])

def fetch_page(address,lo,hi,page):
    q=urllib.parse.urlencode({"module":"logs","action":"getLogs","address":address,
        "fromBlock":lo,"toBlock":hi,"page":page,"offset":OFFSET})
    req=urllib.request.Request(BASE+"?"+q,headers={"User-Agent":"CryptoAI-Lab-Phase191/5.1"})
    with urllib.request.urlopen(req,timeout=30) as r: obj=json.load(r)
    result=obj.get("result")
    if not isinstance(result,list): raise RuntimeError("indexed source did not return a log list: "+str(obj)[:200])
    return result

def collect(address,lo,hi):
    rows=[]
    for page in range(1,101):
        batch=fetch_page(address,lo,hi,page); rows.extend(batch)
        if len(batch)<OFFSET: break
    else: raise RuntimeError("pagination safety cap reached")
    ids=set(); height_hash={}
    for x in rows:
        for k in ("blockHash","transactionHash","logIndex","blockNumber","address","topics","data"):
            if k not in x: raise RuntimeError("missing immutable log field: "+k)
        bh=x["blockHash"].lower(); th=x["transactionHash"].lower()
        if not hexword(bh,32) or not hexword(th,32): raise RuntimeError("malformed provenance hash")
        if x["address"].lower()!=address.lower(): raise RuntimeError("wrong emitter contract")
        if not isinstance(x["topics"],list) or not x["topics"] or any(not hexword(t,32) for t in x["topics"]):
            raise RuntimeError("malformed event topics")
        if not isinstance(x["data"],str) or not x["data"].startswith("0x") or len(x["data"])%2:
            raise RuntimeError("malformed event data")
        bn=int(x["blockNumber"],16); li=int(x["logIndex"],16)
        if not lo<=bn<=hi: raise RuntimeError("log outside fixed window")
        ident=(bh,th,li)
        if ident in ids: raise RuntimeError("duplicate log identity")
        ids.add(ident)
        old=height_hash.setdefault(bn,bh)
        if old!=bh: raise RuntimeError("conflicting block hash at same height")
    return {"from":lo,"to":hi,"contract":address.lower(),"logs":len(rows),"blocks_with_logs":len(height_hash)}

def main():
    out=[]
    for lo,hi in WINDOWS:
        for address in (USDC,USDT): out.append(collect(address,lo,hi))
    if any(x["logs"]==0 for x in out): raise RuntimeError("empty contract/window coverage")
    print(json.dumps({"schema":"phase191-routescan-data-only-v2","windows":out},sort_keys=True,separators=(",",":")))
if __name__=="__main__": main()
