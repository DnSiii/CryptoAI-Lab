#!/usr/bin/env python3
"""Phase180 deterministic Bitcoin mainnet header DATA gate. No alpha/PnL logic.

Input must include enough pre-roll to verify every retarget boundary encountered in
TRAIN.  Rows at/after the holdout firewall are forbidden.  Header timestamps are
consensus fields, not wall-clock availability; downstream features still require t-1.
"""
from __future__ import annotations
import argparse, csv, hashlib, json
from datetime import datetime, timezone
from pathlib import Path

FIREWALL = datetime(2024,1,18,tzinfo=timezone.utc).timestamp()
REQ = ("height","hash","previousblockhash","time","bits")
POW_LIMIT = 0x00000000FFFF0000000000000000000000000000000000000000000000000000
TARGET_TIMESPAN = 14*24*60*60

def sha256(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20), b""): h.update(b)
    return h.hexdigest()

def mtp(prev_times):
    x=sorted(prev_times[-11:]); return x[len(x)//2]

def bits_to_target(bits: str) -> int:
    n=int(bits,16); exp=n>>24; mant=n & 0x007fffff
    if n & 0x00800000 or mant==0: raise ValueError(f"invalid compact target:{bits}")
    return mant << (8*(exp-3)) if exp>=3 else mant >> (8*(3-exp))

def target_to_bits(target: int) -> str:
    raw=target.to_bytes((target.bit_length()+7)//8 or 1,"big")
    if raw[0]&0x80: raw=b"\x00"+raw
    exp=len(raw); mant=int.from_bytes(raw[:3].ljust(3,b"\x00"),"big")
    return f"{(exp<<24)|mant:08x}"

def expected_retarget(prev_bits: str, first_time: int, last_time: int) -> str:
    span=max(TARGET_TIMESPAN//4,min(last_time-first_time,TARGET_TIMESPAN*4))
    target=min(bits_to_target(prev_bits)*span//TARGET_TIMESPAN,POW_LIMIT)
    return target_to_bits(target)

def audit(path: Path):
    rows=list(csv.DictReader(path.open(newline="",encoding="utf-8")))
    if not rows: raise ValueError("empty input")
    missing=[c for c in REQ if c not in rows[0]]
    if missing: raise ValueError(f"missing columns: {missing}")
    parsed=[]
    for r in rows:
        parsed.append({**r,"height":int(r["height"]),"time":int(r["time"]),"bits":r["bits"].lower()})
    parsed.sort(key=lambda r:r["height"])
    failures=[]; pathologies={"nonpositive_delta":0,"gap_gt_2x":0,"gap_gt_3x":0,"gap_gt_6x":0,"gap_gt_12x":0,"retarget_boundaries":0}
    seen_h={}; seen_pair=set(); times=[]; by_height={}
    for i,r in enumerate(parsed):
        h=r["height"]; pair=(h,r["hash"])
        if h in seen_h and seen_h[h]!=r["hash"]: failures.append(f"conflicting_height:{h}")
        if pair in seen_pair: failures.append(f"duplicate:{h}:{r['hash']}")
        seen_h[h]=r["hash"]; seen_pair.add(pair)
        try:
            target=bits_to_target(r["bits"])
            if target>POW_LIMIT: failures.append(f"target_above_pow_limit:{h}")
            if len(r["hash"])!=64 or any(c not in "0123456789abcdefABCDEF" for c in r["hash"]): failures.append(f"invalid_hash_encoding:{h}")
            elif int(r["hash"],16)>target: failures.append(f"pow_invalid:{h}")
        except ValueError:
            failures.append(f"invalid_bits:{h}:{r['bits']}")
        if r["time"] >= FIREWALL: failures.append(f"firewall:{h}")
        if i:
            p=parsed[i-1]
            if h != p["height"]+1: failures.append(f"height_gap:{p['height']}->{h}")
            if r["previousblockhash"] != p["hash"]: failures.append(f"parent_mismatch:{h}")
            d=r["time"]-p["time"]
            if d<=0: pathologies["nonpositive_delta"]+=1
            for k in (2,3,6,12):
                if d>k*600: pathologies[f"gap_gt_{k}x"]+=1
            if h%2016==0:
                pathologies["retarget_boundaries"]+=1
                first=by_height.get(h-2016)
                if first is None: failures.append(f"retarget_missing_preroll:{h}")
                else:
                    try:
                        expected=expected_retarget(p["bits"],first["time"],p["time"])
                        if r["bits"]!=expected: failures.append(f"retarget_mismatch:{h}:{r['bits']}!={expected}")
                    except ValueError: failures.append(f"retarget_invalid_parent_bits:{h}")
            elif r["bits"] != p["bits"]: failures.append(f"bits_change_off_boundary:{h}")
        if len(times)>=11 and r["time"] <= mtp(times): failures.append(f"mtp_violation:{h}")
        times.append(r["time"]); by_height[h]=r
    out={"status":"PASS" if not failures else "FAIL","source_sha256":sha256(path),"rows":len(parsed),"first_height":parsed[0]["height"],"last_height":parsed[-1]["height"],"failures":failures,"pathologies":pathologies,"firewall_utc":"2024-01-18T00:00:00Z","consensus_scope":"bitcoin-mainnet"}
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("csv",type=Path); ap.add_argument("--out",type=Path)
    a=ap.parse_args(); out=audit(a.csv); s=json.dumps(out,sort_keys=True,indent=2)+"\n"
    if a.out: a.out.write_text(s,encoding="utf-8")
    print(s,end=""); raise SystemExit(0 if out["status"]=="PASS" else 2)
if __name__=="__main__": main()
