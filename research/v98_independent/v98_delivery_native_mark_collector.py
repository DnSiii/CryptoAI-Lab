#!/usr/bin/env python3
"""V98-only authorized-network capture of original USD-M fundingRate markPrice pages.

This is an evidence ACQUISITION utility, not an origin attestation, economic
backtest or paper/live engine. Only exposed 2022-2025 Clean-4 requests are made.
Requires network access where Binance USD-M API is legally reachable.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, parse_qs
from urllib.request import Request, build_opener, HTTPRedirectHandler

from v98_delivery_evidence_gate import (
    ASSETS, START, END, EXPECTED_COUNT, EIGHT_HOURS_MS,
    PINNED_EXPECTED_FUNDING_SHA256, expected_events, fail,
)
from v98_authorized_funding_mark_ingest import validate as independent_import

HOSTS = ("fapi.binance.com", "fapi1.binance.com")
MAX_PAGE = 1000


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def fetch_official(url, timeout=20):
    """Return HTTP response as original bytes, including original server Date."""
    opener = build_opener(NoRedirect)
    request = Request(url, headers={"Accept": "application/json",
                                    "User-Agent": "V98-Independent-Source-Custody/1"})
    try:
        with opener.open(request, timeout=timeout) as response:
            body = response.read()
            retrieved = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
            return int(response.status), {"Date": response.headers.get("Date", "")}, body, retrieved
    except HTTPError as exc:
        raise RuntimeError(f"BINANCE_HTTP_{exc.code}_HOST_{urlsplit(url).hostname}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"BINANCE_NETWORK_UNAVAILABLE_HOST_{urlsplit(url).hostname}") from exc


def _unique(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("DUPLICATE_EXCHANGE_JSON_KEY")
        obj[key] = value
    return obj


def _page(url, fetcher, timeout):
    last = None
    for attempt in range(3):
        try:
            status, headers, body, retrieved = fetcher(url, timeout)
            if type(status) is not int or status != 200:
                raise RuntimeError(f"BINANCE_HTTP_{status}_HOST_{urlsplit(url).hostname}")
            if not isinstance(body, bytes):
                raise ValueError("NON_BYTES_ORIGINAL_BODY")
            data = json.loads(body.decode("utf-8"), object_pairs_hook=_unique)
            if not isinstance(data, list) or not data or len(data) > MAX_PAGE:
                raise ValueError("OFFICIAL_PAGE_SHAPE")
            return headers, body, retrieved, data
        except RuntimeError as exc:
            last = exc
            # A legal/regional HTTP block is not transient and MUST NOT be
            # circumvented by switching hosts. Stop and request authorized export.
            if any(x in str(exc) for x in ("HTTP_451", "HTTP_403", "HTTP_418")):
                raise
            if attempt == 2:
                raise
            time.sleep(min(2 ** attempt, 4))
    raise last


def collect(expected_csv, expected_sha, output_dir, fetcher=fetch_official, timeout=20):
    """Capture and independently reconcile ALL pinned native events before publish.

    No output is published on a partial capture. The only published transport
    is authorized_funding_pages.jsonl, compatible with the V98 evidence gate.
    """
    expected = expected_events(expected_csv, expected_sha)
    if len(expected) != EXPECTED_COUNT:
        fail("COLLECTOR_EXPECTED_COUNT")
    output_dir = Path(output_dir)
    # Reject conflicting evidence BEFORE requesting historical pages. The
    # authorized exchange-origin CSV is a third mutually exclusive transport.
    # A symlinked directory could redirect private raw response bytes.
    if output_dir.is_symlink():
        raise ValueError("SYMLINKED_EVIDENCE_DIRECTORY")
    transport_names = (
        "authorized_funding_pages.jsonl",
        "native_pages_manifest.json",
        "authorized_exchange_export_manifest.json",
    )
    if any((output_dir / name).exists() or (output_dir / name).is_symlink()
           for name in transport_names):
        raise FileExistsError("EXISTING_NATIVE_EVIDENCE_MUST_NOT_BE_OVERWRITTEN")
    pages = []
    observed = set()
    for asset in ASSETS:
        cursor = START
        while cursor < END:
            response = None
            last_error = None
            for host in HOSTS:
                url = "https://" + host + "/fapi/v1/fundingRate?" + urlencode({
                    "symbol": asset, "startTime": cursor, "endTime": END - 1,
                    "limit": MAX_PAGE,
                })
                try:
                    headers, body, retrieved, rows = _page(url, fetcher, timeout)
                    response = (url, headers, body, retrieved, rows)
                    break
                except RuntimeError as exc:
                    last_error = exc
                    if "NETWORK_UNAVAILABLE" not in str(exc):
                        raise
            if response is None:
                raise RuntimeError("ALL_OFFICIAL_HOSTS_UNAVAILABLE_" + str(last_error))
            url, headers, body, retrieved, rows = response
            if not isinstance(headers, dict) or not headers.get("Date"):
                raise ValueError("MISSING_ORIGINAL_SERVER_DATE")
            previous = cursor - 1
            for row in rows:
                if not isinstance(row, dict) or row.get("symbol") != asset:
                    raise ValueError("NATIVE_SYMBOL_MISMATCH")
                ts = row.get("fundingTime")
                if type(ts) is not int or not cursor <= ts < END or ts <= previous:
                    raise ValueError("NATIVE_TIMESTAMP_OUT_OF_REQUEST_OR_ORDER")
                slot = START + (ts - START) // EIGHT_HOURS_MS * EIGHT_HOURS_MS
                if ts - slot > 60000 or (asset, slot) not in expected or (asset, slot) in observed:
                    raise ValueError("NATIVE_UNEXPECTED_OR_DUPLICATE_EVENT")
                if not {"fundingRate", "markPrice"}.issubset(row):
                    raise ValueError("NATIVE_MISSING_RATE_OR_MARK")
                observed.add((asset, slot))
                previous = ts
            pages.append({
                "url": url, "status": 200, "response_headers": headers,
                "retrieved_at_utc": retrieved, "response_body": body.decode("utf-8"),
                "response_body_sha256": hashlib.sha256(body).hexdigest(),
            })
            if len(rows) < MAX_PAGE:
                break
            cursor = previous + 1
    if observed != set(expected):
        raise ValueError(f"NATIVE_INCOMPLETE_{len(set(expected)-observed)}_MISSING")
    # Recheck after the network capture to catch a competing handoff.
    if output_dir.is_symlink():
        raise ValueError("SYMLINKED_EVIDENCE_DIRECTORY")
    if any((output_dir / name).exists() or (output_dir / name).is_symlink()
           for name in transport_names):
        raise FileExistsError("EXISTING_NATIVE_EVIDENCE_MUST_NOT_BE_OVERWRITTEN")
    final = output_dir / "authorized_funding_pages.jsonl"
    # Validate before creating the destination. A failed audit must not leave
    # an empty directory that looks like an attempted published capture.
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        raw = tmp / final.name
        raw.write_text("".join(json.dumps(p, separators=(",", ":")) + "\n" for p in pages), encoding="utf-8")
        receipt = independent_import(raw, expected_csv, tmp / "native_receipt.json")
        if receipt["records"] != len(expected):
            raise ValueError("INDEPENDENT_RECONCILIATION_COUNT")
        # Fail closed on an existing destination; publish the verified bytes
        # through an exclusive file create, never overwriting prior evidence.
        if output_dir.exists() and not output_dir.is_dir():
            raise FileExistsError("EVIDENCE_DESTINATION_NOT_DIRECTORY")
        output_dir.mkdir(parents=True, exist_ok=True)
        with final.open("x", encoding="utf-8") as handle:
            handle.write(raw.read_text(encoding="utf-8"))
        return {"decision": "CAPTURED_STRUCTURAL_ONLY_ORIGIN_UNATTESTED",
                "events": len(observed), "pages": len(pages),
                "raw_jsonl_sha256": hashlib.sha256(final.read_bytes()).hexdigest(),
                "source_receipt": receipt["decision"],
                "2026_training_accessed": False, "pnl_computed": False,
                "account_execution_costs_verified": False,
                "paper_or_live_authorized": False}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--expected-funding-csv", type=Path, required=True)
    p.add_argument("--expected-funding-sha256", required=True)
    p.add_argument("--evidence-dir", type=Path, required=True)
    p.add_argument("--timeout", type=int, default=20)
    args = p.parse_args()
    result = collect(args.expected_funding_csv, args.expected_funding_sha256,
                     args.evidence_dir, timeout=args.timeout)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
