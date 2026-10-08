#!/usr/bin/env python3
"""Phase195-J: fixed TRAIN complete receipt payload parity. DATA_ONLY, never promote."""
import concurrent.futures
import hashlib
import json
import re
import v99_phase195g_transport_stage_audit as g

EXPECTED_TX_COUNT=102
FIELDS=("hash","number","timestamp","receiptsRoot","transactionsRoot","gasUsed","logsBloom")

def fixed_hex(value,size=None):
    if not isinstance(value,str) or re.fullmatch(r"0x(?:[0-9a-fA-F]{2})*",value) is None:
        raise ValueError("invalid_hex_bytes")
    if size is not None and len(value)!=2+size*2:raise ValueError("invalid_hex_width")
    return value.lower()

def result(call,endpoint,method,params):
    answer=call(endpoint,method,params)
    if answer.get("status")!="HTTP_200_RPC_RESULT":
        raise ValueError("rpc_unavailable:"+method+":"+str(answer.get("status"))+
                         ":"+str(answer.get("http_code",answer.get("rpc_code",""))))
    return answer["result"]

def normalized(header,receipts):
    txs=header["transactions"]
    if not isinstance(receipts,list) or len(receipts)!=len(txs):
        raise ValueError("incomplete_receipt_set")
    out=[];next_log=0;previous_gas=0
    for i,(tx,rec) in enumerate(zip(txs,receipts)):
        if not isinstance(rec,dict):raise ValueError("invalid_receipt_type")
        if (g.qty(rec["transactionIndex"])!=i or
            fixed_hex(rec["transactionHash"],32)!=fixed_hex(tx,32) or
            fixed_hex(rec["blockHash"],32)!=fixed_hex(header["hash"],32) or
            g.qty(rec["blockNumber"])!=g.HEIGHT):
            raise ValueError("receipt_identity")
        gas=g.qty(rec["cumulativeGasUsed"])
        if gas<previous_gas:raise ValueError("cumulative_gas_decreased")
        previous_gas=gas
        status=g.qty(rec["status"])
        kind=g.qty(rec.get("type","0x0"))
        if status not in (0,1) or kind not in (0,1,2):raise ValueError("receipt_fork_fields")
        bloom=fixed_hex(rec["logsBloom"],256)
        logs=rec["logs"]
        if not isinstance(logs,list):raise ValueError("invalid_logs_list")
        canon_logs=[]
        for log in logs:
            if (g.qty(log["logIndex"])!=next_log or
                g.qty(log["transactionIndex"])!=i or
                fixed_hex(log["transactionHash"],32)!=fixed_hex(tx,32) or
                fixed_hex(log["blockHash"],32)!=fixed_hex(header["hash"],32) or
                g.qty(log["blockNumber"])!=g.HEIGHT or
                log.get("removed") is not False):
                raise ValueError("log_identity")
            next_log+=1
            topics=log["topics"]
            if not isinstance(topics,list) or len(topics)>4:
                raise ValueError("invalid_topic_list")
            canon_logs.append([fixed_hex(log["address"],20),
                               [fixed_hex(t,32) for t in topics],fixed_hex(log["data"])])
        out.append([i,fixed_hex(tx,32),gas,status,kind,bloom,canon_logs])
    if previous_gas!=g.qty(header["gasUsed"]):
        raise ValueError("block_gas_mismatch")
    payload=json.dumps(out,separators=(",",":"),ensure_ascii=True).encode()
    return {"receipt_count":len(out),"all_log_count":next_log,
            "canonical_receipt_sha256":hashlib.sha256(payload).hexdigest()}

def fetch_individual(call,endpoint,txs):
    # Preflight fixed indices prevents wasting 102 RPC requests on an unsupported method.
    indices=sorted({0,len(txs)//2,len(txs)-1})
    found={}
    missing=[]
    for i in indices:
        try:
            found[i]=result(call,endpoint,"eth_getTransactionReceipt",[txs[i]])
        except ValueError as exc:
            missing.append(str(i)+":"+str(exc)[:55])
            continue
        if not isinstance(found[i],dict):
            missing.append(str(i)+":null_receipt")
    if missing:
        raise ValueError("fixed_probe_unavailable:"+",".join(missing))
    pending=[i for i in range(len(txs)) if i not in found]
    def one(i):
        rec=result(call,endpoint,"eth_getTransactionReceipt",[txs[i]])
        if not isinstance(rec,dict):raise ValueError("missing_individual_receipt")
        return i,rec
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for i,rec in pool.map(one,pending):found[i]=rec
    return [found[i] for i in range(len(txs))]

def hold(reason,**extra):
    return dict(decision=reason,phase="195-J",economic_trials=0,
                holdout_accessed=False,promotion_authorized=False,
                receipt_root_proven=False,independent_consensus_proven=False,
                historical_latency_proven=False,full_train_coverage_proven=False,
                provider_independence_proven=False,**extra)

def run(call=g.rpc):
    endpoints={k:g.ENDPOINTS[k] for k in ("drpc","publicnode")}
    if len(set(endpoints.values()))!=2:return hold("HOLD_ENDPOINT_ALIAS")
    try:
        headers={}
        for name,endpoint in endpoints.items():
            if result(call,endpoint,"eth_chainId",[])!="0x1":
                return hold("HOLD_WRONG_CHAIN",operator=name)
            headers[name]=result(call,endpoint,"eth_getBlockByNumber",[hex(g.HEIGHT),False])
            h=headers[name]
            if not isinstance(h,dict):return hold("HOLD_HEADER_MISSING",operator=name)
            if (g.qty(h["number"])!=g.HEIGHT or
                not g.TRAIN_START<=g.qty(h["timestamp"])<g.TRAIN_END):
                return hold("HOLD_TRAIN_FIREWALL",operator=name)
        a=headers["drpc"];b=headers["publicnode"]
        if any(a.get(f)!=b.get(f) for f in FIELDS):
            return hold("HOLD_HEADER_DISAGREEMENT")
        txs=a.get("transactions")
        if not isinstance(txs,list) or len(txs)!=EXPECTED_TX_COUNT or len(set(txs))!=len(txs):
            return hold("HOLD_FIXED_TX_CARDINALITY",observed_count=len(txs) if isinstance(txs,list) else None)
        for tx in txs:fixed_hex(tx,32)
        bulk=result(call,endpoints["drpc"],"eth_getBlockReceipts",[hex(g.HEIGHT)])
        baseline=normalized(a,bulk)
        comparison={}
        for label in ("publicnode","drpc"):
            try:
                receipts=fetch_individual(call,endpoints[label],txs)
                digest=normalized(a,receipts)
                comparison[label]={"status":"COMPLETE_STRUCTURAL_RECEIPTS",
                                   **digest,"matches_drpc_bulk":digest==baseline}
            except (ValueError,TypeError,KeyError) as exc:
                comparison[label]={"status":"HOLD_INDIVIDUAL_RECEIPTS",
                                   "error_code":str(exc)[:110] if isinstance(exc,ValueError) else type(exc).__name__}
        cross=comparison["publicnode"].get("matches_drpc_bulk") is True
        same=comparison["drpc"].get("matches_drpc_bulk") is True
        return hold("HOLD_RECEIPTS_ROOT_AND_CONSENSUS_UNPROVEN",
                    fixed_train_height=g.HEIGHT,block_hash=fixed_hex(a["hash"],32),
                    drpc_bulk=baseline,individual_comparison=comparison,
                    cross_operator_payload_parity=cross,
                    same_operator_transport_parity=same)
    except (ValueError,TypeError,KeyError) as exc:
        return hold("HOLD_RECEIPT_TRANSPORT_OR_STRUCTURE",
                    error_code=str(exc)[:110] if isinstance(exc,ValueError) else type(exc).__name__)

if __name__=="__main__":
    print(json.dumps(run(),sort_keys=True,separators=(",",":")))
