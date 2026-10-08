#!/usr/bin/env python3
"""Phase195-G: fixed-TRAIN archival RPC transport attribution, DATA_ONLY.

Untrusted HTTP/RPC responses never prove consensus, receiptsRoot, historical
availability, provider independence, coverage, or eligibility for PnL.
"""
import json
import re
import urllib.error
import urllib.request

HEIGHT=17_000_000
TRAIN_START,TRAIN_END=1_638_316_800,1_705_536_000
USDC='0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'
TOPICS={'mint':'0xab8530f87dc9b59234c4623bf917212bb2536d647574c8e7e5da92c2ede0c9f8',
        'burn':'0xcc16f5dbb4873280815c1ee09dbd06736cffcc184412cf7a71a0fdb75d397ca5'}
ENDPOINTS={'publicnode':'https://ethereum-rpc.publicnode.com',
           'llamarpc':'https://eth.llamarpc.com','drpc':'https://eth.drpc.org'}
MAX_BYTES=2_000_000
RPC_ID=1957

def no_duplicates(pairs):
    d={}
    for k,v in pairs:
        if k in d: raise ValueError('duplicate_json_key')
        d[k]=v
    return d

def no_nonfinite(value):
    raise ValueError('nonfinite_json_number')

def rpc(endpoint,method,params,opener=None):
    opener=opener or urllib.request.urlopen
    body=json.dumps({'jsonrpc':'2.0','id':RPC_ID,'method':method,'params':params},
                    separators=(',',':')).encode()
    req=urllib.request.Request(endpoint,data=body,headers={
        'Content-Type':'application/json',
        'User-Agent':'CryptoAI-Lab-Phase195G-DATA-ONLY/1'})
    try:
        with opener(req,timeout=12) as f: raw=f.read(MAX_BYTES+1)
    except urllib.error.HTTPError as exc:
        return {'status':'HTTP_ERROR','http_code':int(exc.code)}
    except (urllib.error.URLError,TimeoutError,OSError) as exc:
        return {'status':'NETWORK_ERROR','error_class':type(exc).__name__}
    if len(raw)>MAX_BYTES: return {'status':'BOUNDED_RESPONSE_TOO_LARGE'}
    try:
        data=json.loads(raw,object_pairs_hook=no_duplicates,parse_constant=no_nonfinite)
    except (ValueError,UnicodeDecodeError):
        return {'status':'INVALID_JSON'}
    if not isinstance(data,dict) or data.get('jsonrpc')!='2.0' or type(data.get('id')) is not int or data['id']!=RPC_ID:
        return {'status':'INVALID_RPC_ENVELOPE'}
    if 'error' in data:
        error=data['error']
        code=error.get('code') if isinstance(error,dict) else None
        return {'status':'RPC_ERROR','rpc_code':code if type(code) is int else None}
    if 'result' not in data: return {'status':'MISSING_RESULT'}
    return {'status':'HTTP_200_RPC_RESULT','result':data['result']}

def qty(v):
    if not isinstance(v,str) or re.fullmatch(r'0x(?:0|[1-9a-f][0-9a-f]*)',v) is None:
        raise ValueError('noncanonical_quantity')
    return int(v,16)

def summarize(method,response):
    out={k:v for k,v in response.items() if k!='result'}
    if response['status']!='HTTP_200_RPC_RESULT': return out
    val=response['result']
    if method=='eth_chainId':
        out['status']='CHAIN_ID_ONE' if val=='0x1' else 'WRONG_OR_INVALID_CHAIN'
    elif method=='eth_getBlockByNumber':
        if not isinstance(val,dict):
            out['status']='MISSING_BLOCK'
        else:
            try:
                height=qty(val['number'])
                timestamp=qty(val['timestamp'])
                out['block_number']=height
                if height==HEIGHT:
                    out['train_timestamp']=TRAIN_START<=timestamp<TRAIN_END
                    if not out['train_timestamp']: out['status']='OUT_OF_TRAIN_HEADER'
                if not isinstance(val.get('hash'),str) or len(val['hash'])!=66:
                    out['status']='INVALID_BLOCK_HASH_FORMAT'
            except (ValueError,KeyError,TypeError):
                out['status']='INVALID_BLOCK_METADATA'
    elif method in ('eth_getLogs','eth_getBlockReceipts'):
        if isinstance(val,list):
            out['unverified_row_count']=len(val)
        else:
            out['status']='INVALID_LIST_TYPE'
    return out

def audit_operator(label,endpoint,call=rpc):
    stages={'chain_id':summarize('eth_chainId',call(endpoint,'eth_chainId',[]))}
    if stages['chain_id']['status']!='CHAIN_ID_ONE':
        return {'operator_label':label,'stages':stages,'skipped':'wrong_or_unavailable_chain'}
    tasks=[
      ('finalized_header','eth_getBlockByNumber',['finalized',False]),
      ('fixed_train_header','eth_getBlockByNumber',[hex(HEIGHT),False]),
      ('fixed_train_mint_logs','eth_getLogs',[{'address':USDC,'topics':[TOPICS['mint']],
          'fromBlock':hex(HEIGHT),'toBlock':hex(HEIGHT)}]),
      ('fixed_train_burn_logs','eth_getLogs',[{'address':USDC,'topics':[TOPICS['burn']],
          'fromBlock':hex(HEIGHT),'toBlock':hex(HEIGHT)}]),
      ('fixed_train_receipts','eth_getBlockReceipts',[hex(HEIGHT)])]
    for stage,method,params in tasks:
        stages[stage]=summarize(method,call(endpoint,method,params))
    return {'operator_label':label,'stages':stages}

def main():
    result={'phase':'195-G','scope':'FIXED_TRAIN_TRANSPORT_DIAGNOSTIC',
      'height':HEIGHT,'operators':[audit_operator(name,url) for name,url in ENDPOINTS.items()],
      'decision':'HOLD_DATA_ONLY_NOT_A_COVERAGE_GATE','economic_trials':0,
      'holdout_accessed':False,'independent_consensus_proven':False,
      'provider_independence_proven':False,'receipts_root_proven':False,
      'historical_latency_proven':False,'train_coverage_proven':False,
      'promotion_authorized':False}
    print(json.dumps(result,sort_keys=True,separators=(',',':')))

if __name__=='__main__': main()
