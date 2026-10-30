from __future__ import annotations

import concurrent.futures
import json
import sys
from pathlib import Path

import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.data import build_canonical
from download_futures_archive import Job, download, months
from sync_paper_data_v13 import (
    CORE_SYMBOLS,
    MAX_FUNDING_LAG_HOURS,
    MAX_PUBLICATION_LAG_HOURS,
    latest_closed_hour,
    request_bytes,
    sync_symbol,
    utc_now,
)


CONFIG_PATH = PROJECT / "config" / "candidate_v15_adaptive_capture.json"
BASE_CONFIG_PATH = PROJECT / "config" / "research_pit48.json"
UNIVERSE_STATE_PATH = PROJECT / "state" / "paper_v15_universe.json"
RUNTIME_CONFIG_PATH = PROJECT / "config" / "research_v15_runtime.json"
BOOTSTRAP_CONFIG_PATH = PROJECT / "config" / "research_v15_bootstrap_runtime.json"
SYNC_V13_PATH = PROJECT / "reports" / "paper_data_sync_v13.json"
REPORT_PATH = PROJECT / "reports" / "paper_data_sync_v15.json"


def request_json(urls: list[str]) -> tuple[object, str]:
    errors: list[str] = []
    for url in urls:
        try:
            payload = request_bytes(url, missing_statuses=(400, 404, 451))
            if payload is not None:
                return json.loads(payload.decode()), url
        except (RuntimeError, json.JSONDecodeError) as exc:
            errors.append(str(exc))
    raise RuntimeError("fontes públicas indisponíveis: " + " | ".join(errors))


def discover_symbols(
    exchange_info: dict,
    tickers: list[dict],
    now: pd.Timestamp,
    universe_config: dict,
) -> list[dict[str, object]]:
    ticker_by_symbol = {
        str(row.get("symbol")): row for row in tickers if row.get("symbol")
    }
    minimum_age = pd.Timedelta(
        f"{int(universe_config['minimum_contract_age_hours'])}h"
    )
    rows: list[dict[str, object]] = []
    for item in exchange_info.get("symbols", []):
        symbol = str(item.get("symbol", ""))
        if (
            item.get("quoteAsset") != universe_config["quote_asset"]
            or item.get("contractType") != universe_config["contract_type"]
            or item.get("status") != universe_config["status"]
            or symbol not in ticker_by_symbol
        ):
            continue
        onboard_raw = item.get("onboardDate")
        if onboard_raw is None:
            continue
        onboard = pd.Timestamp(int(onboard_raw), unit="ms", tz="UTC")
        if now - onboard < minimum_age:
            continue
        try:
            quote_volume = float(ticker_by_symbol[symbol].get("quoteVolume", 0.0))
        except (TypeError, ValueError):
            continue
        if quote_volume <= 0.0:
            continue
        rows.append(
            {
                "symbol": symbol,
                "onboard_date": onboard.isoformat(),
                "quote_volume_24h": quote_volume,
            }
        )
    rows.sort(key=lambda row: float(row["quote_volume_24h"]), reverse=True)
    return rows[: int(universe_config["discovery_top_n"])]


def month_shift(value: pd.Timestamp, months_back: int) -> str:
    year = value.year
    month = value.month - months_back
    while month <= 0:
        year -= 1
        month += 12
    return f"{year:04d}-{month:02d}"


def previous_month(value: pd.Timestamp) -> str:
    return month_shift(value, 1)


def canonical_ready(symbol: str) -> bool:
    root = PROJECT / "data" / "canonical"
    return all(
        (root / f"{symbol}_{suffix}.csv").exists()
        and (root / f"{symbol}_{suffix}.csv").stat().st_size > 0
        for suffix in ("1h", "funding")
    )


def bootstrap_symbol(symbol: str, start_month: str, end_month: str) -> None:
    jobs = [
        Job(kind, symbol, month)
        for month in months(start_month, end_month)
        for kind in ("klines", "fundingRate")
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(download, jobs))
    if not any(
        row["status"] in {"downloaded", "cached"}
        and row["job"]["kind"] == "klines"
        for row in results
    ):
        raise RuntimeError(f"sem histórico mensal para {symbol}")
    payload = {
        "cutoff_month": end_month,
        "interval": "1h",
        "market": "Binance USD-M perpetual futures",
        "source": "https://data.binance.vision",
        "symbols": {symbol: start_month},
    }
    BOOTSTRAP_CONFIG_PATH.write_text(json.dumps(payload, indent=2) + "\n")
    build_canonical(PROJECT, BOOTSTRAP_CONFIG_PATH.name)


def load_verified_boundary(now: pd.Timestamp) -> pd.Timestamp:
    if SYNC_V13_PATH.exists():
        report = json.loads(SYNC_V13_PATH.read_text())
        value = report.get("expected_latest_closed_hour")
        if value:
            return pd.Timestamp(value)
    return latest_closed_hour(now)


def main() -> None:
    candidate = json.loads(CONFIG_PATH.read_text())
    dynamic = candidate["dynamic_universe"]
    base = json.loads(BASE_CONFIG_PATH.read_text())
    now = utc_now()
    verified_boundary = load_verified_boundary(now)
    discovery_errors: list[str] = []
    discovery_sources: list[str] = []
    discovered: list[dict[str, object]] = []
    try:
        exchange_info, exchange_source = request_json(
            [
                dynamic["exchange_info_url"],
                dynamic["fallback_exchange_info_url"],
            ]
        )
        tickers, ticker_source = request_json(
            [dynamic["ticker_url"], dynamic["fallback_ticker_url"]]
        )
        if not isinstance(exchange_info, dict) or not isinstance(tickers, list):
            raise RuntimeError("formato inesperado na descoberta pública")
        discovered = discover_symbols(exchange_info, tickers, now, dynamic)
        discovery_sources = [exchange_source, ticker_source]
    except RuntimeError as exc:
        discovery_errors.append(str(exc))

    previous = (
        json.loads(UNIVERSE_STATE_PATH.read_text())
        if UNIVERSE_STATE_PATH.exists()
        else {}
    )
    persistent: dict[str, dict[str, object]] = dict(previous.get("symbols", {}))
    for symbol, start_month in base["symbols"].items():
        persistent.setdefault(
            symbol,
            {
                "source": "v14_legacy_universe",
                "start_month": start_month,
                "discovered_at_utc": None,
                "eligible_after_timestamp": f"{start_month}-01T00:00:00+00:00",
            },
        )
    new_symbols: list[str] = []
    for row in discovered:
        symbol = str(row["symbol"])
        if symbol in persistent:
            persistent[symbol]["latest_quote_volume_24h"] = row["quote_volume_24h"]
            continue
        onboard = pd.Timestamp(str(row["onboard_date"]))
        start_month = max(
            month_shift(now, int(dynamic["bootstrap_calendar_months"])),
            f"{onboard.year:04d}-{onboard.month:02d}",
        )
        persistent[symbol] = {
            "source": "dynamic_binance_discovery",
            "start_month": start_month,
            "onboard_date": row["onboard_date"],
            "discovered_at_utc": now.isoformat(),
            "eligible_after_timestamp": verified_boundary.isoformat(),
            "latest_quote_volume_24h": row["quote_volume_24h"],
        }
        new_symbols.append(symbol)

    bootstrap_errors: dict[str, str] = {}
    end_month = previous_month(now)
    for symbol, item in persistent.items():
        if canonical_ready(symbol):
            continue
        try:
            bootstrap_symbol(symbol, str(item["start_month"]), end_month)
        except Exception as exc:
            bootstrap_errors[symbol] = str(exc)

    ready_symbols = {
        symbol: str(item["start_month"])
        for symbol, item in persistent.items()
        if canonical_ready(symbol)
    }
    runtime_config = {
        "cutoff_month": end_month,
        "interval": "1h",
        "market": "Binance USD-M perpetual futures",
        "source": "official Binance public archives plus public futures discovery",
        "universe_rule": "persistent discovery plus point-in-time trailing liquidity",
        "symbols": ready_symbols,
    }
    RUNTIME_CONFIG_PATH.write_text(json.dumps(runtime_config, indent=2) + "\n")

    results: dict[str, dict[str, object]] = {}
    sync_errors: dict[str, str] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        futures = {
            pool.submit(sync_symbol, symbol, now, True): symbol
            for symbol in ready_symbols
        }
        for future in concurrent.futures.as_completed(futures):
            symbol = futures[future]
            try:
                key, value = future.result()
                results[key] = value
            except Exception as exc:
                sync_errors[symbol] = str(exc)

    target = latest_closed_hour(now)
    core_latest = {
        symbol: pd.Timestamp(results[symbol]["klines"]["latest"])
        for symbol in CORE_SYMBOLS
        if symbol in results
    }
    source_available = (
        min(core_latest.values()) if len(core_latest) == len(CORE_SYMBOLS) else None
    )
    publication_lag_hours = (
        max(0, int((target - source_available).total_seconds() // 3600))
        if source_available is not None
        else None
    )
    active_symbols = [
        symbol
        for symbol, item in results.items()
        if pd.Timestamp(item["klines"]["latest"])
        >= target - pd.Timedelta(hours=MAX_PUBLICATION_LAG_HOURS)
    ]
    funding_lag_hours = {
        symbol: (
            max(
                0,
                int(
                    (
                        target - pd.Timestamp(results[symbol]["funding"]["latest"])
                    ).total_seconds()
                    // 3600
                ),
            )
            if results[symbol]["funding"]["latest"] is not None
            else None
        )
        for symbol in active_symbols
    }
    funding_stale = [
        symbol
        for symbol, lag in funding_lag_hours.items()
        if lag is None or lag > MAX_FUNDING_LAG_HOURS
    ]
    universe_state = {
        "mode": "PUBLIC_DATA_ONLY",
        "candidate_version": candidate["version"],
        "updated_at_utc": now.isoformat(),
        "verified_boundary": verified_boundary.isoformat(),
        "symbols": persistent,
    }
    UNIVERSE_STATE_PATH.parent.mkdir(exist_ok=True)
    UNIVERSE_STATE_PATH.write_text(json.dumps(universe_state, indent=2) + "\n")
    report = {
        "mode": "PUBLIC_DATA_ONLY",
        "private_api_used": False,
        "candidate": candidate["name"],
        "generated_at_utc": now.isoformat(),
        "target_latest_closed_hour": target.isoformat(),
        "expected_latest_closed_hour": (
            source_available.isoformat() if source_available is not None else None
        ),
        "publication_lag_hours": publication_lag_hours,
        "maximum_publication_lag_hours": MAX_PUBLICATION_LAG_HOURS,
        "maximum_funding_lag_hours": MAX_FUNDING_LAG_HOURS,
        "discovery_sources": discovery_sources,
        "discovery_errors": discovery_errors,
        "discovery_top_n": dynamic["discovery_top_n"],
        "persistent_universe_size": len(persistent),
        "ready_universe_size": len(ready_symbols),
        "new_symbols": new_symbols,
        "bootstrap_errors": bootstrap_errors,
        "sync_errors": sync_errors,
        "symbols": results,
        "funding_lag_hours": funding_lag_hours,
        "funding_stale": funding_stale,
        "core_stale": (
            list(CORE_SYMBOLS)
            if publication_lag_hours is None
            or publication_lag_hours > MAX_PUBLICATION_LAG_HOURS
            else []
        ),
    }
    REPORT_PATH.parent.mkdir(exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if report["core_stale"]:
        raise RuntimeError("V15 sem dados atuais para BTC/ETH")


if __name__ == "__main__":
    main()
