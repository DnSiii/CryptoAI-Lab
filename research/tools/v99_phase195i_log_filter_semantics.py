#!/usr/bin/env python3
"""Phase195-I fixed TRAIN blockHash-vs-range RPC log transport diagnostic. DATA_ONLY."""
import hashlib
import json
import re
import v99_phase195g_transport_stage_audit as g

def _hex(value,nbytes=None):
    if not isinstance(value,str) or re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*',value) is None:
        raise ValueError("noncanonical_hex_data")
    if nbytes is not None and len(value)!=2+2*nbytes:raise ValueError("hex_length")
    return value.lower()

def summarize_logs(answer,block_hash,topic):
    if answer.get("status")!="HTTP_200_RPC_RESULT":
        return {k:v for k,v in answer.items() if k!="result"}
    rows=answer.get("result")
    if not isinstance(rows,list):return {"status":"INVALID_LOGS_TYPE"}
    seen=set();entries=[]
    try:
        for row in rows:
            if not isinstance(row,dict):raise ValueError("row_type")
            idx=g.qty(row["logIndex"]);txidx=g.qty(row["transactionIndex"])
            if idx in seen:raise ValueError("duplicate_log_index")
            seen.add(idx)
            topics=row["topics"]
            if not isinstance(topics,list) or not 1<=len(topics)<=4:
                raise ValueError("topic_shape")
            topics=[_hex(x,32) for x in topics]
            if not (_hex(row["blockHash"],32)==block_hash.lower()
                    and g.qty(row["blockNumber"])==g.HEIGHT
                    and _hex(row["address"],20)==g.USDC
                    and topics[0]==topic
                    and row.get("removed") is False):
                raise ValueError("log_provenance")
            entries.append([idx,txidx,_hex(row["transactionHash"],32),
                            topics,_hex(row["data"])])
    except (KeyError,ValueError,TypeError,IndexError):
        return {"status":"INVALID_LOG_ROW"}
    entries.sort(key=lambda x:x[0])
    return {"status":"PROVISIONAL_UNVERIFIED_LOG_TRANSPORT","count":len(entries),
            "digest":hashlib.sha256(json.dumps(entries,separators=(",",":")).encode()).hexdigest()}

def _hold(reason,**fields):
    return dict(decision=reason,economic_trials=0,holdout_accessed=False,
                promotion_authorized=False,receipt_root_proven=False,
                full_train_coverage_proven=False,historical_latency_proven=False,
                provider_independence_proven=False,**fields)

def run(call=g.rpc):
    headers={}
    for label in ("publicnode","drpc"):
        endpoint=g.ENDPOINTS[label]
        chain=call(endpoint,"eth_chainId",[])
        if chain.get("status")!="HTTP_200_RPC_RESULT" or chain.get("result")!="0x1":
            return _hold("HOLD_CHAIN_ID",operator=label)
        block=call(endpoint,"eth_getBlockByNumber",[hex(g.HEIGHT),False])
        if block.get("status")!="HTTP_200_RPC_RESULT" or not isinstance(block.get("result"),dict):
            return _hold("HOLD_HEADER_TRANSPORT",operator=label)
        h=block["result"]
        try:
            if g.qty(h["number"])!=g.HEIGHT or not g.TRAIN_START<=g.qty(h["timestamp"])<g.TRAIN_END:
                return _hold("HOLD_TRAIN_FIREWALL")
            headers[label]=(_hex(h["hash"],32),g.qty(h["timestamp"]))
        except (ValueError,TypeError,KeyError):
            return _hold("HOLD_INVALID_HEADER",operator=label)
    if headers["publicnode"]!=headers["drpc"]:
        return _hold("HOLD_HEADER_DISAGREEMENT")
    block_hash=headers["drpc"][0]
    out={}
    for label in ("publicnode","drpc"):
        endpoint=g.ENDPOINTS[label];out[label]={}
        for name,topic in g.TOPICS.items():
            params={
                "height_range":{"address":g.USDC,"topics":[topic],
                                "fromBlock":hex(g.HEIGHT),"toBlock":hex(g.HEIGHT)},
                "block_hash":{"address":g.USDC,"topics":[topic],"blockHash":block_hash}}
            out[label][name]={mode:summarize_logs(
                call(endpoint,"eth_getLogs",[p]),block_hash,topic)
                for mode,p in params.items()}
    parity={}
    for name in g.TOPICS:
        modes=[out[label][name][mode] for label in ("publicnode","drpc")
               for mode in ("height_range","block_hash")]
        good=all(x["status"]=="PROVISIONAL_UNVERIFIED_LOG_TRANSPORT" for x in modes)
        parity[name]={"all_four_transports_available":good,
                      "same_log_digest_if_available":good and len({x["digest"] for x in modes})==1,
                      "same_log_count_if_available":good and len({x["count"] for x in modes})==1}
    return _hold("HOLD_LOG_TRANSPORT_DIAGNOSTIC_ONLY",fixed_train_height=g.HEIGHT,
                 cross_source_header_hash=block_hash,queries=out,parity=parity)

if __name__=="__main__":
    try: print(json.dumps(run(),sort_keys=True,separators=(",",":")))
    except Exception as exc:
        print(json.dumps(_hold("HOLD_UNEXPECTED_TRANSPORT",error_class=type(exc).__name__),
                         sort_keys=True,separators=(",",":")))
