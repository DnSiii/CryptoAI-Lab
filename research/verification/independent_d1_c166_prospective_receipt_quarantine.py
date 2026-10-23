"""C166: independently quarantine prospective OKX receipts from sealed D1 TRAIN.

Read-only, source-only. Current first-party HTTP observations are NOT historical
account-native fees, executed fills, or settled funding cashflow. Never orders.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

TRAIN_END = datetime(2023, 10, 1, tzinfo=timezone.utc)
ASSETS = ("BTC", "ETH")
MARKET_SCHEMA = "V99_R106_OKX_PROSPECTIVE_ASOF_V1"
TERMS_SCHEMA = "V99_R106_OKX_NATIVE_TERMS_ASOF_V1"


def _utc(value):
    if type(value) is not str:
        raise ValueError("C166_MISSING_UTC")
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("C166_BAD_UTC") from exc
    if stamp.tzinfo is None or stamp.utcoffset().total_seconds() != 0:
        raise ValueError("C166_NON_UTC")
    return stamp


def _positive(value):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("C166_BAD_CONTRACT_QUANTITY") from exc
    if not number.is_finite() or number <= 0:
        raise ValueError("C166_NONPOSITIVE_CONTRACT_QUANTITY")
    return number


def _load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("C166_MISSING_OR_INVALID_RECEIPT") from exc


def _check_hash(folder, name, expected):
    if type(expected) is not str or len(expected) != 64:
        raise ValueError("C166_INVALID_SHA256")
    try:
        actual = hashlib.sha256((folder / name).read_bytes()).hexdigest()
    except OSError as exc:
        raise ValueError("C166_MISSING_RAW_RECEIPT") from exc
    if actual != expected:
        raise ValueError("C166_TAMPERED_RAW_RECEIPT")


def quarantine_prospective_receipts(market_folder, terms_folder):
    """Verify actual raw BTC/ETH receipt bytes, then DENY TRAIN use.

    A successful result certifies only internal raw-byte integrity and
    observation-time separation. It cannot authenticate account history.
    """
    market_folder, terms_folder = Path(market_folder), Path(terms_folder)
    market, terms = _load(market_folder / "manifest.json"), _load(terms_folder / "manifest.json")
    if (market.get("schema") != MARKET_SCHEMA or terms.get("schema") != TERMS_SCHEMA
            or market.get("provider") != "OKX" or terms.get("provider") != "OKX"):
        raise ValueError("C166_WRONG_SOURCE_SCHEMA")
    for document in (market, terms):
        if (document.get("mode") != "DATA_ONLY"
                or document.get("economic_trials") != 0
                or document.get("promotion_authorized") is not False
                or document.get("real_orders_enabled") is not False
                or document.get("paper_publication_authorized") is not False):
            raise ValueError("C166_UNAUTHORIZED_ECONOMIC_CLAIM")
    if (market.get("first_party_observation_only_not_venue_signed") is not True
            or terms.get("fee_schedule_independently_proven") is not False
            or terms.get("funding_cashflows_settled_and_pit_authenticated") is not False
            or terms.get("historical_first_seen_authenticated") is not False):
        raise ValueError("C166_MISREPRESENTED_PROVENANCE")
    market_time = _utc(market.get("first_received_utc"))
    terms_time = _utc(terms.get("acquisition_last_utc"))
    if market_time < TRAIN_END or terms_time < TRAIN_END:
        raise ValueError("C166_PROSPECTIVE_RECEIPT_BACKDATED")
    if (type(market.get("instruments")) is not dict
            or type(terms.get("contracts")) is not dict):
        raise ValueError("C166_MISSING_INSTRUMENTS")
    min_swap_base = {}
    for asset in ASSETS:
        inst = asset + "-USDT-SWAP"
        m = market["instruments"].get(inst)
        t = terms["contracts"].get(inst)
        if type(m) is not dict or type(t) is not dict:
            raise ValueError("C166_MISSING_BTC_ETH_SWAP")
        if (m.get("instrument") != inst or m.get("first_observed_now") is not True
                or type(m.get("confirmed_candles")) is not int
                or m["confirmed_candles"] < 1):
            raise ValueError("C166_UNVERIFIED_MARKET_OBSERVATION")
        latest = _utc(m.get("latest_confirmed_open_utc"))
        if latest < TRAIN_END or latest > _utc(m.get("received_utc")):
            raise ValueError("C166_MARKET_RECEIPT_TIME_TRAVEL")
        contract = t.get("contract")
        if (type(contract) is not dict or contract.get("instId") != inst
                or contract.get("ctType") != "linear"
                or contract.get("ctValCcy") != asset
                or contract.get("settleCcy") != "USDT"
                or contract.get("state") != "live"):
            raise ValueError("C166_INVALID_NATIVE_CONTRACT")
        notice = t.get("funding_notice")
        if (type(notice) is not dict or notice.get("instId") != inst
                or notice.get("settled_cashflow_authenticated") is not False):
            raise ValueError("C166_FUNDING_NOTICE_MISUSED_AS_SETTLEMENT")
        if (_utc(t.get("contract_received_utc")) < TRAIN_END
                or _utc(t.get("funding_received_utc")) < TRAIN_END):
            raise ValueError("C166_BACKDATED_NATIVE_TERMS")
        _check_hash(market_folder, inst + ".raw.json", m.get("source_raw_sha256"))
        _check_hash(terms_folder, "metadata_" + inst + ".raw.json",
                    t.get("contract_raw_sha256"))
        _check_hash(terms_folder, "funding_" + inst + ".raw.json",
                    t.get("funding_raw_sha256"))
        min_swap_base[asset] = str(_positive(contract.get("ctVal")) *
                                   _positive(contract.get("lotSz")))
    return {
        "status": "C166_CURRENT_FIRST_PARTY_BYTES_VERIFIED_TRAIN_QUARANTINED",
        "raw_receipts_sha256_verified": 6,
        "observed_2026_min_swap_base_by_asset_not_historical": min_swap_base,
        "missing_for_historical_train": [
            "15864h_four_leg_paired_historical_market_coverage",
            "asof_2021_2023_native_contract_and_spot_lots",
            "account_specific_historical_fee_tiers",
            "actual_settled_funding_cashflows",
            "real_execution_and_slippage_receipts",
        ],
        "train_market_economics_authorized": False,
        "exchange_account_history_authenticated": False,
        "validation_opened": False,
        "final_holdout_opened": False,
        "promotion_authorized": False,
        "orders_enabled": False,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipts-root", required=True)
    args = parser.parse_args()
    root = Path(args.receipts_root)
    markets = root / "receipts/v99_r106_okx"
    terms = root / "receipts/v99_r106_okx_terms"
    shared = sorted({p.name for p in markets.iterdir() if p.is_dir()} &
                    {p.name for p in terms.iterdir() if p.is_dir()})
    if not shared:
        raise ValueError("C166_NO_COMMON_HOURLY_RECEIPT")
    result = quarantine_prospective_receipts(markets / shared[-1], terms / shared[-1])
    print(json.dumps({"bucket": shared[-1], **result}, sort_keys=True))


if __name__ == "__main__":
    main()
