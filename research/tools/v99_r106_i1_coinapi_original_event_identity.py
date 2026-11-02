"""CoinAPI ORIGINAL 100ns OPEN/MARK event identity; source-only, NO ECONOMICS.

Requires the separate complete 661d original-byte oracle before public audit.
Never launders derived daily bytes into the Tardis/Deribit original manifest.
Prereg: V99_R106_I1_COINAPI_ORIGINAL_EVENT_IDENTITY_PREREG_20261102.md
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from research.tools.v99_r106_i1_coinapi_661d_original_byte_chain import verify as verify_chain
from research.tools.v99_r106_i1_coinapi_derived_day_bridge import (
    SCHEMA as SPEC_SCHEMA, _source,
)
from research.tools.v99_r106_i1_coinapi_quote_intake import (
    COLUMNS, SITE_UUID, _original_rows, nonnegative, ticks100ns,
)
from research.tools.v99_r106_i1_local_tape_import import FIRST, END
from research.tools.v99_r106_i1_original_event_quote_identity import (
    _equal, _requests,
)

SCHEMA = "V99_I1_COINAPI_ORIGINAL_100NS_EVENT_IDENTITY_V1"


def _safe(root, path):
    root, path = Path(root), Path(path)
    if (not path.is_file() or path.is_symlink()
            or not path.resolve().is_relative_to(root.resolve())):
        raise ValueError("UNSAFE_OR_MISSING_COINAPI_EVENT_SOURCE")
    return path


def audit_requests(spec_root, original_root, requests):
    """Replay ORIGINAL per-symbol rows, never the derived day, for exact requests.

    This helper is independently unit-tested on a small fixture. Public audit()
    additionally REQUIRES the entire 661-day original-byte chain first.
    """
    spec_root, original_root = Path(spec_root), Path(original_root)
    if (not spec_root.is_dir() or spec_root.is_symlink()
            or not original_root.is_dir() or original_root.is_symlink()
            or not isinstance(requests, dict) or not requests):
        raise ValueError("MISSING_COINAPI_EVENT_REQUESTS_OR_ROOT")
    wanted = defaultdict(lambda: defaultdict(list))
    for key, quote in requests.items():
        if (not isinstance(key, tuple) or len(key) != 3
                or type(key[0]) is not int or key[1] not in ("BTC", "ETH")
                or key[1] != quote.asset or key[2] != quote.symbol):
            raise ValueError("INVALID_COINAPI_EVENT_REQUEST")
        at, asset, symbol = key
        quote.check(at)
        day = datetime.fromtimestamp(at / 1000, timezone.utc).date()
        if not FIRST <= day < END:
            raise ValueError("COINAPI_EVENT_OUTSIDE_SEALED_TRAIN")
        for candidate_day in (day - timedelta(days=1), day):
            if FIRST <= candidate_day < END:
                wanted[candidate_day][symbol].append(key)

    best = {}
    files_checked = 0
    for day in sorted(wanted):
        spec_path = _safe(spec_root, spec_root / (day.isoformat() + ".json"))
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        if (not isinstance(spec, dict) or set(spec) != {"schema", "day", "sources"}
                or spec["schema"] != SPEC_SCHEMA or spec["day"] != day.isoformat()
                or not isinstance(spec["sources"], list)):
            raise ValueError("INVALID_COINAPI_EVENT_DAY_SPEC")
        for symbol, keys in wanted[day].items():
            matches = [item for item in spec["sources"]
                       if isinstance(item, dict) and item.get("symbol") == symbol]
            if len(matches) != 1:
                raise ValueError("MISSING_OR_DUPLICATED_COINAPI_ORIGINAL_CONTRACT")
            path, verified_symbol = _source(matches[0], day)
            _safe(original_root, path)
            if verified_symbol != symbol:
                raise ValueError("COINAPI_EVENT_SYMBOL_IDENTITY_MISMATCH")
            files_checked += 1
            ordered = sorted(set(keys))
            pointer = 0
            last = None
            previous_tick = -1
            rows = 0
            lower = int(datetime(day.year, day.month, day.day,
                                 tzinfo=timezone.utc).timestamp()) * 10_000_000
            upper = lower + 86400 * 10_000_000

            def record(key, candidate):
                if candidate is None:
                    return
                earlier = best.get(key)
                if earlier is None or candidate[0] > earlier[0]:
                    best[key] = candidate

            for raw, _delimiter in _original_rows(path):
                rows += 1
                if (raw.get(None) is not None
                        or any(raw.get(k) is None for k in COLUMNS)
                        or (raw["id_site_coinapi"]
                            and not SITE_UUID.fullmatch(raw["id_site_coinapi"]))):
                    raise ValueError("MALFORMED_ORIGINAL_COINAPI_EVENT_ROW")
                venue_tick = ticks100ns(raw["time_exchange"])
                arrival_tick = ticks100ns(raw["time_coinapi"])
                if (not lower <= arrival_tick < upper
                        or venue_tick > arrival_tick
                        or arrival_tick < previous_tick):
                    raise ValueError("NONCAUSAL_OR_OUT_OF_ORDER_COINAPI_EVENT")
                previous_tick = arrival_tick
                # Last receipt wins, INCLUDING zero-sided/crossed books.
                while (pointer < len(ordered)
                       and ordered[pointer][0] * 10_000 <= arrival_tick):
                    record(ordered[pointer], last)
                    pointer += 1
                bid, ask, bid_size, ask_size = (
                    nonnegative(raw[k]) for k in
                    ("bid_px", "ask_px", "bid_sx", "ask_sx"))
                venue_us = venue_tick // 10
                arrival_us = (arrival_tick + 9) // 10
                if arrival_us >= upper // 10:
                    raise ValueError("CEILED_COINAPI_EVENT_ARRIVAL_ESCAPES_DAY")
                mapped = {
                    "bid_price": str(bid), "ask_price": str(ask),
                    "bid_amount": str(bid_size), "ask_amount": str(ask_size),
                }
                last = (arrival_tick, (
                    arrival_us, day.toordinal(), rows, venue_us, mapped))
            if rows == 0:
                raise ValueError("EMPTY_ORIGINAL_COINAPI_EVENT_SOURCE")
            for key in ordered[pointer:]:
                record(key, last)
            # _source hashed original bytes before reading. Detect concurrent
            # changes, including a replacement between hash and EOF.
            _source(matches[0], day)

    for key, quote in requests.items():
        candidate = best.get(key)
        if candidate is None:
            raise ValueError("MISSING_ORIGINAL_COINAPI_LAST_ASOF_RECEIPT")
        _equal(quote, candidate[1], key[0])
    return {
        "schema": SCHEMA,
        "status": "COINAPI_ORIGINAL_100NS_BBO_EVENT_PARITY_ONLY",
        "original_event_quote_identities_checked": len(requests),
        "original_symbol_day_files_replayed": files_checked,
        "provider_100ns_last_arrival_verified": True,
        "derived_day_claimed_original": False,
        "native_quote_size_units_certified": False,
        "historical_native_fees_margin_delivery_certified": False,
        "original_exchange_fills_certified": False,
        "economic_train_executed": False,
        "promotion_authorized": False,
        "validation_opened": False, "holdout_opened": False,
        "orders_enabled": False,
    }


def audit(spec_root, original_root, derived_root, journal,
          *, license_document=None):
    """NONFIXTURE source-only public entry point; complete original chain first."""
    chain = verify_chain(spec_root, original_root, derived_root,
                         fixture=False, license_document=license_document)
    if chain["fixture"] is not False or chain["promotion_authorized"] is not False:
        raise ValueError("UNTRUSTED_COINAPI_ORIGINAL_CHAIN")
    result = audit_requests(spec_root, original_root, _requests(journal))
    result["original_661d_byte_chain_verified"] = True
    result["original_vendor_files_byte_replayed"] = (
        chain["original_vendor_files_byte_replayed"])
    result["original_venue_capture_completeness_certified"] = False
    result["signed_native_wallet_replayed"] = False
    return result


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("spec_root")
    p.add_argument("original_root")
    p.add_argument("derived_root")
    p.add_argument("nonfixture_journal_json")
    p.add_argument("--license-document", required=True)
    args = p.parse_args()
    journal = json.loads(Path(args.nonfixture_journal_json).read_text(encoding="utf-8"))
    print(json.dumps(audit(args.spec_root, args.original_root, args.derived_root,
                           journal, license_document=args.license_document),
                     sort_keys=True))
