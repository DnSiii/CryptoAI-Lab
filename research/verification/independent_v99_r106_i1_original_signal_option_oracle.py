"""Independent raw-byte original I1 signal-to-option-source intersection oracle.

No imports from the primary join, execution readiness or signal evaluator.
Never certifies historical fills, fees, margin, economic ROI or complete lifecycles.
"""
from __future__ import annotations
import csv
import hashlib
import json
import math
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

UTC = timezone.utc
END = int(datetime(2023, 10, 1, tzinfo=UTC).timestamp() * 1000)
EDGES = [int(datetime.fromisoformat(x).replace(tzinfo=UTC).timestamp()*1000) for x in (
    "2021-12-09T00:00:00", "2022-04-20T04:00:00", "2022-08-30T09:00:00",
    "2023-01-09T14:00:00", "2023-05-21T19:00:00", "2023-10-01T00:00:00")]
DAY_US = 86_400_000_000


def original_quotes(root: Path):
    manifest_bytes = (root / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    if (manifest.get("classification") != "PARTIAL_SOURCE_SAMPLE_ONLY_NOT_EXECUTION_OR_PNL"
            or manifest.get("complete_train") is not False
            or manifest.get("asof_quote_coverage") is not False
            or [x.get("date") for x in manifest.get("days", [])] !=
                ["2022-01-01", "2023-01-01"]):
        raise AssertionError("FORGED_ORIGINAL_PARTIAL_MANIFEST")
    records = []
    total = 0
    for day in manifest["days"]:
        filename = day["sample_file"]
        if not isinstance(filename, str) or Path(filename).name != filename:
            raise AssertionError("UNSAFE_ORIGINAL_SOURCE_PATH")
        raw = (root / filename).read_bytes()
        if hashlib.sha256(raw).hexdigest() != day["csv_sha256"]:
            raise AssertionError("TAMPERED_ORIGINAL_OPTION_SOURCE")
        d = date.fromisoformat(day["date"])
        low = int(datetime(d.year, d.month, d.day, tzinfo=UTC).timestamp()*1_000_000)
        high = low + DAY_US
        with (root / filename).open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            required = {"exchange","symbol","timestamp","local_timestamp",
                        "bid_price","ask_price","bid_amount","ask_amount"}
            if not required.issubset(reader.fieldnames or []):
                raise AssertionError("ORIGINAL_QUOTE_FIELDS_MISSING")
            n = 0
            for row in reader:
                n += 1
                if row["exchange"] != "deribit":
                    raise AssertionError("WRONG_ORIGINAL_VENUE")
                try:
                    event = int(row["timestamp"])
                    arrival = int(row["local_timestamp"])
                except (ValueError, TypeError) as exc:
                    raise AssertionError("BAD_ORIGINAL_CLOCK") from exc
                if not low <= arrival < high:
                    raise AssertionError("FUTURE_ORIGINAL_DAY_CLOCK")
                # Do not discard impossible event clocks before last-arrival
                # selection: newer anomalous updates revoke older books.
                records.append((arrival,event,row))
            if n != day["rows_partial"] or n > 2000:
                raise AssertionError("ORIGINAL_SAMPLE_COUNT_CHANGED")
            total += n
    if total != 4000:
        raise AssertionError("ORIGINAL_SOURCE_SAMPLE_NOT_4000")
    return records, hashlib.sha256(manifest_bytes).hexdigest()


def _parsed(row):
    parts = row["symbol"].split("-")
    if len(parts) != 4 or parts[0] not in ("BTC","ETH") or parts[3] != "P":
        return None
    try:
        exp = int(datetime.strptime(parts[1].upper(), "%d%b%y").replace(
            hour=8,tzinfo=UTC).timestamp()*1_000_000)
        strike = float(parts[2])
        values = [float(row[x]) for x in ("bid_price","ask_price","bid_amount","ask_amount")]
    except (ValueError, TypeError, OverflowError):
        return None
    if not (all(math.isfinite(x) and x > 0 for x in [strike]+values)
            and values[0] < values[1]):
        return None
    return parts[0], exp, strike


def _ready(records, ms, asset):
    t = ms * 1000
    last = {}
    for arrival,event,row in records:
        # Last predecision physical update wins, even when its event is stale.
        # Filtering freshness before choosing last would resurrect revoked books.
        if not arrival < t:
            continue
        # Last physical update wins, including invalid quotes.
        name = row["symbol"]
        if name not in last or arrival >= last[name][0]:
            last[name] = (arrival,event,row)
    by_exp = {}
    for arrival,event,row in last.values():
        if not t - 300_000_000 <= event <= arrival < t:
            continue
        p = _parsed(row)
        if p is None or p[0] != asset:
            continue
        if not (21*DAY_US <= p[1]-t <= 45*DAY_US and p[1] < END*1000):
            continue
        by_exp.setdefault(p[1],[]).append((arrival,event,p[2]))
    return any(a[2] != b[2] and abs(a[0]-b[0]) <= 1_000_000
               and abs(a[1]-b[1]) <= 1_000_000
               for quotes in by_exp.values()
               for i,a in enumerate(quotes) for b in quotes[i+1:])


def verify(signal_path: Path, root: Path, result: dict):
    signal_bytes = signal_path.read_bytes()
    signal = json.loads(signal_bytes)
    records, manifest_sha = original_quotes(root)
    if (result.get("schema") != "V99_I1_ORIGINAL_SIGNAL_OPTION_SOURCE_INTERSECTION_V1"
            or result.get("status") != "BLOCKED_PARTIAL_ORIGINAL_OPTION_ARCHIVE"
            or result.get("source_signal_sha256") != hashlib.sha256(signal_bytes).hexdigest()
            or result.get("source_partial_manifest_sha256") != manifest_sha
            or result.get("original_source_rows") != 4000
            or result.get("original_signal_observations") != 182
            or result.get("positive_original_causal_signals") != 132
            or result.get("certified_complete_option_lifecycles") != 0):
        raise AssertionError("FORGED_JOIN_OR_SOURCE_IDENTITY")
    for k in ("economic_train_executed","historical_option_fills_certified",
              "native_fee_tier_authenticated","native_margin_authenticated",
              "validation_opened","holdout_opened","orders_enabled","promotion_authorized"):
        if result.get(k) is not False:
            raise AssertionError("FORGED_ECONOMIC_STATUS")
    dates = []
    d = date(2021,12,13)
    while d + timedelta(days=21) < date(2023,10,1):
        dates.append(d)
        d += timedelta(days=7)
    expected = [(int(datetime(x.year,x.month,x.day,tzinfo=UTC).timestamp()*1000),a)
                for x in dates for a in ("BTC","ETH")]
    if len(expected) != 182 or [(r["decision_ms"],r["asset"]) for r in signal["rows"]] != expected:
        raise AssertionError("UNTRUSTED_CAUSAL_SIGNAL_GRID")
    decisions = []
    folds = {str(f): {a:{"positive":0,"source_ready":0,"intersection":0}
                      for a in ("BTC","ETH")} for f in range(1,6)}
    for row in signal["rows"]:
        t,a = row["decision_ms"],row["asset"]
        f = next((i for i in range(1,6) if EDGES[i-1] <= t < EDGES[i]),None)
        if f != row["fold"] or row["signal"] not in (
            "POSITIVE_EX_ANTE_PREMIUM","NO_PREMIUM","NO_30D_HISTORY"):
            raise AssertionError("FORGED_SIGNAL_FOLD_OR_VALUE")
        pos = row["signal"] == "POSITIVE_EX_ANTE_PREMIUM"
        ready = _ready(records,t,a)
        cross = pos and ready
        fold = folds[str(f)][a]
        fold["positive"] += int(pos)
        fold["source_ready"] += int(ready)
        fold["intersection"] += int(cross)
        decisions.append({"decision_ms":t,"asset":a,"fold":f,
                          "causal_signal":row["signal"],
                          "original_two_leg_source_ready":ready,
                          "signal_and_source_intersection":cross})
    if (result.get("decisions") != decisions or result.get("folds") != folds
            or result.get("original_source_ready_asset_weeks") != sum(
                x[a]["source_ready"] for x in folds.values() for a in ("BTC","ETH"))
            or result.get("signal_source_intersections") != sum(
                x[a]["intersection"] for x in folds.values() for a in ("BTC","ETH"))):
        raise AssertionError("FORGED_ORIGINAL_SOURCE_INTERSECTION")
    return {"status":"INDEPENDENT_ORIGINAL_SIGNAL_AND_OPTION_BYTES_RECONCILED",
            "signal_observations":len(decisions),
            "source_ready_asset_weeks":result["original_source_ready_asset_weeks"],
            "signal_source_intersections":result["signal_source_intersections"],
            "economic_train_executed":False,"promotion_authorized":False}


def main(signal_path, root, result_path):
    signal_path,root,result_path = Path(signal_path),Path(root),Path(result_path)
    result = json.loads(result_path.read_text(encoding="utf-8"))
    checked = verify(signal_path,root,result)
    forged = json.loads(json.dumps(result))
    forged["signal_source_intersections"] += 1
    try:
        verify(signal_path,root,forged)
    except AssertionError as exc:
        if str(exc) != "FORGED_ORIGINAL_SOURCE_INTERSECTION":
            raise
    else:
        raise AssertionError("FORGED_INTERSECTION_ACCEPTED")
    forged = json.loads(json.dumps(result))
    forged["source_partial_manifest_sha256"] = "0"*64
    try:
        verify(signal_path,root,forged)
    except AssertionError as exc:
        if str(exc) != "FORGED_JOIN_OR_SOURCE_IDENTITY":
            raise
    else:
        raise AssertionError("FORGED_SOURCE_SHA_ACCEPTED")
    print(json.dumps({**checked,"forged_intersection_rejected":True,
                      "forged_source_sha_rejected":True},sort_keys=True))
    return checked


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_original_signal_option_oracle SIGNAL_JSON PARTIAL_ROOT RESULT_JSON")
    main(*sys.argv[1:])
