# Phase117 frozen preregistered implementation; train-only execution.
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
OUT = PROJECT / "reports" / "candidate_v99_r106_phase117_mark_index_dislocation_stress_train_alpha.json"
CDN = "https://data.binance.vision/"
INTERVAL = "1h"
ROLL_HOURS = 24
ALPHA_GROSS = 0.20
TRAIN_START = pd.Timestamp("2021-12-01T00:00:00Z")
TRAIN_END = pd.Timestamp("2024-01-18T00:00:00Z")


class MissingArchive(Exception):
    pass


def get(url: str) -> bytes:
    last = None
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CryptoAI-v99-r106-phase117"})
            with urllib.request.urlopen(req, timeout=120) as response:
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
    raw = get(CDN + key)
    want = get(CDN + key + ".CHECKSUM").decode().split()[0]
    if hashlib.sha256(raw).hexdigest() != want:
        raise RuntimeError("sha256 " + key)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"crc {key}: {bad}")
    return raw


def parse_close(raw: bytes, key: str) -> list[tuple[pd.Timestamp, float]]:
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        if len(names) != 1:
            raise RuntimeError(f"unexpected zip member count {key}: {len(names)}")
        rows = list(csv.reader(io.TextIOWrapper(archive.open(names[0]), encoding="utf-8-sig")))
    if rows and rows[0] and not rows[0][0].strip().lstrip("-").isdigit():
        rows = rows[1:]
    out = []
    last = None
    for row in rows:
        if len(row) != 12:
            raise RuntimeError(f"kline row shape {key}: {len(row)}")
        try:
            ts = int(row[0])
            close = float(row[4])
        except (TypeError, ValueError) as exc:
            raise RuntimeError("parse " + key) from exc
        if not np.isfinite(close) or close <= 0:
            raise RuntimeError("invalid close " + key)
        t = pd.Timestamp(ts, unit="ms", tz="UTC")
        if last is not None and t <= last:
            raise RuntimeError("nonmonotone/duplicate timestamp " + key)
        last = t
        if TRAIN_START <= t < TRAIN_END:
            out.append((t, close))
    return out


def paired_rows(mark_raw: bytes, mark_key: str, index_raw: bytes, index_key: str):
    m = parse_close(mark_raw, mark_key)
    i = parse_close(index_raw, index_key)
    if [x[0] for x in m] != [x[0] for x in i]:
        raise RuntimeError(f"mark/index timestamp misalignment: {mark_key} | {index_key}")
    return [(mt, mc, ic) for (mt, mc), (_, ic) in zip(m, i)]


def monthly_key(kind: str, symbol: str, year: int, month: int) -> str:
    ym = f"{year:04d}-{month:02d}"
    return f"data/futures/um/monthly/{kind}/{symbol}/{INTERVAL}/{symbol}-{INTERVAL}-{ym}.zip"


def daily_key(kind: str, symbol: str, date: dt.date) -> str:
    return f"data/futures/um/daily/{kind}/{symbol}/{INTERVAL}/{symbol}-{INTERVAL}-{date.isoformat()}.zip"


def month_dates(first: dt.date, last: dt.date, missing: set[str], year: int, month: int) -> list[dt.date]:
    start = max(first, dt.date(year, month, 1))
    next_month = dt.date(year + 1, 1, 1) if month == 12 else dt.date(year, month + 1, 1)
    end = min(last, next_month - dt.timedelta(days=1))
    if end < start:
        return []
    return [
        start + dt.timedelta(days=n)
        for n in range((end - start).days + 1)
        if (start + dt.timedelta(days=n)).isoformat() not in missing
    ]


def load_month(job):
    symbol, year, month, dates = job
    mk = monthly_key("markPriceKlines", symbol, year, month)
    ik = monthly_key("indexPriceKlines", symbol, year, month)

    # January 2024 monthly archives are prohibited because they contain post-train rows.
    # A pre-2024 monthly pair is also unusable when its timestamp vectors differ.
    monthly_integrity_fallback = 0
    if year < 2024:
        try:
            mr = verified_zip(mk)
            ir = verified_zip(ik)
            rows = paired_rows(mr, mk, ir, ik)
            return symbol, rows, {
                "monthly_pairs": 1, "daily_pairs": 0, "monthly_fallbacks": 0,
                "monthly_alignment_fallbacks": 0, "daily_pair_rejections": 0,
            }
        except MissingArchive:
            pass
        except RuntimeError as exc:
            if "timestamp misalignment" not in str(exc):
                raise
            monthly_integrity_fallback = 1

    rows = []
    daily_pairs = 0
    daily_pair_rejections = 0
    for date in dates:
        mkd = daily_key("markPriceKlines", symbol, date)
        ikd = daily_key("indexPriceKlines", symbol, date)
        mr = verified_zip(mkd)
        ir = verified_zip(ikd)
        try:
            day_rows = paired_rows(mr, mkd, ir, ikd)
        except RuntimeError as exc:
            if "timestamp misalignment" not in str(exc):
                raise
            daily_pair_rejections += 1
            continue
        rows.extend(day_rows)
        daily_pairs += 1
    return symbol, rows, {
        "monthly_pairs": 0,
        "daily_pairs": daily_pairs,
        "monthly_fallbacks": 1 if year < 2024 else 0,
        "monthly_alignment_fallbacks": monthly_integrity_fallback,
        "daily_pair_rejections": daily_pair_rejections,
    }


def robust_z(frame: pd.DataFrame) -> pd.DataFrame:
    n = frame.notna().sum(axis=1)
    med = frame.median(axis=1)
    delta = frame.sub(med, axis=0)
    mad = delta.abs().median(axis=1)
    valid = (n >= 10) & np.isfinite(mad) & (mad > 1e-12)
    return delta.div(mad.where(valid), axis=0).where(valid, np.nan)


def main() -> None:
    assert (PROJECT / "research/v99_r106_phase117_mark_index_dislocation_stress_prereg.md").exists()
    phase116 = json.loads((PROJECT / "reports/candidate_v99_r106_phase116_mark_index_data_audit.json").read_text())
    assert phase116["status"] == "DATA_AUDIT_COMPLETE"
    assert phase116["holdout_market_values_not_downloaded_or_parsed"]
    assert phase116["alpha_prohibited"] and not phase116["basis_values_computed"] and not phase116["return_relation_computed"]
    assert phase116["summary"]["timestamp_alignment_failures"] == 0

    cfg, data, raw, ex, guard, gross, quarantined, metadata = p1.r98.r36.v15_setup()
    symbols = [s for s in data.close.columns if s in phase116["paired"]]

    jobs = []
    for symbol in symbols:
        info = phase116["paired"][symbol]
        if not info["first"]:
            continue
        first = max(dt.date.fromisoformat(info["first"]), TRAIN_START.date())
        last = min(dt.date.fromisoformat(info["last"]), (TRAIN_END - pd.Timedelta(hours=1)).date())
        missing = set(info["missing_dates"])
        cursor = dt.date(first.year, first.month, 1)
        final_month = dt.date(last.year, last.month, 1)
        while cursor <= final_month:
            dates = month_dates(first, last, missing, cursor.year, cursor.month)
            if dates:
                jobs.append((symbol, cursor.year, cursor.month, dates))
            cursor = dt.date(cursor.year + 1, 1, 1) if cursor.month == 12 else dt.date(cursor.year, cursor.month + 1, 1)

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        loaded = list(pool.map(load_month, jobs))

    mark = pd.DataFrame(index=data.close.index, columns=data.close.columns, dtype=float)
    index = pd.DataFrame(index=data.close.index, columns=data.close.columns, dtype=float)
    stats = defaultdict(int)
    for symbol, rows, st in loaded:
        for k, v in st.items():
            stats[k] += v
        if symbol not in mark.columns:
            continue
        for t, m, i in rows:
            if t in mark.index and TRAIN_START <= t < TRAIN_END:
                mark.at[t, symbol] = m
                index.at[t, symbol] = i

    valid = (mark > 0) & (index > 0)
    basis = np.log(mark.where(valid) / index.where(valid))
    stress = basis.pow(2).rolling(ROLL_HOURS, min_periods=ROLL_HOURS).mean().pow(0.5)
    z = robust_z(stress)
    score = -z
    lagged = score.shift(1)
    bounded = np.tanh(lagged)
    bounded = bounded.where(lagged.notna().sum(axis=1) >= 10, 0).fillna(0)
    targets = bounded.div(bounded.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0)

    result = p1.run_targets(data, targets, ex, guard, float(ex["severe_cost_per_side"]), ALPHA_GROSS)
    diagnostic = p47.diag(result, data.close.index, TRAIN_START, TRAIN_END)
    passed = bool(diagnostic["stable_train"])

    mask = (mark.index >= TRAIN_START) & (mark.index < TRAIN_END)
    observed = int((mark.loc[mask].notna() & index.loc[mask].notna()).sum().sum())
    active_signal_hours = int((targets.abs().sum(axis=1) > 0).loc[(targets.index >= TRAIN_START) & (targets.index < TRAIN_END)].sum())

    out = {
        "study": "V99 R106 Phase117 — MARK/INDEX 24H DISLOCATION-STRESS QUALITY TRAIN-ONLY alpha gate",
        "status": "TRAIN_ALPHA_PASS_FREEZE_FOR_DOWNSTREAM" if passed else "TRAIN_ALPHA_REJECT",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "precommitment": {
            "prereg": "research/v99_r106_phase117_mark_index_dislocation_stress_prereg.md",
            "source": "official Binance USD-M markPriceKlines + indexPriceKlines 1h close",
            "feature": "24h RMS of log(mark/index), cross-sectional median/MAD robust z",
            "direction": "negative stress z: long lower dislocation stress, short higher dislocation stress",
            "direction_discards_basis_sign": True,
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
        "train_start": TRAIN_START.isoformat(),
        "train_end_exclusive": TRAIN_END.isoformat(),
        "data_integrity": {
            "observed_paired_symbol_hours": observed,
            "active_signal_hours": active_signal_hours,
            **dict(stats),
            "january_2024_monthly_archive_requested": False,
            "checksums_and_zip_crc_verified": True,
            "mark_index_timestamp_alignment_required": True,
        },
        "diagnostic": diagnostic,
        "selected_train_only": "mark_index_24h_dislocation_stress_quality" if passed else None,
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
