#!/usr/bin/env python3
"""Independent V98 HQ source receipt reconciliation. DATA_ONLY, no prices or PnL.

Compares two separately executed parser paths: immutable strict inventory
(the original complete-grid source remains rejected) and the new HQ masked
canonical source. This audit never rehabilitates the strict source.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PINNED_MANIFEST = "02f1eef3fb3bd5a8a4f7ab7e60379474f091c961f9be98217b8b9792f75ef3a9"
ASSETS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")
GAP = dt.datetime(2023, 3, 24, 13, tzinfo=dt.timezone.utc)
PINNED_PARTIAL_CLOSE = {
    "BTCUSDT": 1679661581646, "ETHUSDT": 1679661583061,
    "BNBUSDT": 1679661581451, "SOLUSDT": 1679661586948,
}
STRICT_REJECTION = "READ_ONLY_100_ARCHIVE_SOURCE_GAP_INVENTORY_NOT_SOURCE_RESCUE"
HQ_SOURCE_PASS = "PASS_HQ_MASKED_SOURCE_ONLY_NOT_ECONOMIC"


def reconcile(inventory: dict, hq: dict) -> dict:
    if inventory.get("decision") != STRICT_REJECTION:
        raise ValueError("HQ_AUDIT_STRICT_REJECTION_NOT_PRESERVED")
    if hq.get("decision") != HQ_SOURCE_PASS:
        raise ValueError("HQ_AUDIT_SOURCE_NOT_ACCEPTED")
    if (inventory.get("holdout_2025_read") is not False or
            inventory.get("historical_system_pnl_computed") is not False or
            hq.get("validation_2025_read") is not False or
            hq.get("data_2026_read") is not False or
            hq.get("historical_system_pnl_computed") is not False or
            hq.get("trading_authorized") is not False or
            hq.get("complete_grid_source_rejection_still_active") is not True):
        raise ValueError("HQ_AUDIT_HOLDOUT_OR_PNL_FIREWALL")
    if (inventory.get("archive_count") != 100 or
            inventory.get("provider_sha256_verified") != 100 or
            inventory.get("expected_asset_hours") != 73152 or
            inventory.get("observed_asset_hours") != 73148 or
            inventory.get("defective_archives") != 4 or
            hq.get("publisher_checksums_verified") != 100 or
            hq.get("calendar_asset_hours") != 73152 or
            hq.get("observed_asset_hours") != 73148 or
            hq.get("masked_asset_hours") != 4 or
            hq.get("publisher_early_close_partial_asset_hours") != 4 or
            hq.get("eligible_full_hour_asset_hours") != 73144 or
            hq.get("pinned_partial_close_ms") != PINNED_PARTIAL_CLOSE or
            hq.get("two_pass_identical") is not True or
            hq.get("publisher_manifest_sha256") != PINNED_MANIFEST):
        raise ValueError("HQ_AUDIT_GLOBAL_COUNTS_OR_PIN")
    strict = inventory.get("archives", [])
    masked = hq.get("archives", [])
    if len(strict) != 100 or len(masked) != 100:
        raise ValueError("HQ_AUDIT_ARCHIVE_COUNT")
    expected = {f"{asset}-1h-{y}-{m:02d}.zip"
                for asset in ASSETS for y, m in
                ([(2022, 12)] + [(y, m) for y in (2023, 2024) for m in range(1, 13)])}
    seen = set()
    gap_count = 0
    manifest = []
    for old, new in zip(strict, masked):
        asset, month = new["asset"], new["month"]
        name = f"{asset}-1h-{month}.zip"
        if name not in expected or name in seen or old.get("archive") != name:
            raise ValueError("HQ_AUDIT_ARCHIVE_IDENTITY")
        seen.add(name)
        digest = old.get("provider_sha256")
        if digest != new.get("sha256") or len(digest) != 64:
            raise ValueError("HQ_AUDIT_PROVIDER_HASH_DIVERGENCE")
        if old.get("rows") != new.get("observed") or old.get("expected_rows") != new.get("observed") + new.get("masked"):
            raise ValueError("HQ_AUDIT_ROW_DIVERGENCE")
        missing = old.get("missing_utc", [])
        expected_gap = asset in ASSETS and month == "2023-03"
        if len(missing) != (1 if expected_gap else 0):
            raise ValueError("HQ_AUDIT_UNEXPECTED_GAP")
        if missing and dt.datetime.fromisoformat(missing[0].replace("Z", "+00:00")) != GAP:
            raise ValueError("HQ_AUDIT_GAP_TIMESTAMP")
        if new.get("partial_hour") != (1 if expected_gap else 0):
            raise ValueError("HQ_AUDIT_PARTIAL_CLOSE_MASK")
        if new.get("masked") != len(missing) or old.get("unexpected_utc") or old.get("duplicate_timestamps") != 0:
            raise ValueError("HQ_AUDIT_MASK_OR_DUPLICATE")
        if old.get("strictly_increasing") is not True:
            raise ValueError("HQ_AUDIT_TIME_ORDER")
        gap_count += len(missing)
        manifest.append(f"{asset}|{month}|{digest}\n")
    if seen != expected or gap_count != 4:
        raise ValueError("HQ_AUDIT_UNIVERSE_OR_GAP_COUNT")
    if hashlib.sha256("".join(manifest).encode("utf-8")).hexdigest() != PINNED_MANIFEST:
        raise ValueError("HQ_AUDIT_MANIFEST_ORDER_OR_HASH")
    canonical = hq.get("canonical_sha256", "")
    if len(canonical) != 64 or any(x not in "0123456789abcdef" for x in canonical):
        raise ValueError("HQ_AUDIT_CANONICAL_HASH_SCHEMA")
    return {
        "decision": "PASS_HQ_INDEPENDENT_SOURCE_RECONCILE_NO_PNL",
        "archive_pairs": len(seen),
        "calendar_asset_hours": 73152,
        "observed_asset_hours": 73148,
        "masked_asset_hours": gap_count,
        "partial_hour_asset_hours": 4,
        "eligible_full_hour_asset_hours": 73144,
        "canonical_sha256": canonical,
        "publisher_manifest_sha256": PINNED_MANIFEST,
        "strict_complete_grid_source_still_rejected": True,
        "training_only_through_2024": True,
        "holdout_2025_read": False,
        "historical_system_pnl_computed": False,
        "trading_authorized": False,
    }


def run():
    old = json.loads((ROOT / "spot_perp_full_gap_inventory.json").read_text())
    hq = json.loads((ROOT / "hq_gap_aware_spot_source_only" / "hq_masked_source_receipt.json").read_text())
    report = reconcile(old, hq)
    (ROOT / "hq_independent_source_reconcile.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("HQ_INDEPENDENT_RECONCILE_PASS", report["canonical_sha256"], flush=True)


if __name__ == "__main__":
    run()
