#!/usr/bin/env python3
"""Phase195-L live independent library oracle. DATA_ONLY, fail closed."""
import json
from v99_phase195l_core import qty,oracle
from v99_phase195l_header import H,verify_header
from v99_phase195l_root import reconstruct
from v99_phase195l_rpc import rpc
ENDPOINTS={"drpc":"https://eth.drpc.org","publicnode":"https://ethereum-rpc.publicnode.com"}
def run(call=rpc):
 result={"phase":"195-L","height":H,"scope":"DATA_ONLY","economic_trials":0,
  "holdout_accessed":False,"promotion_authorized":False,
  "independent_consensus_anchor":False,"historical_latency_proven":False,
  "full_train_coverage_proven":False,"provider_independent_receipt_parity":False}
 try:
  result["oracle"]=oracle()
  headers={}
  for name,url in ENDPOINTS.items():
   if qty(call(url,"eth_chainId",[]))!=1:raise ValueError("wrong_chain:"+name)
   block=call(url,"eth_getBlockByNumber",[hex(H),False])
   if not isinstance(block,dict):raise ValueError("missing_header:"+name)
   verify_header(block);headers[name]=block
  for key in ("hash","number","timestamp","receiptsRoot","transactionsRoot","gasUsed","logsBloom"):
   if headers["drpc"][key]!=headers["publicnode"][key]:
    raise ValueError("cross_source_header_disagreement:"+key)
  result.update(reconstruct(headers["drpc"],
    call(ENDPOINTS["drpc"],"eth_getBlockReceipts",[hex(H)])))
  result["decision"]="PROVISIONAL_ROOT_MATCH_UNANCHORED"
 except Exception as exc:
  result["decision"]="HOLD_ROOT_OR_TRANSPORT"
  result["reason"]=str(exc)[:120] if isinstance(exc,ValueError) else type(exc).__name__
 return result
if __name__=="__main__":
 print(json.dumps(run(),sort_keys=True,separators=(",",":")))
