from __future__ import annotations

import argparse
import concurrent.futures
import functools
import hashlib
import io
import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
PUBLIC_ARCHIVE = "https://data.binance.vision/data/futures/um/daily"
PUBLIC_KLINES_REST = "https://fapi.binance.com/fapi/v1/klines"
PUBLIC_KLINES_REST_FALLBACK = "https://www.binance.com/fapi/v1/klines"
PUBLIC_FUNDING_REST = "https://fapi.binance.com/fapi/v1/fundingRate"
PUBLIC_FUNDING_REST_FALLBACK = "https://www.binance.com/fapi/v1/fundingRate"
PAPER_SEED_ARCHIVE = PROJECT / "data" / "paper_seed_v13.zip"
CONFIG_NAME = "research_pit48.json"
CORE_SYMBOLS = ("BTCUSDT", "ETHUSDT")
MAX_PUBLICATION_LAG_HOURS = 48
MAX_FUNDING_LAG_HOURS = 12
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


def request_bytes(
    url: str,
    attempts: int = 5,
    missing_statuses: tuple[int, ...] = (404,),
) -> bytes | None:
    error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "CryptoAI-V13-paper-public-data/1.0"},
            )
            with urllib.request.urlopen(request, timeout=45) as response:
                return response.read()
        except (
            TimeoutError,
            ConnectionError,
            urllib.error.HTTPError,
            urllib.error.URLError,
        ) as exc:
            error = exc
            if (
                isinstance(exc, urllib.error.HTTPError)
                and exc.code in missing_statuses
            ):
                return None
            if isinstance(exc, urllib.error.HTTPError) and 400 <= exc.code < 500:
                break
            time.sleep(min(12.0, 1.5 * (2**attempt)))
    raise RuntimeError(f"falha no arquivo público {url}: {error}")


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


def last_csv_timestamp(path: Path) -> pd.Timestamp | None:
    if not path.exists() or path.stat().st_size == 0:
        return None
    with path.open("rb") as stream:
        stream.seek(max(0, path.stat().st_size - 4096))
        lines = [line for line in stream.read().splitlines() if line]
    if not lines:
        return None
    value = lines[-1].decode().split(",", 1)[0]
    if value == "timestamp":
        return None
    return pd.Timestamp(value)


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


@functools.cache
def paper_seed_names() -> frozenset[str]:
    if not PAPER_SEED_ARCHIVE.exists():
        return frozenset()
    with zipfile.ZipFile(PAPER_SEED_ARCHIVE) as archive:
        return frozenset(archive.namelist())


def read_paper_seed(name: str) -> pd.DataFrame:
    with zipfile.ZipFile(PAPER_SEED_ARCHIVE) as archive:
        with archive.open(name) as stream:
            return pd.read_csv(stream)


def merge_paper_seed(symbols: tuple[str, ...]) -> int:
    """Merge the compact, frozen post-July seed into a rebuilt/cache data set."""
    rows_added = 0
    seed_names = paper_seed_names()
    for symbol in symbols:
        for suffix in ("1h", "funding"):
            seed_name = f"{symbol}_{suffix}.csv"
            target_path = PROJECT / "data" / "canonical" / seed_name
            if seed_name not in seed_names or not target_path.exists():
                continue
            seed = read_paper_seed(seed_name)
            if seed.empty:
                continue
            seed_last = pd.to_datetime(
                seed["timestamp"], utc=True, format="mixed"
            ).max()
            current_last = last_csv_timestamp(target_path)
            if current_last is not None and current_last >= seed_last:
                continue
            current = pd.read_csv(target_path)
            before = len(current)
            combined = pd.concat([current, seed], ignore_index=True)
            combined["timestamp"] = pd.to_datetime(
                combined["timestamp"], utc=True, format="mixed"
            )
            combined = combined.drop_duplicates("timestamp", keep="last").sort_values(
                "timestamp"
            )
            write_csv_atomic(combined, target_path)
            rows_added += len(combined) - before
    return rows_added


def archive_url(kind: str, symbol: str, day: str) -> str:
    if kind == "klines":
        stem = f"{symbol}-1h-{day}"
        return f"{PUBLIC_ARCHIVE}/klines/{symbol}/1h/{stem}.zip"
    stem = f"{symbol}-fundingRate-{day}"
    return f"{PUBLIC_ARCHIVE}/fundingRate/{symbol}/{stem}.zip"


def verified_archive(url: str) -> bytes | None:
    payload = request_bytes(url)
    if payload is None:
        return None
    checksum_payload = request_bytes(url + ".CHECKSUM")
    if checksum_payload is None:
        raise RuntimeError(f"checksum ausente para {url}")
    expected = checksum_payload.decode().split()[0]
    actual = hashlib.sha256(payload).hexdigest()
    if actual != expected:
        raise RuntimeError(f"checksum inválido para {url}: {actual} != {expected}")
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        if archive.testzip() is not None:
            raise RuntimeError(f"CRC inválido em {url}")
    return payload


def archive_csv(payload: bytes, names: tuple[str, ...] | None = None) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(members) != 1:
            raise RuntimeError(f"esperado um CSV no arquivo, encontrados {members}")
        with archive.open(members[0]) as stream:
            return pd.read_csv(stream, names=names, header=None if names else "infer")


def public_klines_url(
    symbol: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    base_url: str = PUBLIC_KLINES_REST,
) -> str:
    query = urllib.parse.urlencode(
        {
            "symbol": symbol,
            "interval": "1h",
            "startTime": int(start.timestamp() * 1000),
            # Binance filters by candle open time. Including the final millisecond
            # lets the target hour through while the parser still rejects any
            # candle that has not fully closed.
            "endTime": int((end + pd.Timedelta("1h")).timestamp() * 1000) - 1,
            "limit": 1500,
        }
    )
    return f"{base_url}?{query}"


def request_public_klines(
    symbol: str, start: pd.Timestamp, end: pd.Timestamp
) -> tuple[bytes | None, str | None]:
    errors: list[str] = []
    for base_url in (PUBLIC_KLINES_REST, PUBLIC_KLINES_REST_FALLBACK):
        try:
            payload = request_bytes(
                public_klines_url(symbol, start, end, base_url),
                missing_statuses=(400, 404),
            )
            return payload, base_url
        except RuntimeError as exc:
            errors.append(str(exc))
    raise RuntimeError(
        f"candles públicos indisponíveis para {symbol}: {' | '.join(errors)}"
    )


def public_klines_frame(
    payload: bytes | None,
    latest_allowed_open: pd.Timestamp,
) -> pd.DataFrame:
    if not payload:
        return pd.DataFrame(columns=CANONICAL_COLUMNS)
    rows = json.loads(payload.decode())
    if not isinstance(rows, list):
        raise RuntimeError("resposta pública de candles não é uma lista")
    if not rows:
        return pd.DataFrame(columns=CANONICAL_COLUMNS)
    if any(
        not isinstance(row, list) or len(row) < len(KLINE_COLUMNS)
        for row in rows
    ):
        raise RuntimeError("resposta pública de candles sem campos obrigatórios")
    incoming = pd.DataFrame(rows, columns=KLINE_COLUMNS)
    incoming["timestamp"] = pd.to_datetime(
        pd.to_numeric(incoming["open_time"], errors="raise"),
        unit="ms",
        utc=True,
    )
    for column in CANONICAL_COLUMNS[1:]:
        incoming[column] = pd.to_numeric(incoming[column], errors="raise")
    latest_allowed = pd.Timestamp(latest_allowed_open)
    if latest_allowed.tzinfo is None:
        latest_allowed = latest_allowed.tz_localize("UTC")
    else:
        latest_allowed = latest_allowed.tz_convert("UTC")
    incoming = incoming.loc[incoming["timestamp"] <= latest_allowed]
    return (
        incoming[list(CANONICAL_COLUMNS)]
        .drop_duplicates("timestamp", keep="last")
        .sort_values("timestamp")
    )


def public_funding_url(
    symbol: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    base_url: str = PUBLIC_FUNDING_REST,
) -> str:
    query = urllib.parse.urlencode(
        {
            "symbol": symbol,
            "startTime": int(start.timestamp() * 1000),
            "endTime": int(end.timestamp() * 1000),
            "limit": 1000,
        }
    )
    return f"{base_url}?{query}"


def request_public_funding(
    symbol: str, start: pd.Timestamp, end: pd.Timestamp
) -> tuple[bytes | None, str | None]:
    errors: list[str] = []
    for base_url in (PUBLIC_FUNDING_REST, PUBLIC_FUNDING_REST_FALLBACK):
        try:
            payload = request_bytes(
                public_funding_url(symbol, start, end, base_url),
                missing_statuses=(400, 404),
            )
            return payload, base_url
        except RuntimeError as exc:
            errors.append(str(exc))
    raise RuntimeError(
        f"funding público indisponível para {symbol}: {' | '.join(errors)}"
    )


def public_funding_frame(payload: bytes | None) -> pd.DataFrame:
    columns = ["timestamp", "funding_rate", "funding_interval_hours"]
    if not payload:
        return pd.DataFrame(columns=columns)
    rows = json.loads(payload.decode())
    if not isinstance(rows, list):
        raise RuntimeError("resposta pública de funding não é uma lista")
    if not rows:
        return pd.DataFrame(columns=columns)
    incoming = pd.DataFrame(rows)
    required = {"fundingTime", "fundingRate"}
    if not required.issubset(incoming.columns):
        raise RuntimeError("resposta pública de funding sem campos obrigatórios")
    incoming["timestamp"] = pd.to_datetime(
        pd.to_numeric(incoming["fundingTime"], errors="raise"),
        unit="ms",
        utc=True,
    ).dt.floor("h")
    incoming["funding_rate"] = pd.to_numeric(
        incoming["fundingRate"], errors="raise"
    )
    incoming = incoming.sort_values("timestamp")
    backward = incoming["timestamp"].diff().dt.total_seconds().div(3600)
    forward = (
        incoming["timestamp"].shift(-1).sub(incoming["timestamp"])
        .dt.total_seconds()
        .div(3600)
    )
    incoming["funding_interval_hours"] = (
        backward.where(backward > 0)
        .fillna(forward.where(forward > 0))
        .fillna(8.0)
    )
    return incoming[columns].drop_duplicates("timestamp", keep="last")


def available_days(start: pd.Timestamp, now: pd.Timestamp) -> list[str]:
    first = start.floor("d")
    last = now.floor("d") - pd.Timedelta(days=1)
    if first > last:
        return []
    return [day.strftime("%Y-%m-%d") for day in pd.date_range(first, last, freq="d")]


def append_klines(
    symbol: str, now: pd.Timestamp, allow_daily_without_seed: bool = False
) -> dict[str, object]:
    path = PROJECT / "data" / "canonical" / f"{symbol}_1h.csv"
    current = pd.read_csv(path)
    current["timestamp"] = pd.to_datetime(current["timestamp"], utc=True)
    original_count = len(current)
    previous_last = current["timestamp"].max()
    frames: list[pd.DataFrame] = []
    archives_found = 0
    public_rest_records = 0
    public_rest_source = None
    days = available_days(previous_last, now) if (
        allow_daily_without_seed or f"{symbol}_1h.csv" in paper_seed_names()
    ) else []
    for day in days:
        payload = verified_archive(archive_url("klines", symbol, day))
        if payload is None:
            continue
        archives_found += 1
        incoming = archive_csv(payload, KLINE_COLUMNS)
        incoming = incoming.loc[incoming["open_time"].astype(str) != "open_time"].copy()
        open_time = pd.to_numeric(incoming["open_time"], errors="raise")
        open_time = open_time.where(open_time <= 10**14, open_time // 1000)
        incoming["timestamp"] = pd.to_datetime(open_time, unit="ms", utc=True)
        for column in CANONICAL_COLUMNS[1:]:
            incoming[column] = pd.to_numeric(incoming[column], errors="raise")
        frames.append(incoming[list(CANONICAL_COLUMNS)])
    latest_before_rest = max(
        [
            timestamp
            for timestamp in [
                previous_last,
                *(frame["timestamp"].max() for frame in frames if len(frame)),
            ]
            if timestamp is not None and pd.notna(timestamp)
        ]
    )
    rest_cursor = latest_before_rest + pd.Timedelta(hours=1)
    rest_end = latest_closed_hour(now)
    while rest_cursor <= rest_end:
        payload, public_rest_source = request_public_klines(
            symbol, rest_cursor, rest_end
        )
        rest_frame = public_klines_frame(payload, rest_end)
        rest_frame = rest_frame.loc[rest_frame["timestamp"] >= rest_cursor]
        if rest_frame.empty:
            break
        frames.append(rest_frame)
        public_rest_records += len(rest_frame)
        next_cursor = pd.Timestamp(rest_frame["timestamp"].max()) + pd.Timedelta(
            hours=1
        )
        if next_cursor <= rest_cursor:
            raise RuntimeError(f"paginação de candles não avançou para {symbol}")
        rest_cursor = next_cursor
    if frames:
        combined = pd.concat(
            [current[list(CANONICAL_COLUMNS)], *frames],
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
        "archives_found": archives_found,
        "public_rest_records": public_rest_records,
        "public_rest_source": public_rest_source,
    }


def append_funding(
    symbol: str, now: pd.Timestamp, allow_daily_without_seed: bool = False
) -> dict[str, object]:
    path = PROJECT / "data" / "canonical" / f"{symbol}_funding.csv"
    current = pd.read_csv(path)
    original_count = len(current)
    if len(current):
        current["timestamp"] = pd.to_datetime(current["timestamp"], utc=True, format="mixed")
        previous_last = current["timestamp"].max()
    else:
        previous_last = None
    start = previous_last if previous_last is not None else now.floor("d")
    frames: list[pd.DataFrame] = []
    archives_found = 0
    public_rest_records = 0
    public_rest_source = None
    days = available_days(start, now) if (
        allow_daily_without_seed or f"{symbol}_funding.csv" in paper_seed_names()
    ) else []
    for day in days:
        payload = verified_archive(archive_url("funding", symbol, day))
        if payload is None:
            continue
        archives_found += 1
        incoming = archive_csv(payload)
        incoming["calc_time"] = pd.to_numeric(incoming["calc_time"], errors="raise")
        incoming["timestamp"] = pd.to_datetime(
            incoming["calc_time"], unit="ms", utc=True
        ).dt.floor("h")
        incoming["funding_rate"] = pd.to_numeric(
            incoming["last_funding_rate"], errors="raise"
        )
        incoming["funding_interval_hours"] = pd.to_numeric(
            incoming["funding_interval_hours"], errors="raise"
        )
        frames.append(
            incoming[["timestamp", "funding_rate", "funding_interval_hours"]]
        )
    latest_before_rest = max(
        [
            timestamp
            for timestamp in [
                previous_last,
                *(frame["timestamp"].max() for frame in frames if len(frame)),
            ]
            if timestamp is not None and pd.notna(timestamp)
        ],
        default=None,
    )
    rest_start = (
        latest_before_rest + pd.Timedelta(milliseconds=1)
        if latest_before_rest is not None
        else now.floor("d")
    )
    rest_end = latest_closed_hour(now)
    if rest_start <= rest_end:
        payload, public_rest_source = request_public_funding(
            symbol, rest_start, rest_end
        )
        rest_frame = public_funding_frame(payload)
        public_rest_records = len(rest_frame)
        if len(rest_frame):
            frames.append(rest_frame)
    if frames:
        combined = pd.concat([current, *frames], ignore_index=True)
        combined = combined.drop_duplicates("timestamp", keep="last").sort_values("timestamp")
        write_csv_atomic(combined, path)
        current = combined
    latest = pd.Timestamp(current["timestamp"].max()) if len(current) else None
    return {
        "previous_last": previous_last.isoformat() if previous_last is not None else None,
        "latest": latest.isoformat() if latest is not None else None,
        "rows_added": int(len(current) - original_count),
        "archives_found": archives_found,
        "public_rest_records": public_rest_records,
        "public_rest_source": public_rest_source,
    }


def sync_symbol(
    symbol: str, now: pd.Timestamp, allow_daily_without_seed: bool = False
) -> tuple[str, dict[str, object]]:
    return symbol, {
        "klines": append_klines(symbol, now, allow_daily_without_seed),
        "funding": append_funding(symbol, now, allow_daily_without_seed),
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
    seed_rows_added = merge_paper_seed(symbols)

    now = utc_now()
    target = latest_closed_hour(now)
    results: dict[str, dict[str, object]] = {}
    errors: dict[str, str] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(sync_symbol, symbol, now): symbol for symbol in symbols}
        for future in concurrent.futures.as_completed(futures):
            symbol = futures[future]
            try:
                key, value = future.result()
                results[key] = value
            except Exception as exc:
                errors[symbol] = str(exc)

    core_latest = {
        symbol: pd.Timestamp(results[symbol]["klines"]["latest"])
        for symbol in CORE_SYMBOLS
        if symbol in results
    }
    source_available = min(core_latest.values()) if len(core_latest) == len(CORE_SYMBOLS) else None
    publication_lag_hours = (
        max(0, int((target - source_available).total_seconds() // 3600))
        if source_available is not None
        else None
    )
    core_stale = list(CORE_SYMBOLS) if (
        publication_lag_hours is None
        or publication_lag_hours > MAX_PUBLICATION_LAG_HOURS
    ) else []
    active_symbols = [
        symbol
        for symbol, item in results.items()
        if pd.Timestamp(item["klines"]["latest"]) >= target
        - pd.Timedelta(hours=MAX_PUBLICATION_LAG_HOURS)
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
    core_funding_stale = [
        symbol for symbol in CORE_SYMBOLS if symbol in funding_stale
    ]
    core_stale = sorted(set(core_stale) | set(core_funding_stale))
    manifest = {
        "mode": "PUBLIC_DATA_ONLY",
        "private_api_used": False,
        "source": [
            PUBLIC_ARCHIVE,
            PUBLIC_KLINES_REST,
            PUBLIC_KLINES_REST_FALLBACK,
            PUBLIC_FUNDING_REST,
            PUBLIC_FUNDING_REST_FALLBACK,
        ],
        "source_method": "OFFICIAL_ARCHIVES_PLUS_PUBLIC_CLOSED_KLINES_AND_FUNDING_REST",
        "generated_at_utc": now.isoformat(),
        "target_latest_closed_hour": target.isoformat(),
        "expected_latest_closed_hour": (
            source_available.isoformat() if source_available is not None else None
        ),
        "publication_lag_hours": publication_lag_hours,
        "maximum_publication_lag_hours": MAX_PUBLICATION_LAG_HOURS,
        "maximum_funding_lag_hours": MAX_FUNDING_LAG_HOURS,
        "funding_lag_hours": funding_lag_hours,
        "bootstrapped": bootstrapped,
        "seed_rows_added": seed_rows_added,
        "symbols": results,
        "errors": errors,
        "core_stale": core_stale,
        "funding_stale": funding_stale,
    }
    output = PROJECT / "reports" / "paper_data_sync_v13.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))
    # Missing funding for a core contract stops the paper.  Non-core contracts
    # are published in ``funding_stale`` and quarantined causally by the paper
    # runners, so one retired satellite contract cannot disable the whole lab.
    if core_stale:
        raise RuntimeError(
            "dados necessários não estão atualizados: "
            f"core={core_stale}, funding={funding_stale}"
        )


if __name__ == "__main__":
    main()
