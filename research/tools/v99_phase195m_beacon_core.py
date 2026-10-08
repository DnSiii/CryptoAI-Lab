"""Phase195-M beacon execution-payload parity, unanchored DATA_ONLY."""
GENESIS=1606824023
H=17000000
def slot_from_timestamp(timestamp):
 if not isinstance(timestamp,int) or timestamp<GENESIS or (timestamp-GENESIS)%12:
  raise ValueError("noncanonical_beacon_timestamp")
 return (timestamp-GENESIS)//12
def compare(block,beacon):
 ts=int(block["timestamp"],16)
 slot=slot_from_timestamp(ts)
 if beacon.get("execution_optimistic") is not False:
  raise ValueError("beacon_execution_optimistic")
 if beacon.get("finalized") is not True:
  raise ValueError("beacon_not_reported_finalized")
 msg=beacon["data"]["message"]
 if int(msg["slot"])!=slot:raise ValueError("slot_mismatch")
 payload=msg["body"]["execution_payload"]
 if int(payload["block_number"])!=H:raise ValueError("execution_height_mismatch")
 if int(payload["timestamp"])!=ts:raise ValueError("execution_timestamp_mismatch")
 if payload["block_hash"].lower()!=block["hash"].lower():raise ValueError("execution_hash_mismatch")
 if payload["receipts_root"].lower()!=block["receiptsRoot"].lower():
  raise ValueError("execution_receipts_root_mismatch")
 return {"slot":slot,"beacon_payload_block_hash":payload["block_hash"].lower(),
         "beacon_payload_receipts_root":payload["receipts_root"].lower(),
         "beacon_reported_finalized":True,"independent_consensus_anchor":False}
