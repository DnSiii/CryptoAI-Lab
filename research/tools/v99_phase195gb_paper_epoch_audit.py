"""Read-only V99 R106 research paper epoch audit. Never publishes, retunes or promotes."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math

VARIANTS = ("r98", "f1", "f3", "f7", "f12")
FINANCIAL = ("gross_result_brl", "fees_brl", "funding_result_brl",
             "transfer_result_brl", "net_result_brl")
MAX_OPERATIONS = 1500

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")

def sha256(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def utc(value):
    if not isinstance(value, str):
        raise ValueError("explicit UTC timestamp required")
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None or stamp.utcoffset() != timedelta(0):
        raise ValueError("non-UTC timestamp")
    return stamp.astimezone(timezone.utc)

def ordered(rows, label, hourly=False):
    if not isinstance(rows, list) or not rows:
        raise ValueError(label + ": missing rows")
    stamps = []
    for row in rows:
        if not isinstance(row, dict) or "timestamp" not in row:
            raise ValueError(label + ": malformed row")
        t = utc(row["timestamp"])
        if hourly and (t.minute or t.second or t.microsecond):
            raise ValueError(label + ": off-hour timestamp")
        if stamps and (t <= stamps[-1] or (hourly and t-stamps[-1] != timedelta(hours=1))):
            raise ValueError(label + ": duplicate, unordered or gapped")
        canonical(row)
        stamps.append(t)
    return stamps

def audit(ledger, now_utc):
    """Audit durable published paper; output HOLD and evidence, never mutate it."""
    if not isinstance(ledger, dict) or ledger.get("mode") != "PAPER_ONLY" or ledger.get("real_orders_enabled") is not False:
        raise ValueError("paper-only/no-real-orders required")
    if ledger.get("same_boundary_for_all_variants") is not True:
        raise ValueError("shared boundary required")
    if set(ledger.get("variants", {})) != set(VARIANTS) or set(ledger.get("backtest_reference", {})) != set(VARIANTS):
        raise ValueError("all five preregistered variants required")
    boundary, latest, now = map(utc, (ledger["paper_start_after_timestamp"],
                                      ledger["latest_data_timestamp"], now_utc))
    if boundary > latest or now < latest:
        raise ValueError("invalid time ordering")
    issues, details, identities = {}, {}, {}
    for name in VARIANTS:
        variant, reference = ledger["variants"][name], ledger["backtest_reference"][name]
        if variant.get("real_orders_enabled") is not False:
            raise ValueError(name + ": real-order flag invalid")
        if utc(variant["paper_start_after_timestamp"]) != boundary:
            raise ValueError(name + ": variant boundary mismatch")
        curve = variant["equity_curve"]
        hours = ordered(curve, name + ": paper", hourly=True)
        if hours[0] != boundary or hours[-1] != latest:
            raise ValueError(name + ": paper interval mismatch")
        refs = ordered(reference["curve"], name + ": backtest")
        operations = variant.get("operations")
        if not isinstance(operations, list):
            raise ValueError(name + ": operations missing")
        seen, previous = set(), None
        for op in operations:
            t, sym = utc(op["timestamp"]), op.get("symbol")
            if not isinstance(sym, str) or not sym or t < boundary or t > latest or (previous and t < previous) or (t,sym) in seen:
                raise ValueError(name + ": invalid, duplicate or out-of-epoch operation")
            previous = t
            seen.add((t,sym))
        if not all(isinstance(x.get("equity_multiple"), (int,float)) and
                   math.isfinite(x["equity_multiple"]) and x["equity_multiple"] > 0 for x in curve):
            raise ValueError(name + ": invalid equity")
        overlap = sum(t >= boundary for t in refs)
        capped = len(operations) >= MAX_OPERATIONS
        incomplete = sum(not all(k in row for k in FINANCIAL) for row in curve)
        flags = []
        if overlap: flags.append("HISTORICAL_REFERENCE_CROSSES_PAPER_BOUNDARY")
        if capped: flags.append("OPERATIONS_CAPPED_UNVERIFIABLE")
        if incomplete: flags.append("CANONICAL_FINANCIAL_DECOMPOSITION_MISSING")
        issues[name] = flags
        identities.setdefault(sha256({"equity_curve":curve,"operations":operations}), []).append(name)
        details[name] = {"paper_hours_including_boundary":len(curve),
                         "last_utc":hours[-1].isoformat(),
                         "reference_points_after_boundary":overlap,
                         "operations":len(operations),"operations_capped":capped,
                         "missing_financial_component_rows":incomplete,
                         "paper_operations_sha256":sha256(operations),
                         "paper_curve_sha256":sha256(curve)}
    duplicates = [names for names in identities.values() if len(names)>1]
    for group in duplicates:
        for name in group:
            issues[name].append("FORWARD_DUPLICATE_OF_"+",".join(n for n in group if n!=name))
    return {"status":"DATA_ONLY/HOLD" if any(issues.values()) else "PAPER_PREFIX_ONLY_NOT_PROMOTION",
            "paper_epoch_version":ledger.get("version"),
            "immutable_published_ledger_sha256":sha256(ledger),
            "published_boundary_utc":boundary.isoformat(),
            "published_latest_utc":latest.isoformat(),
            "stale_hours_at_audit":(now-latest).total_seconds()/3600,
            "variants":details,"flags":issues,
            "distinct_forward_traces":len(identities),
            "forward_duplicate_groups":duplicates,
            "old_epoch_rewrite_authorized":False,
            "new_epoch_publication_authorized":False,
            "independent_receipts_authenticated":False,
            "canonical_pnl_authenticated":False,
            "holdout_accessed":False,"promotion_authorized":False}

def new_epoch_prereg(*, old_audit, epoch_id, first_new_utc,
                     first_receipt_utc=None, input_hash=None):
    """Quarantine-only manifest. Claimed receipts are NOT authentication."""
    if not isinstance(epoch_id,str) or not epoch_id.startswith("v99-r106-"):
        raise ValueError("versioned research epoch id required")
    old_last, new_first = utc(old_audit["published_latest_utc"]), utc(first_new_utc)
    if new_first.minute or new_first.second or new_first.microsecond or new_first <= old_last:
        raise ValueError("new epoch must start after immutable baseline at whole UTC hour")
    if not first_receipt_utc or not input_hash:
        return {"status":"QUARANTINE_NO_AUTHENTICATED_RECEIPT",
                "publication_authorized":False,"epoch_id":epoch_id,
                "old_baseline_sha256":old_audit["immutable_published_ledger_sha256"]}
    receipt = utc(first_receipt_utc)
    earliest = receipt.replace(minute=0,second=0,microsecond=0)+timedelta(hours=2)
    if new_first < earliest:
        raise ValueError("t-1 violation: decision before safe receipt close")
    if len(input_hash)!=64 or any(c not in "0123456789abcdef" for c in input_hash):
        raise ValueError("sha256 input hash required")
    return {"status":"QUARANTINE_AWAIT_INDEPENDENT_AUTHENTICATION",
            "publication_authorized":False,"promotion_authorized":False,
            "epoch_id":epoch_id,
            "old_baseline_sha256":old_audit["immutable_published_ledger_sha256"],
            "old_latest_utc":old_last.isoformat(),
            "first_new_decision_utc":new_first.isoformat(),
            "claimed_receipt_utc":receipt.isoformat(),
            "input_sha256":input_hash,
            "receipt_independently_authenticated":False,
            "warning":"No inherited ROI, backfill, holdout or promotion."}
