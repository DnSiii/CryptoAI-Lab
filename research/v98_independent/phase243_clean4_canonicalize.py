#!/usr/bin/env python3
"""V98 Clean-4 source-only canonical panel, fail closed; never reads XRP or 2026+."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
from phase243_binance_archive_ingest import _parse_month
from phase243_clean4_official_archive_acquire import ASSETS, MONTHS

def canonicalize(root: Path, dest: Path, receipt_file: Path) -> dict:
    root, dest = Path(root), Path(dest)
    if any("v98_independent" not in p.resolve().parts for p in (root, dest, receipt_file)):
        raise ValueError("V98_NAMESPACE_REQUIRED")
    receipt = json.loads(Path(receipt_file).read_text())
    if (receipt.get("assets") != list(ASSETS) or receipt.get("months") != 37
        or receipt.get("verified_archives") != 148 or len(receipt.get("receipts", {})) != 148
        or not receipt.get("source_only") or receipt.get("holdout_accessed") is not False):
        raise ValueError("INCOMPLETE_OR_UNTRUSTED_RECEIPT")
    output, manifests, fingerprints = {}, {}, set()
    for asset in ASSETS:
        frames, months = [], {}
        for month in MONTHS:
            name = f"{asset}-1h-{month}.zip"
            path = root / "klines" / asset / "1h" / name
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"MISSING_OR_SYMLINKED_ARCHIVE:{name}")
            witness = receipt["receipts"].get(f"{asset}/{month}")
            if not isinstance(witness, dict):
                raise ValueError(f"MISSING_RECEIPT:{name}")
            expected_url = f"https://data.binance.vision/data/futures/um/monthly/klines/{asset}/1h/{name}"
            if witness.get("url") != expected_url or witness.get("checksum_url") != expected_url + ".CHECKSUM":
                raise ValueError(f"WRONG_PROVENANCE:{name}")
            checksum_path = path.with_name(name + ".CHECKSUM")
            if checksum_path.is_symlink() or not checksum_path.is_file():
                raise ValueError(f"MISSING_CHECKSUM:{name}")
            import re
            match = re.fullmatch(r"([0-9a-fA-F]{64})\s+\*?([^/\\\s]+)", checksum_path.read_text().strip())
            if not match or match.group(2) != name:
                raise ValueError(f"INVALID_CHECKSUM:{name}")
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            if sha != witness.get("sha256") or sha != match.group(1).lower():
                raise ValueError(f"CHECKSUM_MISMATCH:{name}")
            frame, ev = _parse_month(path, asset, month)
            if ev["archive_sha256"] != sha:
                raise ValueError(f"PARSER_HASH_MISMATCH:{name}")
            frames.append(frame)
            months[month] = ev
        panel = pd.concat(frames, ignore_index=True)
        times = pd.DatetimeIndex(panel.open_time)
        if (len(panel) != 27048 or times[0] != pd.Timestamp("2022-12-01T00:00:00Z")
            or times[-1] != pd.Timestamp("2025-12-31T23:00:00Z")
            or times.has_duplicates or not times.is_monotonic_increasing
            or not (times[1:] - times[:-1] == pd.Timedelta(hours=1)).all()):
            raise ValueError(f"CHRONOLOGY_FAILURE:{asset}")
        fingerprint = hashlib.sha256(panel[["open","close","volume","quote_volume"]].to_numpy(dtype="<f8").tobytes()).hexdigest()
        if fingerprint in fingerprints:
            raise ValueError("CROSS_ASSET_DUPLICATE_PANEL")
        fingerprints.add(fingerprint)
        output[asset] = panel.to_csv(index=False, float_format="%.12g").encode()
        manifests[asset] = {"rows":len(panel), "months":months,
                            "canonical_sha256":hashlib.sha256(output[asset]).hexdigest(),
                            "panel_fingerprint":fingerprint}
    # Only publish after ALL source and chronological checks pass.
    dest.mkdir(parents=True, exist_ok=True)
    for asset, data in output.items():
        (dest / f"{asset}_1h.csv").write_bytes(data)
    manifest = {"mode":"V98_CLEAN4_SOURCE_ONLY", "assets":manifests,
                "holdout_accessed":False, "promotion_eligible":False,
                "funding_reconciled":False, "economic_validation":False}
    (dest / "source_manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2)+"\n")
    return manifest

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    result = canonicalize(args.archive_root, args.output_root, args.receipt)
    print(json.dumps({"status":"CLEAN4_CANONICAL_SOURCE_PASS_NOT_PNL",
                      "assets":list(result["assets"]), "rows_per_asset":27048}))
