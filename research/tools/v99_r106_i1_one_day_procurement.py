"""Select ONE ex-ante, paid, calendar-eligible I1 source sample; never PnL.

Preregistered in V99_R106_I1_ONE_DAY_CALENDAR_ELIGIBLE_PROCUREMENT_PREREG_20261029.md.
Original historical instrument listing is a NECESSARY, incomplete screen only.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from research.tools.v99_r106_i1_original_intent_binding import bind
from research.verification.independent_v99_r106_i1_historical_instruments import audit

DAY = 86_400_000
END = 1696118400000
SCHEMA = "V99_I1_SINGLE_PRESELECTED_PAID_SOURCE_DAY_V1"


def select(registry_root, original_signal_file):
    root = Path(registry_root)
    signal_path = Path(original_signal_file)
    # The primary cannot accept self-declared projections without the original
    # Deribit exchange gzip and independent original-byte parity audit.
    if audit(root) is not True:
        raise ValueError("ORIGINAL_DERIBIT_REGISTRY_NOT_VERIFIED")
    original = bind(signal_path)
    registry_path = root / "native_instrument_registry.json"
    registry_bytes = registry_path.read_bytes()
    registry = json.loads(registry_bytes)
    assert len(original["intents"]) == 180 and original["positive_fixed_intents"] == 132
    candidates = []
    for i in range(0, 180, 2):
        pair = original["intents"][i:i+2]
        assert [x["asset"] for x in pair] == ["BTC", "ETH"]
        ms = pair[0]["decision_ms"]
        assert pair[1]["decision_ms"] == ms and pair[1]["fold"] == pair[0]["fold"]
        monday = datetime.fromtimestamp(ms / 1000, timezone.utc)
        assert monday.weekday() == 0 and monday.hour == 0
        sunday = monday - timedelta(days=1)
        # Tardis first-of-month sample cannot be the paid proof.
        if sunday.day == 1:
            continue
        eligible_assets = []
        for intent in pair:
            if intent["signal"] != "POSITIVE_EX_ANTE_PREMIUM":
                continue
            by_expiry = defaultdict(list)
            for row in registry["registry"][intent["asset"]]:
                try:
                    exp, created = int(row["expiration_timestamp"]), int(row["creation_timestamp"])
                    if (created > ms or not 28*DAY <= exp-ms <= 35*DAY
                            or exp >= END or row["settlement_currency"] != intent["asset"]):
                        continue
                    if any(row[k] is None or float(row[k]) <= 0 for k in
                           ("strike", "contract_size", "min_trade_amount", "tick_size")):
                        continue
                    by_expiry[exp].append(row)
                except (TypeError, ValueError, KeyError) as exc:
                    raise ValueError("MALFORMED_ORIGINAL_CONTRACT") from exc
            possible = []
            for exp, rows in by_expiry.items():
                unique = {float(row["strike"]) for row in rows}
                if len(unique) >= 2:
                    possible.append((exp, -len(unique), sorted(
                        (row["instrument_name"] for row in rows))))
            if not possible:
                continue
            exp, _, symbols = min(possible)
            eligible_assets.append({
                "asset": intent["asset"], "fold": intent["fold"],
                "listed_expiry_utc": datetime.fromtimestamp(exp/1000,timezone.utc).isoformat(),
                "native_put_symbols_same_expiry": symbols,
                "retrospective_listed_pair_only": True,
            })
        if eligible_assets:
            candidates.append({
                "monday_decision_utc": monday.isoformat(),
                "sunday_source_date_utc": sunday.date().isoformat(),
                "fold": pair[0]["fold"], "assets": eligible_assets,
            })
    candidates.sort(key=lambda row: (-len(row["assets"]), row["monday_decision_utc"]))
    target = candidates[0] if candidates else None
    return {
        "schema": SCHEMA,
        "status": ("ONE_PRESELECTED_LICENSED_SAMPLE_REQUEST_NOT_RECEIVED"
                   if target else "NO_ELIGIBLE_TARGET_SOURCE_HOLD"),
        "target": target,
        "eligible_nonfree_mondays_count_audit_only": len(candidates),
        "original_signal_sha256": hashlib.sha256(signal_path.read_bytes()).hexdigest(),
        "original_registry_projection_sha256": hashlib.sha256(registry_bytes).hexdigest(),
        "source_registry_run": 40148052668,
        "source_signal_run": 40326586848,
        "source_license_received": False,
        "original_sunday_quotes_received": False,
        "original_executable_two_strike_books_certified": False,
        "historical_option_lifecycles_certified": 0,
        "historical_native_fee_tier_certified": False,
        "economic_train_executed": False,
        "roi_calculated": False,
        "validation_opened": False,
        "holdout_opened": False,
        "orders_enabled": False,
        "promotion_authorized": False,
    }


def main(root, signals, output):
    result = select(root, signals)
    Path(output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_one_day_procurement ROOT SIGNAL OUT")
    main(*sys.argv[1:])
