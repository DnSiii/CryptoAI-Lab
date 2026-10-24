#!/usr/bin/env python3
"""Independent CSV/manifest check of bounded SOURCE sample; never certifies full TRAIN."""
import csv
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

root = Path("tardis_quote_probe")
m = json.loads((root / "manifest.json").read_text())
assert m["classification"] == "PARTIAL_SOURCE_SAMPLE_ONLY_NOT_EXECUTION_OR_PNL"
assert m["complete_train"] is False and m["asof_quote_coverage"] is False
assert [d["date"] for d in m["days"]] == ["2022-01-01", "2023-01-01"]
for d in m["days"]:
    p = root / d["sample_file"]
    assert hashlib.sha256(p.read_bytes()).hexdigest() == d["csv_sha256"]
    with p.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == d["rows_partial"] and 0 < len(rows) <= 2000
    start = int(datetime.combine(date.fromisoformat(d["date"]), datetime.min.time(),
                                 tzinfo=timezone.utc).timestamp() * 1_000_000)
    assert all(start <= int(r["local_timestamp"]) < start + 86400 * 1_000_000 for r in rows)
    assert all(r["exchange"] == "deribit" for r in rows)
    assert all("-" in r["symbol"] and r["symbol"].endswith(("-C", "-P")) for r in rows)
    assert all(int(r["timestamp"]) > 0 for r in rows)
    n = 0
    for r in rows:
        try:
            if (0 < float(r["bid_price"]) < float(r["ask_price"])
                and float(r["bid_amount"]) > 0 and float(r["ask_amount"]) > 0):
                n += 1
        except (ValueError, TypeError):
            pass
    assert n == d["two_sided_positive_quotes_partial"]
    print(f"ORACLE PASS {d['date']} partial_rows={len(rows)} two_sided={n}")
print("SOURCE SAMPLE ONLY: no full TRAIN coverage, fill, fees, economic gate or promotion.")
