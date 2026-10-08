"""Phase195-L canonical receipt payload and log checks."""
import rlp
from v99_phase195l_core import qty,raw,bloom
from v99_phase195l_header import H
def encode_one(block,tx,i,rec,next_log,previous_gas):
 if not isinstance(rec,dict):raise ValueError("null_receipt")
 if (qty(rec["transactionIndex"])!=i or raw(rec["transactionHash"],32)!=raw(tx,32)
  or raw(rec["blockHash"],32)!=raw(block["hash"],32) or qty(rec["blockNumber"])!=H):
  raise ValueError("receipt_identity")
 gas=qty(rec["cumulativeGasUsed"])
 if gas<previous_gas:raise ValueError("gas_regression")
 kind=qty(rec.get("type","0x0"));status=qty(rec["status"])
 if kind not in (0,1,2) or status not in (0,1):raise ValueError("fork_type_or_status")
 logs=rec["logs"]
 if not isinstance(logs,list):raise ValueError("invalid_logs")
 canon=[]
 for log in logs:
  if (qty(log["logIndex"])!=next_log or qty(log["transactionIndex"])!=i
   or qty(log["blockNumber"])!=H or raw(log["blockHash"],32)!=raw(block["hash"],32)
   or raw(log["transactionHash"],32)!=raw(tx,32) or log.get("removed") is not False):
   raise ValueError("log_identity")
  topics=log["topics"]
  if not isinstance(topics,list) or len(topics)>4:raise ValueError("invalid_topics")
  canon.append([raw(log["address"],20),[raw(t,32) for t in topics],raw(log["data"])])
  next_log+=1
 rb=bloom(logs)
 if rb!=raw(rec["logsBloom"],256):raise ValueError("receipt_bloom_mismatch")
 payload=rlp.encode([status,gas,rb,canon])
 return (bytes([kind])+payload if kind else payload),gas,next_log,rb
