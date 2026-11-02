#!/usr/bin/env python3
"""V98-only preregistered native signed funding-carry source diagnostic.
This is NOT a strategy, executable edge, historical PnL or candidate selection.
"""
import csv
import hashlib
import io
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from datetime import datetime, timezone

ASSETS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")
START = 1735689600000
HOUR = 3600000
SLOT = 8 * HOUR
MONTHS = tuple("2025-%02d" % k for k in range(1, 13))
BUDGETS = (30, 50, 70)
RECEIPT_SHA = "7ce4ec7e2a6980838fa0179729b3cc6da8f131806b03e070590146d6d6ca046b"
FIELDS = ("asset", "funding_slot_ms", "funding_rate", "source_csv_sha256")
FILE = "v98_funding_carry_2025_source_events.csv"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def strict_decimal(raw):
    try:
        x = Decimal(raw)
    except (InvalidOperation, TypeError):
        raise ValueError("CARRY_RATE_DECIMAL")
    if not x.is_finite() or abs(x) > 1:
        raise ValueError("CARRY_RATE_RANGE")
    return x


def generate(nh_dir, out_dir):
    nh_dir = Path(nh_dir)
    out_dir = Path(out_dir)
    receipt_raw = (nh_dir / "nh_2025_official_source_receipt.json").read_bytes()
    if digest(receipt_raw) != RECEIPT_SHA:
        raise ValueError("CARRY_ORIGIN_RECEIPT_SHA")
    receipt = json.loads(receipt_raw)
    if receipt.get("decision") != "PASS_NH_2025_OFFICIAL_SOURCE_ONLY_NOT_VALIDATION":
        raise ValueError("CARRY_ORIGIN_DECISION")
    if set(receipt.get("assets", {})) != set(ASSETS):
        raise ValueError("CARRY_ORIGIN_UNIVERSE")
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(FIELDS)
    source_hashes = {}
    monthly = {}
    for asset in ASSETS:
        raw = (nh_dir / (asset + "_funding_2025.csv")).read_bytes()
        source_hashes[asset] = digest(raw)
        if source_hashes[asset] != receipt["assets"][asset]["funding_envelope_csv_sha256"]:
            raise ValueError("CARRY_FUNDING_CSV_SOURCE_SHA_" + asset)
        rows = csv.DictReader(io.StringIO(raw.decode("utf-8"), newline=""))
        required = {"funding_slot_ms", "funding_rate", "mark_lower_bound",
                    "mark_upper_bound", "exchange_offset_ms"}
        if not rows.fieldnames or not required.issubset(set(rows.fieldnames)):
            raise ValueError("CARRY_SOURCE_SCHEMA")
        sums = {month: Decimal(0) for month in MONTHS}
        counts = {month: 0 for month in MONTHS}
        n = 0
        for row in rows:
            if n >= 1095:
                raise ValueError("CARRY_TOO_MANY_EVENTS")
            ts = START + n * SLOT
            if int(row["funding_slot_ms"]) != ts:
                raise ValueError("CARRY_EVENT_CLOCK")
            offset = int(row["exchange_offset_ms"])
            if offset < 0 or offset > 60000:
                raise ValueError("CARRY_EVENT_OFFSET")
            # Mark values are prices, not rates.
            try:
                lower = Decimal(row["mark_lower_bound"])
                upper = Decimal(row["mark_upper_bound"])
            except InvalidOperation:
                raise ValueError("CARRY_MARK_DECIMAL")
            if not lower.is_finite() or not upper.is_finite() or lower <= 0 or upper < lower:
                raise ValueError("CARRY_MARK_ENVELOPE")
            rate = strict_decimal(row["funding_rate"])
            month = datetime.fromtimestamp(ts / 1000, timezone.utc).strftime("%Y-%m")
            if month not in sums:
                raise ValueError("CARRY_FUTURE_DATE")
            sums[month] += rate
            counts[month] += 1
            writer.writerow((asset, ts, row["funding_rate"], source_hashes[asset]))
            n += 1
        if n != 1095 or sum(counts.values()) != 1095:
            raise ValueError("CARRY_EVENT_COUNT")
        monthly[asset] = {
            m: {"events": counts[m], "signed_short_perp_funding_bps": str(sums[m] * 10000)}
            for m in MONTHS
        }
    raw = output.getvalue().encode("utf-8")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / FILE).write_bytes(raw)
    comparison = {}
    for budget in BUDGETS:
        comparison[str(budget)] = {
            "asset_months_signed_funding_above_budget": sum(
                Decimal(monthly[a][m]["signed_short_perp_funding_bps"]) > budget
                for a in ASSETS for m in MONTHS
            ),
            "asset_months_signed_funding_at_or_below_budget": sum(
                Decimal(monthly[a][m]["signed_short_perp_funding_bps"]) <= budget
                for a in ASSETS for m in MONTHS
            ),
        }
    return {
        "decision": "PASS_NATIVE_SIGNED_FUNDING_SOURCE_FEASIBILITY_NOT_PNL",
        "preregistration": "v98_funding_carry_source_prereg_20261101.md",
        "native_receipt_sha256": RECEIPT_SHA,
        "source_csv_sha256_by_asset": source_hashes,
        "canonical_event_csv": FILE,
        "canonical_event_sha256": digest(raw),
        "funding_events": 4380,
        "asset_months": 48,
        "months": list(MONTHS),
        "monthly": monthly,
        "fee_budgets_bps": list(BUDGETS),
        "fee_comparisons": comparison,
        "positive_signed_funding_months": sum(
            Decimal(monthly[a][m]["signed_short_perp_funding_bps"]) > 0
            for a in ASSETS for m in MONTHS
        ),
        "negative_signed_funding_months": sum(
            Decimal(monthly[a][m]["signed_short_perp_funding_bps"]) < 0
            for a in ASSETS for m in MONTHS
        ),
        "signed_funding_is_not_pnl": True,
        "basis_borrow_spread_slippage_collateral_excluded": True,
        "account_specific_fees_verified": False,
        "executable_edge_proven": False,
        "2025_exposed_training_only": True,
        "2026_plus_accessed": False,
        "holdout_accessed": False,
        "external_benchmarks_accessed": False,
        "candidate_promoted": False,
        "trading_authorized": False,
    }
