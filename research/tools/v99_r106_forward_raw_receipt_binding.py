"""Independent raw-byte receipt binding for forward journal. Read-only, fail-closed."""
import argparse
import hashlib
import json
from pathlib import Path
from research.tools.v99_r106_forward_receipt_preflight import check, utc
from research.tools.v99_r106_forward_journal_structural_gate import verify

def audit(journal, manifest, raw_dir):
    provenance = check(manifest, raw_dir, phase="forward")
    structure = verify(journal, {**provenance, "epoch_id": manifest.get("epoch_id"),
                                  "epoch_start_utc": manifest.get("epoch_start_utc")})
    errors = list(provenance["errors"]) + list(structure["errors"])
    indexed = {}
    for receipt in manifest.get("receipts", []):
        if not isinstance(receipt, dict):
            errors.append("INVALID_RECEIPT_ENTRY")
            continue
        name = receipt.get("raw_file")
        if not isinstance(name, str) or Path(name).name != name or name in (".", ".."):
            errors.append("UNSAFE_RAW_FILE")
            continue
        try:
            data = (raw_dir / name).read_bytes()
            actual = hashlib.sha256(data).hexdigest()
            if actual != receipt.get("sha256"):
                errors.append("RAW_BYTE_HASH_MISMATCH")
                continue
            indexed[actual] = receipt
        except OSError:
            errors.append("RAW_FILE_UNAVAILABLE")
    for i, event in enumerate(journal.get("events", [])):
        if not isinstance(event, dict):
            continue
        receipt = indexed.get(event.get("receipt_sha256"))
        if receipt is None:
            errors.append(f"EVENT_{i}_NO_AUTHENTIC_RAW_RECEIPT")
            continue
        try:
            if utc(receipt["acquired_utc"]) > utc(event["event_utc"]):
                errors.append(f"EVENT_{i}_RECEIPT_ACQUIRED_AFTER_EVENT")
        except (ValueError, TypeError, KeyError):
            errors.append(f"EVENT_{i}_INVALID_RECEIPT_TIME")
        if event.get("type") == "FILL" and receipt.get("kind") != "execution":
            errors.append(f"EVENT_{i}_WRONG_RECEIPT_KIND")
        if event.get("type") == "FUNDING":
            if receipt.get("kind") != "funding" or receipt.get("settlement_event_id") != event.get("settlement_event_id"):
                errors.append(f"EVENT_{i}_FUNDING_SETTLEMENT_MISMATCH")
    return {"status": "RAW_RECEIPT_BINDING_PRECHECK_ONLY" if not errors else "BLOCKED",
            "errors": sorted(set(errors)), "events_checked": len(journal.get("events", [])),
            "publication_authorized": False, "real_orders_authorized": False,
            "economic_validation_complete": False}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--journal", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--raw-dir", required=True, type=Path)
    args = parser.parse_args()
    result = audit(json.loads(args.journal.read_text()), json.loads(args.manifest.read_text()), args.raw_dir)
    print(json.dumps(result, sort_keys=True))
    if result["status"] == "BLOCKED":
        raise SystemExit(2)

if __name__ == "__main__":
    main()
