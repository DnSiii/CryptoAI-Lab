#!/usr/bin/env python3
"""V98 Phase275 Binance USD-M premiumIndexKlines DATA_ONLY acquisition."""
from __future__ import annotations
import argparse,csv,datetime as dt,hashlib,io,json,math,re,time,urllib.request,zipfile
from pathlib import Path

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
YEARS=(2023,2024,2025)
MONTHS=tuple((y,m) for y in YEARS for m in range(1,13))
INTERVAL="1h"
BASE="https://data.binance.vision/data/futures/um/monthly/premiumIndexKlines"
EXPECTED_PER_ASSET=26304
EXPECTED_TOTAL=105216
EXPECTED_ARCHIVES=144
CHECK_RE=re.compile(rb"([0-9a-fA-F]{64})[ \t]+\*?([^\s]+)[\r\n]*\Z")
UA="CryptoAI-Lab-V98-Phase275/1.0"

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def month_hours(year:int,month:int):
    start=dt.datetime(year,month,1,tzinfo=dt.timezone.utc)
    end=dt.datetime(year+1,1,1,tzinfo=dt.timezone.utc) if month==12 else dt.datetime(year,month+1,1,tzinfo=dt.timezone.utc)
    n=int((end-start).total_seconds()//3600)
    return [int((start+dt.timedelta(hours=i)).timestamp()*1000) for i in range(n)]

def urls(asset:str,year:int,month:int):
    name=f"{asset}-{INTERVAL}-{year}-{month:02d}.zip"
    url=f"{BASE}/{asset}/{INTERVAL}/{name}"
    return name,url,url+".CHECKSUM"

def download(url:str,cap:int,attempts:int=4):
    last=None
    for i in range(attempts):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":UA})
            with urllib.request.urlopen(req,timeout=60) as r:
                raw=r.read(cap+1)
            if not raw or len(raw)>cap:raise ValueError("empty/oversized response")
            return raw
        except Exception as e:
            last=e
            if i+1<attempts:time.sleep(min(2**i,4))
    raise last

def verify_fetch(root:Path,asset:str,year:int,month:int):
    name,url,curl=urls(asset,year,month)
    side=download(curl,4096)
    m=CHECK_RE.fullmatch(side)
    if not m or m.group(2)!=name.encode():
        raise ValueError(f"{name}: invalid checksum sidecar")
    raw=download(url,15_000_000)
    digest=sha(raw)
    if digest!=m.group(1).decode().lower():
        raise ValueError(f"{name}: sha256 mismatch")
    d=root/asset/INTERVAL
    d.mkdir(parents=True,exist_ok=True)
    (d/name).write_bytes(raw)
    (d/(name+".CHECKSUM")).write_bytes(side)
    return {"asset":asset,"year":year,"month":month,"name":name,"url":url,
            "archive_sha256":digest,"bytes":len(raw),"checksum_verified":True}

def parse_archive(path:Path,asset:str,year:int,month:int):
    expected_member=f"{asset}-{INTERVAL}-{year}-{month:02d}.csv"
    with zipfile.ZipFile(path) as zf:
        infos=zf.infolist()
        if len(infos)!=1 or infos[0].is_dir() or infos[0].filename!=expected_member:
            raise ValueError(f"{path.name}: unexpected ZIP member")
        raw=zf.read(infos[0])
    rows=list(csv.reader(io.StringIO(raw.decode("utf-8-sig"))))
    if not rows:raise ValueError(f"{path.name}: empty CSV")
    # Header is allowed; Binance historical files may be headerless or headed.
    try:int(rows[0][0]); data=rows
    except Exception:data=rows[1:]
    out=[]
    for row in data:
        if len(row)<5:raise ValueError(f"{path.name}: short row")
        try:
            ts=int(row[0]);vals=[float(row[i]) for i in range(1,5)]
        except Exception as e:raise ValueError(f"{path.name}: parse error") from e
        if not all(math.isfinite(v) for v in vals):
            raise ValueError(f"{path.name}: non-finite OHLC")
        o,h,l,c=vals
        if h<max(o,c)-1e-15 or l>min(o,c)+1e-15 or h<l:
            raise ValueError(f"{path.name}: OHLC geometry")
        out.append((ts,o,h,l,c))
    expected=month_hours(year,month)
    stamps=[r[0] for r in out]
    if stamps!=expected:
        missing=len(set(expected)-set(stamps));extra=len(set(stamps)-set(expected));dup=len(stamps)-len(set(stamps))
        raise ValueError(f"{path.name}: hourly grid mismatch rows={len(stamps)} expected={len(expected)} missing={missing} extra={extra} dup={dup}")
    return out,sha(raw)

def canonical_bytes(rows):
    s=io.StringIO(newline="")
    w=csv.writer(s,lineterminator="\n")
    w.writerow(["asset","open_time_ms","open","high","low","close"])
    for asset,ts,o,h,l,c in rows:
        w.writerow([asset,ts,format(o,".17g"),format(h,".17g"),format(l,".17g"),format(c,".17g")])
    return s.getvalue().encode()

def reconstruct(root:Path,ledger):
    rows=[];members={};counts={}
    for asset in ASSETS:
        n=0
        for year,month in MONTHS:
            name,_,_=urls(asset,year,month)
            parsed,member_sha=parse_archive(root/asset/INTERVAL/name,asset,year,month)
            members[f"{asset}:{year}-{month:02d}"]=member_sha
            rows.extend((asset,*x) for x in parsed);n+=len(parsed)
        counts[asset]=n
    payload=canonical_bytes(rows)
    meta={"counts":counts,"total_rows":len(rows),"member_sha256":members,
          "canonical_sha256":sha(payload),
          "ledger_sha256":sha(json.dumps(ledger,sort_keys=True,separators=(",",":")).encode())}
    return payload,meta

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--archive-root",type=Path,default=Path("research/v98_independent/phase275_premium_archives"))
    ap.add_argument("--out-dir",type=Path,default=Path("research/v98_independent/data/phase275_premium_index"))
    ap.add_argument("--manifest",type=Path,default=Path("research/v98_independent/phase275_premium_index_manifest.json"))
    a=ap.parse_args()
    ledger=[];errors=[]
    for asset in ASSETS:
        for year,month in MONTHS:
            try:ledger.append(verify_fetch(a.archive_root,asset,year,month))
            except Exception as e:
                errors.append({"asset":asset,"year":year,"month":month,"error":f"{type(e).__name__}: {e}"})
    first_meta=second_meta=None;canon=b""
    if not errors and len(ledger)==EXPECTED_ARCHIVES:
        canon,first_meta=reconstruct(a.archive_root,ledger)
        canon2,second_meta=reconstruct(a.archive_root,ledger)
        if canon2!=canon:raise RuntimeError("non-deterministic canonical reconstruction")
    counts=(first_meta or {}).get("counts",{})
    gates={
      "all_144_archives_available":len(ledger)==EXPECTED_ARCHIVES and not errors,
      "all_checksums_verified":len(ledger)==EXPECTED_ARCHIVES and all(x["checksum_verified"] for x in ledger),
      "exact_rows_per_asset":bool(counts) and all(counts.get(a)==EXPECTED_PER_ASSET for a in ASSETS),
      "exact_total_asset_hours":bool(first_meta) and first_meta.get("total_rows")==EXPECTED_TOTAL,
      "deterministic_reconstruction":bool(first_meta) and first_meta==second_meta,
      "canonical_hash_recorded":bool(first_meta and first_meta.get("canonical_sha256")),
      "training_period_only":True,
    }
    decision="PASS_DATA_ONLY" if all(gates.values()) else "FAIL_DATA_NO_ALPHA"
    manifest={"engine":"V98 Independent","phase":275,"kind":"DATA_ONLY_BINANCE_PREMIUM_INDEX",
      "decision":decision,"source":"Binance official public-data premiumIndexKlines",
      "source_base":BASE,"assets":list(ASSETS),"interval":INTERVAL,"period":["2023-01","2025-12"],
      "expected_archives":EXPECTED_ARCHIVES,"expected_hours_per_asset":EXPECTED_PER_ASSET,
      "expected_asset_hours":EXPECTED_TOTAL,"archive_ledger":ledger,"archive_errors":errors,
      "reconstruction":first_meta,"second_reconstruction":second_meta,"gates":gates,
      "alpha_executed":False,"pnl_executed":False,"crypto_return_join":False,
      "direction_selected":False,"parameter_search":False,"validation_accessed":False,"holdout_accessed":False,
      "phase083_selection_use":False,"v14_used":False,"v15_used":False,"v99_used":False,
      "preregistration":"research/v98_independent/phase275_premium_index_dataonly_prereg.md"}
    a.out_dir.mkdir(parents=True,exist_ok=True)
    (a.out_dir/"premium_index_1h.csv").write_bytes(canon)
    a.manifest.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"decision":decision,"archive_count":len(ledger),"errors":errors[:8],
      "counts":counts,"total_rows":(first_meta or {}).get("total_rows"),"gates":gates,
      "canonical_sha256":(first_meta or {}).get("canonical_sha256")},indent=2,sort_keys=True))

if __name__=="__main__":main()
