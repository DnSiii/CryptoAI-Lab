"""Phase195-L independent pre-Shanghai execution header reconstruction."""
import rlp
from eth_utils import keccak
from v99_phase195l_core import qty,raw
H=17000000
T0,T1=1638316800,1705536000
def verify_header(x):
 if qty(x["number"])!=H or not T0<=qty(x["timestamp"])<T1:raise ValueError("train_firewall")
 if any(x.get(k) is not None for k in ("withdrawalsRoot","blobGasUsed","excessBlobGas","parentBeaconBlockRoot")):
  raise ValueError("unexpected_fork_field")
 if qty(x["difficulty"])!=0 or raw(x["nonce"],8)!=bytes(8):raise ValueError("post_merge_invariant")
 if raw(x["sha3Uncles"],32)!=keccak(rlp.encode([])):raise ValueError("uncles_invariant")
 if qty(x["gasUsed"])>qty(x["gasLimit"]):raise ValueError("gas_limit_invariant")
 fields=[raw(x[k],n) for k,n in (("parentHash",32),("sha3Uncles",32),("miner",20),
   ("stateRoot",32),("transactionsRoot",32),("receiptsRoot",32),("logsBloom",256))]
 fields += [qty(x[k]) for k in ("difficulty","number","gasLimit","gasUsed","timestamp")]
 fields += [raw(x["extraData"]),raw(x["mixHash"],32),raw(x["nonce"],8),qty(x["baseFeePerGas"])]
 if keccak(rlp.encode(fields))!=raw(x["hash"],32):raise ValueError("header_hash_mismatch")
 return True
