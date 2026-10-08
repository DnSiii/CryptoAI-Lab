"""Synthetic Phase195-S adversarial Merkle controls; no live trusted root."""
import copy,hashlib,importlib.util
from pathlib import Path
sp=importlib.util.spec_from_file_location("s",Path(__file__).resolve().parents[1]/"tools"/"v99_phase195s_historical_roots.py")
s=importlib.util.module_from_spec(sp);sp.loader.exec_module(s)
def h(x):return "0x"+hashlib.sha256(x.encode()).hexdigest()
def fixture():
 p={"slot":s.SLOT,"fork":"capella","checkpoint_slot":s.CAPELLA_SLOT,"beacon_block_root":h("block"),"block_roots_branch":[h("b"+str(i)) for i in range(13)],"state_roots_root":h("state"),"historical_roots_branch":[h("h"+str(i)) for i in range(24)],"historical_roots_length":s.HIST_LENGTH,"beacon_state_branch":[h("s"+str(i)) for i in range(5)]}
 b=s.branch(s.h32(p["beacon_block_root"],"b"),p["block_roots_branch"],s.SLOT_INDEX,13,"b")
 batch=s.pair(b,s.h32(p["state_roots_root"],"s"))
 v=s.branch(batch,p["historical_roots_branch"],s.HIST_INDEX,24,"h")
 root=s.branch(s.pair(v,s.HIST_LENGTH.to_bytes(32,"little")),p["beacon_state_branch"],7,5,"state")
 p["beacon_state_root"]="0x"+root.hex();return p
def reject(p,reason):
 try:s.verify(p)
 except ValueError as e:assert reason in str(e),(reason,str(e))
 else:raise AssertionError("unsafe_acceptance")
def main():
 p=fixture();r=s.verify(p);assert r["decision"].endswith("UNANCHORED") and not r["promotion_authorized"]
 assert (s.HIST_INDEX,s.SLOT_INDEX,s.HIST_LENGTH)==(753,5413,758)
 n=2
 for field,value,reason in [("slot",s.SLOT+1,"fixed_slot"),("slot",True,"fixed_slot"),("fork","deneb","unsupported"),("checkpoint_slot",s.CAPELLA_SLOT-1,"checkpoint_slot"),("checkpoint_slot",s.DENEB_SLOT,"checkpoint_slot"),("historical_roots_length",757,"frozen_historical"),("historical_roots_length",True,"frozen_historical"),("beacon_block_root",h("wrong"),"state_root_merkle"),("state_roots_root",h("wrong"),"state_root_merkle"),("beacon_state_root",h("wrong"),"state_root_merkle"),("beacon_block_root","0X"+"0"*64,"invalid_beacon"),("beacon_block_root","0x"+"0"*63,"invalid_beacon")]:
  q=copy.deepcopy(p);q[field]=value;reject(q,reason);n+=1
 for field in ("block_roots_branch","historical_roots_branch","beacon_state_branch"):
  q=copy.deepcopy(p);q[field].pop();reject(q,"branch_length");n+=1
  q=copy.deepcopy(p);q[field][0]=h("corrupt");reject(q,"state_root_merkle");n+=1
 q=copy.deepcopy(p);q["unknown"]=1;reject(q,"unexpected_proof_schema");n+=1
 q=copy.deepcopy(p);q.pop("state_roots_root");reject(q,"unexpected_proof_schema");n+=1
 q=copy.deepcopy(p);q["historical_roots_branch"][0]="0x00";reject(q,"invalid_historical_roots_sibling");n+=1
 print("PASS Phase195-S",n,"synthetic controls; no authenticated anchor")
if __name__=="__main__":main()
