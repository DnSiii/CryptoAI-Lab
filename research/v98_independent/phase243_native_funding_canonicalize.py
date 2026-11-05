#!/usr/bin/env python3
"""V98-only native funding canonicalization. Source accounting, never a PnL claim."""
import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from phase243_clean4_official_archive_acquire import ASSETS, MONTHS
from phase243_native_funding_archive import BASE, audit

def canonicalize(root, receipt_path, output_root):
    root, receipt_path, output_root = map(Path, (root, receipt_path, output_root))
    if any("v98_independent" not in p.absolute().parts for p in (root, receipt_path, output_root)):
        raise ValueError("V98_NAMESPACE_REQUIRED")
    receipt = json.loads(receipt_path.read_text())
    if (receipt.get("verified_archives") != 148 or receipt.get("complete") is not True
            or receipt.get("holdout_accessed") is not False
            or receipt.get("economic_validation") is not False
            or len(receipt.get("receipts", {})) != 148):
        raise ValueError("INCOMPLETE_FUNDING_PROVENANCE")
    outputs, summary = {}, {}
    for asset in ASSETS:
        records = []
        prev = None
        for month in MONTHS:
            name = f"{asset}-fundingRate-{month}.zip"
            path = root / "fundingRate" / asset / name
            sidecar = path.with_name(name + ".CHECKSUM")
            witness = receipt["receipts"].get(f"{asset}/{month}")
            expected_url = f"{BASE}/{asset}/{name}"
            if (not isinstance(witness, dict) or witness.get("url") != expected_url
                    or witness.get("checksum_url") != expected_url + ".CHECKSUM"):
                raise ValueError(f"INVALID_FUNDING_WITNESS:{asset}/{month}")
            if any(p.is_symlink() or not p.is_file() for p in (path, sidecar)):
                raise ValueError(f"MISSING_FUNDING_SOURCE:{asset}/{month}")
            match = re.fullmatch(r"([0-9a-fA-F]{64})\s+\*?([^/\\\s]+)", sidecar.read_text().strip())
            if not match or match.group(2) != name:
                raise ValueError(f"INVALID_FUNDING_SIDECAR:{asset}/{month}")
            blob = path.read_bytes()
            digest = hashlib.sha256(blob).hexdigest()
            if digest != match.group(1).lower() or digest != witness.get("sha256"):
                raise ValueError(f"FUNDING_PROVENANCE_MISMATCH:{asset}/{month}")
            evidence = audit(blob, asset, month)
            if any(evidence[k] != witness.get(k) for k in ("events", "first_ms", "last_ms")):
                raise ValueError(f"FUNDING_RECEIPT_MISMATCH:{asset}/{month}")
            with zipfile.ZipFile(io.BytesIO(blob)) as archive:
                reader = csv.DictReader(io.StringIO(archive.read(name.replace(".zip", ".csv")).decode("utf-8-sig")))
                cols = set(reader.fieldnames or ())
                tcol, rcol = (("calc_time", "last_funding_rate") if "calc_time" in cols
                              else ("fundingTime", "fundingRate"))
                for row in reader:
                    t = int(row[tcol])
                    rate = float(row[rcol])
                    if prev is not None and (t <= prev or t - prev > 24 * 3600000):
                        raise ValueError(f"FUNDING_CROSS_MONTH_CHRONOLOGY:{asset}/{month}")
                    prev = t
                    records.append((t, rate))
        if not records:
            raise ValueError(f"EMPTY_FUNDING:{asset}")
        stream = io.StringIO()
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("funding_time_ms", "funding_rate"))
        for t, rate in records:
            writer.writerow((t, format(rate, ".17g")))
        data = stream.getvalue().encode()
        outputs[asset] = data
        summary[asset] = {"events": len(records), "first_ms": records[0][0],
                          "last_ms": records[-1][0], "sha256": hashlib.sha256(data).hexdigest()}
    output_root.mkdir(parents=True, exist_ok=True)
    for asset, data in outputs.items():
        (output_root / f"{asset}_native_funding.csv").write_bytes(data)
    manifest = {"mode": "V98_NATIVE_FUNDING_CANONICAL_SOURCE_ONLY",
                "assets": summary, "funding_reconciled": False,
                "economic_validation": False, "holdout_accessed": False}
    (output_root / "funding_manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    return manifest

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--output-root", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(canonicalize(a.root, a.receipt, a.output_root), sort_keys=True))
