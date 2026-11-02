"""Authenticated, bounded original CoinAPI QUOTES object acquisition (TRAIN only).

One explicitly selected historical S3 key at a time. A separate written
operator authorization is required before billable HEAD/GET. The output is
original compressed bytes, not an execution/fill/fee/economic attestation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

from research.tools.v99_r106_i1_coinapi_quote_intake import inspect, original_partition, SYMBOL
from research.tools.v99_r106_i1_coinapi_inventory_probe import ENDPOINT, BUCKET

SCHEMA = "V99_I1_COINAPI_AUTHENTICATED_ORIGINAL_OBJECT_V1"
MAX_OBJECT_BYTES = 2_147_483_648


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def acquire(source_key, symbol, output_root, *, license_document,
            license_sha256, authorize_billable_read=False,
            api_key=None, runner=subprocess.run, max_bytes=MAX_OBJECT_BYTES):
    """Acquire a single named original object; never enumerate/buy in bulk."""
    if (not isinstance(source_key, str) or not isinstance(symbol, str)
            or SYMBOL.fullmatch(symbol) is None):
        raise ValueError("INVALID_EXPLICIT_ORIGINAL_SYMBOL")
    original_partition(source_key, symbol)
    if type(max_bytes) is not int or not 0 < max_bytes <= MAX_OBJECT_BYTES:
        raise ValueError("INVALID_MAX_SOURCE_BYTES")
    if type(authorize_billable_read) is not bool:
        raise ValueError("INVALID_BILLABLE_AUTHORIZATION")
    license_file = Path(license_document)
    if (not license_file.is_file() or license_file.is_symlink()
            or not 0 < license_file.stat().st_size <= 4_000_000
            or not isinstance(license_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", license_sha256) is None
            or _sha256(license_file) != license_sha256):
        raise ValueError("MISSING_OR_CHANGED_WRITTEN_LICENSE_EVIDENCE")
    key = (os.getenv("COINAPI_API_KEY", "") if api_key is None else api_key)
    if not isinstance(key, str):
        raise ValueError("INVALID_PROVIDER_CREDENTIAL")
    report = {
        "schema": SCHEMA, "status": "BLOCKED_NO_COINAPI_API_KEY",
        "source_key": source_key, "symbol": symbol,
        "operator_license_document_sha256_not_legally_verified": license_sha256,
        "original_object_acquired": False,
        "original_quote_size_units_certified": False,
        "vendor_historical_capture_completeness_certified": False,
        "historical_native_fee_margin_delivery_certified": False,
        "economic_train_executed": False, "promotion_authorized": False,
        "validation_opened": False, "holdout_opened": False,
        "orders_enabled": False,
    }
    if not key.strip():
        return report
    if not authorize_billable_read:
        report["status"] = "BLOCKED_BILLABLE_PROVIDER_READ_NOT_AUTHORIZED"
        return report
    root = Path(output_root)
    if root.exists() and (root.is_symlink() or not root.is_dir()):
        raise ValueError("UNSAFE_OUTPUT_ROOT")
    root.mkdir(parents=True, exist_ok=True)
    name = hashlib.sha256(source_key.encode("utf-8")).hexdigest() + ".csv.gz"
    target, sidecar = root / name, root / (name + ".source.json")
    if target.exists() or target.is_symlink() or sidecar.exists() or sidecar.is_symlink():
        raise ValueError("REFUSE_OVERWRITE_ORIGINAL_SOURCE")
    env = os.environ.copy()
    env.update({
        "AWS_ACCESS_KEY_ID": key.strip(), "AWS_SECRET_ACCESS_KEY": "coinapi",
        "AWS_DEFAULT_REGION": "us-east-1", "AWS_EC2_METADATA_DISABLED": "true",
        "AWS_PAGER": "", "AWS_CLI_AUTO_PROMPT": "off",
    })
    base = ["aws", "s3api"]
    options = ["--endpoint-url", ENDPOINT, "--bucket", BUCKET,
               "--key", source_key, "--no-cli-pager", "--output", "json"]

    def execute(args):
        try:
            return runner(args, env=env, capture_output=True, text=True,
                          timeout=300, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ValueError("PROVIDER_OR_NETWORK_FAILURE_REDACTED") from exc

    head = execute(base + ["head-object"] + options)
    if head.returncode:
        report["status"] = "BLOCKED_PROVIDER_HEAD_OR_ENTITLEMENT"
        return report
    try:
        metadata = json.loads(head.stdout)
        length = metadata["ContentLength"]
    except (ValueError, TypeError, KeyError) as exc:
        raise ValueError("INVALID_ORIGINAL_PROVIDER_HEAD") from exc
    if type(length) is not int or length <= 0 or length > max_bytes:
        raise ValueError("UNKNOWN_EMPTY_OR_OVERSIZED_ORIGINAL_OBJECT")
    fd, temporary_name = tempfile.mkstemp(prefix=".coinapi-original-", suffix=".tmp", dir=root)
    os.close(fd)
    temporary = Path(temporary_name)
    side_temp = None
    try:
        get = execute(base + ["get-object"] + options + [str(temporary)])
        if get.returncode:
            report["status"] = "BLOCKED_PROVIDER_GET_OR_ENTITLEMENT"
            return report
        if temporary.stat().st_size != length:
            raise ValueError("PROVIDER_HEAD_GET_LENGTH_MISMATCH")
        inspected = inspect(temporary, venue="DERIBIT", symbol=symbol,
                            licensed=True, source_key=source_key)
        if inspected["original_bytes"] != length:
            raise ValueError("ORIGINAL_INTAKE_SIZE_MISMATCH")
        if _sha256(temporary) != inspected["original_sha256"]:
            raise ValueError("ORIGINAL_BYTES_CHANGED_AFTER_INTAKE")
        report.update({
            "status": "ORIGINAL_PROVIDER_OBJECT_FORMAT_VERIFIED_NOT_ECONOMICS",
            "original_object_acquired": True,
            "original_gzip_sha256": inspected["original_sha256"],
            "original_bytes": length,
            "original_rows": inspected["rows"],
            "original_executable_depth_rows_not_fills": inspected["two_sided_positive_depth_rows"],
            "provider_etag_not_sha256_attestation": metadata.get("ETag"),
            "local_original_filename": name,
        })
        fd2, side_temp_name = tempfile.mkstemp(prefix=".coinapi-original-meta-", suffix=".tmp", dir=root)
        side_temp = Path(side_temp_name)
        with os.fdopen(fd2, "w", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, target)
            try:
                os.link(side_temp, sidecar)
            except OSError:
                target.unlink()
                raise
        except FileExistsError as exc:
            raise ValueError("REFUSE_OVERWRITE_ORIGINAL_SOURCE") from exc
        return report
    finally:
        temporary.unlink(missing_ok=True)
        if side_temp is not None:
            side_temp.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Licensed original CoinAPI single-object acquisition; NO ORDERS")
    parser.add_argument("--source-key", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--license-document", required=True)
    parser.add_argument("--license-sha256", required=True)
    parser.add_argument("--authorize-billable-provider-read", action="store_true")
    args = parser.parse_args(argv)
    result = acquire(args.source_key, args.symbol, args.output_root,
                     license_document=args.license_document,
                     license_sha256=args.license_sha256,
                     authorize_billable_read=args.authorize_billable_provider_read)
    print(json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
