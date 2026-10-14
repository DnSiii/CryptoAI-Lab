"""First-party Binance Vision ZIP + .CHECKSUM as-of receipt, DATA_ONLY.

Used when USD-M REST returns 451. The CDN's timestamp is NOT a venue-signed
publication time or a historical first-discovery receipt. A daily archive
may only support a NEW forward epoch after its observed acquisition time.
No exchange orders, backtest, train, holdout or historical paper mutation.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.request import Request, urlopen

BASE="https://data.binance.vision/data/futures/um/daily/klines"
SYMBOLS=("BTCUSDT","ETHUSDT","SOLUSDT")
MAX_ARCHIVE_BYTES=5_000_000
MAX_CHECKSUM_BYTES=1024
MAX_CSV_UNCOMPRESSED=1_000_000
UTC=timezone.utc
HEX64=re.compile(r"^[a-fA-F0-9]{64}$")

def utc(value):
    if not isinstance(value,str): raise ValueError("explicit UTC timestamp required")
    t=datetime.fromisoformat(value.replace("Z","+00:00"))
    if t.tzinfo is None or t.utcoffset()!=timedelta(0):
        raise ValueError("only UTC timestamp accepted")
    return t.astimezone(UTC)

def iso(t):
    return t.astimezone(UTC).isoformat()

def now():
    return datetime.now(UTC)

def first_safe(received):
    t=utc(received)
    return iso(t.replace(minute=0,second=0,microsecond=0)+timedelta(hours=2))

def canonical_url(symbol,day):
    if symbol not in SYMBOLS:raise ValueError("non-allowlisted symbol")
    if not isinstance(day,str) or not re.fullmatch(r"20\d\d-\d\d-\d\d",day):
        raise ValueError("invalid ISO archive day")
    d=datetime.strptime(day,"%Y-%m-%d").date()
    if d>=now().date():raise ValueError("today/future daily archive forbidden")
    filename=f"{symbol}-1h-{day}.zip"
    return f"{BASE}/{symbol}/1h/{filename}"

def get(url,limit):
    if not url.startswith(BASE+"/") or ("?" in url or "#" in url):
        raise ValueError("source host/path not approved")
    start=now()
    req=Request(url,headers={"User-Agent":"CryptoAI-R106-archive-asof/1.0"})
    with urlopen(req,timeout=40) as response:
        if response.status!=200:
            raise ValueError("archive source HTTP status not 200")
        body=response.read(limit+1)
        hdr=response.headers
        source_date=hdr.get("Date")
        media=hdr.get("Content-Type")
        etag=hdr.get("ETag")
    end=now()
    if len(body)==0 or len(body)>limit:
        raise ValueError("empty or oversized source response")
    if (end-start).total_seconds()>60:
        raise ValueError("receipt acquisition exceeded one minute")
    # CDN response Date is contextual evidence, not an exchange signature.
    if source_date:
        server=parsedate_to_datetime(source_date)
        if server.tzinfo is None:raise ValueError("source Date missing timezone")
        if abs((server.astimezone(UTC)-end).total_seconds())>120:
            raise ValueError("CDN Date and runner clock diverged >120s")
    return {"bytes":body,"source_url":url,"request_utc":iso(start),
            "received_utc":iso(end),"http_date":source_date,
            "http_content_type":media,"http_etag":etag,
            "byte_count":len(body),"sha256":hashlib.sha256(body).hexdigest()}

def check_checksum(payload,checksum,symbol,day):
    if not isinstance(payload,bytes) or not isinstance(checksum,bytes):
        raise ValueError("original source bytes required")
    try:
        line=checksum.decode("ascii").strip()
    except UnicodeError as e:
        raise ValueError("invalid .CHECKSUM encoding") from e
    parts=line.split()
    if len(parts) not in (1,2) or not HEX64.fullmatch(parts[0]):
        raise ValueError("malformed first-party SHA256 checksum")
    if len(parts)==2 and parts[1].removeprefix("*")!=f"{symbol}-1h-{day}.zip":
        raise ValueError("checksum filename mismatch")
    real=hashlib.sha256(payload).hexdigest()
    if real!=parts[0].lower():
        raise ValueError("first-party archive checksum mismatch")
    return real

def parse_zip(payload,symbol,day):
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            files=archive.infolist()
            if len(files)!=1 or not files[0].filename.endswith(".csv"):
                raise ValueError("exactly one raw CSV member required")
            info=files[0]
            if info.filename!=f"{symbol}-1h-{day}.csv":
                raise ValueError("unexpected archive member")
            if info.file_size>MAX_CSV_UNCOMPRESSED:
                raise ValueError("uncompressed CSV too large")
            if archive.testzip() is not None:
                raise ValueError("corrupt ZIP CRC")
            content=archive.read(info)
    except (zipfile.BadZipFile,RuntimeError) as e:
        raise ValueError("invalid Binance archive ZIP") from e
    text=content.decode("utf-8-sig")
    rows=list(csv.reader(io.StringIO(text)))
    if rows and rows[0] and rows[0][0].lower()=="open_time":
        rows=rows[1:]
    if len(rows)!=24:
        raise ValueError("daily 1h ZIP must contain exactly 24 candles")
    expected=int(datetime.fromisoformat(day).replace(tzinfo=UTC).timestamp()*1000)
    stamps=[]
    for index,row in enumerate(rows):
        if len(row)<12:
            raise ValueError("ZIP kline fewer than 12 columns")
        try:
            opening=int(row[0])
            close=int(row[6])
        except (ValueError,TypeError) as e:
            raise ValueError("invalid native UTC epoch") from e
        # Binance Vision may use milliseconds or microseconds; normalize.
        unit=1000 if opening>=10**15 else 1
        start_ms=opening//unit
        close_ms=close//unit
        if opening%unit or (unit>1 and close%unit!=unit-1):
            raise ValueError("unrecognized native timestamp precision")
        if start_ms!=expected+index*3_600_000 or close_ms!=start_ms+3_600_000-1:
            raise ValueError("candle timestamp out-of-day, duplicated or gapped")
        try:
            o,h,l,c,volume,quote=(Decimal(row[i]) for i in (1,2,3,4,5,7))
        except (InvalidOperation,TypeError) as e:
            raise ValueError("malformed native OHLCV") from e
        if (not all(x.is_finite() for x in (o,h,l,c,volume,quote)) or
            l>min(o,c) or h<max(o,c) or volume<0 or quote<0 or l<=0):
            raise ValueError("invalid OHLCV price/volume semantics")
        stamps.append(iso(datetime.fromtimestamp(start_ms/1000,UTC)))
    return {"symbol":symbol,"day":day,"rows":len(rows),
            "first_candle_open_utc":stamps[0],
            "last_candle_open_utc":stamps[-1],
            "last_candle_close_utc":iso(datetime.fromtimestamp((expected+86400000)/1000,UTC)),
            "csv_sha256":hashlib.sha256(content).hexdigest()}

def receive(symbol,day):
    link=canonical_url(symbol,day)
    archive=get(link,MAX_ARCHIVE_BYTES)
    checksum=get(link+".CHECKSUM",MAX_CHECKSUM_BYTES)
    digest=check_checksum(archive["bytes"],checksum["bytes"],symbol,day)
    summary=parse_zip(archive["bytes"],symbol,day)
    if utc(archive["received_utc"])<utc(summary["last_candle_close_utc"]):
        raise ValueError("archive received before final candle closed")
    return {"symbol":symbol,"day":day,"archive":archive,
            "checksum":checksum,"verified_sha256":digest,"parsed":summary}

def collect(day):
    results=[receive(sym,day) for sym in SYMBOLS]
    latest=max(utc(x["archive"]["received_utc"]) for x in results)
    manifest={"schema":"V99_R106_ARCHIVE_ASOF_RECEIPT_V1",
              "status":"PROSPECTIVE_ARCHIVE_OBSERVED_DATA_ONLY",
              "first_party_archive_host":"data.binance.vision",
              "source_method":"HTTPS Binance Vision daily ZIP plus official SHA256 checksum",
              "archive_day_utc":day,"assets":{},
              "receipt_latest_utc":iso(latest),
              "earliest_safe_new_decision_utc":first_safe(iso(latest)),
              "source_content_checksum_verified":True,
              "cdn_date_is_not_exchange_signed":True,
              "historical_first_seen_authenticated":False,
              "historical_exchange_listing_authenticated":False,
              "paper_backfill_authorized":False,
              "paper_publication_authorized":False,
              "promotion_authorized":False,
              "real_orders_enabled":False,
              "economic_trials":0,"holdout_accessed":False}
    for item in results:
        manifest["assets"][item["symbol"]]={
            "archive_response":{k:v for k,v in item["archive"].items() if k!="bytes"},
            "checksum_response":{k:v for k,v in item["checksum"].items() if k!="bytes"},
            "verified_archive_sha256":item["verified_sha256"],
            "parsed":item["parsed"]}
    return manifest,results

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--day",help="UTC published archive day, default UTC today minus 2 days")
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    day=args.day or (now()-timedelta(days=2)).strftime("%Y-%m-%d")
    manifest,results=collect(day)
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n")
    for item in results:
        sym=item["symbol"]
        (args.out/f"{sym}-1h-{day}.zip").write_bytes(item["archive"]["bytes"])
        (args.out/f"{sym}-1h-{day}.zip.CHECKSUM").write_bytes(item["checksum"]["bytes"])
    print(json.dumps({"status":manifest["status"],"day":day,
                      "assets":list(manifest["assets"]),
                      "first_safe_decision":manifest["earliest_safe_new_decision_utc"],
                      "promotion_authorized":False},sort_keys=True))

if __name__=="__main__":
    main()
