#!/usr/bin/env python3
"""Phase195-H fixed-TRAIN cross-source header and receipt structure (DATA_ONLY).

Untrusted providers, no receiptsRoot reconstruction or independent consensus.
A structural match never authorizes PnL, holdout or promotion.
"""
import hashlib
import json
import v99_phase195g_transport_stage_audit as g

HEIGHT=g.HEIGHT

def require(condition,reason):
    if not condition: raise ValueError(reason)

def fetch(call,endpoint,method,params):
    response=call(endpoint,method,params)
    require(response.get('status')=='HTTP_200_RPC_RESULT',
            'rpc_unavailable:'+method+':'+str(response.get('status')))
    return response['result']

def validate(public_header,drpc_header,receipts,logs_by_topic):
    require(isinstance(public_header,dict) and isinstance(drpc_header,dict),'header_type')
    for h in (public_header,drpc_header):
        require(g.qty(h['number'])==HEIGHT,'wrong_height')
        require(g.TRAIN_START<=g.qty(h['timestamp'])<g.TRAIN_END,'train_firewall')
    for key in ('hash','parentHash','receiptsRoot','transactionsRoot','number','timestamp','gasUsed','logsBloom'):
        require(public_header.get(key)==drpc_header.get(key),'cross_source_header_disagreement:'+key)
    txs=drpc_header.get('transactions')
    require(isinstance(txs,list) and all(isinstance(x,str) and len(x)==66 for x in txs),'tx_hashes_missing')
    require(len(txs)==len(set(x.lower() for x in txs)),'duplicate_tx')
    require(isinstance(receipts,list) and len(receipts)==len(txs),'receipt_cardinality')
    next_log=0;last_gas=0;native={topic:[] for topic in g.TOPICS.values()}
    for i,(tx,rec) in enumerate(zip(txs,receipts)):
        require(isinstance(rec,dict),'receipt_type')
        require(g.qty(rec['transactionIndex'])==i and rec['transactionHash'].lower()==tx.lower(),'receipt_order')
        require(rec['blockHash'].lower()==drpc_header['hash'].lower() and g.qty(rec['blockNumber'])==HEIGHT,'receipt_block_linkage')
        gas=g.qty(rec['cumulativeGasUsed'])
        require(gas>=last_gas,'cumulative_gas_decreased')
        last_gas=gas
        require(g.qty(rec['status']) in (0,1),'invalid_receipt_status')
        logs=rec.get('logs')
        require(isinstance(logs,list),'missing_logs')
        for log in logs:
            require(g.qty(log['logIndex'])==next_log and g.qty(log['transactionIndex'])==i,'global_log_index')
            require(log['transactionHash'].lower()==tx.lower() and log['blockHash'].lower()==drpc_header['hash'].lower() and g.qty(log['blockNumber'])==HEIGHT,'log_block_linkage')
            require(log.get('removed') is False,'removed_log')
            if log['address'].lower()==g.USDC and log.get('topics'):
                topic=log['topics'][0].lower()
                if topic in native:
                    native[topic].append([i,next_log,tx.lower(),log['data'].lower()])
            next_log+=1
    require(last_gas==g.qty(drpc_header['gasUsed']),'block_gas_used_mismatch')
    for topic in g.TOPICS.values():
        rows=logs_by_topic.get(topic)
        require(isinstance(rows,list),'missing_eth_getLogs')
        actual=[]
        for log in rows:
            require(log['address'].lower()==g.USDC and log['topics'][0].lower()==topic,'eth_getLogs_topic_mismatch')
            actual.append([g.qty(log['transactionIndex']),g.qty(log['logIndex']),log['transactionHash'].lower(),log['data'].lower()])
        require(actual==native[topic],'eth_getLogs_receipts_mismatch')
    return {'status':'PROVISIONAL_CROSS_SOURCE_STRUCTURAL_MATCH_NOT_ROOT_PROOF',
            'fixed_train_height':HEIGHT,'tx_count':len(txs),'receipt_count':len(receipts),
            'all_logs_count':next_log,
            'native_event_counts':{name:len(native[topic]) for name,topic in g.TOPICS.items()},
            'header_hash':drpc_header['hash'].lower(),
            'unverified_receipts_root_claim':drpc_header['receiptsRoot'].lower(),
            'receipt_tx_index_digest':hashlib.sha256(json.dumps(
                [[i,tx.lower()] for i,tx in enumerate(txs)],separators=(',',':')).encode()).hexdigest(),
            'independent_consensus_anchor_proven':False,
            'receipts_root_recomputed':False,'operator_independence_proven':False,
            'historical_latency_proven':False,'train_coverage_proven':False,
            'economic_trials':0,'holdout_accessed':False,'promotion_authorized':False}

def run(call=g.rpc):
    public=g.ENDPOINTS['publicnode'];drpc=g.ENDPOINTS['drpc']
    for endpoint in (public,drpc):
        require(fetch(call,endpoint,'eth_chainId',[])=='0x1','wrong_chain')
    a=fetch(call,public,'eth_getBlockByNumber',[hex(HEIGHT),False])
    b=fetch(call,drpc,'eth_getBlockByNumber',[hex(HEIGHT),False])
    receipts=fetch(call,drpc,'eth_getBlockReceipts',[hex(HEIGHT)])
    logs={topic:fetch(call,drpc,'eth_getLogs',[{'address':g.USDC,'topics':[topic],
        'fromBlock':hex(HEIGHT),'toBlock':hex(HEIGHT)}]) for topic in g.TOPICS.values()}
    return validate(a,b,receipts,logs)

def main():
    try: result=run()
    except Exception as exc:
        result={'status':'HOLD_STRUCTURAL_OR_TRANSPORT',
                'reason':str(exc)[:130] if isinstance(exc,ValueError) else type(exc).__name__,
                'economic_trials':0,'holdout_accessed':False,'promotion_authorized':False}
        print(json.dumps(result,sort_keys=True));raise SystemExit(2)
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__': main()
