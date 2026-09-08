from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from run_v99_r25_trisleeve_meta import cap
import run_v99_r37_crash_shield as r37

r37.r36.cap = cap
r36 = r37.r36

REPORT = PROJECT / "reports" / "v99_r39_tail_precursor_audit.json"


def rank_auc(feature: pd.Series, label: pd.Series, higher_is_risky: bool = True) -> float:
    frame = pd.concat([feature.rename("x"), label.rename("y")], axis=1).dropna()
    pos = frame.loc[frame.y.astype(bool), "x"]
    neg = frame.loc[~frame.y.astype(bool), "x"]
    if len(pos) == 0 or len(neg) == 0:
        return 0.5
    ranks = frame["x"].rank(method="average")
    pos_rank_sum = float(ranks.loc[frame.y.astype(bool)].sum())
    n1, n0 = len(pos), len(neg)
    auc = (pos_rank_sum - n1 * (n1 + 1) / 2.0) / max(1.0, n1 * n0)
    return float(auc if higher_is_risky else 1.0 - auc)


def feature_table(targets: pd.DataFrame, close: pd.DataFrame, equity: pd.Series) -> pd.DataFrame:
    idx = targets.index.intersection(close.index).intersection(equity.index)
    t = targets.reindex(index=idx, columns=close.columns).fillna(0.0)
    c = close.reindex(index=idx, columns=close.columns)
    gross = t.abs().sum(axis=1).replace(0.0, np.nan)
    share = t.abs().div(gross, axis=0).fillna(0.0)
    sign = np.sign(t)
    top_share = share.max(axis=1)
    top_symbol = share.idxmax(axis=1)
    rows = np.arange(len(idx))
    cols = c.columns.get_indexer(top_symbol)

    out = pd.DataFrame(index=idx)
    out["gross"] = gross.fillna(0.0)
    out["net_abs"] = t.sum(axis=1).abs()
    out["top_share"] = top_share
    out["top2_share"] = np.sort(share.to_numpy(), axis=1)[:, -2:].sum(axis=1)
    out["active_names"] = t.abs().gt(1e-8).sum(axis=1).astype(float)

    for hours in (1, 3, 6, 12, 24):
        signed = sign * c.pct_change(hours, fill_method=None)
        top_signed = pd.Series(
            signed.to_numpy()[rows, np.maximum(cols, 0)], index=idx
        ).where(cols >= 0, 0.0)
        out[f"top_adverse_{hours}h"] = (-top_signed).clip(lower=0.0).fillna(0.0)
        adverse = (-signed).clip(lower=0.0)
        contribution = share * adverse
        out[f"max_loss_contrib_{hours}h"] = contribution.max(axis=1).fillna(0.0)
        out[f"weighted_adverse_{hours}h"] = contribution.sum(axis=1).fillna(0.0)

    btc = c["BTCUSDT"]
    net_sign = np.sign(t.sum(axis=1))
    for hours in (1, 3, 6, 12, 24, 72):
        bret = btc.pct_change(hours, fill_method=None)
        out[f"btc_abs_{hours}h"] = bret.abs().fillna(0.0)
        out[f"net_btc_adverse_{hours}h"] = (-(net_sign * bret)).clip(lower=0.0).fillna(0.0)

    hourly = c.pct_change(fill_method=None)
    out["breadth_negative_1h"] = (hourly < 0.0).mean(axis=1)
    out["breadth_abs_1h_gt2"] = (hourly.abs() >= 0.02).mean(axis=1)
    out["cross_section_vol_1h"] = hourly.std(axis=1).fillna(0.0)
    out["btc_realized_vol_24h"] = btc.pct_change(fill_method=None).rolling(24, min_periods=12).std().fillna(0.0)

    eq = equity.reindex(idx).astype(float)
    ret1 = eq.pct_change(fill_method=None)
    out["equity_r3h"] = eq.pct_change(3, fill_method=None).fillna(0.0)
    out["equity_r6h"] = eq.pct_change(6, fill_method=None).fillna(0.0)
    out["equity_r24h"] = eq.pct_change(24, fill_method=None).fillna(0.0)
    out["equity_dd"] = (eq / eq.cummax() - 1.0).fillna(0.0)
    out["equity_neg_streak"] = ret1.lt(0.0).astype(float).rolling(6, min_periods=1).sum()
    return out.replace([np.inf, -np.inf], np.nan).fillna(0.0)


def outcomes(equity: pd.Series) -> pd.DataFrame:
    r = equity.astype(float).pct_change(fill_method=None)
    nxt1 = r.shift(-1)
    nxt3 = equity.shift(-3) / equity - 1.0
    nxt6 = equity.shift(-6) / equity - 1.0
    out = pd.DataFrame(index=equity.index)
    out["next1_return"] = nxt1
    out["next3_return"] = nxt3
    out["next6_return"] = nxt6
    out["tail1"] = nxt1 <= -0.025
    out["tail3"] = nxt3 <= -0.045
    out["tail6"] = nxt6 <= -0.060
    out["severe1"] = nxt1 <= -0.040
    return out


def summarize_feature(frame: pd.DataFrame, feature: str, label: str, train_end: pd.Timestamp) -> dict:
    direction_low = feature in {"equity_r3h", "equity_r6h", "equity_r24h", "equity_dd"}
    series = frame[feature]
    lab = frame[label].astype(bool)
    train = frame.index <= train_end
    test = frame.index > train_end

    def stats(mask):
        x = series.loc[mask]
        y = lab.loc[mask]
        if len(x) == 0:
            return {}
        risky = x.loc[y]
        normal = x.loc[~y]
        return {
            "n": int(len(x)),
            "events": int(y.sum()),
            "event_rate": float(y.mean()),
            "event_median": float(risky.median()) if len(risky) else 0.0,
            "normal_median": float(normal.median()) if len(normal) else 0.0,
            "auc": rank_auc(x, y, higher_is_risky=not direction_low),
        }

    return {"train": stats(train), "holdout": stats(test)}


def threshold_stability(frame: pd.DataFrame, feature: str, label: str, train_end: pd.Timestamp) -> list[dict]:
    low_risky = feature in {"equity_r3h", "equity_r6h", "equity_r24h", "equity_dd"}
    train = frame.loc[frame.index <= train_end]
    test = frame.loc[frame.index > train_end]
    qs = (0.80, 0.90, 0.95, 0.975) if not low_risky else (0.20, 0.10, 0.05, 0.025)
    rows = []
    for q in qs:
        threshold = float(train[feature].quantile(q))
        if low_risky:
            train_gate = train[feature] <= threshold
            test_gate = test[feature] <= threshold
        else:
            train_gate = train[feature] >= threshold
            test_gate = test[feature] >= threshold
        for name, sample, gate in (("train", train, train_gate), ("holdout", test, test_gate)):
            base_rate = float(sample[label].mean()) if len(sample) else 0.0
            gated_rate = float(sample.loc[gate, label].mean()) if gate.any() else 0.0
            rows.append({
                "quantile": q,
                "threshold": threshold,
                "split": name,
                "coverage": float(gate.mean()) if len(gate) else 0.0,
                "events_captured": float((gate & sample[label].astype(bool)).sum() / max(1, sample[label].astype(bool).sum())),
                "base_event_rate": base_rate,
                "gated_event_rate": gated_rate,
                "lift": gated_rate / max(base_rate, 1e-12),
            })
    return rows


def main():
    cand, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    cost = float(ex["base_cost_per_side"])
    r30, r30_targets, hedge_active = r37.build_r30(data, raw, ex, guard, gross, cost)
    features = feature_table(r30_targets, data.close, r30.equity)
    outcome = outcomes(r30.equity)
    frame = features.join(outcome).dropna(subset=["next1_return", "next3_return", "next6_return"])
    split = int(len(frame) * 0.60)
    train_end = frame.index[max(0, split - 1)]

    labels = ("tail1", "tail3", "tail6", "severe1")
    feature_names = list(features.columns)
    ranking = {}
    for label in labels:
        rows = []
        for feature in feature_names:
            s = summarize_feature(frame, feature, label, train_end)
            train_auc = s["train"].get("auc", 0.5)
            hold_auc = s["holdout"].get("auc", 0.5)
            rows.append({
                "feature": feature,
                **s,
                "stable_score": float(min(train_auc, hold_auc)),
                "mean_auc": float((train_auc + hold_auc) / 2.0),
            })
        rows.sort(key=lambda x: (x["stable_score"], x["mean_auc"]), reverse=True)
        ranking[label] = rows

    stable_features = []
    for label in labels:
        for row in ranking[label][:12]:
            if row["stable_score"] >= 0.57:
                stable_features.append((label, row["feature"], row["stable_score"]))
    seen = set()
    threshold_tests = {}
    for label, feature, score in sorted(stable_features, key=lambda x: x[2], reverse=True):
        key = f"{label}:{feature}"
        if key in seen:
            continue
        seen.add(key)
        threshold_tests[key] = threshold_stability(frame, feature, label, train_end)

    # Multi-feature combinations are intentionally tiny and predeclared; this is
    # a diagnostic check of whether independent causal precursors compound lift.
    candidates = [
        ("top_share", "max_loss_contrib_3h"),
        ("top_share", "max_loss_contrib_6h"),
        ("max_loss_contrib_3h", "btc_abs_3h"),
        ("max_loss_contrib_6h", "net_btc_adverse_6h"),
        ("weighted_adverse_3h", "cross_section_vol_1h"),
    ]
    combos = []
    for f1, f2 in candidates:
        q1 = float(frame.loc[frame.index <= train_end, f1].quantile(0.90))
        q2 = float(frame.loc[frame.index <= train_end, f2].quantile(0.90))
        gate = (frame[f1] >= q1) & (frame[f2] >= q2)
        for label in ("tail1", "tail3", "severe1"):
            entry = {"features": [f1, f2], "thresholds": [q1, q2], "label": label}
            for split_name, mask in (("train", frame.index <= train_end), ("holdout", frame.index > train_end)):
                sample = frame.loc[mask]
                g = gate.loc[mask]
                base = float(sample[label].mean())
                gated = float(sample.loc[g, label].mean()) if g.any() else 0.0
                entry[split_name] = {
                    "coverage": float(g.mean()),
                    "event_capture": float((g & sample[label].astype(bool)).sum() / max(1, sample[label].astype(bool).sum())),
                    "base_rate": base,
                    "gated_rate": gated,
                    "lift": gated / max(base, 1e-12),
                }
            combos.append(entry)

    r30_summary = r36.stats(r30.equity)
    out = {
        "study": "V99 R39 R30 causal tail precursor audit",
        "status": "DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION",
        "objective": "identify features already observable at close t that consistently precede R30 next-interval and next-3h/6h tail losses, using a fixed 60/40 chronological split before designing another protection rule",
        "r30_fixed_base": r37.R30_BASE,
        "r30_summary": r30_summary,
        "r30_hedge_active_fraction": float(hedge_active.mean()),
        "train_end": train_end.isoformat(),
        "rows": int(len(frame)),
        "label_rates": {label: {"overall": float(frame[label].mean()), "train": float(frame.loc[frame.index <= train_end, label].mean()), "holdout": float(frame.loc[frame.index > train_end, label].mean())} for label in labels},
        "feature_rankings": ranking,
        "threshold_stability": threshold_tests,
        "predeclared_pair_tests": combos,
        "disclosure": "Diagnostic only. Features at timestamp t use only target weights, price history and shadow equity available by close t. Outcomes begin strictly after t. Thresholds are estimated only on the first 60% and evaluated unchanged on the last 40%. This report must not itself promote a candidate.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({
        "study": out["study"],
        "r30_summary": r30_summary,
        "label_rates": out["label_rates"],
        "top_features": {k: v[:10] for k, v in ranking.items()},
        "pair_tests": combos,
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
