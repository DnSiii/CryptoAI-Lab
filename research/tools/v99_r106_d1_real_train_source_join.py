"""D1 historical TRAIN join of ORIGINAL OKX receipts, never an economic backtest.

Downloads are performed by a read-only GitHub workflow. This program
independently verifies every original OHLC page and funding ZIP before joining
the exact 2021-12-09..2023-10-01 TRAIN grid. Missing/off-grid funding is
explicitly retained, never zero-filled, rounded, or forward-filled.
No orders, ROI, account fills, or validation/holdout access.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from research.verification.independent_d1_native_train_receipts import verify
from research.verification.independent_d1_okx_bulk_funding import check

START = int(datetime(2021, 12, 9, tzinfo=timezone.utc).timestamp() * 1000)
END = int(datetime(2023, 10, 1, tzinfo=timezone.utc).timestamp() * 1000)
HOUR = 3600000
EIGHT_HOURS = 8 * HOUR
HOURS = (END - START) // HOUR
PRICE_INST = ("BTC-USDT", "BTC-USDT-SWAP", "ETH-USDT", "ETH-USDT-SWAP")
FUND_INST = ("BTC-USDT-SWAP", "ETH-USDT-SWAP")
EXPECTED_SLOTS = tuple(range(START, END, EIGHT_HOURS))
NO_PROMOTION = {
    "historical_economic_trial_run": False,
    "native_fee_tier_authenticated": False,
    "actual_account_fills_authenticated": False,
    "actual_account_funding_cash_authenticated": False,
    "validation_opened": False,
    "holdout_opened": False,
    "paper_publication_authorized": False,
    "orders_enabled": False,
    "promotion_authorized": False,
}


def utc_iso(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()


def strict_json(path):
    def unique(pairs):
        d = {}
        for k, v in pairs:
            if k in d:
                raise ValueError("D1_DUPLICATE_JSON_KEY")
            d[k] = v
        return d
    return json.loads(path.read_bytes(), object_pairs_hook=unique)


def joined_train(price_root, funding_root, output_root):
    price_root, funding_root, output_root = map(Path, (price_root, funding_root, output_root))
    output_root.mkdir(parents=True, exist_ok=True)
    # Reparse original venue bytes independently, not just downloader manifests.
    price_proof = verify(price_root)
    funding_proof = check(funding_root)
    if price_proof["status"] != "INDEPENDENT_FOUR_LEG_TRAIN_SOURCE_COMPLETE_NO_ECONOMICS":
        raise ValueError("D1_PRICE_SOURCE_INCOMPLETE")
    if funding_proof["status"] != "INDEPENDENT_PARTIAL_FIRST_PARTY_FUNDING_NO_ECONOMICS":
        raise ValueError("D1_FUNDING_SOURCE_AUDIT_FAILED")

    opens = {}
    for inst in PRICE_INST:
        raw = strict_json(price_root / inst / "train_opens.json")
        if len(raw) != HOURS:
            raise ValueError("D1_PRICE_GRID_INCOMPLETE")
        stamps = [x["ts"] for x in raw]
        if stamps != list(range(START, END, HOUR)):
            raise ValueError("D1_PRICE_HOURLY_ALIGNMENT_FAILED")
        opens[inst] = [x["open"] for x in raw]

    rates, funding_audit = {}, {}
    expected = set(EXPECTED_SLOTS)
    for inst in FUND_INST:
        raw = strict_json(funding_root / inst / "funding_rows.json")
        timestamps = [x["settlement_ms"] for x in raw]
        if timestamps != sorted(set(timestamps)) or any(t < START or t >= END for t in timestamps):
            raise ValueError("D1_DUPLICATE_OR_SEALED_FUNDING")
        all_rates = {x["settlement_ms"]: x["venue_rate"] for x in raw}
        exact = {t: r for t, r in all_rates.items() if t in expected}
        missing = sorted(expected - set(exact))
        off_grid = sorted(set(all_rates) - expected)
        rates[inst] = exact
        funding_audit[inst] = {
            "raw_venue_settlements": len(raw),
            "expected_preregistered_exact_8h_slots": len(EXPECTED_SLOTS),
            "exact_8h_slots_matched": len(exact),
            "exact_8h_slots_missing": len(missing),
            "off_grid_original_settlements": len(off_grid),
            "first_missing_utc": utc_iso(missing[0]) if missing else None,
            "last_missing_utc": utc_iso(missing[-1]) if missing else None,
            "first_original_settlement_utc": utc_iso(timestamps[0]) if timestamps else None,
            "last_original_settlement_utc": utc_iso(timestamps[-1]) if timestamps else None,
            "missing_exact_slots_utc": [utc_iso(t) for t in missing],
            "off_grid_original_settlements_utc": [utc_iso(t) for t in off_grid],
        }

    # Source-joined data is *not* a trade simulation. Null funding means
    # UNKNOWN, not 0. Settlement at t is not available for a t-1 decision.
    sha = hashlib.sha256()
    joined_path = output_root / "train_joined_source_only.jsonl"
    with joined_path.open("wb") as stream:
        for i in range(HOURS):
            t = START + i * HOUR
            row = {
                "hour_ms": t,
                "market_open": {inst: opens[inst][i] for inst in PRICE_INST},
                "venue_settlement_at_hour_not_t_minus_1": {
                    inst: rates[inst].get(t) for inst in FUND_INST
                },
            }
            raw = (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
            sha.update(raw)
            stream.write(raw)

    missing_any = any(v["exact_8h_slots_missing"] or v["off_grid_original_settlements"]
                      for v in funding_audit.values())
    report = {
        "schema": "D1_REAL_TRAIN_SOURCE_JOIN_FAIL_CLOSED_V1",
        "status": "BLOCKED_MISSING_OR_OFF_GRID_FUNDING_AND_NATIVE_EXECUTION_EVIDENCE"
                  if missing_any else "BLOCKED_MISSING_NATIVE_EXECUTION_AND_FEE_EVIDENCE",
        "price_receipts_independently_verified": True,
        "funding_archives_independently_verified": True,
        "venue_publication_not_account_cash_receipt": True,
        "full_preregistered_train_start_utc": utc_iso(START),
        "full_preregistered_train_end_exclusive_utc": utc_iso(END),
        "joined_hours": HOURS,
        "joined_sha256": sha.hexdigest(),
        "price_instruments": list(PRICE_INST),
        "funding": funding_audit,
        "source_artifacts": {
            "price_run_id": 40019588739,
            "funding_run_id": 40019980953,
        },
        "independent_price_oracle": price_proof,
        "independent_funding_oracle": funding_proof,
        "economics_blockers": [
            "Missing preregistered 8-hour funding fixes, including 2021-12 to 2022-02",
            "Irregular published funding timestamps cannot be silently snapped to 8h",
            "No authenticated account-specific historical OKX fee tier validity",
            "No historical executed fills; must explicitly model fills and liquidation/margin",
        ],
        **NO_PROMOTION,
    }
    (output_root / "source_join_gate.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": report["status"], "joined_hours": HOURS,
        "sha256": report["joined_sha256"],
        "funding": {k: {field: v[field] for field in (
            "raw_venue_settlements", "exact_8h_slots_matched",
            "exact_8h_slots_missing", "off_grid_original_settlements",
            "first_missing_utc")} for k, v in funding_audit.items()},
        "historical_economic_trial_run": False,
        "promotion_authorized": False,
    }, sort_keys=True), flush=True)
    return report


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: python -m research.tools.v99_r106_d1_real_train_source_join PRICE_ROOT FUND_ROOT OUTPUT_ROOT")
    report = joined_train(*sys.argv[1:])
    # Expected fail-closed: price completeness alone cannot unlock economics.
    return 2 if report["status"].startswith("BLOCKED") else 0


if __name__ == "__main__":
    sys.exit(main())
