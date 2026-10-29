"""Fixed 28–35d I1 first-party Deribit listed-pair feasibility; SOURCE ONLY.

Preregistered V99_R106_I1_FIXED_TENOR_FIRSTPARTY_LISTING_GATE_PREREG_20261028.md.
Does not imply historic tradability, bid/ask, fills, margin, ROI or promotion.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

from research.tools.v99_r106_i1_original_intent_binding import bind
from research.tools.v99_r106_i1_train_numeric_gate import _fold

LOW = 28 * 86_400_000
HIGH = 35 * 86_400_000
END = 1696118400000
SCHEMA = "V99_I1_FIRSTPARTY_FIXED_TENOR_LISTING_180_INTENTS_V1"


def run(registry_path, original_signal_path):
    original = bind(Path(original_signal_path))
    registry = json.loads(Path(registry_path).read_text())
    if (registry.get("schema") != "V99_I1_DERIBIT_HISTORICAL_INSTRUMENT_REGISTRY_V1"
            or registry.get("historical_executable_quotes_authenticated") is not False
            or set(registry.get("registry", {})) != {"BTC", "ETH"}):
        raise ValueError("UNVERIFIED_FIRSTPARTY_NATIVE_REGISTRY")
    rows = []
    folds = {str(i): {"positive": 0, "listed_pairs": 0,
                       "positive_and_listed": 0, "positive_without_listing": 0}
             for i in range(1, 6)}
    for intent in original["intents"]:
        ms, asset, fold = intent["decision_ms"], intent["asset"], intent["fold"]
        if fold != _fold(ms):
            raise ValueError("FIXED_FOLD_MISMATCH")
        strikes = defaultdict(set)
        for contract in registry["registry"][asset]:
            try:
                exp, created = (int(contract[k]) for k in
                                ("expiration_timestamp", "creation_timestamp"))
                if (created > ms or not LOW <= exp-ms <= HIGH or exp >= END
                        or contract["settlement_currency"] != asset):
                    continue
                if any(contract[k] is None or float(contract[k]) <= 0
                       for k in ("strike", "contract_size",
                                 "min_trade_amount", "tick_size")):
                    continue
                strikes[exp].add(float(contract["strike"]))
            except (TypeError, ValueError, KeyError) as exc:
                raise ValueError("MALFORMED_FIRSTPARTY_CONTRACT_TERMS") from exc
        max_strikes = max(map(len, strikes.values()), default=0)
        listed = max_strikes >= 2
        positive = intent["signal"] == "POSITIVE_EX_ANTE_PREMIUM"
        f = folds[str(fold)]
        f["positive"] += int(positive)
        f["listed_pairs"] += int(listed)
        f["positive_and_listed"] += int(positive and listed)
        f["positive_without_listing"] += int(positive and not listed)
        rows.append({"decision_ms": ms, "asset": asset, "fold": fold,
                     "signal": intent["signal"],
                     "max_same_expiry_native_put_strikes": max_strikes,
                     "native_listed_pair_necessary_only": listed,
                     "positive_signal_and_listed_pair": positive and listed})
    if len(rows) != 180:
        raise ValueError("MISSING_FIXED_TRAIN_INTENTS")
    no_positive_listed = [int(k) for k,v in folds.items()
                          if v["positive_and_listed"] == 0]
    return {
        "schema": SCHEMA,
        "status": ("STRUCTURALLY_REJECT_FIXED_I1_ZERO_POSITIVE_LISTING_FOLD"
                   if no_positive_listed else
                   "LISTING_NECESSARY_ONLY_ECONOMICS_UNVERIFIED"),
        "asset_week_intents": 180,
        "positive_intents": original["positive_fixed_intents"],
        "listed_pair_intents": sum(r["native_listed_pair_necessary_only"] for r in rows),
        "positive_and_listed_intents": sum(r["positive_signal_and_listed_pair"] for r in rows),
        "positive_without_listing": sum(
            r["signal"]=="POSITIVE_EX_ANTE_PREMIUM"
            and not r["native_listed_pair_necessary_only"] for r in rows),
        "zero_positive_listed_folds": no_positive_listed,
        "folds": folds, "rows": rows,
        "firstparty_registry_retrospective_not_asof_quote": True,
        "historical_option_lifecycles_certified": 0,
        "native_fee_margin_index_authenticated": False,
        "economic_train_executed": False,
        "roi_calculated": False,
        "validation_opened": False, "holdout_opened": False,
        "orders_enabled": False, "promotion_authorized": False,
    }


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_fixed_tenor_listing_gate REGISTRY_JSON ORIGINAL_SIGNAL_JSON OUTPUT_JSON")
    result = run(sys.argv[1], sys.argv[2])
    Path(sys.argv[3]).write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k != "rows"}, sort_keys=True))
