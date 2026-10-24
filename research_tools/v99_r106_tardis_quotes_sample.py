#!/usr/bin/env python3
"""Bounded historical quote SOURCE probe. No strategies, orders, ROI, or holdout."""
import csv
import gzip
import hashlib
import io
import json
import pathlib
import urllib.request
from datetime import datetime, timezone

OUT = pathlib.Path("tardis_quote_probe")
OUT.mkdir(exist_ok=True)
DATES = ("2022-01-01", "2023-01-01")  # TRAIN-only sample dates, fixed before any request
LIMIT = 2000
FIELDS = ("exchange", "symbol", "timestamp", "local_timestamp",
          "ask_amount", "ask_price", "bid_price", "bid_amount")
manifest = {"classification": "PARTIAL_SOURCE_SAMPLE_ONLY_NOT_EXECUTION_OR_PNL",
            "provider": "Tardis.dev; reconstructed exchange WebSocket L2 quotes, not original Deribit-hosted receipts",
            "complete_train": False, "asof_quote_coverage": False, "days": []}
for day in DATES:
    url = "https://datasets.tardis.dev/v1/deribit/quotes/" + day.replace("-", "/") + "/OPTIONS.csv.gz"
    request = urllib.request.Request(url, headers={"User-Agent": "V99-research-source-probe/1.0"})
    # gzip stream is deliberately read only up to LIMIT rows; not a complete daily file.
    with urllib.request.urlopen(request, timeout=90) as response:
        status = response.status
        if status != 200:
            raise RuntimeError(f"source HTTP {status} for {day}")
        with gzip.GzipFile(fileobj=response) as gz:
            reader = csv.DictReader(io.TextIOWrapper(gz, encoding="utf-8", newline=""))
            if not reader.fieldnames or not set(FIELDS).issubset(reader.fieldnames):
                raise RuntimeError(f"missing quote schema: {reader.fieldnames}")
            rows = []
            for row in reader:
                if len(rows) >= LIMIT:
                    break
                rows.append({k: row[k] for k in FIELDS})
    if not rows:
        raise RuntimeError(f"empty quote sample {day}")
    output = OUT / f"deribit_options_quotes_{day}.csv"
    with output.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    raw = output.read_bytes()
    first_us = int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp() * 1_000_000)
    last_us = first_us + 86_400_000_000
    if any(not (first_us <= int(r["local_timestamp"]) < last_us) for r in rows):
        raise RuntimeError(f"sample local timestamp outside {day}")
    both = 0
    for r in rows:
        try:
            bid, ask = float(r["bid_price"]), float(r["ask_price"])
            ba, aa = float(r["bid_amount"]), float(r["ask_amount"])
            if 0 < bid < ask and ba > 0 and aa > 0:
                both += 1
        except (ValueError, TypeError):
            continue
    manifest["days"].append({"date": day, "url": url, "http_status": status,
                              "rows_partial": len(rows), "two_sided_positive_quotes_partial": both,
                              "csv_sha256": hashlib.sha256(raw).hexdigest(),
                              "sample_file": output.name,
                              "first_local_timestamp": rows[0]["local_timestamp"],
                              "last_local_timestamp": rows[-1]["local_timestamp"]})
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(json.dumps(manifest, indent=2))
