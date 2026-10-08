"""Fixed Era Bellatrix parity; DATA_ONLY, no consensus proof."""
import hashlib,json,snappy
from v99_phase195p_era_range import run as archive,range_read
from v99_phase195q_bellatrix import parse
def run():
 out={"phase":"195-Q","economic_trials":0,"holdout_accessed":False,
      "promotion_authorized":False,"independent_consensus_anchor":False}
 try:
  p=archive();out["archive_status"]=p["decision"]
  if p["decision"]!="PROVISIONAL_ERA_RECORD_AVAILABLE_UNANCHORED":
   out["decision"]="HOLD_ARCHIVE";return out
  pos=p["absolute_offset"];n=p["record_bytes"]
  data=range_read(pos+8,pos+7+n)
  if hashlib.sha256(data).hexdigest()!=p["record_sha256"]:
   raise ValueError("archive_record_changed")
  ssz=snappy.StreamDecompressor().decompress(data)
  if not 1076<=len(ssz)<=2000000:raise ValueError("ssz_size")
  out.update(parse(ssz))
  out["decision"]="PROVISIONAL_ERA_PAYLOAD_MATCH_UNANCHORED"
 except Exception as exc:
  reason=str(exc) if isinstance(exc,ValueError) else type(exc).__name__
  out["reason"]=reason[:90]
  out["decision"]=("SAFETY_HALT_ERA_MISMATCH" if reason in
   ("slot_mismatch","height_mismatch","timestamp_mismatch","hash_mismatch","root_mismatch")
   else "HOLD_ERA_SSZ")
 return out
if __name__=="__main__":print(json.dumps(run(),sort_keys=True))
