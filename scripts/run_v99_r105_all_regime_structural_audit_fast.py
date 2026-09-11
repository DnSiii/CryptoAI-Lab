from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r105_all_regime_structural_audit as audit


def fast_trade_episodes(result, data, start, end, direction_regime, vol_regime):
    required = (
        result.open_positions,
        result.asset_gross,
        result.asset_fees,
        result.asset_funding,
    )
    if any(x is None for x in required):
        return [], 0

    full_index = result.equity.index
    selected = full_index[(full_index >= start) & (full_index <= end)]
    if len(selected) < 2:
        return [], 0

    positions = result.open_positions.reindex(selected).fillna(0.0).to_numpy(dtype=float, copy=False)
    signs = np.sign(positions).astype(np.int8)
    net = (
        result.asset_gross.reindex(selected).fillna(0.0)
        - result.asset_fees.reindex(selected).fillna(0.0)
        - result.asset_funding.reindex(selected).fillna(0.0)
    ).to_numpy(dtype=float, copy=False)
    equity = result.equity.reindex(full_index).ffill()
    direction = direction_regime.reindex(full_index).fillna("UNKNOWN")
    vol = vol_regime.reindex(full_index).fillna("UNKNOWN")

    first_global_pos = full_index.get_loc(selected[0])
    previous_sign = np.zeros(signs.shape[1], dtype=np.int8)
    if isinstance(first_global_pos, (int, np.integer)) and first_global_pos > 0:
        prior_ts = full_index[int(first_global_pos) - 1]
        previous_sign = np.sign(
            result.open_positions.loc[prior_ts].fillna(0.0).to_numpy(dtype=float)
        ).astype(np.int8)

    trades = []
    open_excluded = 0
    for col, sym in enumerate(result.open_positions.columns):
        s = signs[:, col]
        if not np.any(s):
            continue
        starts = np.flatnonzero(np.r_[True, s[1:] != s[:-1]])
        ends = np.r_[starts[1:] - 1, len(s) - 1]
        for run_no, (lo, hi) in enumerate(zip(starts, ends)):
            sign = int(s[int(lo)])
            if sign == 0:
                continue
            inherited = bool(int(lo) == 0 and previous_sign[col] == sign)
            still_open = bool(int(hi) == len(s) - 1 and sign != 0)
            if inherited:
                continue
            if still_open:
                open_excluded += 1
                continue
            entry_ts = selected[int(lo)]
            exit_ts = selected[int(hi)]
            global_entry_pos = full_index.get_loc(entry_ts)
            prior_ts = (
                full_index[max(0, int(global_entry_pos) - 1)]
                if isinstance(global_entry_pos, (int, np.integer))
                else entry_ts
            )
            entry_equity = max(float(equity.loc[prior_ts]), 1e-12)
            pnl = float(np.sum(net[int(lo): int(hi) + 1, col]))
            trades.append(
                {
                    "symbol": str(sym),
                    "sign": sign,
                    "entry": entry_ts,
                    "exit": exit_ts,
                    "entry_equity": entry_equity,
                    "pnl": pnl,
                    "pnl_return": float(pnl / entry_equity),
                    "inherited": False,
                    "direction_regime": str(direction.loc[prior_ts]),
                    "volatility_regime": str(vol.loc[prior_ts]),
                }
            )
    trades.sort(key=lambda x: (x["entry"], x["symbol"]))
    return trades, int(open_excluded)


def fast_analyze_result(result, data, direction, vol, start, end):
    trades, open_excluded = fast_trade_episodes(result, data, start, end, direction, vol)
    return {
        "global": audit.path_metrics(result, start, end, trades),
        "regimes": audit.regime_metrics(result, trades, direction, vol, start, end),
        "trade_diagnostics": {
            "closed_trade_episodes": int(len(trades)),
            "open_trade_episodes_excluded": int(open_excluded),
            "episode_definition": "contiguous nonzero post-trade position with unchanged sign; same-sign resizing stays in one episode; inherited and still-open boundary episodes are excluded",
            "transition_hour_note": "asset P&L, fees and funding come from the exact replay. For diagnostic episode segmentation, a sign-flip hour is attributed to the newly opened sign. This can slightly move per-trade quality statistics but does not change equity, ROI, drawdown, days, costs, or regime path returns. A future promotion candidate must use an exact transition-split ledger before final freeze.",
        },
    }


audit.trade_episodes = fast_trade_episodes
audit.analyze_result = fast_analyze_result

if __name__ == "__main__":
    audit.main()
