"""Phase195-L ordered MPT root, using independent trie package."""
import rlp
from trie import HexaryTrie
from v99_phase195l_core import qty,raw
from v99_phase195l_receipt import encode_one
def reconstruct(block,receipts):
 txs=block["transactions"]
 if not isinstance(txs,list) or len(txs)!=102 or len(set(t.lower() for t in txs))!=102:
  raise ValueError("fixed_tx_cardinality")
 for tx in txs:raw(tx,32)
 if not isinstance(receipts,list) or len(receipts)!=102:raise ValueError("missing_receipts")
 trie=HexaryTrie(db={});gas=0;log_index=0;combined=0
 for i,(tx,rec) in enumerate(zip(txs,receipts)):
  payload,gas,log_index,bb=encode_one(block,tx,i,rec,log_index,gas)
  combined |= int.from_bytes(bb,"big")
  trie[rlp.encode(i)]=payload
 if gas!=qty(block["gasUsed"]):raise ValueError("block_gas_mismatch")
 if combined.to_bytes(256,"big")!=raw(block["logsBloom"],256):
  raise ValueError("block_bloom_mismatch")
 if trie.root_hash!=raw(block["receiptsRoot"],32):
  raise ValueError("receipts_root_mismatch")
 return {"receipt_count":len(receipts),"all_log_count":log_index,
         "computed_root":"0x"+trie.root_hash.hex()}
