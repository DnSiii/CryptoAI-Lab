from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
PUBLIC_API = os.environ.get(
    "BINANCE_FUTURES_PUBLIC_BASE", "https://fapi.binance.com"
).rstrip("/")
CONFIG_NAME = "research_pit48.json"
CORE_SYMBOLS = ("BTCUSDT", "ETHUSDT")
KLINE_COLUMNS = (
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_volume",
    "trades",
    "taker_buy_base",
    "taker_buy_quote",
    "ignore",
)
CANONICAL_COLUMNS = (
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "quote_volume",
    "trades",
)


def request_json(path: str, params: dict[str, object], attempts: int = 5) -> object:
    query = urllib.parse.urlencode(params)
    url = f"{PUBLIC_API}{path}?{query}"
    error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "CryptoAI-V13-paper-public-data/1.0"},
            )
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.loads(response.read())
        except (
            TimeoutError,
            ConnectionError,
            urllib.error.HTTPError,
            urllib.error.URLError,
        ) as exc:
            error = exc
            if isinstance(exc, urllib.error.HTTPError) and 400 <= exc.code < 500:
                break
            time.sleep(min(12.0, 1.5 * (2**attempt)))
    raise RuntimeError(f"falha na API pública {url}: {error}")


def utc_now() -> pd.Timestamp:
    return pd.Timestamp.now(tz="UTC")


def latest_closed_hour(now: pd.Timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(now)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return timestamp.floor("h") - pd.Timedelta(hours=1)


def write_csv_atomic(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False)
    temporary.replace(path)


def canonical_ready(symbols: tuple[str, ...]) -> bool:
    expected = [
        PROJECT / "data" / "canonical" / f"{symbol}_{suffix}.csv"
        for symbol in symbols
        for suffix in ("1h", "funding")
    ]
    return all(path.exists() and path.stat().st_size > 0 for path in expected)


def bootstrap_canonical() -> None:
    subprocess.run(
        [
            sys.executable,
            str(PROJECT / "scripts" / "download_futures_archive.py"),
            "--config",
            CONFIG_NAME,
            "--workers",
            "32",
        ],
        cwd=PROJECT,
        check=True,
    )
    sys.path.insert(0, str(PROJECT / "src"))
    from cryptoai_v13.data import build_canonical

    build_canonical(PROJECT, CONFIG_NAME)


def fetch_closed_klines(
    symbol: str, start: pd.Timestamp, end: pd.Timestamp, now: pd.Timestamp
) -> list[list[object]]:
    rows: list[list[object]] = []
    cursor = start
    now_ms = int(now.timestamp() * 1000)
    while cursor <= end:
        payload = request_json(
            "/fapi/v1/klines",
            {
                "symbol": symbol,
                "interval": "1h",
                "startTime": int(cursor.timestamp() * 1000),
                "endTime": int(end.timestamp() * 1000 + 3_599_999),
                "limit": 1500,
            },
        )
        if not isinstance(payload, list) or not payload:
            break
        accepted = [
            row
            for row in payload
            if len(row) >= 12 and int(row[6]) < now_ms
        ]
        rows.extend(accepted)
        next_cursor = pd.to_datetime(int(payload[-1][0]), unit="ms", utc=True) + pd.Timedelta(hours=1)
        if next_cursor <= cursor:
            raise RuntimeError(f"paginação de klines não avançou para {symbol}")
        cursor = next_cursor
        if len(payload) < 1500:
            break
    return rows


def append_klines(symbol: str, end: pd.Timestamp, now: pd.Timestamp) -> dict[str, object]:
    path = PROJECT / "data" / "canonical" / f"{symbol}_1h.csv"
    current = pd.read_csv(path)
    current["timestamp"] = pd.to_datetime(current["timestamp"], utc=True)
    original_count = len(current)
    previous_last = current["timestamp"].max()
    start = previous_last + pd.Timedelta(hours=1)
    rows = fetch_closed_klines(symbol, start, end, now) if start <= end else []
    if rows:
        incoming = pd.DataFrame(rows, columns=KLINE_COLUMNS)
        open_time = pd.to_numeric(incoming["open_time"], errors="raise")
        open_time = open_time.where(open_time <= 10**14, open_time // 1000)
        incoming["timestamp"] = pd.to_datetime(open_time, unit="ms", utc=True)
        for column in CANONICAL_COLUMNS[1:]:
            incoming[column] = pd.to_numeric(incoming[column], errors="raise")
        combined = pd.concat(
            [current[list(CANONICAL_COLUMNS)], incoming[list(CANONICAL_COLUMNS)]],
            ignore_index=True,
        )
        combined = combined.drop_duplicates("timestamp", keep="last").sort_values("timestamp")
        write_csv_atomic(combined, path)
        current = combined
    latest = pd.Timestamp(current["timestamp"].max())
    return {
        "previous_last": previous_last.isoformat(),
        "latest": latest.isoformat(),
        "rows_added": int(len(current) - original_count),
        "rows_received": len(rows),
        "fresh_through_closed_hour": bool(latest >= end),
    }


def fetch_funding(symbol: str, start_ms: int, end_ms: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    cursor = start_ms
    while cursor <= end_ms:
        payload = request_json(
            "/fapi/v1/fundingRate",
            {
                "symbol": symbol,
                "startTime": cursor,
                "endTime": end_ms,
                "limit": 1000,
            },
        )
        if not isinstance(payload, list) or not payload:
            break
        rows.extend(payload)
        next_cursor = int(payload[-1]["fundingTime"]) + 1
        if next_cursor <= cursor:
            raise RuntimeError(f"paginação de funding não avançou para {symbol}")
        cursor = next_cursor
        if len(payload) < 1000:
            break
    return rows


def append_funding(symbol: str, now: pd.Timestamp) -> dict[str, object]:
    path = PROJECT / "data" / "canonical" / f"{symbol}_funding.csv"
    current = pd.read_csv(path)
    if len(current):
        current["timestamp"] = pd.to_datetime(current["timestamp"], utc=True, format="mixed")
        previous_last = current["timestamp"].max()
        start_ms = int(previous_last.timestamp() * 1000) + 1
    else:
        previous_last = None
        start_ms = 0
    end_ms = int(now.timestamp() * 1000)
    payload = fetch_funding(symbol, start_ms, end_ms)
    if payload:
        incoming = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(
                    [int(row["fundingTime"]) for row in payload], unit="ms", utc=True
                ).floor("h"),
                "funding_rate": [float(row["fundingRate"]) for row in payload],
                "funding_interval_hours": 8.0,
            }
        )
        combined = pd.concat([current, incoming], ignore_index=True)
        combined = combined.drop_duplicates("timestamp", keep="last").sort_values("timestamp")
        write_csv_atomic(combined, path)
        current = combined
    latest = pd.Timestamp(current["timestamp"].max()) if len(current) else None
    return {
        "previous_last": previous_last.isoformat() if previous_last is not None else None,
        "latest": latest.isoformat() if latest is not None else None,
        "rows_added": len(payload),
    }


def sync_symbol(symbol: str, end: pd.Timestamp, now: pd.Timestamp) -> tuple[str, dict[str, object]]:
    return symbol, {
        "klines": append_klines(symbol, end, now),
        "funding": append_funding(symbol, now),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument(
        "--skip-bootstrap",
        action="store_true",
        help="falha se o cache canônico não estiver disponível",
    )
    args = parser.parse_args()
    config = json.loads((PROJECT / "config" / CONFIG_NAME).read_text())
    symbols = tuple(config["symbols"])
    bootstrapped = False
    if not canonical_ready(symbols):
        if args.skip_bootstrap:
            raise RuntimeError("cache canônico ausente e bootstrap foi desabilitado")
        bootstrap_canonical()
        bootstrapped = True

    now = utc_now()
    end = latest_closed_hour(now)
    results: dict[str, dict[str, object]] = {}
    errors: dict[str, str] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(sync_symbol, symbol, end, now): symbol for symbol in symbols}
        for future in concurrent.futures.as_completed(futures):
            symbol = futures[future]
            try:
                key, value = future.result()
                results[key] = value
            except Exception as exc:
                errors[symbol] = str(exc)

    core_stale = [
        symbol
        for symbol in CORE_SYMBOLS
        if symbol in errors
        or not results.get(symbol, {}).get("klines", {}).get(
            "fresh_through_closed_hour", False
        )
    ]
    manifest = {
        "mode": "PUBLIC_DATA_ONLY",
        "private_api_used": False,
        "generated_at_utc": now.isoformat(),
        "expected_latest_closed_hour": end.isoformat(),
        "bootstrapped": bootstrapped,
        "symbols": results,
        "errors": errors,
        "core_stale": core_stale,
    }
    output = PROJECT / "reports" / "paper_data_sync_v13.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))
    if core_stale:
        raise RuntimeError(f"dados centrais não estão atualizados: {core_stale}")


if __name__ == "__main__":
    main()
