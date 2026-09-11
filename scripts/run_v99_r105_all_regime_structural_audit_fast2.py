from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r105_all_regime_structural_audit as audit
import run_v99_r105_all_regime_structural_audit_fast as fast


def fixed_regime_path_metrics(result, mask, start, end, trades):
    equity = result.equity.loc[start:end].dropna().astype(float)
    if len(equity) < 2:
        return {}
    hourly = equity.pct_change(fill_method=None).fillna(0.0)
    m = mask.reindex(hourly.index).fillna(False).astype(bool)
    selected = hourly.where(m, 0.0)
    if not int(m.sum()):
        return {"active_hours": 0, **audit.trade_metrics(trades)}
    path = (1.0 + selected.clip(lower=-0.999999)).cumprod()
    dd = path / path.cummax() - 1.0
    per_hour = hourly[m]
    frame = pd.DataFrame({"r": hourly, "active": m})
    active_frame = frame.loc[frame["active"]].copy()
    active_days = active_frame.groupby(active_frame.index.normalize())["r"].apply(
        lambda x: float(np.prod(1.0 + x.to_numpy()) - 1.0)
    )
    return {
        "roi": float(path.iloc[-1] - 1.0),
        "max_drawdown": float(dd.min()),
        "max_drawdown_abs": abs(float(dd.min())),
        "worst_day": float(active_days.min()) if len(active_days) else 0.0,
        "worst_day_abs": abs(float(active_days.min())) if len(active_days) else 0.0,
        "positive_day_ratio": float((active_days > 0).mean()) if len(active_days) else 0.0,
        "positive_days": int((active_days > 0).sum()),
        "negative_days": int((active_days < 0).sum()),
        "max_consecutive_negative_days": audit.max_streak((active_days < 0).to_numpy()),
        "active_hours": int(m.sum()),
        "active_days": int(len(active_days)),
        "mean_active_hour": float(per_hour.mean()) if len(per_hour) else 0.0,
        **audit.trade_metrics(trades),
    }


audit.trade_episodes = fast.fast_trade_episodes
audit.analyze_result = fast.fast_analyze_result
audit.regime_path_metrics = fixed_regime_path_metrics

if __name__ == "__main__":
    audit.main()
