#!/usr/bin/env python3
"""V98 Phase243 DATA_ONLY XRP aggTrades tape adjudication.

Implements the frozen 2026-10-14 preregistration. No alpha, PnL, holdout,
repair, source replacement, strategy selection, or promotion.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import time
import zipfile
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "phase243_aggtrades_tape_result.json"
CAPTURE = ROOT / "phase243_aggtrades_tape_capture"
DAY = "2023-11-14"
HOUR_MS = 1699959600000  # 2023-11-14 11:00:00 UTC
HOUR_END_MS = HOUR_MS + 3_600_000

URLS = {
    "monthly_1h": "https://data.binance.vision/data/futures/um/monthly/klines/XRPUSDT/1h/XRPUSDT-1h-2023-11.zip",
    "daily_1h": "https://data.binance.vision/data/futures/um/daily/klines/XRPUSDT/1h/XRPUSDT-1h-2023-11-14.zip",
    "daily_1m": "https://data.binance.vision/data/futures/um/daily/klines/XRPUSDT/1m/XRPUSDT-1m-2023-11-14.zip",
    "aggtrades": "https://data.binance.vision/data/futures/um/daily/aggTrades/XRPUSDT/XRPUSDT-aggTrades-2023-11-14.zip",
}
CAPS = {"monthly_1h": 12_000_000, "daily_1h": 12_000_000,
        "daily_1m": 20_000_000, "aggtrades": 80_000_000}
CHECKSUM = re.compile(rb"([0-9a-fA-F]{64})[ \t]+\*?([^\s]+)[\r\n]*\Z")

def download(url: str, cap: int) -> bytes:
    p = urlparse(url)
    if p.scheme != "https" or p.netloc != "data.binance.vision" or not p.path.startswith("/data/futures/um/"):
        raise ValueError("unapproved URL")
    last = None
    for attempt in range(4):
        try:
            req = Request(url, headers={"User-Agent": "V98-Independent-Phase243-AggTrades/1.0"})
            with urlopen(req, timeout=60) as r:
                final = urlparse(r.geturl())
                if final.scheme != "https" or final.netloc != "data.binance.vision":
                    raise ValueError("unexpected redirect")
                raw = r.read(cap + 1)
            if not raw or len(raw) > cap:
                raise ValueError("empty/oversized response")
            return raw
        except HTTPError as e:
            last = e
            if e.code not in (429, 500, 502, 503, 504) or attempt == 3:
                raise
        except (OSError, TimeoutError) as e:
            last = e
            if attempt == 3:
                raise
        time.sleep(min(2 ** attempt, 4))
    raise RuntimeError(type(last).__name__ if last else "download failed")

def fetch_verified(key: str):
    url = URLS[key]
    name = url.rsplit("/", 1)[-1]
    side = download(url + ".CHECKSUM", 2048)
    m = CHECKSUM.fullmatch(side)
    if not m or m.group(2) != name.encode():
        raise ValueError(f"{key}: invalid checksum sidecar")
    raw = download(url, CAPS[key])
    digest = hashlib.sha256(raw).hexdigest()
    if digest != m.group(1).decode().lower():
        raise ValueError(f"{key}: checksum mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        members = zf.infolist()
        expected = name[:-4] + ".csv"
        if len(members) != 1 or members[0].filename != expected or members[0].is_dir():
            raise ValueError(f"{key}: unexpected ZIP member")
        member = zf.read(members[0])
    CAPTURE.mkdir(parents=True, exist_ok=True)
    (CAPTURE / name).write_bytes(raw)
    (CAPTURE / (name + ".CHECKSUM")).write_bytes(side)
    return member, {
        "url": url,
        "archive_sha256": digest,
        "member_sha256": hashlib.sha256(member).hexdigest(),
        "checksum_verified": True,
        "source_authentication": "provider checksum only; not independent signature",
    }

def dec(x):
    try:
        d = Decimal(str(x).strip())
    except (InvalidOperation, ValueError):
        raise ValueError(f"invalid decimal: {x!r}")
    if not d.is_finite():
        raise ValueError("non-finite decimal")
    return d

def rows(member: bytes):
    text = member.decode("utf-8-sig")
    return list(csv.reader(io.StringIO(text)))

KLINE_NAMES = {
    "open_time": 0, "open": 1, "high": 2, "low": 3, "close": 4,
    "volume": 5, "close_time": 6, "quote_volume": 7, "trades": 8,
    "taker_buy_volume": 9, "taker_buy_quote_volume": 10,
}

def parse_klines(member: bytes):
    rr = rows(member)
    if not rr:
        raise ValueError("empty kline CSV")
    header = [x.strip().lower() for x in rr[0]]
    has_header = any("open_time" == x or "open time" == x for x in header)
    data = rr[1:] if has_header else rr
    idx = dict(KLINE_NAMES)
    if has_header:
        aliases = {
            "open_time": ("open_time","open time"),
            "open": ("open",), "high": ("high",), "low": ("low",), "close": ("close",),
            "volume": ("volume",), "close_time": ("close_time","close time"),
            "quote_volume": ("quote_volume","quote asset volume","quote_volume"),
            "trades": ("count","number of trades","trades"),
            "taker_buy_volume": ("taker_buy_volume","taker buy base asset volume"),
            "taker_buy_quote_volume": ("taker_buy_quote_volume","taker buy quote asset volume"),
        }
        for key, opts in aliases.items():
            found = next((header.index(o) for o in opts if o in header), None)
            if found is None:
                raise ValueError(f"kline header missing {key}: {header}")
            idx[key] = found
    out = []
    for r in data:
        if len(r) < 11:
            continue
        ot = int(r[idx["open_time"]])
        out.append({
            "open_time": ot,
            "open": dec(r[idx["open"]]), "high": dec(r[idx["high"]]),
            "low": dec(r[idx["low"]]), "close": dec(r[idx["close"]]),
            "base": dec(r[idx["volume"]]), "quote": dec(r[idx["quote_volume"]]),
            "trades": int(r[idx["trades"]]),
            "taker_buy_base": dec(r[idx["taker_buy_volume"]]),
            "taker_buy_quote": dec(r[idx["taker_buy_quote_volume"]]),
        })
    if not out:
        raise ValueError("no parsed kline rows")
    return out

AGG_DEFAULT = {
    "agg_id": 0, "price": 1, "qty": 2, "first_id": 3,
    "last_id": 4, "time": 5, "buyer_maker": 6,
}

def parse_agg(member: bytes):
    rr = rows(member)
    if not rr:
        raise ValueError("empty aggTrades CSV")
    header = [x.strip().lower() for x in rr[0]]
    has_header = any(x in header for x in ("agg_trade_id","aggtradeid","aggregate_trade_id"))
    data = rr[1:] if has_header else rr
    idx = dict(AGG_DEFAULT)
    if has_header:
        aliases = {
            "agg_id": ("agg_trade_id","aggtradeid","aggregate_trade_id"),
            "price": ("price",), "qty": ("quantity","qty"),
            "first_id": ("first_trade_id","firsttradeid"),
            "last_id": ("last_trade_id","lasttradeid"),
            "time": ("transact_time","timestamp","time"),
            "buyer_maker": ("is_buyer_maker","buyer_maker","isbuyermaker"),
        }
        for key, opts in aliases.items():
            found = next((header.index(o) for o in opts if o in header), None)
            if found is None:
                raise ValueError(f"aggTrades header missing {key}: {header}")
            idx[key] = found
    out = []
    prev_agg = None
    prev_time = None
    for r in data:
        if len(r) < 7:
            raise ValueError("short aggTrades row")
        aid = int(r[idx["agg_id"]]); price = dec(r[idx["price"]]); qty = dec(r[idx["qty"]])
        fid = int(r[idx["first_id"]]); lid = int(r[idx["last_id"]]); ts = int(r[idx["time"]])
        bm_raw = r[idx["buyer_maker"]].strip().lower()
        if bm_raw not in ("true","false"):
            raise ValueError("invalid buyer-maker boolean")
        if price <= 0 or qty <= 0 or fid > lid:
            raise ValueError("invalid trade geometry")
        if prev_agg is not None and aid <= prev_agg:
            raise ValueError("aggregate IDs not strictly increasing")
        if prev_time is not None and ts < prev_time:
            raise ValueError("timestamps decrease")
        if not (1699920000000 <= ts < 1700006400000):  # 2023-11-14 UTC
            raise ValueError("aggTrades outside frozen UTC day")
        out.append({"agg_id": aid, "price": price, "qty": qty, "first_id": fid,
                    "last_id": lid, "time": ts, "buyer_maker": bm_raw == "true"})
        prev_agg, prev_time = aid, ts
    if not out:
        raise ValueError("no parsed aggTrades rows")
    return out

def kline_hour(rows_, hour_ms: int):
    hit = [r for r in rows_ if r["open_time"] == hour_ms]
    if len(hit) != 1:
        raise ValueError(f"expected one 1h candle, got {len(hit)}")
    return hit[0]

def aggregate_minutes(rows_, hour_ms: int):
    x = [r for r in rows_ if hour_ms <= r["open_time"] < hour_ms + 3_600_000]
    if len(x) != 60:
        raise ValueError(f"expected 60 one-minute candles, got {len(x)}")
    x.sort(key=lambda r:r["open_time"])
    return {
        "open": x[0]["open"], "high": max(r["high"] for r in x),
        "low": min(r["low"] for r in x), "close": x[-1]["close"],
        "base": sum((r["base"] for r in x), Decimal(0)),
        "quote": sum((r["quote"] for r in x), Decimal(0)),
        "trades": sum(r["trades"] for r in x),
        "taker_buy_base": sum((r["taker_buy_base"] for r in x), Decimal(0)),
        "taker_buy_quote": sum((r["taker_buy_quote"] for r in x), Decimal(0)),
    }

def aggregate_tape(rows_):
    x = [r for r in rows_ if HOUR_MS <= r["time"] < HOUR_END_MS]
    if not x:
        raise ValueError("no aggTrades in frozen hour")
    contiguous = all(x[i]["first_id"] == x[i-1]["last_id"] + 1 for i in range(1,len(x)))
    raw_trade_count = sum(r["last_id"] - r["first_id"] + 1 for r in x)
    return {
        "open": x[0]["price"], "high": max(r["price"] for r in x),
        "low": min(r["price"] for r in x), "close": x[-1]["price"],
        "base": sum((r["qty"] for r in x), Decimal(0)),
        "quote": sum((r["price"] * r["qty"] for r in x), Decimal(0)),
        "taker_buy_base": sum((r["qty"] for r in x if not r["buyer_maker"]), Decimal(0)),
        "taker_buy_quote": sum((r["price"] * r["qty"] for r in x if not r["buyer_maker"]), Decimal(0)),
        "agg_records": len(x),
        "first_agg_id": x[0]["agg_id"], "last_agg_id": x[-1]["agg_id"],
        "first_trade_id": x[0]["first_id"], "last_trade_id": x[-1]["last_id"],
        "raw_trade_count": raw_trade_count, "raw_trade_ids_contiguous": contiguous,
    }

def tol(field: str, ref: Decimal):
    if field in ("base","taker_buy_base"):
        return max(Decimal("0.000001"), Decimal("0.000000001") * abs(ref))
    if field in ("quote","taker_buy_quote"):
        return max(Decimal("0.0001"), Decimal("0.000000001") * abs(ref))
    return Decimal(0)

def compare(tape, ref):
    fields = ("open","high","low","close","base","quote","taker_buy_base","taker_buy_quote")
    checks = {}
    for f in fields:
        diff = abs(tape[f] - ref[f])
        allowed = tol(f, ref[f])
        checks[f] = {"match": diff <= allowed, "abs_diff": str(diff), "tolerance": str(allowed)}
    if tape["raw_trade_ids_contiguous"]:
        checks["trades"] = {"match": tape["raw_trade_count"] == ref["trades"],
                            "tape": tape["raw_trade_count"], "reference": ref["trades"],
                            "definition_match": True}
    else:
        checks["trades"] = {"match": None, "definition_match": False}
    required = [v["match"] for v in checks.values() if v["match"] is not None]
    return {"all_required_match": all(required), "checks": checks}

def public_decimal_dict(d):
    return {k:(str(v) if isinstance(v, Decimal) else v) for k,v in d.items()}

def main():
    report = {
        "engine":"V98 Independent","phase":243,"mode":"DATA_ONLY_NO_ALPHA_NO_PNL",
        "preregistration":"research/v98_independent/phase243_prereg_20261014_0847_aggtrades_tape.md",
        "holdout_accessed":False,"alpha_or_pnl_computed":False,"promotion_eligible":False,
        "source_repair_performed":False,"v16_used":False,"v99_used":False,
        "status":"INCONCLUSIVE_TAPE_SOURCE","sources":{}
    }
    try:
        CAPTURE.mkdir(parents=True, exist_ok=True)
        payloads={}
        for key in URLS:
            payloads[key], report["sources"][key] = fetch_verified(key)
        monthly = parse_klines(payloads["monthly_1h"])
        daily1h = parse_klines(payloads["daily_1h"])
        daily1m = parse_klines(payloads["daily_1m"])
        tape_rows = parse_agg(payloads["aggtrades"])
        m1h = kline_hour(monthly,HOUR_MS)
        d1h = kline_hour(daily1h,HOUR_MS)
        m1 = aggregate_minutes(daily1m,HOUR_MS)
        tape = aggregate_tape(tape_rows)
        cmp_monthly = compare(tape,m1h)
        cmp_daily1h = compare(tape,d1h)
        cmp_1m = compare(tape,m1)
        report["hour_utc"]="2023-11-14T11:00:00Z"
        report["tape_summary"]=public_decimal_dict(tape)
        report["reference_identity"]={
            "monthly_1h_equals_daily_1h": all(m1h[k]==d1h[k] for k in m1h),
            "daily_1m_aggregate_equals_daily_1h": all(m1[k]==d1h[k] for k in ("open","high","low","close","base","quote","trades","taker_buy_base","taker_buy_quote"))
        }
        report["comparisons"]={"monthly_1h":cmp_monthly,"daily_1h":cmp_daily1h,"daily_1m_aggregate":cmp_1m}
        support=[name for name,c in report["comparisons"].items() if c["all_required_match"]]
        report["supported_references"]=support
        if support:
            report["status"]="CONSISTENT_SAME_PROVIDER_UNAUTHENTICATED"
        else:
            report["status"]="QUARANTINED_SOURCE_CONFLICT"
        report["interpretation"]="Same-provider tape is diagnostic only; it cannot independently authenticate or repair the canonical training source."
    except Exception as exc:
        report["status"]="INCONCLUSIVE_TAPE_SOURCE"
        report["error_type"]=type(exc).__name__
        report["error"]=str(exc)[:800]
    OUT.write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"status":report["status"],"supported_references":report.get("supported_references",[]),
                      "error":report.get("error")},sort_keys=True))
    if report["status"]=="INCONCLUSIVE_TAPE_SOURCE":
        raise SystemExit(2)

if __name__=="__main__":
    main()
