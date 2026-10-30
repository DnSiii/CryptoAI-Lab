from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


KLINE_COLUMNS = (
    "open_time", "open", "high", "low", "close", "volume", "close_time",
    "quote_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore",
)


@dataclass(frozen=True)
class FuturesData:
    frames: dict[str, pd.DataFrame]
    funding: pd.DataFrame
    symbols: tuple[str, ...]

    @property
    def close(self) -> pd.DataFrame:
        return self.frames["close"]


def _read_zip_csv(path: Path, names: tuple[str, ...] | None = None) -> pd.DataFrame:
    with zipfile.ZipFile(path) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(members) != 1:
            raise ValueError(f"{path}: esperado um CSV, encontrados {members}")
        with archive.open(members[0]) as stream:
            return pd.read_csv(stream, names=names, header=None if names else "infer")


def build_canonical(project: Path, config_name: str = "research.json") -> dict:
    config = json.loads((project / "config" / config_name).read_text())
    out = project / "data" / "canonical"
    out.mkdir(parents=True, exist_ok=True)
    manifest: dict = {"symbols": {}, "interval": "1h", "cutoff_month": config["cutoff_month"]}
    for symbol in config["symbols"]:
        kline_parts = []
        for path in sorted((project / "data" / "raw" / "klines" / symbol).glob("*.zip")):
            frame = _read_zip_csv(path, KLINE_COLUMNS)
            kline_parts.append(frame)
        if not kline_parts:
            raise FileNotFoundError(f"sem klines para {symbol}")
        klines = pd.concat(kline_parts, ignore_index=True)
        # Alguns arquivos recentes passaram a incluir cabeçalho, enquanto os
        # antigos não incluem. A leitura uniforme com nomes explícitos exige
        # remover essas linhas de cabeçalho intercaladas.
        klines = klines.loc[klines["open_time"].astype(str) != "open_time"].copy()
        klines["open_time"] = pd.to_numeric(klines["open_time"], errors="raise")
        # Os arquivos USD-M continuam em milissegundos; normalização defensiva.
        klines.loc[klines["open_time"] > 10**14, "open_time"] //= 1000
        klines["timestamp"] = pd.to_datetime(klines["open_time"], unit="ms", utc=True)
        numeric = ["open", "high", "low", "close", "volume", "quote_volume", "trades"]
        for column in numeric:
            klines[column] = pd.to_numeric(klines[column], errors="coerce")
        klines = klines.drop_duplicates("timestamp", keep="last").sort_values("timestamp")
        expected = pd.date_range(klines["timestamp"].iloc[0], klines["timestamp"].iloc[-1], freq="h", tz="UTC")
        missing_hours = expected.difference(pd.DatetimeIndex(klines["timestamp"]))
        keep = ["timestamp", "open", "high", "low", "close", "volume", "quote_volume", "trades"]
        kline_path = out / f"{symbol}_1h.csv"
        klines[keep].to_csv(kline_path, index=False)

        funding_parts = []
        for path in sorted((project / "data" / "raw" / "fundingRate" / symbol).glob("*.zip")):
            funding_parts.append(_read_zip_csv(path))
        funding = pd.concat(funding_parts, ignore_index=True) if funding_parts else pd.DataFrame()
        if funding.empty:
            funding = pd.DataFrame(columns=["timestamp", "funding_rate", "funding_interval_hours"])
        else:
            funding["calc_time"] = pd.to_numeric(funding["calc_time"], errors="raise")
            funding["timestamp"] = pd.to_datetime(funding["calc_time"], unit="ms", utc=True).dt.floor("h")
            funding["funding_rate"] = pd.to_numeric(funding["last_funding_rate"], errors="coerce")
            funding["funding_interval_hours"] = pd.to_numeric(funding["funding_interval_hours"], errors="coerce")
            funding = funding.drop_duplicates("timestamp", keep="last").sort_values("timestamp")
        funding_path = out / f"{symbol}_funding.csv"
        funding[["timestamp", "funding_rate", "funding_interval_hours"]].to_csv(funding_path, index=False)
        manifest["symbols"][symbol] = {
            "rows": int(len(klines)),
            "first": klines["timestamp"].iloc[0].isoformat(),
            "last": klines["timestamp"].iloc[-1].isoformat(),
            "funding_rows": int(len(funding)),
            "missing_hours": int(len(missing_hours)),
            "first_missing_hour": missing_hours[0].isoformat() if len(missing_hours) else None,
            "price_sha256": __import__("hashlib").sha256(kline_path.read_bytes()).hexdigest(),
            "funding_sha256": __import__("hashlib").sha256(funding_path.read_bytes()).hexdigest(),
        }
    stem = Path(config_name).stem.upper()
    suffix = "" if config_name == "research.json" else f"_{stem}"
    (project / "data" / f"CANONICAL_MANIFEST{suffix}.json").write_text(
        json.dumps(manifest, indent=2) + "\n")
    return manifest


def load_data(project: Path, config_name: str = "research.json") -> FuturesData:
    config = json.loads((project / "config" / config_name).read_text())
    symbols = tuple(config["symbols"])
    raw = {}
    funding_raw = {}
    for symbol in symbols:
        frame = pd.read_csv(project / "data" / "canonical" / f"{symbol}_1h.csv")
        frame.index = pd.to_datetime(frame.pop("timestamp"), utc=True)
        raw[symbol] = frame
        funds = pd.read_csv(project / "data" / "canonical" / f"{symbol}_funding.csv")
        if len(funds):
            funds.index = pd.to_datetime(funds.pop("timestamp"), utc=True, format="mixed")
            funding_raw[symbol] = funds["funding_rate"].astype(float)
        else:
            funding_raw[symbol] = pd.Series(dtype=float)
    start = min(frame.index.min() for frame in raw.values())
    end = max(frame.index.max() for frame in raw.values())
    index = pd.date_range(start, end, freq="h", tz="UTC")
    frames = {
        field: pd.DataFrame({symbol: raw[symbol][field].reindex(index) for symbol in symbols}, index=index)
        for field in ("open", "high", "low", "close", "volume", "quote_volume", "trades")
    }
    funding = pd.DataFrame({symbol: funding_raw[symbol].reindex(index).fillna(0.0) for symbol in symbols}, index=index)
    return FuturesData(frames=frames, funding=funding, symbols=symbols)


def point_in_time_liquid_view(data: FuturesData, top_n: int = 20,
                              lookback_hours: int = 24 * 30,
                              minimum_history_hours: int = 24 * 30) -> tuple[FuturesData, pd.DataFrame]:
    """Build a causal liquidity-filtered view and return its membership.

    Membership at close ``t`` uses quote volume only through ``t-1``. Signals
    computed from this view therefore cannot use the execution hour's volume.
    Delisted contracts remain in the source panel and can be selected while
    they were historically liquid.
    """
    quote_volume = data.frames["quote_volume"].where(data.close.notna())
    trailing = quote_volume.shift(1).rolling(
        lookback_hours, min_periods=min(lookback_hours, max(24 * 7, lookback_hours // 2))).mean()
    history = data.close.notna().shift(1).rolling(
        minimum_history_hours, min_periods=minimum_history_hours).sum()
    liquid_rank = trailing.rank(axis=1, ascending=False, method="first")
    membership = ((liquid_rank <= top_n)
                  & (history >= minimum_history_hours)
                  & data.close.notna())
    frames = {field: frame.where(membership) for field, frame in data.frames.items()}
    funding = data.funding.where(membership, 0.0)
    return FuturesData(frames=frames, funding=funding, symbols=data.symbols), membership


def validate_data(data: FuturesData) -> dict:
    errors = []
    symbols = {}
    for symbol in data.symbols:
        close = data.frames["close"][symbol].dropna()
        for field in ("open", "high", "low", "close"):
            values = data.frames[field][symbol].reindex(close.index)
            if values.isna().any() or not np.isfinite(values).all() or (values <= 0).any():
                errors.append(f"{symbol}: {field} inválido")
        opened = data.frames["open"][symbol].reindex(close.index)
        high = data.frames["high"][symbol].reindex(close.index)
        low = data.frames["low"][symbol].reindex(close.index)
        if (high < pd.concat([opened, close], axis=1).max(axis=1)).any():
            errors.append(f"{symbol}: máxima abaixo de open/close")
        if (low > pd.concat([opened, close], axis=1).min(axis=1)).any():
            errors.append(f"{symbol}: mínima acima de open/close")
        symbols[symbol] = {
            "rows": int(len(close)),
            "first": close.index[0].isoformat(),
            "last": close.index[-1].isoformat(),
            "funding_events": int((data.funding[symbol] != 0).sum()),
        }
    return {"errors": errors, "symbols": symbols}
