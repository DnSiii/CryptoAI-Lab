from __future__ import annotations

import io
import re
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode
import xml.etree.ElementTree as ET

import pandas as pd
import requests

S3_LISTING_PREFIX = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
DOWNLOAD_PREFIX = "https://data.binance.vision"

_KLINE_COLUMNS = [
    "open_time", "open", "high", "low", "close", "volume", "close_time",
    "quote_volume", "trades", "taker_buy_base_volume", "taker_buy_quote_volume", "ignore",
]


@dataclass(frozen=True)
class SymbolArchive:
    symbol: str
    first_month: str | None
    last_month: str | None
    monthly_files: int

    @property
    def delisted(self) -> bool:
        return False if self.last_month is None else self.last_month < "2026-07"


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": "CryptoAI-Lab/0.1 research-only"})
    return s


def _s3_list(prefix: str, *, delimiter: str | None = "/", timeout: int = 30) -> tuple[list[str], list[str]]:
    """Return (common_prefixes, object_keys) from Binance Vision's S3-compatible listing."""
    session = _session()
    prefixes: list[str] = []
    keys: list[str] = []
    marker: str | None = None
    while True:
        params = {"prefix": prefix}
        if delimiter is not None:
            params["delimiter"] = delimiter
        if marker:
            params["marker"] = marker
        url = f"{S3_LISTING_PREFIX}?{urlencode(params)}"
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        root = ET.fromstring(response.text)
        ns = {"s3": root.tag.split("}")[0].strip("{")} if "}" in root.tag else {}

        def findall(path: str):
            return root.findall(path, ns) if ns else root.findall(path)

        for cp in findall("s3:CommonPrefixes" if ns else "CommonPrefixes"):
            node = cp.find("s3:Prefix", ns) if ns else cp.find("Prefix")
            if node is not None and node.text:
                prefixes.append(node.text)
        for obj in findall("s3:Contents" if ns else "Contents"):
            node = obj.find("s3:Key", ns) if ns else obj.find("Key")
            if node is not None and node.text:
                keys.append(node.text)
        trunc_node = root.find("s3:IsTruncated", ns) if ns else root.find("IsTruncated")
        truncated = trunc_node is not None and (trunc_node.text or "").lower() == "true"
        if not truncated:
            break
        next_node = root.find("s3:NextMarker", ns) if ns else root.find("NextMarker")
        if next_node is not None and next_node.text:
            marker = next_node.text
        elif prefixes:
            marker = prefixes[-1]
        elif keys:
            marker = keys[-1]
        else:
            break
    return prefixes, keys


def list_usdm_funding_symbols() -> list[str]:
    prefixes, _ = _s3_list("data/futures/um/monthly/fundingRate/")
    symbols = sorted({p.rstrip("/").split("/")[-1] for p in prefixes})
    return [s for s in symbols if s.endswith("USDT") and "_" not in s]


def inspect_symbol_archive(symbol: str) -> SymbolArchive:
    prefix = f"data/futures/um/monthly/fundingRate/{symbol}/"
    _, keys = _s3_list(prefix, delimiter=None)
    pattern = re.compile(rf"{re.escape(symbol)}-fundingRate-(\d{{4}}-\d{{2}})\.zip$")
    months = sorted(m.group(1) for key in keys if (m := pattern.search(key)))
    return SymbolArchive(symbol, months[0] if months else None, months[-1] if months else None, len(months))


def discover_archives(*, max_workers: int = 16) -> list[SymbolArchive]:
    symbols = list_usdm_funding_symbols()
    rows: list[SymbolArchive] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(inspect_symbol_archive, s): s for s in symbols}
        for fut in as_completed(futures):
            try:
                rows.append(fut.result())
            except Exception:
                continue
    return sorted(rows, key=lambda x: (x.first_month or "9999-99", x.symbol))


def _download_zip(url: str, cache_path: Path, *, retries: int = 3) -> bytes | None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists() and cache_path.stat().st_size > 0:
        return cache_path.read_bytes()
    session = _session()
    for attempt in range(retries):
        try:
            r = session.get(url, timeout=45)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            if not r.content.startswith(b"PK"):
                return None
            cache_path.write_bytes(r.content)
            return r.content
        except requests.RequestException:
            if attempt + 1 == retries:
                raise
            time.sleep(1.5 * (attempt + 1))
    return None


def _months(start: str, end: str) -> list[str]:
    start_p = pd.Period(pd.Timestamp(start), freq="M")
    end_p = pd.Period(pd.Timestamp(end), freq="M")
    return [str(p) for p in pd.period_range(start_p, end_p, freq="M")]


def _read_csv_from_zip(blob: bytes, header: bool | None = None) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not names:
            return pd.DataFrame()
        with zf.open(names[0]) as fh:
            if header is True:
                return pd.read_csv(fh)
            if header is False:
                return pd.read_csv(fh, header=None)
            raw = fh.read()
    first = raw.splitlines()[0].decode("utf-8", "ignore").lower() if raw else ""
    has_header = any(token in first for token in ("open_time", "calc_time", "funding", "symbol"))
    return pd.read_csv(io.BytesIO(raw), header=0 if has_header else None)


def load_klines(symbol: str, start: str, end: str, cache_dir: Path) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for month in _months(start, end):
        url = f"{DOWNLOAD_PREFIX}/data/futures/um/monthly/klines/{symbol}/1h/{symbol}-1h-{month}.zip"
        blob = _download_zip(url, cache_dir / "klines" / symbol / f"{month}.zip")
        if blob is None:
            continue
        df = _read_csv_from_zip(blob)
        if df.empty:
            continue
        if all(isinstance(c, int) for c in df.columns):
            df = df.iloc[:, : len(_KLINE_COLUMNS)]
            df.columns = _KLINE_COLUMNS[: len(df.columns)]
        else:
            df = df.rename(columns={c: str(c).strip().lower() for c in df.columns})
        needed = {"open_time", "open", "high", "low", "close"}
        if not needed.issubset(df.columns):
            continue
        frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    out = pd.concat(frames, ignore_index=True)
    ts = pd.to_numeric(out["open_time"], errors="coerce")
    unit = "us" if ts.dropna().median() > 10**14 else "ms"
    out.index = pd.to_datetime(ts, unit=unit, utc=True, errors="coerce")
    out = out[~out.index.isna()]
    for col in ("open", "high", "low", "close", "volume"):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    cols = [c for c in ("open", "high", "low", "close", "volume") if c in out.columns]
    out = out[cols].sort_index()
    out = out[~out.index.duplicated(keep="last")]
    return out.loc[pd.Timestamp(start, tz="UTC") : pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)]


def load_funding(symbol: str, start: str, end: str, cache_dir: Path) -> pd.Series:
    rows: list[pd.DataFrame] = []
    for month in _months(start, end):
        url = f"{DOWNLOAD_PREFIX}/data/futures/um/monthly/fundingRate/{symbol}/{symbol}-fundingRate-{month}.zip"
        blob = _download_zip(url, cache_dir / "funding" / symbol / f"{month}.zip")
        if blob is None:
            continue
        df = _read_csv_from_zip(blob)
        if not df.empty:
            rows.append(df)
    if not rows:
        return pd.Series(dtype=float, name=symbol)
    df = pd.concat(rows, ignore_index=True)
    df.columns = [str(c).strip().lower() for c in df.columns]
    time_col = next((c for c in df.columns if "calc_time" in c or "fundingtime" in c or c == "time"), None)
    rate_col = next((c for c in df.columns if "funding" in c and "rate" in c), None)
    if time_col is None or rate_col is None:
        if df.shape[1] >= 3:
            time_col, rate_col = df.columns[0], df.columns[-1]
        else:
            return pd.Series(dtype=float, name=symbol)
    ts = pd.to_numeric(df[time_col], errors="coerce")
    if ts.notna().mean() > 0.8:
        unit = "us" if ts.dropna().median() > 10**14 else "ms"
        idx = pd.to_datetime(ts, unit=unit, utc=True, errors="coerce")
    else:
        idx = pd.to_datetime(df[time_col], utc=True, errors="coerce")
    rates = pd.to_numeric(df[rate_col], errors="coerce")
    s = pd.Series(rates.to_numpy(), index=idx, name=symbol).dropna().sort_index()
    s = s[~s.index.duplicated(keep="last")]
    return s.loc[pd.Timestamp(start, tz="UTC") : pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)]
