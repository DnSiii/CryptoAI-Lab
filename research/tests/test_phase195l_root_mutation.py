"""Phase195-L 102-receipt trie reconstruction and mutation controls."""
import pathlib,sys,rlp
from trie import HexaryTrie
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"tools"))
from v99_phase195l_root import reconstruct
block={"hash":"0x"+"11"*32,"transactions":[],
       "logsBloom":"0x"+bytes(256).hex(),"gasUsed":hex(102*21000)}
recs=[];t=HexaryTrie(db={})
for i in range(102):
 tx="0x"+i.to_bytes(32,"big").hex()
 block["transactions"].append(tx)
 gas=(i+1)*21000
 recs.append({"transactionIndex":hex(i),"transactionHash":tx,
  "blockHash":block["hash"],"blockNumber":hex(17000000),
  "cumulativeGasUsed":hex(gas),"status":"0x1","type":"0x2",
  "logsBloom":block["logsBloom"],"logs":[]})
 t[rlp.encode(i)]=b"\x02"+rlp.encode([1,gas,bytes(256),[]])
block["receiptsRoot"]="0x"+t.root_hash.hex()
assert reconstruct(block,recs)["receipt_count"]==102
recs[7]["status"]="0x0"
try:reconstruct(block,recs)
except ValueError as e:assert str(e)=="receipts_root_mismatch"
else:raise AssertionError("mutation_accepted")
print({"phase":"195-L","synthetic_root_replay":"PASS",
       "root_mutation_rejected":True,"economic_trials":0})
