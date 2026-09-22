from __future__ import annotations

import concurrent.futures
import csv
import datetime as dt
import hashlib
import io
import json
import math
import re
import statistics
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "reports" / "candidate_v99_r106_phase114_bookdepth_data_audit.json"
S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
CDN = "https://data.binance.vision/"
NS = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
START = dt.date(2021, 12, 1)


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "CryptoAI-v99-r106-phase114"})
    with urllib.request.urlopen(req, timeout=120) as response:
        return response.read()


def list_keys(prefix: str) -> list[str]:
    keys: list[str] = []
    token = None
    while True:
        q = {"list-type": "2", "prefix": prefix, "max-keys": "1000"}
        if token:
            q["continuation-token"] = token
        root = ET.fromstring(get(S3 + "?" + urllib.parse.urlencode(q)))
        keys.extend(node.text for node in root.findall("s3:Contents/s3:Key", NS) if node.text)
        truncated = root.findtext("s3:IsTruncated", default="false", namespaces=NS).lower() == "true"
        if not truncated:
            break
        token = root.findtext("s3:NextContinuationToken", namespaces=NS)
        if not token:
            raise RuntimeError("truncated listing without continuation token")
    return keys


def verify(key: str) -> dict:
    raw = get(CDN + key)
    want = get(CDN + key + ".CHECKSUM").decode().split()[0]
    got = hashlib.sha256(raw).hexdigest()
    if got != want:
        raise RuntimeError("sha256 " + key)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"crc {key}: {bad}")
        names = archive.namelist()
        if len(names) != 1:
            raise RuntimeError(f"unexpected zip member count {key}: {len(names)}")
        reader = csv.DictReader(io.TextIOWrapper(archive.open(names[0]), encoding="utf-8-sig"))
        header = list(reader.fieldnames or [])
        required = {"timestamp", "percentage", "depth", "notional"}
        if not required.issubset(set(header)):
            raise RuntimeError(f"schema {key}: {header}")
        rows, pairs, timestamps, bands, last_t = 0, set(), [], set(), None
        for row in reader:
            rows += 1
            try:
                t = dt.datetime.fromisoformat(row["timestamp"].strip().replace("Z", "+00:00"))
                pct = float(row["percentage"]); depth = float(row["depth"]); notional = float(row["notional"])
            except (TypeError, ValueError) as exc:
                raise RuntimeError("parse " + key) from exc
            if not all(math.isfinite(x) for x in (pct, depth, notional)):
                raise RuntimeError("nonfinite " + key)
            if depth < 0 or notional < 0:
                raise RuntimeError("negative depth/notional " + key)
            if last_t is not None and t < last_t:
                raise RuntimeError("timestamp order " + key)
            last_t = t
            pair = (t.isoformat(), pct)
            if pair in pairs:
                raise RuntimeError("duplicate timestamp/percentage " + key)
            pairs.add(pair); timestamps.append(t); bands.add(pct)
    if rows == 0:
        raise RuntimeError("empty " + key)
    unique_ts = sorted(set(timestamps))
    deltas = [(b-a).total_seconds() for a,b in zip(unique_ts, unique_ts[1:]) if b > a]
    return {"key": key, "header": header, "rows": rows, "unique_timestamps": len(unique_ts), "bands": sorted(bands), "cadence_seconds_median": statistics.median(deltas) if deltas else None, "cadence_seconds_min": min(deltas) if deltas else None, "cadence_seconds_max": max(deltas) if deltas else None, "first_timestamp": unique_ts[0].isoformat(), "last_timestamp": unique_ts[-1].isoformat()}


def main() -> None:
    assert (PROJECT / "research/v99_r106_phase114_bookdepth_data_audit_prereg.md").exists()
    phase112 = json.loads((PROJECT / "reports/candidate_v99_r106_phase112_premium_index_data_audit.json").read_text())
    train_end = dt.date.fromisoformat(phase112["train_end"])
    manifest = json.loads((PROJECT / "data/CANONICAL_MANIFEST_RESEARCH_PIT48.json").read_text())
    symbols = sorted(manifest["symbols"])

    def one(symbol: str):
        prefix = f"data/futures/um/daily/bookDepth/{symbol}/"
        admitted = []
        for key in list_keys(prefix):
            m = re.search(rf"/{re.escape(symbol)}-bookDepth-(\d{{4}}-\d{{2}}-\d{{2}})\.zip$", key, re.I)
            if not m: continue
            date = dt.date.fromisoformat(m.group(1))
            # Registered train end is 2024-01-18 00:00 UTC. A daily 2024-01-18 archive
            # contains observations after that instant, so only earlier archive dates are admissible.
            if START <= date < train_end:
                admitted.append((date, key))
        return symbol, sorted(admitted)

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        listed = list(pool.map(one, symbols))
    per_symbol, samples = {}, []
    for symbol, files in listed:
        if not files:
            per_symbol[symbol] = {"observed_files":0,"first":None,"last":None,"expected_files":0,"missing_dates":[],"coverage_ratio":0.0}; continue
        first,last=files[0][0],files[-1][0]; observed={d for d,_ in files}
        expected=[first+dt.timedelta(days=i) for i in range((last-first).days+1)]
        missing=[d.isoformat() for d in expected if d not in observed]
        per_symbol[symbol]={"observed_files":len(files),"first":first.isoformat(),"last":last.isoformat(),"expected_files":len(expected),"missing_dates":missing,"coverage_ratio":len(observed)/len(expected)}
        seen=set()
        for date,key in files:
            q=(date.year,(date.month-1)//3+1)
            if q not in seen: seen.add(q); samples.append(key)
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        verified=list(pool.map(verify,samples))
    schemas={}; bands=set(); medians=[]
    for row in verified:
        h=tuple(row["header"]); schemas[h]=schemas.get(h,0)+1; bands.update(row["bands"])
        if row["cadence_seconds_median"] is not None: medians.append(float(row["cadence_seconds_median"]))
    out={
      "study":"V99 R106 Phase114 — orthogonal Binance USD-M bookDepth DATA AUDIT ONLY","status":"DATA_AUDIT_COMPLETE",
      "frozen_assets_untouched":{"v16":True,"v99_frozen":True},"train_start":START.isoformat(),"train_end_exclusive":train_end.isoformat()+"T00:00:00Z",
      "strict_boundary_policy":"daily archive date strictly before train_end; boundary-day archive excluded to prevent post-train observations",
      "holdout_market_values_not_downloaded_or_parsed":True,"object_listing_metadata_only":True,
      "source":{"listing":S3,"download":CDN+"data/futures/um/daily/bookDepth/<SYMBOL>/","official_public_archive":True},"symbols":per_symbol,
      "summary":{"symbols":len(symbols),"symbols_with_data":sum(v["observed_files"]>0 for v in per_symbol.values()),"observed_files":sum(v["observed_files"] for v in per_symbol.values()),"missing_dates":sum(len(v["missing_dates"]) for v in per_symbol.values()),"integrity_files_verified":len(verified),"sample_rows_verified":sum(v["rows"] for v in verified),"schema_variants":len(schemas),"bands":sorted(bands),"sample_median_cadence_seconds_min":min(medians) if medians else None,"sample_median_cadence_seconds_median":statistics.median(medians) if medians else None,"sample_median_cadence_seconds_max":max(medians) if medians else None},
      "schema_inventory":[{"header":list(h),"sample_files":n} for h,n in schemas.items()],
      "integrity_sampling":{"method":"first available admitted archive of every calendar quarter per canonical symbol","checks":["SHA256","ZIP CRC","nonempty CSV","required schema","parseable monotone timestamps","finite percentage/depth/notional","nonnegative depth/notional","unique timestamp/percentage rows"],"samples":verified},
      "alpha_prohibited":True,"return_relation_computed":False,"next_gate":"Review coverage/schema/cadence only. Any bookDepth alpha requires separate post-audit preregistration before PnL.",
      "disclosure":"No post-train archive content, order-book alpha, predictive relation, return/PnL comparison, regime selection or benchmark selection is computed in Phase114."}
    OUT.write_text(json.dumps(out,indent=2)+"\n"); print(json.dumps(out["summary"],indent=2))

if __name__ == "__main__": main()
