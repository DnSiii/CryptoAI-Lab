"""Fail-closed, read-only published R106 paper audit and immutable provenance witness.

Reads ONLY the durable publication ledger. No market-data download, no replay,
no strategy optimization, no orders and no write to the paper-results branch.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from research.tools.v99_phase195gb_paper_epoch_audit import audit, canonical


def inspect(raw: bytes, captured_at_utc: str) -> dict:
    if not isinstance(raw, bytes):
        raise ValueError("raw ledger bytes are required")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result
    def reject_constant(value):
        raise ValueError("nonfinite JSON constant: " + value)
    ledger = json.loads(raw, object_pairs_hook=unique, parse_constant=reject_constant)
    if not isinstance(ledger, dict):
        raise ValueError("published ledger must be object")
    result = audit(ledger, captured_at_utc)
    return {
        "status": "DATA_ONLY_HOLD" if result["status"] == "DATA_ONLY/HOLD" else "OBSERVED_ONLY_NOT_PROMOTION",
        "source": "durable_paper_results_published_ledger",
        "raw_published_sha256": hashlib.sha256(raw).hexdigest(),
        "canonical_published_sha256": hashlib.sha256(canonical(ledger)).hexdigest(),
        "observed_at_utc": captured_at_utc,
        "published_last_utc": result["published_latest_utc"],
        "published_boundary_utc": result["published_boundary_utc"],
        "staleness_hours": result["stale_hours_at_audit"],
        "distinct_forward_traces": result["distinct_forward_traces"],
        "forward_duplicate_groups": result["forward_duplicate_groups"],
        "variants": result["variants"],
        "flags": result["flags"],
        "historic_train_end_utc": "2024-01-18T00:00:00+00:00",
        "independent_exchange_receipts_authenticated": False,
        "full_trading_costs_authenticated": False,
        "publication_authorized": False,
        "promotion_authorized": False,
        "holdout_accessed_for_selection": False,
        "economic_trials": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    captured_at = datetime.now(timezone.utc).isoformat()
    report = inspect(args.ledger.read_bytes(), captured_at)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"phase": "R106 paper source audit", "status": report["status"],
                      "sha256": report["raw_published_sha256"],
                      "paper_end": report["published_last_utc"],
                      "distinct_traces": report["distinct_forward_traces"],
                      "publication_authorized": False,
                      "promotion_authorized": False}, sort_keys=True))


if __name__ == "__main__":
    main()
