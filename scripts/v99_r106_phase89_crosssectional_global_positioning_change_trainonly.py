#!/usr/bin/env python3
"""V99 R106 Phase89 — preregistered train-only cross-sectional global positioning change.

Research-only. Never reads holdout. No parameter search, sign flip, threshold search or rescue.
Signal is fixed by the Phase89 preregistration:
  x_{s,t}=log(global_ratio_{s,t}/global_ratio_{s,t-1}) using adjacent source hours only;
  at each simultaneous hour rank x cross-sectionally among symbols with valid data;
  raw target = -(percentile_rank - 0.5);
  normalize cross-sectionally to fixed gross exposure 0.20;
  execute the resulting target one hour later (causal t-1).

This file intentionally fails closed when required inputs are absent/ambiguous. It writes only
train-only evidence and never inspects or selects on final holdout observations.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Dict, Iterable, Tuple

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "evidence" / "v99_r106_phase89_crosssectional_global_positioning_change_trainonly.json"
GROSS = 0.20
MIN_ASSETS = 10
SEVERE_ONE_WAY_COST = 0.0010  # 10 bps per unit turnover; fixed severe research cost.
FOLDS = 4

# Candidate paths are discovery only, never selection. Exact column semantics are checked below.
CANDIDATE_FILES = [
    ROOT / "data" / "native" / "global_long_short_account_ratio_1h.csv",
    ROOT / "data" / "global_long_short_account_ratio_1h.csv",
    ROOT / "data" / "global_positioning_1h.csv",
]
PRICE_FILES = [
    ROOT / "data" / "native" / "ohlcv_1h.csv",
    ROOT / "data" / "ohlcv_1h.csv",
    ROOT / "data" / "prices_1h.csv",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def first_existing(paths: Iterable[Path]) -> Path:
    for p in paths:
        if p.exists():
            return p
    raise FileNotFoundError("required input not found: " + ", ".join(map(str, paths)))


def pick_col(df: pd.DataFrame, names: Iterable[str], label: str) -> str:
    low = {c.lower(): c for c in df.columns}
    hits = [low[n.lower()] for n in names if n.lower() in low]
    hits = list(dict.fromkeys(hits))
    if len(hits) != 1:
        raise ValueError(f"{label}: expected exactly one semantic column, got {hits}; columns={list(df.columns)}")
    return hits[0]


def load_long(path: Path, value_names: Iterable[str]) -> pd.DataFrame:
    df = pd.read_csv(path)
    ts = pick_col(df, ["timestamp", "open_time", "time", "datetime"], "timestamp")
    sym = pick_col(df, ["symbol", "asset", "ticker"], "symbol")
    val = pick_col(df, value_names, "value")
    out = df[[ts, sym, val]].copy()
    out.columns = ["timestamp", "symbol", "value"]
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True, errors="raise")
    out["symbol"] = out["symbol"].astype(str)
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    if out.duplicated(["timestamp", "symbol"]).any():
        raise ValueError(f"duplicate timestamp/symbol rows in {path}")
    return out.sort_values(["symbol", "timestamp"])


def metrics(r: pd.Series) -> Dict[str, float]:
    r = r.dropna().astype(float)
    eq = (1.0 + r).cumprod()
    roi = float(eq.iloc[-1] - 1.0) if len(eq) else float("nan")
    peak = eq.cummax()
    dd = float(((eq / peak) - 1.0).min()) if len(eq) else float("nan")
    gp = float(r[r > 0].sum())
    gl = float(-r[r < 0].sum())
    pf = gp / gl if gl > 0 else (float("inf") if gp > 0 else float("nan"))
    return {"n": int(len(r)), "roi": roi, "profit_factor": pf, "max_drawdown": dd, "mean": float(r.mean()) if len(r) else float("nan")}


def main() -> None:
    ratio_path = first_existing(CANDIDATE_FILES)
    price_path = first_existing(PRICE_FILES)
    ratio = load_long(ratio_path, ["long_short_ratio", "global_long_short_ratio", "ratio"])
    price = load_long(price_path, ["close", "close_price"])

    if (ratio["value"] <= 0).any():
        raise ValueError("global positioning ratio must be strictly positive")
    if (price["value"] <= 0).any():
        raise ValueError("close must be strictly positive")

    # Same-symbol adjacent-hour change only; gaps are invalid rather than silently bridged.
    ratio["prev_ts"] = ratio.groupby("symbol")["timestamp"].shift(1)
    ratio["prev"] = ratio.groupby("symbol")["value"].shift(1)
    adjacent = (ratio["timestamp"] - ratio["prev_ts"]) == pd.Timedelta(hours=1)
    ratio["x"] = np.where(adjacent, np.log(ratio["value"] / ratio["prev"]), np.nan)

    # Cross-sectional simultaneous ranking. Average ties is deterministic.
    ratio["n_cs"] = ratio.groupby("timestamp")["x"].transform("count")
    ratio["rank"] = ratio.groupby("timestamp")["x"].rank(method="average", pct=True)
    ratio["raw"] = np.where(ratio["n_cs"] >= MIN_ASSETS, -(ratio["rank"] - 0.5), np.nan)
    denom = ratio.groupby("timestamp")["raw"].transform(lambda s: s.abs().sum())
    ratio["target_t"] = np.where(denom > 0, GROSS * ratio["raw"] / denom, np.nan)

    # Explicit causal t-1 execution: target formed at t can only be held for t->t+1.
    ratio["exec_ts"] = ratio["timestamp"] + pd.Timedelta(hours=1)
    pos = ratio[["exec_ts", "symbol", "target_t"]].rename(columns={"exec_ts": "timestamp", "target_t": "weight"})

    price["next_ts"] = price.groupby("symbol")["timestamp"].shift(-1)
    price["next_close"] = price.groupby("symbol")["value"].shift(-1)
    price["ret_fwd"] = np.where(
        (price["next_ts"] - price["timestamp"]) == pd.Timedelta(hours=1),
        price["next_close"] / price["value"] - 1.0,
        np.nan,
    )
    m = pos.merge(price[["timestamp", "symbol", "ret_fwd"]], on=["timestamp", "symbol"], how="inner")
    m = m.dropna(subset=["weight", "ret_fwd"])
    if m.empty:
        raise ValueError("no aligned causal observations")

    # Train-only boundary is supplied by the existing research runtime. Fail closed if absent.
    train_end = os.environ.get("V99_TRAIN_END_UTC")
    holdout_start = os.environ.get("V99_HOLDOUT_START_UTC")
    if not train_end or not holdout_start:
        raise RuntimeError("V99_TRAIN_END_UTC and V99_HOLDOUT_START_UTC are mandatory; refusing implicit holdout access")
    train_end_ts = pd.Timestamp(train_end)
    holdout_ts = pd.Timestamp(holdout_start)
    if train_end_ts.tzinfo is None: train_end_ts = train_end_ts.tz_localize("UTC")
    if holdout_ts.tzinfo is None: holdout_ts = holdout_ts.tz_localize("UTC")
    if not train_end_ts < holdout_ts:
        raise ValueError("invalid train/holdout chronology")
    m = m[m["timestamp"] <= train_end_ts].copy()
    if (m["timestamp"] >= holdout_ts).any():
        raise AssertionError("holdout observation reached Phase89 train-only evaluator")

    # Portfolio return and turnover/cost are computed chronologically.
    wide = m.pivot(index="timestamp", columns="symbol", values="weight").fillna(0.0).sort_index()
    retw = m.pivot(index="timestamp", columns="symbol", values="ret_fwd").reindex_like(wide).fillna(0.0)
    gross_ret = (wide * retw).sum(axis=1)
    turnover = wide.diff().abs().sum(axis=1).fillna(wide.abs().sum(axis=1))
    net = gross_ret - SEVERE_ONE_WAY_COST * turnover

    # Temporal folds only; no random CV and no fold-driven tuning.
    chunks = np.array_split(np.arange(len(net)), FOLDS)
    folds = [metrics(net.iloc[idx]) for idx in chunks if len(idx)]
    healthy = sum(int(f["roi"] > 0 and f["profit_factor"] > 1.0) for f in folds)

    # Robust concentration diagnostic: remove top 1% hourly returns, not used to tune anything.
    cut = net.quantile(0.99)
    robust = net[net <= cut]
    report = {
        "phase": 89,
        "status": "TRAIN_ONLY_EVIDENCE",
        "hypothesis": "cross-sectional contrarian rank of adjacent-hour global positioning change",
        "causality": "feature at t; execution at t+1",
        "gross_exposure": GROSS,
        "min_assets": MIN_ASSETS,
        "severe_one_way_cost": SEVERE_ONE_WAY_COST,
        "train_end_utc": str(train_end_ts),
        "holdout_start_utc": str(holdout_ts),
        "holdout_rows_read": 0,
        "inputs": {
            "ratio": {"path": str(ratio_path.relative_to(ROOT)), "sha256": sha256(ratio_path)},
            "price": {"path": str(price_path.relative_to(ROOT)), "sha256": sha256(price_path)},
        },
        "overall": metrics(net),
        "robust_ex_top1pct": metrics(robust),
        "temporal_folds": folds,
        "healthy_folds": healthy,
        "anti_overfit": {"grid": False, "threshold_search": False, "sign_flip": False, "rescue": False},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
