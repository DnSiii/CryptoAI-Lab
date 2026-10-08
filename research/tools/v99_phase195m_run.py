#!/usr/bin/env python3
"""Phase195-M fixed TRAIN beacon payload parity. DATA_ONLY."""
import json,urllib.request,urllib.error
from v99_phase195l_rpc import rpc
from v99_phase195l_header import verify_header,H
from v99_phase195m_beacon_core import compare,slot_from_timestamp
def run():
 out={"phase":"195-M","economic_trials":0,"holdout_accessed":False,
      "promotion_authorized":False,"independent_consensus_anchor":False}
 try:
  block=rpc("https://eth.drpc.org","eth_getBlockByNumber",[hex(H),False])
  verify_header(block)
  if block["hash"].lower()!="0x96cfa0fb5e50b0a3f6cc76f3299cfbf48f17e8b41798d1394474e67ec8a97e9f":
   raise ValueError("fixed_hash_changed")
  if block["receiptsRoot"].lower()!="0xdafc7e17d609503a08b1406eb69c714cb3e7ba51e84580977c449999068ae513":
   raise ValueError("fixed_root_changed")
  slot=slot_from_timestamp(int(block["timestamp"],16))
  url="https://ethereum-beacon-api.publicnode.com/eth/v2/beacon/blocks/"+str(slot)
  req=urllib.request.Request(url,headers={"Accept":"application/json"})
  with urllib.request.urlopen(req,timeout=40) as f:beacon=json.load(f)
  out.update(compare(block,beacon))
  out["decision"]="PROVISIONAL_BEACON_PAYLOAD_PARITY_UNANCHORED"
 except Exception as e:
  out["decision"]="HOLD_BEACON_TRANSPORT_OR_MISMATCH"
  out["reason"]="http_"+str(e.code) if isinstance(e,urllib.error.HTTPError) else str(e)[:100]
 return out
if __name__=="__main__":print(json.dumps(run(),sort_keys=True))
