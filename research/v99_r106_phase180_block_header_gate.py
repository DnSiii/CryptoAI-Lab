#!/usr/bin/env python3
"""Phase180 deterministic Bitcoin header DATA gate. No alpha/PnL logic."""
from __future__ import annotations
import argparse, csv, hashlib, json
from datetime import datetime, timezone
from pathlib import Path

FIREWALL = datetime(2024,1,18,tzinfo=timezone.utc).timestamp()
REQ = ("height","hash","previousblockhash","time","bits")

def sha256(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20), b""): h.update(b)
    return h.hexdigest()

def mtp(prev_times):
    x=sorted(prev_times[-11:]); return x[len(x)//2]

def audit(path: Path):
    rows=list(csv.DictReader(path.open(newline="",encoding="utf-8")))
    if not rows: raise ValueError("empty input")
    missing=[c for c in REQ if c not in rows[0]]
    if missing: raise ValueError(f"missing columns: {missing}")
    parsed=[]
    for r in rows:
        parsed.append({**r,"height":int(r["height"]),"time":int(r["time"])})
    parsed.sort(key=lambda r:r["height"])
    failures=[]; pathologies={"nonpositive_delta":0,"gap_gt_2x":0,"gap_gt_3x":0,"gap_gt_6x":0,"gap_gt_12x":0,"retarget_boundaries":0}
    seen_h={}; seen_pair=set(); times=[]
    for i,r in enumerate(parsed):
        h=r["height"]; pair=(h,r["hash"])
        if h in seen_h and seen_h[h]!=r["hash"]: failures.append(f"conflicting_height:{h}")
        if pair in seen_pair: failures.append(f"duplicate:{h}:{r['hash']}")
        seen_h[h]=r["hash"]; seen_pair.add(pair)
        if r["time"] >= FIREWALL: failures.append(f"firewall:{h}")
        if i:
            p=parsed[i-1]
            if h != p["height"]+1: failures.append(f"height_gap:{p['height']}->{h}")
            if r["previousblockhash"] != p["hash"]: failures.append(f"parent_mismatch:{h}")
            d=r["time"]-p["time"]
            if d<=0: pathologies["nonpositive_delta"]+=1
            for k in (2,3,6,12):
                if d>k*600: pathologies[f"gap_gt_{k}x"]+=1
            if h%2016==0: pathologies["retarget_boundaries"]+=1
            elif r["bits"] != p["bits"]: failures.append(f"bits_change_off_boundary:{h}")
        if len(times)>=11 and r["time"] <= mtp(times): failures.append(f"mtp_violation:{h}")
        times.append(r["time"])
    out={"status":"PASS" if not failures else "FAIL","source_sha256":sha256(path),"rows":len(parsed),"first_height":parsed[0]["height"],"last_height":parsed[-1]["height"],"failures":failures,"pathologies":pathologies,"firewall_utc":"2024-01-18T00:00:00Z"}
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("csv",type=Path); ap.add_argument("--out",type=Path)
    a=ap.parse_args(); out=audit(a.csv); s=json.dumps(out,sort_keys=True,indent=2)+"\n"
    if a.out: a.out.write_text(s,encoding="utf-8")
    print(s,end=""); raise SystemExit(0 if out["status"]=="PASS" else 2)
if __name__=="__main__": main()
