"""Phase195-M synthetic beacon parity and negative controls."""
import pathlib,sys,copy
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"tools"))
from v99_phase195m_beacon_core import compare,GENESIS,slot_from_timestamp
slot=7000000
ts=GENESIS+12*slot
block={"timestamp":hex(ts),"hash":"0x"+"11"*32,"receiptsRoot":"0x"+"22"*32}
beacon={"finalized":True,"execution_optimistic":False,"data":{"message":{"slot":str(slot),
 "body":{"execution_payload":{"block_number":"17000000","timestamp":str(ts),
 "block_hash":block["hash"],"receipts_root":block["receiptsRoot"]}}}}}
assert compare(block,beacon)["slot"]==slot
def reject(mut,reason):
 x=copy.deepcopy(beacon);mut(x)
 try:compare(block,x)
 except ValueError as e:assert str(e)==reason,(e,reason)
 else:raise AssertionError("accepted:"+reason)
reject(lambda x:x["data"]["message"]["body"]["execution_payload"].update(block_hash="0x"+"33"*32),"execution_hash_mismatch")
reject(lambda x:x["data"]["message"]["body"]["execution_payload"].update(receipts_root="0x"+"33"*32),"execution_receipts_root_mismatch")
reject(lambda x:x.update(finalized=False),"beacon_not_reported_finalized")
reject(lambda x:x["data"]["message"].update(slot=str(slot+1)),"slot_mismatch")
print({"phase":"195-M","synthetic_controls":5,"economic_trials":0,"status":"PASS"})
