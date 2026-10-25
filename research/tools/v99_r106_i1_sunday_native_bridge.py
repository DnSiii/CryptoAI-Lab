"""Join original TRAIN Sunday ticker samples to independently verified Deribit registry.

This is a provenance screen, NOT historical tradability, fill, fee or PnL.
"""
from __future__ import annotations
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from research.tools.v99_r106_i1_full_archive_intake import native_contracts, historical_price_grid_ok
from research.verification.independent_v99_r106_i1_sunday_ticker_oracle import verify


def screen(ticker_root, native_root, output):
    ticker_root, native_root = Path(ticker_root), Path(native_root)
    # Independently reparse original minute gzip; native_contracts independently
    # replays and SHA-checks first-party Deribit instrument response gzip.
    original_pairs = verify(ticker_root)
    native = native_contracts(native_root)
    ticker = json.loads((ticker_root/"report.json").read_text())
    rows = []
    for day in ticker["days"]:
        decision = datetime.fromisoformat(day["decision_utc"]).astimezone(timezone.utc)
        by_asset = {"BTC":{}, "ETH":{}}
        counters = {"no_native_asof":0,"offgrid":0,"valid":0}
        for book in day["last_eligible_books"]:
            asset = book["asset"]
            meta = native[asset].get(book["symbol"])
            expiry_ms = int(datetime.fromisoformat(book["expiry"]).timestamp()*1000)
            if (meta is None or meta["creation_timestamp"] > int(decision.timestamp()*1000)
                or meta["expiration_timestamp"] != expiry_ms
                or meta["settlement_currency"] != asset
                or float(meta["strike"]) != float(book["strike"])
                or any(meta[k] is None or float(meta[k]) <= 0 for k in
                       ("contract_size","min_trade_amount","tick_size"))):
                counters["no_native_asof"] += 1
                continue
            if not historical_price_grid_ok(meta, decision,
                                           book["bid_coin"],book["ask_coin"]):
                counters["offgrid"] += 1
                continue
            by_asset[asset].setdefault(book["expiry"],set()).add(book["strike"])
            counters["valid"] += 1
        pairs = {asset:any(len(strikes)>=2 for strikes in by_asset[asset].values())
                 for asset in ("BTC","ETH")}
        rows.append({"day":day["day"],"source_pairs":day["two_strike_pairs"],
                     "original_registry_asof_and_grid_pairs":pairs,
                     "native_filter":counters})
    result = {"schema":"V99_I1_ORIGINAL_SUNDAY_TICKER_NATIVE_LISTING_BRIDGE_V1",
        "ticker_report_sha256":hashlib.sha256((ticker_root/"report.json").read_bytes()).hexdigest(),
        "native_registry_sha256":hashlib.sha256((native_root/"native_instrument_registry.json").read_bytes()).hexdigest(),
        "ticker_original_bytes_independently_replayed":True,
        "first_party_instrument_bytes_independently_replayed":True,
        "source_asset_week_pairs":original_pairs,
        "native_asof_grid_pairs":sum(sum(x["original_registry_asof_and_grid_pairs"].values()) for x in rows),
        "days":rows, "full_train_required":182,
        "status":"TWO_SUNDAY_SAMPLES_NOT_COMPLETE_EXECUTABLE_ARCHIVE",
        "account_fee_tier_asof_certified":False,
        "native_lot_conversion_certified":False,
        "holding_period_liquidity_certified":False,
        "margin_liquidation_certified":False,
        "economic_train_executed":False,"validation_opened":False,"holdout_opened":False,
        "orders_enabled":False,"promotion_authorized":False}
    dest = Path(output)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"source_pairs":original_pairs,"native_asof_grid_pairs":result["native_asof_grid_pairs"],
                      "days":rows,"economic_train":False,"promotion":False}))
    return result


if __name__=="__main__":
    if len(sys.argv)!=4:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_sunday_native_bridge TICKER_DIR NATIVE_DIR OUTPUT")
    screen(*sys.argv[1:])
