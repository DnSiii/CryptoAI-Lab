"""Phase195-R: Bellatrix SSZ transaction-list canonicality and MPT."""
import hashlib,struct,rlp
from eth_utils import keccak
from trie import HexaryTrie
from v99_phase195q_bellatrix import parse,read32

EXPECTED_COUNT=102
def transactions(ssz):
 parse(ssz)
 body=ssz[100+84:]
 payload=body[read32(body,380):]
 start=read32(payload,504)
 buf=payload[start:]
 if len(buf)<4:raise ValueError("missing_transactions")
 first=read32(buf,0)
 if first%4 or first<4 or first>len(buf):
  raise ValueError("transaction_list_offset")
 count=first//4
 if count!=EXPECTED_COUNT:raise ValueError("transaction_count_mismatch")
 offsets=[read32(buf,4*i) for i in range(count)]
 if offsets[0]!=first or offsets!=sorted(offsets) or offsets[-1]>=len(buf):
  raise ValueError("transaction_list_offsets")
 ends=offsets[1:]+[len(buf)]
 txs=[buf[a:b] for a,b in zip(offsets,ends)]
 if any(not 1<=len(tx)<=131072 for tx in txs):
  raise ValueError("transaction_size")
 hashes=[keccak(tx) for tx in txs]
 if len(set(hashes))!=count:raise ValueError("duplicate_transactions")
 trie=HexaryTrie(db={})
 for i,tx in enumerate(txs):trie[rlp.encode(i)]=tx
 return {"transaction_count":count,"computed_transactions_root":"0x"+trie.root_hash.hex(),
         "first_tx_hash":"0x"+hashes[0].hex(),"last_tx_hash":"0x"+hashes[-1].hex(),
         "transaction_bytes_sha256":hashlib.sha256(b"".join(txs)).hexdigest(),
         "transaction_hashes":["0x"+h.hex() for h in hashes]}
