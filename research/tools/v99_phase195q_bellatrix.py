"""Fixed TRAIN Bellatrix SSZ payload parser; no consensus proof."""
import hashlib
import struct
from v99_phase195n_run import EXPECTED_HASH, EXPECTED_ROOT
SLOT=6173989
HEIGHT=17000000
TIMESTAMP=1606824023+12*SLOT
def read32(b,i):return struct.unpack_from("<I",b,i)[0]
def read64(b,i):return struct.unpack_from("<Q",b,i)[0]
def parse(ssz):
 if not 144896<=SLOT//32<194048:raise ValueError("wrong_fork")
 if len(ssz)<1076:raise ValueError("short_ssz")
 if read32(ssz,0)!=100:raise ValueError("signed_offset")
 msg=ssz[100:]
 if read64(msg,0)!=SLOT:raise ValueError("slot_mismatch")
 if read32(msg,80)!=84:raise ValueError("body_offset")
 body=msg[84:]
 offsets=[read32(body,i) for i in (200,204,208,212,216,380)]
 if offsets!=sorted(offsets) or offsets[0]<384 or offsets[-1]>=len(body):
  raise ValueError("body_offsets")
 payload=body[offsets[-1]:]
 if len(payload)<508:raise ValueError("short_payload")
 extra,txs=read32(payload,436),read32(payload,504)
 if not 508<=extra<=txs<=len(payload) or txs-extra>32:
  raise ValueError("payload_offsets")
 height=read64(payload,404);timestamp=read64(payload,428)
 h="0x"+payload[472:504].hex();root="0x"+payload[84:116].hex()
 if height!=HEIGHT:raise ValueError("height_mismatch")
 if timestamp!=TIMESTAMP:raise ValueError("timestamp_mismatch")
 if h!=EXPECTED_HASH:raise ValueError("hash_mismatch")
 if root!=EXPECTED_ROOT:raise ValueError("root_mismatch")
 return {"fork":"bellatrix","slot":SLOT,"height":height,"timestamp":timestamp,
  "block_hash":h,"receipts_root":root,"ssz_bytes":len(ssz),
  "ssz_sha256":hashlib.sha256(ssz).hexdigest()}
