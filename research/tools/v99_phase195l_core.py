"""Phase195-L Ethereum library primitives, DATA_ONLY."""
import re,rlp
from eth_utils import keccak
from trie import HexaryTrie
def qty(x):
 if not isinstance(x,str) or re.fullmatch(r"0x(?:0|[1-9a-f][0-9a-f]*)",x) is None:raise ValueError("noncanonical_quantity")
 return int(x,16)
def raw(x,n=None):
 if not isinstance(x,str) or re.fullmatch(r"0x(?:[0-9a-fA-F]{2})*",x) is None:raise ValueError("noncanonical_hex")
 v=bytes.fromhex(x[2:])
 if n is not None and len(v)!=n:raise ValueError("invalid_hex_width")
 return v
def bloom(logs):
 bits=0
 for log in logs:
  for item in [raw(log["address"],20)]+[raw(t,32) for t in log["topics"]]:
   h=keccak(item)
   for i in (0,2,4):bits|=1<<(int.from_bytes(h[i:i+2],"big")&2047)
 return bits.to_bytes(256,"big")
def oracle():
 assert keccak(b"").hex()=="c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
 assert keccak(b"abc").hex()=="4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45"
 assert HexaryTrie(db={}).root_hash.hex()=="56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"
 t=HexaryTrie(db={});t[rlp.encode(0)]=rlp.encode([1,21000,bytes(256),[]]);old=t.root_hash
 t[rlp.encode(0)]=rlp.encode([0,21000,bytes(256),[]])
 assert old!=t.root_hash
 return "PASS_INDEPENDENT_LIBRARY_VECTORS"
