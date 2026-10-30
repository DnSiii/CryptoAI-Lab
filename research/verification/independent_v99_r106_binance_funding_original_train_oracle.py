"""Independent original Binance funding ZIP + publisher CHECKSUM oracle, no primary imports."""
from __future__ import annotations
import csv
import hashlib
import io
import json
import math
import re
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

A = int(datetime(2021, 12, 9, tzinfo=timezone.utc).timestamp() * 1000)
B = int(datetime(2023, 10, 1, tzinfo=timezone.utc).timestamp() * 1000)
EIGHT_HOURS = 28_800_000
ORIGINAL_SLOTS = set(range(A, B, EIGHT_HOURS))
EDGES = [A + h * 3_600_000 for h in (0, 3172, 6345, 9518, 12691, 15864)]
EXPECTED_MONTHS = [f"{y}-{m:02d}" for y in (2021, 2022, 2023) for m in range(1,13)
                   if (y,m) >= (2021,12) and (y,m) <= (2023,9)]

def verify(root):
    root = Path(root)
    report = json.loads((root / "binance_funding_source_only.json").read_bytes())
    if report.get("schema") != "V99_R106_BINANCE_ORIGINAL_FUNDING_SOURCE_ONLY_V1":
        raise ValueError("ORACLE_WRONG_SCHEMA")
    if report.get("months") != EXPECTED_MONTHS:
        raise ValueError("ORACLE_MONTH_SCOPE")
    if len(report.get("files", [])) != 44:
        raise ValueError("ORACLE_EXPECTED_44_FILES")
    if report.get("source_is_not_account_settled_cash") is not True or report.get("source_is_not_okx") is not True:
        raise ValueError("ORACLE_FALSE_NATIVE_ACCOUNT_CLAIM")
    for key in ("economic_train_executed","native_account_fees_certified",
                "historical_fills_certified","roi_calculated","validation_opened",
                "final_holdout_opened","promotion_authorized",
                "paper_publication_authorized","orders_enabled"):
        if report.get(key) is not False:
            raise ValueError("ORACLE_FALSE_ECONOMIC_PERMISSION_" + key)
    rows = {"BTCUSDT": [], "ETHUSDT": []}
    valid = 0
    expected_names = {(symbol, month) for symbol in rows for month in EXPECTED_MONTHS}
    actual_names = {(x.get("symbol"), x.get("month")) for x in report["files"]}
    if expected_names != actual_names or len(actual_names) != 44:
        raise ValueError("ORACLE_FORGED_MONTH_LIST")
    valid_names = set()
    for item in report["files"]:
        symbol, month = item["symbol"], item["month"]
        filename = f"{symbol}-fundingRate-{month}.zip"
        if item.get("filename") != filename:
            raise ValueError("ORACLE_FILENAME_MISMATCH")
        path = root / "raw_ephemeral" / filename
        check = root / "raw_ephemeral" / (filename + ".CHECKSUM")
        if item.get("status") != "PUBLISHER_CHECKSUM_AND_ROWS_VERIFIED":
            if item.get("publisher_checksum_verified") is not False or path.exists() or check.exists():
                raise ValueError("ORACLE_UNVERIFIED_SOURCE_PRESENT")
            continue
        if not path.is_file() or not check.is_file():
            raise ValueError("ORACLE_ORIGINAL_BYTES_MISSING")
        archive = path.read_bytes()
        checksum = check.read_bytes()
        if len(archive) > 8*1024*1024 or len(checksum) > 4096:
            raise ValueError("ORACLE_UNBOUNDED_BYTES")
        match = re.search(rb"\b([0-9a-fA-F]{64})\b", checksum)
        if not match:
            raise ValueError("ORACLE_PUBLISHER_CHECKSUM_MISSING")
        expected = match.group(1).decode().lower()
        actual = hashlib.sha256(archive).hexdigest()
        if actual != expected or item.get("published_sha256") != expected or item.get("zip_sha256") != actual:
            raise ValueError("ORACLE_PUBLISHER_SHA256_DISAGREEMENT")
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            members = [m for m in z.infolist() if not m.is_dir()]
            if len(members) != 1 or members[0].file_size > 24*1024*1024 or not members[0].filename.endswith(".csv"):
                raise ValueError("ORACLE_ZIP_MEMBERS")
            with z.open(members[0]) as stream:
                data = stream.read(24*1024*1024+1)
        if len(data) > 24*1024*1024:
            raise ValueError("ORACLE_DECOMPRESSED_CAP")
        reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
        if not {"calc_time","funding_interval_hours","last_funding_rate"}.issubset(reader.fieldnames or []):
            raise ValueError("ORACLE_ORIGINAL_HEADER")
        parsed = []
        previous = -1
        for row in reader:
            ts = int(row["calc_time"])
            interval = float(row["funding_interval_hours"])
            rate = float(row["last_funding_rate"])
            if not math.isfinite(rate) or not math.isfinite(interval) or interval <= 0:
                raise ValueError("ORACLE_NONFINITE_ROW")
            if ts <= previous or datetime.fromtimestamp(ts/1000,timezone.utc).strftime("%Y-%m") != month:
                raise ValueError("ORACLE_NONMONOTONE_OR_MONTH")
            previous = ts
            parsed.append((ts,interval,rate))
        if not parsed:
            raise ValueError("ORACLE_EMPTY_ORIGINAL_CSV")
        for key, value in (("original_rows",len(parsed)),("first_ms",parsed[0][0]),
                           ("last_ms",parsed[-1][0]),
                           ("off_8h_interval_rows",sum(interval != 8 for _,interval,_ in parsed))):
            if item.get(key) != value:
                raise ValueError("ORACLE_FILE_METADATA_MISMATCH_"+key)
        rows[symbol].extend(parsed)
        valid += 1
        valid_names.add(filename)
    actual_files = {p.name for p in (root/"raw_ephemeral").glob("*") if p.is_file()}
    if actual_files != valid_names | {n+".CHECKSUM" for n in valid_names}:
        raise ValueError("ORACLE_EXTRA_ORIGINAL_FILES")
    for symbol in rows:
        in_train = [(t,iv,r) for t,iv,r in rows[symbol] if A <= t < B]
        counter = Counter(t for t,_,_ in in_train)
        exact = {t for t in ORIGINAL_SLOTS if counter[t] == 1}
        expected = dict(original_rows_all_months=len(rows[symbol]),
                        original_rows_train=len(in_train),
                        exact_train_slots=len(exact),
                        expected_train_slots=1983,
                        offgrid_train_rows=sum(t not in ORIGINAL_SLOTS for t,_,_ in in_train),
                        non8h_interval_train_rows=sum(iv != 8 for _,iv,_ in in_train),
                        duplicate_train_timestamps=sum(n-1 for n in counter.values() if n>1),
                        five_folds=[])
        for a,b in zip(EDGES,EDGES[1:]):
            exp = sum(a <= t < b for t in ORIGINAL_SLOTS)
            obs = sum(a <= t < b for t in exact)
            expected["five_folds"].append(dict(expected=exp,observed=obs,missing=exp-obs))
        if report["folds"].get(symbol) != expected:
            raise ValueError("ORACLE_INDEPENDENT_FIVEFOLD_DISAGREEMENT_"+symbol)
    complete = (valid == 44 and all(report["folds"][symbol]["exact_train_slots"] == 1983
                and report["folds"][symbol]["non8h_interval_train_rows"] == 0
                and report["folds"][symbol]["duplicate_train_timestamps"] == 0 for symbol in rows))
    expected_status = "BINANCE_PUBLISHED_FUNDING_TRAIN_COVERAGE_PASS" if complete else "SOURCE_HOLD"
    if report.get("status") != expected_status:
        raise ValueError("ORACLE_FALSE_COVERAGE_PROMOTION")
    print(json.dumps(dict(oracle="INDEPENDENT_PUBLISHER_BYTES_AND_FIVE_FOLD_PASS",
                          status=expected_status, verified_archives=valid,
                          exact_slots_by_asset={s:report["folds"][s]["exact_train_slots"] for s in rows},
                          account_settlement_certified=False, promotion=False), sort_keys=True))
    return report

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_binance_funding_original_train_oracle OUT")
    verify(sys.argv[1])
