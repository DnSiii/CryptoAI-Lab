"""Phase195-R archive transaction trie parity. DATA_ONLY."""
import hashlib,json,snappy
from v99_phase195p_era_range import run as archive,range_read
from v99_phase195l_rpc import rpc
from v99_phase195l_header import H,verify_header
from v99_phase195r_transaction_trie import transactions
def run():
 out={"phase":"195-R","economic_trials":0,"holdout_accessed":False,
      "promotion_authorized":False,"independent_consensus_anchor":False}
 try:
  p=archive()
  if p["decision"]!="PROVISIONAL_ERA_RECORD_AVAILABLE_UNANCHORED":
   out["decision"]="HOLD_ARCHIVE";return out
  pos=p["absolute_offset"];n=p["record_bytes"]
  data=range_read(pos+8,pos+7+n)
  if hashlib.sha256(data).hexdigest()!=p["record_sha256"]:
   raise ValueError("record_changed")
  ssz=snappy.StreamDecompressor().decompress(data)
  info=transactions(ssz)
  block=rpc("https://eth.drpc.org","eth_getBlockByNumber",[hex(H),False])
  verify_header(block)
  if info["computed_transactions_root"]!=block["transactionsRoot"].lower():
   raise ValueError("transactions_root_mismatch")
  if info["transaction_hashes"]!=[x.lower() for x in block["transactions"]]:
   raise ValueError("transaction_hashes_mismatch")
  info.pop("transaction_hashes")
  out.update(info)
  out["decision"]="PROVISIONAL_ERA_TX_TRIE_MATCH_UNANCHORED"
 except Exception as e:
  out["reason"]=str(e)[:80] if isinstance(e,ValueError) else type(e).__name__
  out["decision"]="HOLD_OR_MISMATCH"
 return out
if __name__=="__main__":print(json.dumps(run(),sort_keys=True))
