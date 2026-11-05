#!/usr/bin/env python3
"""V98 Phase243 Clean-4 only archive assembler. No XRP, 2026+, alpha or PnL.

Reuses the independently audited Binance 12-field monthly parser, but does not
invoke the legacy five-asset assemble() entrypoint. Fails closed before writes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
import pandas as pd
from phase243_binance_archive_ingest import _parse_month, MONTHS, CUTOFF

CLEAN4 = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")

def _reject_symlink_components(path: Path):
    """Reject symlinks anywhere in the supplied path, not just at its leaf."""
    for part in (path.absolute(), *path.absolute().parents):
        if part.is_symlink():
            raise ValueError("SYMLINKED_PATH_COMPONENT")


def assemble_clean4(archive_root: Path, output_root: Path, *, write: bool = False):
    root, dest = Path(archive_root), Path(output_root)
    if "v98_independent" not in root.resolve().parts or "v98_independent" not in dest.resolve().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    _reject_symlink_components(root)
    _reject_symlink_components(dest)
    if len(MONTHS) != 37 or MONTHS[0] != "2022-12" or MONTHS[-1] != "2025-12":
        raise ValueError("TRAINING_CALENDAR_CHANGED")
    manifest = {"mode": "V98_PHASE243_CLEAN4_SOURCE_ONLY", "assets": {}, "training_cut_exclusive": CUTOFF.isoformat(),
                "xrp_quarantined": True, "holdout_accessed": False, "pnl_computed": False, "promotion_eligible": False}
    frames, fingerprints = {}, set()
    for asset in CLEAN4:
        pieces, evidence = [], {}
        for month in MONTHS:
            archive = root / "klines" / asset / "1h" / f"{asset}-1h-{month}.zip"
            _reject_symlink_components(archive)
            frame, receipt = _parse_month(archive, asset, month)
            pieces.append(frame)
            evidence[month] = receipt
        joined = pd.concat(pieces, ignore_index=True)
        times = pd.DatetimeIndex(joined.open_time)
        if (times.has_duplicates or not times.is_monotonic_increasing or
            times[0] != pd.Timestamp("2022-12-01T00:00:00Z") or
            times[-1] != CUTOFF - pd.Timedelta(hours=1) or
            not (times[1:] - times[:-1] == pd.Timedelta(hours=1)).all()):
            raise ValueError("CLEAN4_CONTINUITY_FAILURE_" + asset)
        fp = hashlib.sha256(joined[["open","close","volume","quote_volume"]].to_numpy(dtype="<f8").tobytes()).hexdigest()
        if fp in fingerprints:
            raise ValueError("DUPLICATED_CROSS_ASSET_PANEL")
        fingerprints.add(fp)
        frames[asset] = joined
        manifest["assets"][asset] = {"months": evidence, "rows": len(joined), "panel_sha256": fp}
    if write:
        # Never overwrite a previous evidence set, including an empty directory.
        # Publish one complete directory after every CSV and manifest is durable.
        if dest.exists():
            raise FileExistsError("OUTPUT_EXISTS_REFUSED")
        dest.parent.mkdir(parents=True, exist_ok=True)
        _reject_symlink_components(dest)
        with tempfile.TemporaryDirectory(prefix=".v98_clean4_stage_", dir=dest.parent) as staging:
            stage = Path(staging)
            for asset, frame in frames.items():
                raw = frame.to_csv(index=False, float_format="%.12g").encode()
                (stage / f"{asset}_1h.csv").write_bytes(raw)
                manifest["assets"][asset]["canonical_sha256"] = hashlib.sha256(raw).hexdigest()
            (stage / "source_manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\\n")
            # Directory rename is atomic on the same filesystem; no partial output.
            os.rename(stage, dest)
    return manifest

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--archive-root", type=Path, required=True)
    p.add_argument("--output-root", type=Path, required=True)
    p.add_argument("--write", action="store_true", help="Explicitly publish validated Clean-4 only")
    a = p.parse_args()
    m = assemble_clean4(a.archive_root, a.output_root, write=a.write)
    print(json.dumps({"mode": m["mode"], "assets": list(m["assets"]), "rows": {a:v["rows"] for a,v in m["assets"].items()}, "published": a.write}))
