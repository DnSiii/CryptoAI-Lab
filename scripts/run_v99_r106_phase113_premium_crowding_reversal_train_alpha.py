# Phase113 frozen preregistered implementation; train-only execution.
from __future__ import annotations

import concurrent.futures
import csv
import datetime as dt
import hashlib
import io
import json
import time
import urllib.error
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase47_downside_semivariance_alpha_audit as p47
import run_v99_r105_all_regime_structural_audit as audit

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "reports" / "candidate_v99_r106_phase113_premium_crowding_reversal_train_alpha.json"
BASE = "https://data.binance.vision/data/futures/um"
INTERVAL = "1h"
ALPHA_GROSS = 0.20
ROLL_HOURS = 8


class MissingArchive(Exception):
    pass


def get(url: str) -> bytes:
    last = None
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CryptoAI-v99-r106-phase113"})
            with urllib.request.urlopen(req, timeout=90) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise MissingArchive(url) from exc
            last = exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last = exc
        time.sleep(2 ** attempt)
    raise last


def verified_zip(key: str) -> bytes:
    raw = get("https://data.binance.vision/" + key)
    checksum = get("https://data.binance.vision/" + key + ".CHECKSUM").decode().split()[0]
    if hashlib.sha256(raw).hexdigest() != checksum:
        raise RuntimeError("sha256 " + key)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"crc {key}: {bad}")
    return raw


def parse_premium_zip(raw: bytes, key: str, cutoff: pd.Timestamp) -> list[tuple[pd.Timestamp, float]]:
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        if len(names) != 1:
            raise RuntimeError(f"unexpected zip member count {key}: {len(names)}")
        rows = list(csv.reader(io.TextIOWrapper(archive.open(names[0]), encoding="utf-8-sig")))
    if rows and rows[0] and not rows[0][0].strip().lstrip("-").isdigit():
        rows = rows[1:]
    out = []
    last_ts = None
    for row in rows:
        if len(row) != 12:
            raise RuntimeError(f"kline row shape {key}: {len(row)}")
        try:
            ts = int(row[0])
            close = float(row[4])
        except (TypeError, ValueError) as exc:
            raise RuntimeError("parse " + key) from exc
        if not np.isfinite(close):
            raise RuntimeError("nonfinite premium close " + key)
        t = pd.Timestamp(ts, unit="ms", tz="UTC")
        if last_ts is not None and t <= last_ts:
            raise RuntimeError("nonmonotone/duplicate timestamp " + key)
        last_ts = t
        if t <= cutoff:
            out.append((t, close))
    return out


def daily_dates_for_month(first: dt.date, last: dt.date, missing: set[str], year: int, month: int) -> list[dt.date]:
    start = max(first, dt.date(year, month, 1))
    if month == 12:
        month_end = dt.date(year + 1, 1, 1) - dt.timedelta(days=1)
    else:
        month_end = dt.date(year, month + 1, 1) - dt.timedelta(days=1)
    end = min(last, month_end)
    if end < start:
        return []
    return [start + dt.timedelta(days=i) for i in range((end - start).days + 1)
            if (start + dt.timedelta(days=i)).isoformat() not in missing]


def load_symbol_month(job):
    symbol, year, month, dates, cutoff = job
    ym = f"{year:04d}-{month:02d}"
    monthly_key = f"data/futures/um/monthly/premiumIndexKlines/{symbol}/{INTERVAL}/{symbol}-{INTERVAL}-{ym}.zip"
    # Never request the January-2024 monthly archive: it contains post-train observations.
    if year < 2024:
        try:
            raw = verified_zip(monthly_key)
            rows = parse_premium_zip(raw, monthly_key, cutoff)
            return symbol, rows, {"monthly": 1, "daily": 0, "monthly_fallback": 0, "key": monthly_key}
        except MissingArchive:
            pass

    rows = []
    daily_count = 0
    for date in dates:
        key = f"data/futures/um/daily/premiumIndexKlines/{symbol}/{INTERVAL}/{symbol}-{INTERVAL}-{date.isoformat()}.zip"
        try:
            raw = verified_zip(key)
        except MissingArchive:
            # Phase112 explicitly accounts for missing daily archives; do not synthesize.
            continue
        rows.extend(parse_premium_zip(raw, key, cutoff))
        daily_count += 1
    return symbol, rows, {
        "monthly": 0,
        "daily": daily_count,
        "monthly_fallback": 1 if year < 2024 else 0,
        "key": f"{symbol}:{ym}",
    }


def robust_z(x: pd.DataFrame) -> pd.DataFrame:
    n = x.notna().sum(axis=1)
    med = x.median(axis=1)
    delta = x.sub(med, axis=0)
    mad = delta.abs().median(axis=1)
    valid = (n >= 10) & np.isfinite(mad) & (mad > 1e-12)
    return delta.div(mad.where(valid), axis=0).where(valid, np.nan)


def main():
    prereg = PROJECT / "research" / "v99_r106_phase113_premium_crowding_reversal_prereg.md"
    assert prereg.exists(), "Phase113 preregistration missing"

    phase112 = json.loads((PROJECT / "reports" / "candidate_v99_r106_phase112_premium_index_data_audit.json").read_text())
    assert phase112["status"] == "DATA_AUDIT_COMPLETE"
    assert phase112["holdout_not_listed_or_parsed"]
    assert phase112["alpha_prohibited"] and phase112["return_relation_computed"] is False

    cfg, data, raw, ex, guard, gross, quarantined, metadata = p1.r98.r36.v15_setup()
    train_end = pd.Timestamp(phase112["train_end"], tz="UTC")
    canonical_start = max(data.close.index[0], pd.Timestamp("2021-12-01", tz="UTC"))

    jobs = []
    for symbol in data.close.columns:
        info = phase112["symbols"].get(symbol)
        if not info or not info["first"]:
            continue
        first = max(dt.date.fromisoformat(info["first"]), canonical_start.date())
        last = min(dt.date.fromisoformat(info["last"]), train_end.date())
        if last < first:
            continue
        missing = set(info["missing_dates"])
        cursor = dt.date(first.year, first.month, 1)
        end_month = dt.date(last.year, last.month, 1)
        while cursor <= end_month:
            dates = daily_dates_for_month(first, last, missing, cursor.year, cursor.month)
            if dates:
                jobs.append((symbol, cursor.year, cursor.month, dates, train_end))
            if cursor.month == 12:
                cursor = dt.date(cursor.year + 1, 1, 1)
            else:
                cursor = dt.date(cursor.year, cursor.month + 1, 1)

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        loaded = list(pool.map(load_symbol_month, jobs))

    premium = pd.DataFrame(index=data.close.index, columns=data.close.columns, dtype=float)
    load_stats = defaultdict(int)
    for symbol, rows, stats in loaded:
        load_stats["monthly_archives"] += stats["monthly"]
        load_stats["daily_archives"] += stats["daily"]
        load_stats["monthly_fallbacks"] += stats["monthly_fallback"]
        if symbol not in premium.columns:
            continue
        for t, value in rows:
            if t in premium.index and canonical_start <= t <= train_end:
                premium.at[t, symbol] = value

    trailing = premium.rolling(ROLL_HOURS, min_periods=ROLL_HOURS).mean()
    z = robust_z(trailing)
    score = -z
    lagged = score.shift(1)
    bounded = np.tanh(lagged)
    bounded = bounded.where(lagged.notna().sum(axis=1) >= 10, 0).fillna(0)
    targets = bounded.div(bounded.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0)

    result = p1.run_targets(data, targets, ex, guard, float(ex["severe_cost_per_side"]), ALPHA_GROSS)
    diagnostic = p47.diag(result, data.close.index, canonical_start, train_end)
    passed = bool(diagnostic["stable_train"])

    observed = int(premium.loc[(premium.index >= canonical_start) & (premium.index <= train_end)].notna().sum().sum())
    active_signal_hours = int((targets.abs().sum(axis=1) > 0).loc[(targets.index >= canonical_start) & (targets.index <= train_end)].sum())

    out = {
        "study": "V99 R106 Phase113 — 8H PREMIUM-BASIS CROWDING REVERSAL TRAIN-ONLY alpha gate",
        "status": "TRAIN_ALPHA_PASS_FREEZE_FOR_DOWNSTREAM" if passed else "TRAIN_ALPHA_REJECT",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "precommitment": {
            "prereg": "research/v99_r106_phase113_premium_crowding_reversal_prereg.md",
            "source": "official Binance USD-M premiumIndexKlines 1h close",
            "feature": "trailing 8h simple mean premium close -> cross-sectional median/MAD robust z",
            "direction": "negative robust z (rich premium short, cheap premium long)",
            "causal_t_minus_1": True,
            "rolling_hours_fixed": ROLL_HOURS,
            "single_hypothesis_no_grid": True,
            "alpha_gross": ALPHA_GROSS,
            "cost_for_selection": "severe",
            "selection_train_only": True,
            "holdout_not_downloaded_or_parsed": True,
            "missing_data_not_filled": True,
            "min_crosssection_assets": 10,
            "tanh_then_l1": True,
        },
        "train_start": canonical_start.isoformat(),
        "train_end": train_end.isoformat(),
        "data_integrity": {
            "observed_symbol_hours": observed,
            "active_signal_hours": active_signal_hours,
            **dict(load_stats),
            "monthly_archive_latest_allowed": "2023-12",
            "january_2024_monthly_archive_requested": False,
            "checksums_and_zip_crc_verified": True,
        },
        "diagnostic": diagnostic,
        "selected_train_only": "premium_8h_crowding_reversal" if passed else None,
        "next_gate": "PASS freezes exact spec for supersevere/regime/benchmark/reproducibility before untouched holdout; FAIL permanent, no retuning.",
        "quarantined_symbols": quarantined,
    }
    OUT.write_text(json.dumps(out, indent=2, default=audit.safe_float) + "\n")
    print(json.dumps({
        "status": out["status"],
        "healthy_folds": diagnostic["healthy_folds"],
        "valid_folds": diagnostic["valid_folds"],
        "train": diagnostic["train"],
        "data_integrity": out["data_integrity"],
    }, indent=2, default=audit.safe_float))


if __name__ == "__main__":
    main()
