#!/usr/bin/env python3
"""V98 Independent Phase1006: O distinct seven-slot source-only growth engine.

Preregistered Phase1005. NO PnL, funding, 2025+, holdout or external engines.
Weights at close(t) are executable no earlier than open(t+1).
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from phase866_k_sevenslot_source import ASSETS, START, END, PINS, pinned_training_frames

ROOT = Path(__file__).resolve().parent
SLEEVE_SHARES = {"growth": .50, "opportunity": .20, "relative_value": .15, "recovery": .15}
GROSS = {0: .35, 1: .90, 2: 1.50}
ASSET_CAP = .70
GROSS_CAP = 1.75
STRESS_EQUITY_FLOOR = .10
LOOKBACK = 720
PATHS = ("O_core_only", "O_full", "O_minus_opportunity", "O_minus_relative_value", "O_minus_recovery")
EXCLUDE = {
    "O_core_only": frozenset(("opportunity", "relative_value", "recovery")),
    "O_full": frozenset(),
    "O_minus_opportunity": frozenset(("opportunity",)),
    "O_minus_relative_value": frozenset(("relative_value",)),
    "O_minus_recovery": frozenset(("recovery",)),
}


def pinned_o_bars(root: Path):
    root = Path(root)
    close, high = pinned_training_frames(root)
    fields = {}
    for a in ASSETS:
        # pinned_training_frames already authenticated exact raw CSV SHA256.
        raw = pd.read_csv(root / (a + "_1h.csv"))
        fields[a] = raw
    op = pd.DataFrame({a: fields[a]["open"].to_numpy(float) for a in ASSETS}, index=close.index)
    low = pd.DataFrame({a: fields[a]["low"].to_numpy(float) for a in ASSETS}, index=close.index)
    if not np.isfinite(op.to_numpy()).all() or not np.isfinite(low.to_numpy()).all():
        raise ValueError("O_NONFINITE_OPEN_LOW")
    if (op <= 0).any().any() or (low <= 0).any().any():
        raise ValueError("O_NONPOSITIVE_OPEN_LOW")
    if (low > np.minimum(op, close)).any().any() or (high < np.maximum(op, close)).any().any():
        raise ValueError("O_INVALID_OHLC_GEOMETRY")
    return op, high, low, close


def normalize(frame: pd.DataFrame) -> np.ndarray:
    v = frame.to_numpy(float)
    v = np.where(np.isfinite(v) & (v > 0), v, 0.)
    s = v.sum(axis=1, keepdims=True)
    return np.divide(v, s, out=np.zeros_like(v), where=s > 0)


def waterfill(scores, gross):
    x = np.asarray(scores, float)
    if x.shape != (4,) or not np.isfinite(x).all() or (x < 0).any() or not 0 <= gross <= GROSS_CAP:
        raise ValueError("O_INVALID_ALLOCATION")
    out = np.zeros(4)
    if x.sum() <= 0:
        return out
    active = x > 0
    remaining = float(gross)
    for _ in range(4):
        if not active.any() or remaining <= 1e-12:
            break
        part = remaining * x * active / (x * active).sum()
        space = np.maximum(ASSET_CAP - out, 0)
        fill = np.minimum(part, space)
        out += fill
        remaining -= float(fill.sum())
        active &= (space - fill) > 1e-12
    if out.max() > ASSET_CAP + 1e-9 or out.sum() > GROSS_CAP + 1e-9:
        raise AssertionError("O_WATERFILL_CAP")
    return out


def causal_shocks(open_, high, low):
    o, h, l = [np.asarray(x, float) for x in (open_, high, low)]
    if o.shape != h.shape or o.shape != l.shape or o.ndim != 2 or o.shape[1] != 4:
        raise ValueError("O_SHOCK_SHAPE")
    if not all(np.isfinite(x).all() for x in (o, h, l)) or (o <= 0).any() or (l <= 0).any() or (h < o).any() or (l > o).any():
        raise ValueError("O_SHOCK_GEOMETRY")
    up = pd.DataFrame(h / o - 1).rolling(LOOKBACK, min_periods=LOOKBACK).max().to_numpy()
    dn = pd.DataFrame(1 - l / o).rolling(LOOKBACK, min_periods=LOOKBACK).max().to_numpy()
    valid = np.isfinite(up).all(axis=1) & np.isfinite(dn).all(axis=1)
    if (dn[valid] >= 1).any():
        raise ValueError("O_SHOCK_LOSS_EXCEEDS_100PCT")
    return dn, up, valid


def robust_scale(w, dn, up):
    """Ex-ante 16-corner survival for each t target against only bars <=t."""
    w, dn, up = [np.asarray(x, float) for x in (w, dn, up)]
    if w.ndim != 2 or w.shape[1] != 4 or w.shape != dn.shape or w.shape != up.shape:
        raise ValueError("O_GOVERNOR_SHAPE")
    if not np.isfinite(w).all() or (w < 0).any() or (w.max(axis=1) > ASSET_CAP + 1e-9).any() or (w.sum(axis=1) > GROSS_CAP + 1e-9).any():
        raise ValueError("O_GOVERNOR_INVALID_WEIGHTS")
    valid = np.isfinite(dn).all(axis=1) & np.isfinite(up).all(axis=1)
    if (dn[valid] < 0).any() or (dn[valid] >= 1).any() or (up[valid] < 0).any():
        raise ValueError("O_GOVERNOR_INVALID_SHOCKS")
    k = np.ones(len(w))
    k[~valid] = 0.
    wsum = w.sum(axis=1)
    for bits in range(16):
        b = np.array([(bits >> j) & 1 for j in range(4)], bool)
        f = np.where(b, 1 + np.where(valid[:, None], up, 0), 1 - np.where(valid[:, None], dn, 0))
        v = w * f
        gross = v.sum(axis=1)
        drift = gross - wsum
        gross_denom = gross - GROSS_CAP * drift
        k = np.minimum(k, np.divide(GROSS_CAP, gross_denom, out=np.full(len(w), np.inf), where=gross_denom > 0))
        asset_denom = v - ASSET_CAP * drift[:, None]
        bound = np.divide(ASSET_CAP, asset_denom, out=np.full_like(v, np.inf), where=asset_denom > 0)
        k = np.minimum(k, bound.min(axis=1))
        # Worst-case equity = 1 + k*drift; must remain >=10% of pre-shock equity.
        k = np.minimum(k, np.divide(1 - STRESS_EQUITY_FLOOR, -drift, out=np.full(len(w), np.inf), where=drift < 0))
    return np.clip(k, 0., 1.)


def verify_corners(w, dn, up, tol=1e-8):
    w, dn, up = [np.asarray(x, float) for x in (w, dn, up)]
    valid = np.isfinite(dn).all(axis=1) & np.isfinite(up).all(axis=1)
    if np.any(w[~valid] != 0):
        return False
    for bits in range(16):
        b = np.array([(bits >> j) & 1 for j in range(4)], bool)
        f = np.where(b, 1 + np.nan_to_num(up, nan=0), 1 - np.nan_to_num(dn, nan=0))
        v = w * f
        eq = 1 - w.sum(axis=1) + v.sum(axis=1)
        if (eq < STRESS_EQUITY_FLOOR - tol).any() or (v.sum(axis=1) > GROSS_CAP * eq + tol).any() or (v > ASSET_CAP * eq[:, None] + tol).any():
            return False
    return True


def compose_o(open_: pd.DataFrame, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, diagnostics=False):
    frames = (open_, high, low, close)
    index = pd.date_range(START, END, freq="h")
    if any(not isinstance(f, pd.DataFrame) or tuple(f.columns) != ASSETS or not f.index.equals(index) for f in frames):
        raise ValueError("O_TRAINING_ONLY_PINNED_CHRONOLOGY")
    if not all(np.isfinite(f.to_numpy(float)).all() for f in frames):
        raise ValueError("O_NONFINITE_BARS")
    if (low <= 0).any().any() or (low > np.minimum(open_, close)).any().any() or (high < np.maximum(open_, close)).any().any():
        raise ValueError("O_INVALID_OHLC")
    logc = np.log(close)
    r = logc.diff()
    mom336 = logc - logc.shift(336)
    mom168 = logc - logc.shift(168)
    mom72 = logc - logc.shift(72)
    mom24 = logc - logc.shift(24)
    downside = r.clip(upper=0).pow(2).rolling(168, min_periods=168).mean().pow(.5)
    core = normalize(((mom336.clip(lower=0) + .5 * (mom72 - mom72.shift(72)).clip(lower=0)) / downside.where(downside > 1e-12)).fillna(0))
    vol168 = r.rolling(168, min_periods=168).std(ddof=0)
    volp40 = vol168.shift(1).rolling(720, min_periods=720).quantile(.40)
    breakout = (close > high.shift(1).rolling(48, min_periods=48).max()) & (mom24 > mom24.shift(24)) & (vol168 < volp40)
    opportunity = normalize((breakout & (mom168 > 0)).astype(float))
    med = mom168.median(axis=1)
    rv = normalize(mom168.sub(med, axis=0).clip(lower=0).where(mom336 > 0, 0).fillna(0))
    market = r.mean(axis=1).fillna(0)
    cum = market.cumsum()
    drawdown = np.exp(cum - cum.rolling(336, min_periods=336).max()) - 1
    breadth = (mom168 > 0).sum(axis=1)
    recover = (drawdown.rolling(168, min_periods=168).min() < -.10) & (market.rolling(24, min_periods=24).sum() > 0) & (breadth > breadth.shift(24))
    recovery = normalize((mom24.clip(lower=0).where(mom168 < 0, 0).fillna(0)).mul(recover.astype(float), axis=0))
    market_vol = market.rolling(168, min_periods=168).std(ddof=0)
    vol_med = market_vol.shift(1).rolling(720, min_periods=720).median()
    market_mom = market.rolling(168, min_periods=168).sum()
    raw_on = (breadth >= 3) & (market_mom > 0) & (market_vol < vol_med) & vol_med.notna()
    raw_off = (breadth <= 1) & (market_mom < 0)
    raw = np.where(raw_on, 2, np.where(raw_off, 0, 1))
    states = np.zeros(len(index), dtype=np.int8)
    state, previous, streak = 0, -1, 0
    for t, candidate in enumerate(raw):
        candidate = int(candidate)
        streak = streak + 1 if candidate == previous else 1
        previous = candidate
        if candidate != state and streak >= 12:
            state = candidate
        states[t] = state
    sleeves = dict(growth=core, opportunity=opportunity, relative_value=rv, recovery=recovery)
    down, up, valid = causal_shocks(open_.to_numpy(float), high.to_numpy(float), low.to_numpy(float))
    out, diag = {}, {}
    for path in PATHS:
        excluded = EXCLUDE[path]
        raw_weights = np.zeros((len(index), 4))
        last = np.zeros(4)
        updates = 0
        for t in range(len(index)):
            if index[t].hour == 23 or (t > 0 and states[t] != states[t-1]):
                score = np.zeros(4)
                active = {k: v[t] for k, v in sleeves.items() if k not in excluded and v[t].sum() > 0}
                budget = sum(SLEEVE_SHARES[k] for k in active)
                if budget:
                    for k, v in active.items():
                        score += SLEEVE_SHARES[k] * v / budget
                last = waterfill(score, GROSS[int(states[t])])
                updates += 1
            raw_weights[t] = last
        scale = robust_scale(raw_weights, down, up)
        weights = raw_weights * scale[:, None]
        if not verify_corners(weights, down, up):
            raise AssertionError("O_EX_ANTE_16_CORNER_SURVIVAL_FAILED")
        frame = pd.DataFrame(weights, index=index, columns=ASSETS)
        out[path] = frame
        diag[path] = {"sha256": hashlib.sha256(frame.to_csv(float_format="%.12g").encode()).hexdigest(),
                      "hours": len(frame), "updates": updates,
                      "max_gross": float(weights.sum(axis=1).max()),
                      "max_asset": float(weights.max()),
                      "gross_l1_turnover": float(np.abs(np.diff(weights, axis=0)).sum()),
                      "scaled_hours": int(((scale < 1-1e-10) & (raw_weights.sum(axis=1) > 0)).sum())}
    if diagnostics:
        return out, {"paths": diag, "regime_hours": {str(s): int((states == s).sum()) for s in (0, 1, 2)},
                     "valid_shock_hours": int(valid.sum()),
                     "sleeve_active_hours": {k: int((v.sum(axis=1) > 0).sum()) for k, v in sleeves.items()}}
    return out


def run_source_only(root=ROOT):
    op, hi, lo, cl = pinned_o_bars(Path(root) / "phase243_clean4_canonical")
    paths, diag = compose_o(op, hi, lo, cl, diagnostics=True)
    return {"phase": 1006, "decision": "SOURCE_ONLY_NO_ECONOMIC_APPROVAL",
            "historical_pnl_computed": False, "validation_2025_read": False,
            "holdout_accessed": False, "external_benchmarks_used": False,
            "source_pins": PINS, "diagnostics": diag}


if __name__ == "__main__":
    result = run_source_only()
    (ROOT / "phase1006_o_sevenslot_source_result.json").write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"phase": 1006, "decision": result["decision"], "paths": result["diagnostics"]["paths"]}, sort_keys=True))
