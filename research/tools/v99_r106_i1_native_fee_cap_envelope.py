"""I1 original source native option fee-cap envelope. NO PNL OR EXECUTION.

A 2019 legacy example and dated 2020 public standard candidate, neither a certified 2021-2023 account fee
schedule. Uses real original quoted prices and first-party delivery index.
No native lot conversion, no model selection, no orders, no sealed data.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

SCHEMA = "V99_I1_ORIGINAL_NATIVE_FEE_CAP_ENVELOPE_V2"
FEE_EXAMPLES = {
    "published_2019_example": {
        "entry_per_unit": Decimal("0.0004"),
        "delivery_per_unit": Decimal("0.0002"),
        "cap_fraction": Decimal("0.20"),
    },
    "published_2020_standard_base_candidate": {
        "entry_per_unit": Decimal("0.0003"),
        "delivery_per_unit": Decimal("0.00015"),
        "cap_fraction": Decimal("0.125"),
    },
}
KEY = lambda x: (x["decision_utc"], x["short_symbol"], x["long_symbol"])


def D(x):
    value = Decimal(str(x))
    if not value.is_finite():
        raise ValueError("NONFINITE_ORIGINAL_VALUE")
    return value


def capped_fee(per_unit, fraction, coin_value):
    if coin_value < 0:
        raise ValueError("NEGATIVE_FEE_BASE")
    cap = fraction * coin_value
    return min(per_unit, cap), (coin_value > 0 and cap < per_unit)


def run(credit_path, terminal_path, output_path):
    cb = Path(credit_path).read_bytes()
    tb = Path(terminal_path).read_bytes()
    credit = json.loads(cb)
    terminal = json.loads(tb)
    if (credit.get("schema") != "V99_I1_ORIGINAL_ENTRY_UNIT_CREDIT_SCREEN_V1"
        or terminal.get("schema") != "V99_I1_ORIGINAL_QUOTE_DELIVERY_TERMINAL_DIAGNOSTIC_V1"
        or terminal.get("original_credit_sha256") != hashlib.sha256(cb).hexdigest()):
        raise ValueError("UNBOUND_ORIGINAL_SOURCE")
    if (credit.get("required_train_asset_weeks") != 182
        or credit.get("sample_asset_weeks_with_original_two_strike_books") != 4
        or terminal.get("certified_full_lifecycles") != 0
        or terminal.get("native_executable_pairs") != 0
        or len(credit.get("rows", [])) != len(terminal.get("rows", []))
        or len(credit["rows"]) != 46):
        raise ValueError("SOURCE_NOT_FIXED_SAMPLE")
    if any(credit.get(k) for k in ("economic_train_run", "orders_enabled", "promotion_authorized")):
        raise ValueError("FALSE_CREDIT_ECONOMICS")
    if any(terminal.get(k) for k in ("economic_train_run", "validation_opened",
                                   "holdout_opened", "orders_enabled",
                                   "promotion_authorized", "roi_calculated")):
        raise ValueError("FALSE_TERMINAL_ECONOMICS")
    terminal_by_key = {KEY(r): r for r in terminal["rows"]}
    if len(terminal_by_key) != 46 or len({KEY(r) for r in credit["rows"]}) != 46:
        raise ValueError("DUPLICATE_SOURCE_PAIR")
    output_rows = []
    counters = {s: {a: defaultdict(int) for a in ("BTC", "ETH")} for s in FEE_EXAMPLES}
    for row in credit["rows"]:
        terminal_row = terminal_by_key.get(KEY(row))
        if terminal_row is None or terminal_row["asset"] != row["asset"]:
            raise ValueError("SOURCE_PAIR_NOT_BOUND")
        asset = row["asset"]
        if asset not in ("BTC", "ETH"):
            raise ValueError("UNKNOWN_ASSET")
        high = D(row["short_strike_usd"])
        low = D(row["long_strike_usd"])
        settlement = D(terminal_row["delivery_index_usd"])
        short_bid = D(row["short_bid_coin"])
        long_ask = D(row["long_ask_coin"])
        if not (high > low > 0 and settlement > 0 and short_bid > 0 and long_ask > 0):
            raise ValueError("INVALID_NATIVE_SOURCE_VALUES")
        short_intrinsic = max(high - settlement, Decimal(0)) / settlement
        long_intrinsic = max(low - settlement, Decimal(0)) / settlement
        if (short_bid - long_ask != D(row["gross_credit_coin_per_source_unit_assumption"])
            or ((max(high - settlement, Decimal(0)) - max(low - settlement, Decimal(0))) / settlement)
               != D(terminal_row["intrinsic_coin_per_assumed_unit"])):
            raise ValueError("SOURCE_PAYOFF_MISMATCH")
        fees = {}
        for scenario, terms in FEE_EXAMPLES.items():
            cap = terms["cap_fraction"]
            short_entry, short_cap = capped_fee(terms["entry_per_unit"], cap, short_bid)
            long_entry, long_cap = capped_fee(terms["entry_per_unit"], cap, long_ask)
            short_delivery, short_dcap = capped_fee(terms["delivery_per_unit"], cap, short_intrinsic)
            long_delivery, long_dcap = capped_fee(terms["delivery_per_unit"], cap, long_intrinsic)
            fees[scenario] = {
                "short_entry_coin": str(short_entry),
                "long_entry_coin": str(long_entry),
                "short_delivery_coin": str(short_delivery),
                "long_delivery_coin": str(long_delivery),
                "total_entry_coin_per_assumed_unit": str(short_entry + long_entry),
                "total_delivery_coin_per_assumed_unit": str(short_delivery + long_delivery),
                "entry_cap_hit_legs": int(short_cap) + int(long_cap),
                "delivery_cap_hit_legs": int(short_dcap) + int(long_dcap),
            }
            counters[scenario][asset]["pairs"] += 1
            counters[scenario][asset]["entry_cap_hit_legs"] += int(short_cap) + int(long_cap)
            counters[scenario][asset]["delivery_cap_hit_legs"] += int(short_dcap) + int(long_dcap)
        output_rows.append({
            "decision_utc": row["decision_utc"], "expiry_utc": row["expiry_utc"],
            "asset": asset, "short_symbol": row["short_symbol"],
            "long_symbol": row["long_symbol"], "fees": fees,
            "historical_native_quantity": None, "historical_fill": False,
            "actual_account_fee": None,
        })
    result = {
        "schema": SCHEMA, "source_credit_sha256": hashlib.sha256(cb).hexdigest(),
        "source_terminal_sha256": hashlib.sha256(tb).hexdigest(),
        "source_pairs": 46, "sampled_asset_weeks": 4,
        "required_asset_weeks": 182, "certified_full_lifecycles": 0,
        "fee_examples": {
            name: {k: str(v) for k, v in values.items()}
            for name, values in FEE_EXAMPLES.items()
        },
        "rows": output_rows,
        "counts_by_asset_not_mixed_currency": {
            scenario: {asset: dict(counters[scenario][asset]) for asset in ("BTC", "ETH")}
            for scenario in FEE_EXAMPLES
        },
        "status": "DATED_2020_PUBLIC_STANDARD_BASE_CANDIDATE_HOLD",
        "public_base_rate_evidence": {
            "venue_announcement_date": "2020-08-12",
            "effective_utc": "2020-08-24T12:00:00Z",
            "btc_eth_option_base_rate": "0.0003",
            "venue_primary_url": "https://insights.deribit.com/exchange-updates/deribit-lowers-option-trading-fees-to-make-the-market-more-accessible-to-retail-traders/",
            "cap_and_delivery_reference": "secondary_2020_mirrored_exchange_information_not_authenticated_original",
            "cap_and_delivery_reference_url": "https://wikibitimg.fx994.com/attach/2020/10/938514373/WBE938514373_15464.pdf",
            "auto_vip_system_announced_2025_not_retroactive": True,
        },
        "historical_2021_2023_continuity_certified": False,
        "historical_actual_account_discount_certified": False,
        "historical_fee_tier_certified": False,
        "native_contract_quantity_certified": False,
        "economic_train_run": False, "roi_calculated": False,
        "validation_opened": False, "holdout_opened": False,
        "orders_enabled": False, "promotion_authorized": False,
    }
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"],
                      "pairs": 46,
                      "counts_by_asset": result["counts_by_asset_not_mixed_currency"],
                      "historical_fee_certified": False,
                      "promotion": False}, sort_keys=True))
    return result


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_native_fee_cap_envelope CREDIT TERMINAL OUTPUT")
    run(*sys.argv[1:])
