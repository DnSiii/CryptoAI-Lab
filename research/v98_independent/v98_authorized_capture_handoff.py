#!/usr/bin/env python3
"""V98-only fail-closed bridge: raw authorized 2022-25 capture -> strict mark importer.

Reuses the independent 13,524-row capture audit and the strict native-rate
expected-event importer. Does NOT acquire data, certify exchange origin, run
PnL, read holdout, or authorize paper/live trading.
"""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import hashlib
import json
import tempfile
from email.utils import format_datetime
from pathlib import Path

from v98_exact_funding_full_history_capture_audit import (
    audit, ASSETS, FIRST, STEP, N, LAST, ENDPOINT, SCOPE,
)
from v98_authorized_funding_mark_ingest import validate

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def bridge(capture_dir: Path, expected_csv: Path, output_dir: Path) -> dict:
    capture_dir = Path(capture_dir).resolve()
    expected_csv = Path(expected_csv).resolve()
    output_dir = Path(output_dir).resolve()
    if output_dir.exists():
        raise ValueError("V98_HANDOFF_OUTPUT_ALREADY_EXISTS")
    # Audit the actual raw bytes, page order, manifest, calendar and hashes
    # BEFORE deriving a new representation. This does not authenticate origin.
    source_receipt = audit(capture_dir)
    if source_receipt["events_reconciled"] != 13524:
        raise ValueError("V98_HANDOFF_INCOMPLETE_CAPTURE")
    transport = json.loads(
        (capture_dir / "v98_exact_funding_full_history_transport.json").read_bytes()
    )
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="v98-handoff-", dir=output_dir.parent) as temp:
        tmp = Path(temp)
        pages = tmp / "v98_authorized_pages.jsonl"
        page_count = 0
        with pages.open("w", encoding="utf-8", newline="\n") as f:
            for asset in ASSETS:
                for page in transport["capture_pages"][asset]:
                    raw_path = capture_dir / page["raw_path"]
                    raw = raw_path.read_bytes()
                    if sha(raw) != page["raw_sha256"]:
                        raise ValueError("V98_HANDOFF_PAGE_SHA_CHANGED")
                    try:
                        body = raw.decode("utf-8", errors="strict")
                    except UnicodeDecodeError:
                        raise ValueError("V98_HANDOFF_NON_UTF8_RAW_BODY")
                    # No synthetic Date/Content-Type fallback: the original
                    # captured transport evidence must contain these fields.
                    obj = {
                        "url": page["request_url"],
                        "status": page["http_status"],
                        "response_headers": page["response_headers"],
                        "retrieved_at_utc": page["response_utc"],
                        "response_body": body,
                        "response_body_sha256": sha(raw),
                    }
                    f.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")
                    page_count += 1
        # Independently reconcile exact mark, rate and every native event
        # using the expected Clean-4 event file from the pinned source bridge.
        receipt = validate(pages, expected_csv, tmp / "v98_authorized_mark_receipt.json")
        if receipt["records"] != 13524 or receipt["pages"] != page_count:
            raise ValueError("V98_HANDOFF_IMPORT_RECONCILIATION")
        result = {
            "decision": "PASS_V98_CAPTURE_TO_NATIVE_MARK_CONTENT_CHAIN_ORIGIN_UNATTESTED",
            "records": receipt["records"],
            "raw_pages": page_count,
            "capture_manifest_sha256": source_receipt["manifest_sha256"],
            "expected_native_sha256": sha(expected_csv.read_bytes()),
            "strict_pages_sha256": sha(pages.read_bytes()),
            "exact_marks_sha256": receipt["exact_marks_csv_sha256"],
            "exchange_origin_independently_attested": False,
            "requires_authorized_independent_transport_attestation": True,
            "2025_exposed_training_only": True,
            "2026_plus_market_data_accessed": False,
            "holdout_accessed": False,
            "pnl_computed": False,
            "paper_live_authorized": False,
        }
        (tmp / "v98_handoff_summary.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n"
        )
        # Publish only a fully verified content chain, never partial output.
        tmp.rename(output_dir)
    return result

def self_test() -> dict:
    """Synthetic 4 x 3381 fixture: end-to-end plus adversarial transport tests."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        capture = root / "capture"
        capture.mkdir()
        expected = root / "native.csv"
        assets, pages = {}, {}
        now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
        with expected.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(("asset", "fundingTime", "fundingRate"))
            for asset in ASSETS:
                for i in range(N):
                    w.writerow((asset, FIRST + i * STEP, "0.0001"))
        for asset in ASSETS:
            rows = [
                {"symbol": asset, "fundingTime": FIRST + i * STEP,
                 "fundingRate": "0.0001", "markPrice": "100.5"}
                for i in range(N)
            ]
            page_list = []
            for offset in range(0, N, 1000):
                chunk = rows[offset:offset + 1000]
                raw = json.dumps(chunk, separators=(",", ":")).encode()
                filename = f"{asset}_page_{offset // 1000 + 1:03d}.json"
                (capture / filename).write_bytes(raw)
                start = FIRST if offset == 0 else rows[offset - 1]["fundingTime"] + 1
                request = now - dt.timedelta(seconds=60 - offset // 1000 * 2)
                response = request + dt.timedelta(seconds=1)
                page_list.append({
                    "request_url": ENDPOINT +
                        f"?symbol={asset}&startTime={start}&endTime={LAST + 60000}&limit=1000",
                    "request_utc": request.isoformat(),
                    "response_utc": response.isoformat(),
                    "http_status": 200,
                    "response_headers": {
                        "Date": format_datetime(response, usegmt=True),
                        "Content-Type": "application/json",
                    },
                    "raw_path": filename,
                    "raw_sha256": sha(raw),
                    "rows": len(chunk),
                    "first_time": chunk[0]["fundingTime"],
                    "last_time": chunk[-1]["fundingTime"],
                })
            assembled = json.dumps(rows, separators=(",", ":")).encode()
            filename = f"{asset}_fundingRate_exact_2022_2025.json"
            (capture / filename).write_bytes(assembled)
            assets[asset] = {
                "path": filename, "sha256": sha(assembled),
                "source_url": page_list[0]["request_url"],
            }
            pages[asset] = page_list
        manifest = {"scope": SCOPE, "assets": assets}
        transport = {
            "scope": SCOPE, "endpoint": ENDPOINT, "created_utc": now.isoformat(),
            "capture_pages": pages, "native_events": 4 * N,
            "operator_asserted_transport_only": True,
            "official_origin_independently_attested": False,
            "2025_exposed_training_only": True,
            "2026_plus_accessed": False, "holdout_accessed": False,
            "pnl_computed": False,
        }
        (capture / "v98_exact_funding_full_history_manifest.json").write_text(
            json.dumps(manifest)
        )
        receipt_path = capture / "v98_exact_funding_full_history_transport.json"
        receipt_path.write_text(json.dumps(transport))
        result = bridge(capture, expected, root / "valid")
        assert result["records"] == 13524 and result["raw_pages"] == 16
        assert (root / "valid" / "v98_authorized_mark_receipt.csv").is_file()
        # A captured HTTP Date inconsistent with retrieval must fail closed.
        original_date = pages[ASSETS[0]][0]["response_headers"]["Date"]
        pages[ASSETS[0]][0]["response_headers"]["Date"] = format_datetime(
            now - dt.timedelta(days=2), usegmt=True
        )
        receipt_path.write_text(json.dumps(transport))
        try:
            bridge(capture, expected, root / "bad_date")
        except ValueError as exc:
            assert "HTTP_DATE_RETRIEVAL_MISMATCH" in str(exc)
        else:
            raise AssertionError("V98_HANDOFF_ACCEPTED_FALSE_HTTP_DATE")
        assert not (root / "bad_date").exists()
        pages[ASSETS[0]][0]["response_headers"]["Date"] = original_date
        # Wrong Content-Type must not be accepted just because JSON parses.
        pages[ASSETS[0]][0]["response_headers"]["Content-Type"] = "text/html"
        receipt_path.write_text(json.dumps(transport))
        try:
            bridge(capture, expected, root / "bad_mime")
        except ValueError as exc:
            assert ("MISSING_OR_INVALID_HTTP_CONTENT_TYPE" in str(exc) or
                    "V98_FULL_AUDIT_HTTP_CONTENT_TYPE" in str(exc))
        else:
            raise AssertionError("V98_HANDOFF_ACCEPTED_FALSE_HTTP_MIME")
        assert not (root / "bad_mime").exists()
        pages[ASSETS[0]][0]["response_headers"]["Content-Type"] = "application/json"
        receipt_path.write_text(json.dumps(transport))
        # A changed original raw page must fail BEFORE native import.
        first = capture / pages[ASSETS[0]][0]["raw_path"]
        first.write_bytes(first.read_bytes() + b" ")
        try:
            bridge(capture, expected, root / "bad_raw")
        except ValueError as exc:
            assert "PAGE_SHA" in str(exc)
        else:
            raise AssertionError("V98_HANDOFF_ACCEPTED_RAW_PAGE_TAMPER")
        assert not (root / "bad_raw").exists()
        return {
            "decision": "PASS_V98_HANDOFF_SYNTHETIC_ONLY_NO_VENDOR_DATA",
            "fixture_events": 13524,
            "fixture_pages": 16,
            "negative_cases": 3,
            "real_mark_events_acquired": 0,
            "exchange_origin_attested": False,
            "pnl_computed": False,
        }

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--capture-dir", type=Path)
    p.add_argument("--expected-native", type=Path)
    p.add_argument("--output-dir", type=Path)
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args()
    if a.self_test:
        print(json.dumps(self_test(), sort_keys=True))
    else:
        if not all((a.capture_dir, a.expected_native, a.output_dir)):
            p.error("--capture-dir --expected-native --output-dir required")
        print(json.dumps(
            bridge(a.capture_dir, a.expected_native, a.output_dir), sort_keys=True
        ))

if __name__ == "__main__":
    main()
