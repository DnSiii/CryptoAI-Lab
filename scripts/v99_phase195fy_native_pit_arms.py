"""Research-only V99 R106 native-universe four-arm point-in-time ablation.

This module never changes frozen engines, published paper, or a holdout.
Only caller-supplied native target matrices and an immutable discovery snapshot
are used. No arm is eligible for promotion without independent source receipts,
chronological train-only routing, temporal folds and severe cost stress.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Mapping

import numpy as np
import pandas as pd

HOUR = timedelta(hours=1)
ARMS = ("legacy_as_is", "fixed_train_universe", "receipt_tminus1", "fixed_and_receipt")


def _utc(value: object) -> pd.Timestamp:
    try:
        stamp = pd.Timestamp(value)
    except (ValueError, TypeError) as exc:
        raise ValueError("invalid UTC timestamp") from exc
    if pd.isna(stamp) or stamp.tzinfo is None or stamp.utcoffset() != timedelta(0):
        raise ValueError("explicit UTC timestamp required")
    return stamp.tz_convert("UTC")


def _decision_after_receipt(receipt: object) -> pd.Timestamp:
    """A receipt during hour h cannot inform the h close; signal t-1."""
    observed = _utc(receipt)
    return observed.floor("h") + pd.Timedelta(hours=2)


def _validate_targets(targets: pd.DataFrame, universe: Mapping, train_end: object) -> tuple[pd.DatetimeIndex, pd.Timestamp]:
    if not isinstance(targets, pd.DataFrame) or targets.empty or targets.shape[1] == 0:
        raise ValueError("nonempty native target matrix required")
    if not isinstance(targets.index, pd.DatetimeIndex):
        raise ValueError("datetime index required")
    idx = targets.index
    if idx.tz is None or any(x.utcoffset() != timedelta(0) for x in idx):
        raise ValueError("all native timestamps must be UTC")
    if (not idx.is_monotonic_increasing or not idx.is_unique or
        any(idx != idx.floor("h")) or
        any((idx[1:] - idx[:-1]) != pd.Timedelta(hours=1))):
        raise ValueError("ordered unique whole-hour index required")
    if not targets.columns.is_unique or not all(isinstance(s, str) and s for s in targets.columns):
        raise ValueError("unique string symbol names required")
    if any(s not in universe for s in targets.columns):
        raise ValueError("universe lacks native target symbols")
    if not all(isinstance(universe[s], dict) for s in targets.columns):
        raise ValueError("invalid universe metadata")
    try:
        values = targets.to_numpy(dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("non-numeric native weights") from exc
    if not np.isfinite(values).all():
        raise ValueError("nonfinite native weights")
    cutoff = _utc(train_end)
    if cutoff < idx[0] or cutoff >= idx[-1]:
        raise ValueError("train cutoff must precede validation observations")
    if cutoff != cutoff.floor("h"):
        raise ValueError("train cutoff must be a whole UTC hour")
    return idx, cutoff


def build_arms(targets: pd.DataFrame, universe: Mapping[str, dict], train_end: object) -> dict[str, pd.DataFrame]:
    """Return deterministic, independently copyable target ablations.

    * legacy_as_is: diagnostic only, may be contaminated.
    * fixed_train_universe: exclude discoveries first seen after train end.
    * receipt_tminus1: earliest safe decision = floor(receipt)+2h.
    * fixed_and_receipt: both restrictions, no as-of lookahead.

    Legacy symbols remain unverified: their source contract must be audited
    separately. No fallback from a missing receipt to listing date is allowed.
    """
    idx, cutoff = _validate_targets(targets, universe, train_end)
    legacy = targets.copy(deep=True)
    fixed = targets.copy(deep=True)
    receipt = targets.copy(deep=True)
    both = targets.copy(deep=True)
    for symbol in targets.columns:
        meta = universe[symbol]
        source = meta.get("source")
        if source == "v14_legacy_universe":
            continue
        if source != "dynamic_binance_discovery":
            raise ValueError(f"{symbol}: unsupported provenance type")
        if not meta.get("discovered_at_utc"):
            raise ValueError(f"{symbol}: first-seen receipt missing")
        first_seen = _utc(meta["discovered_at_utc"])
        first_safe_decision = _decision_after_receipt(first_seen)
        if first_seen > cutoff:
            fixed.loc[:, symbol] = 0.0
            both.loc[:, symbol] = 0.0
        unsafe = idx < first_safe_decision
        receipt.loc[unsafe, symbol] = 0.0
        both.loc[unsafe, symbol] = 0.0
    return dict(zip(ARMS, (legacy, fixed, receipt, both)))


def audit_arms(targets: pd.DataFrame, universe: Mapping[str, dict], train_end: object) -> dict:
    arms = build_arms(targets, universe, train_end)
    original = arms["legacy_as_is"].to_numpy(dtype=float)
    result = {}
    for key, matrix in arms.items():
        changed = original - matrix.to_numpy(dtype=float)
        blocked = np.abs(changed) > 1e-12
        result[key] = {
            "blocked_nonzero_target_cells": int(blocked.sum()),
            "blocked_absolute_target_weight_sum": float(np.abs(changed).sum()),
            "nonzero_target_cells_remaining": int((np.abs(matrix.to_numpy(dtype=float)) > 1e-12).sum()),
        }
    return {
        "status": "DATA_ONLY_HOLD",
        "source_receipts_independently_authenticated": False,
        "legacy_source_provenance_validated": False,
        "holdout_accessed": False,
        "publication_authorized": False,
        "promotion_authorized": False,
        "train_end": _utc(train_end).isoformat(),
        "target_start": targets.index[0].isoformat(),
        "target_end": targets.index[-1].isoformat(),
        "arms": result,
    }
