#!/usr/bin/env python3
"""Independent V98-only Decimal replay of signed native funding source feasibility.
Does not import the producer or any strategy/physical PnL engine.
"""
import copy
import csv
import hashlib
import io
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

ASSETS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")
MONTHS = tuple("2025-%02d" % m for m in range(1, 13))
FIELDS = ("asset", "funding_slot_ms", "funding_rate", "source_csv_sha256")
START = 1735689600000
SLOT = 28800000
BUDGETS = (30, 50, 70)
RECEIPT_SHA = "7ce4ec7e2a6980838fa0179729b3cc6da8f131806b03e070590146d6d6ca046b"


def audit(raw, receipt):
    if receipt.get("decision") != "PASS_NATIVE_SIGNED_FUNDING_SOURCE_FEASIBILITY_NOT_PNL":
        raise ValueError("CARRY_ORACLE_DECISION")
    if receipt.get("native_receipt_sha256") != RECEIPT_SHA:
        raise ValueError("CARRY_ORACLE_ORIGIN")
    if receipt.get("canonical_event_sha256") != hashlib.sha256(raw).hexdigest():
        raise ValueError("CARRY_ORACLE_HASH")
    if receipt.get("preregistration") != "v98_funding_carry_source_prereg_20261101.md":
        raise ValueError("CARRY_ORACLE_PREREG")
    for key in ("2026_plus_accessed", "holdout_accessed",
                "external_benchmarks_accessed", "candidate_promoted",
                "trading_authorized", "account_specific_fees_verified",
                "executable_edge_proven"):
        if receipt.get(key) is not False:
            raise ValueError("CARRY_ORACLE_FIREWALL")
    for key in ("signed_funding_is_not_pnl",
                "basis_borrow_spread_slippage_collateral_excluded",
                "2025_exposed_training_only"):
        if receipt.get(key) is not True:
            raise ValueError("CARRY_ORACLE_CAVEAT")
    if receipt.get("fee_budgets_bps") != list(BUDGETS) or receipt.get("months") != list(MONTHS):
        raise ValueError("CARRY_ORACLE_FIXED_SCOPE")
    hashes = receipt.get("source_csv_sha256_by_asset")
    if not isinstance(hashes, dict) or set(hashes) != set(ASSETS):
        raise ValueError("CARRY_ORACLE_SOURCE_ASSETS")
    if any(not isinstance(v, str) or len(v) != 64 or
           any(c not in "0123456789abcdef" for c in v) for v in hashes.values()):
        raise ValueError("CARRY_ORACLE_SOURCE_SHA_FORMAT")
    stream = io.StringIO(raw.decode("utf-8"), newline="")
    reader = csv.DictReader(stream)
    if tuple(reader.fieldnames or ()) != FIELDS:
        raise ValueError("CARRY_ORACLE_SCHEMA")
    sums = {a: {m: Decimal(0) for m in MONTHS} for a in ASSETS}
    counts = {a: {m: 0 for m in MONTHS} for a in ASSETS}
    index = 0
    for row in reader:
        if index >= 4380:
            raise ValueError("CARRY_ORACLE_EXCESS_EVENTS")
        a = ASSETS[index // 1095]
        k = index % 1095
        ts = START + k * SLOT
        if row["asset"] != a or int(row["funding_slot_ms"]) != ts:
            raise ValueError("CARRY_ORACLE_EVENT_ORDER")
        if row["source_csv_sha256"] != hashes[a]:
            raise ValueError("CARRY_ORACLE_EVENT_CUSTODY")
        try:
            rate = Decimal(row["funding_rate"])
        except InvalidOperation:
            raise ValueError("CARRY_ORACLE_RATE_PARSE")
        if not rate.is_finite() or abs(rate) > 1:
            raise ValueError("CARRY_ORACLE_RATE")
        month = datetime.fromtimestamp(ts / 1000, timezone.utc).strftime("%Y-%m")
        if month not in sums[a]:
            raise ValueError("CARRY_ORACLE_YEAR")
        sums[a][month] += rate
        counts[a][month] += 1
        index += 1
    if index != 4380 or receipt.get("funding_events") != 4380 or receipt.get("asset_months") != 48:
        raise ValueError("CARRY_ORACLE_EVENT_COUNT")
    monthly = receipt.get("monthly", {})
    if set(monthly) != set(ASSETS):
        raise ValueError("CARRY_ORACLE_MONTHLY_ASSETS")
    positive = negative = 0
    for a in ASSETS:
        if set(monthly[a]) != set(MONTHS):
            raise ValueError("CARRY_ORACLE_MONTHS")
        for m in MONTHS:
            expected = sums[a][m] * Decimal(10000)
            row = monthly[a][m]
            if row["events"] != counts[a][m] or Decimal(row["signed_short_perp_funding_bps"]) != expected:
                raise ValueError("CARRY_ORACLE_SIGNED_SUM")
            positive += expected > 0
            negative += expected < 0
    if receipt.get("positive_signed_funding_months") != positive or receipt.get("negative_signed_funding_months") != negative:
        raise ValueError("CARRY_ORACLE_SIGN_COUNTS")
    comparisons = receipt.get("fee_comparisons", {})
    if set(comparisons) != {str(x) for x in BUDGETS}:
        raise ValueError("CARRY_ORACLE_BUDGETS")
    for b in BUDGETS:
        above = sum(sums[a][m] * 10000 > b for a in ASSETS for m in MONTHS)
        row = comparisons[str(b)]
        if row != {
            "asset_months_signed_funding_above_budget": above,
            "asset_months_signed_funding_at_or_below_budget": 48 - above,
        }:
            raise ValueError("CARRY_ORACLE_BUDGET_ARITHMETIC")
    return {"decision": "PASS_INDEPENDENT_SIGNED_FUNDING_SOURCE_AUDIT_NOT_PNL",
            "events_replayed": index, "asset_months": 48,
            "positive_months": positive, "negative_months": negative,
            "fee_comparisons": comparisons, "candidate_promoted": False}


def tamper(raw, receipt):
    cases = []
    x = copy.deepcopy(receipt)
    x["monthly"][ASSETS[0]][MONTHS[0]]["signed_short_perp_funding_bps"] = "99999"
    cases.append((raw, x))
    x = copy.deepcopy(receipt)
    x["fee_comparisons"]["30"]["asset_months_signed_funding_above_budget"] += 1
    cases.append((raw, x))
    x = copy.deepcopy(receipt)
    x["trading_authorized"] = True
    cases.append((raw, x))
    rows = raw.decode("utf-8").splitlines(keepends=True)
    rows[1], rows[2] = rows[2], rows[1]
    altered = "".join(rows).encode("utf-8")
    x = copy.deepcopy(receipt)
    x["canonical_event_sha256"] = hashlib.sha256(altered).hexdigest()
    cases.append((altered, x))
    rejected = 0
    for b, r in cases:
        try:
            audit(b, r)
        except (ValueError, KeyError, TypeError):
            rejected += 1
        else:
            raise AssertionError("CARRY_ORACLE_TAMPER_ACCEPTED")
    return rejected
