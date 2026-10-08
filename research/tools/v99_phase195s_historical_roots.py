"""Phase195-S: pre-Capella historical_roots Merkle proof. DATA_ONLY.
A path match does NOT authenticate the supplied BeaconState checkpoint or
prove the supplied BeaconBlock root was computed from archive SSZ.
"""
import hashlib,json,re
SLOT=6173989
CAPELLA_SLOT=194048*32
DENEB_SLOT=269568*32
HIST_INDEX=SLOT//8192
SLOT_INDEX=SLOT%8192
HIST_LENGTH=CAPELLA_SLOT//8192
HEX=re.compile(r"0x[0-9a-f]{64}\Z")
def h32(x,name):
 if not isinstance(x,str) or not HEX.fullmatch(x):raise ValueError("invalid_"+name)
 return bytes.fromhex(x[2:])
def pair(a,b):
 if len(a)!=32 or len(b)!=32:raise ValueError("non32_node")
 return hashlib.sha256(a+b).digest()
def branch(leaf,siblings,index,depth,name):
 if not isinstance(siblings,list) or len(siblings)!=depth:raise ValueError("invalid_"+name+"_branch_length")
 if type(index)!=int or not 0<=index<2**depth:raise ValueError("invalid_"+name+"_index")
 node=leaf
 for level,s in enumerate(siblings):
  other=h32(s,name+"_sibling")
  node=pair(other,node) if (index>>level)&1 else pair(node,other)
 return node
def verify(proof):
 if not isinstance(proof,dict):raise ValueError("invalid_proof")
 required={"slot","fork","checkpoint_slot","beacon_block_root","block_roots_branch","state_roots_root","historical_roots_branch","historical_roots_length","beacon_state_branch","beacon_state_root"}
 if set(proof)!=required:raise ValueError("unexpected_proof_schema")
 if type(proof["slot"])!=int or proof["slot"]!=SLOT:raise ValueError("fixed_slot_mismatch")
 if proof["fork"]!="capella":raise ValueError("unsupported_checkpoint_fork")
 if type(proof["checkpoint_slot"])!=int or not CAPELLA_SLOT<=proof["checkpoint_slot"]<DENEB_SLOT:raise ValueError("checkpoint_slot_outside_capella")
 if type(proof["historical_roots_length"])!=int or proof["historical_roots_length"]!=HIST_LENGTH:raise ValueError("frozen_historical_roots_length_mismatch")
 block=branch(h32(proof["beacon_block_root"],"beacon_block_root"),proof["block_roots_branch"],SLOT_INDEX,13,"block_roots")
 batch=pair(block,h32(proof["state_roots_root"],"state_roots_root"))
 vector=branch(batch,proof["historical_roots_branch"],HIST_INDEX,24,"historical_roots")
 lst=pair(vector,HIST_LENGTH.to_bytes(32,"little"))
 state=branch(lst,proof["beacon_state_branch"],7,5,"beacon_state")
 if state!=h32(proof["beacon_state_root"],"beacon_state_root"):raise ValueError("state_root_merkle_mismatch")
 return {"phase":"195-S","decision":"PROVISIONAL_MERKLE_PATH_MATCH_UNANCHORED","scope":"DATA_ONLY","slot":SLOT,"historical_index":HIST_INDEX,"slot_index":SLOT_INDEX,"historical_accumulator":"historical_roots","checkpoint_fork":"capella","computed_beacon_state_root":"0x"+state.hex(),"beacon_block_ssz_root_independently_computed":False,"trusted_finality_checkpoint_verified":False,"authenticated_consensus_ancestry":False,"economic_trials":0,"holdout_accessed":False,"promotion_authorized":False}
def no_duplicates(pairs):
 obj={}
 for k,v in pairs:
  if k in obj:raise ValueError("duplicate_json_key")
  obj[k]=v
 return obj
def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument("--proof");a=p.parse_args()
 result={"phase":"195-S","decision":"HOLD_NO_AUTHENTICATED_PROOF_INPUT","scope":"DATA_ONLY","economic_trials":0,"holdout_accessed":False,"promotion_authorized":False,"authenticated_consensus_ancestry":False}
 if a.proof:
  try:
   with open(a.proof,encoding="utf-8") as f:proof=json.load(f,object_pairs_hook=no_duplicates)
   result=verify(proof)
  except (ValueError,TypeError,OSError) as e:
   result.update(decision="HOLD_INVALID_PROOF",reason=str(e)[:100])
 print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
