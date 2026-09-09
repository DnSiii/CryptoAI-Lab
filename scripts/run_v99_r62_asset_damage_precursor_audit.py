from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r61_core_asset_whipsaw_audit as r61
import run_v99_r59_h15_mild_crash as r59

r36 = r59.r36
REPORT = PROJECT / "reports" / "v99_r62_asset_damage_precursor_audit.json"
PARENT = r59.PARENT


def damage_features(result) -> pd.DataFrame:
    eq = result.equity.astype(float)
    net_pnl = (result.asset_gross - result.asset_fees - result.asset_funding).fillna(0.0)
    idx = eq.index.intersection(net_pnl.index)
    eq = eq.reindex(idx)
    pnl = net_pnl.reindex(idx).fillna(0.0)

    out = pd.DataFrame(index=idx)
    out["dd_depth"] = (1.0 - eq / eq.cummax()).clip(lower=0.0)

    for hours in (24, 72, 168):
        roll = pnl.rolling(hours, min_periods=1).sum()
        denom = eq.abs().replace(0.0, np.nan)

        portfolio = roll.sum(axis=1)
        core = roll.reindex(columns=["BTCUSDT", "ETHUSDT"]).sum(axis=1)
        btc = roll["BTCUSDT"] if "BTCUSDT" in roll.columns else pd.Series(0.0, index=idx)
        eth = roll["ETHUSDT"] if "ETHUSDT" in roll.columns else pd.Series(0.0, index=idx)
        worst = roll.min(axis=1)

        losses = (-roll.clip(upper=0.0)).sum(axis=1)
        core_losses = (-roll.reindex(columns=["BTCUSDT", "ETHUSDT"]).clip(upper=0.0)).sum(axis=1)
        eth_losses = (-eth.clip(upper=0.0))
        btc_losses = (-btc.clip(upper=0.0))
        worst_losses = (-worst.clip(upper=0.0))

        out[f"portfolio_loss_{hours}h"] = (-portfolio / denom).clip(lower=0.0).fillna(0.0)
        out[f"core_loss_{hours}h"] = (-core / denom).clip(lower=0.0).fillna(0.0)
        out[f"btc_loss_{hours}h"] = (-btc / denom).clip(lower=0.0).fillna(0.0)
        out[f"eth_loss_{hours}h"] = (-eth / denom).clip(lower=0.0).fillna(0.0)
        out[f"worst_asset_loss_{hours}h"] = (worst_losses / denom).fillna(0.0)
        out[f"total_asset_loss_{hours}h"] = (losses / denom).fillna(0.0)
        out[f"core_loss_share_{hours}h"] = (core_losses / losses.replace(0.0, np.nan)).fillna(0.0)
        out[f"eth_loss_share_{hours}h"] = (eth_losses / losses.replace(0.0, np.nan)).fillna(0.0)
        out[f"btc_loss_share_{hours}h"] = (btc_losses / losses.replace(0.0, np.nan)).fillna(0.0)
        out[f"worst_loss_share_{hours}h"] = (worst_losses / losses.replace(0.0, np.nan)).fillna(0.0)
        out[f"losing_assets_{hours}h"] = (roll < 0.0).sum(axis=1).astype(float)

        # How much of current realized damage is concentrated in the two core assets.
        out[f"core_damage_intensity_{hours}h"] = (
            out[f"core_loss_{hours}h"] * out[f"core_loss_share_{hours}h"]
        )
        out[f"worst_damage_intensity_{hours}h"] = (
            out[f"worst_asset_loss_{hours}h"] * out[f"worst_loss_share_{hours}h"]
        )

    # Acceleration: recent realized damage relative to the prior window.
    out["portfolio_loss_accel_24_vs_72"] = (
        out["portfolio_loss_24h"] - out["portfolio_loss_72h"] / 3.0
    ).clip(lower=0.0)
    out["core_loss_accel_24_vs_72"] = (
        out["core_loss_24h"] - out["core_loss_72h"] / 3.0
    ).clip(lower=0.0)
    out["worst_loss_accel_24_vs_72"] = (
        out["worst_asset_loss_24h"] - out["worst_asset_loss_72h"] / 3.0
    ).clip(lower=0.0)

    return out.replace([np.inf, -np.inf], np.nan).fillna(0.0)


def audit(frame: pd.DataFrame, train_end: pd.Timestamp, lo: float, hi: float) -> dict:
    cohort = frame.loc[(frame["dd_depth"] >= lo) & (frame["dd_depth"] < hi)].copy()
    train = cohort.loc[cohort.index <= train_end]
    hold = cohort.loc[cohort.index > train_end]
    labels = ("deepen_7d_5pp", "deepen_14d_8pp")
    exclude = {"dd_depth", "current_dd", "future_dd7", "future_dd14", *labels}
    features = [c for c in cohort.columns if c not in exclude]

    rankings = {}
    thresholds = {}
    for label in labels:
        ranked = []
        for feature in features:
            tr = r61.split_stats(train, feature, label)
            ho = r61.split_stats(hold, feature, label)
            ranked.append({
                "feature": feature,
                "train": tr,
                "holdout": ho,
                "stable_auc": float(min(tr["auc"], ho["auc"])),
                "mean_auc": float((tr["auc"] + ho["auc"]) / 2.0),
            })
        ranked.sort(key=lambda x: (x["stable_auc"], x["mean_auc"]), reverse=True)
        rankings[label] = ranked
        for row in ranked[:18]:
            if row["stable_auc"] >= 0.56:
                thresholds[f"{label}:{row['feature']}"] = r61.threshold_rows(
                    train, hold, row["feature"], label
                )

    return {
        "depth_range": [lo, hi],
        "rows": int(len(cohort)),
        "train_rows": int(len(train)),
        "holdout_rows": int(len(hold)),
        "event_rates": {
            label: {
                "train": float(train[label].mean()) if len(train) else 0.0,
                "holdout": float(hold[label].mean()) if len(hold) else 0.0,
            }
            for label in labels
        },
        "feature_rankings": rankings,
        "threshold_stability": thresholds,
    }


def main():
    cand, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    cost = float(ex["base_cost_per_side"])
    parent, shadow, targets, active = r59.build_parent(data, raw, ex, guard, gross, cost)

    features = damage_features(parent)
    labels = r61.continuation_labels(parent.equity)
    frame = features.join(labels).dropna(subset=["future_dd7", "future_dd14"])
    split = int(len(frame) * 0.60)
    train_end = frame.index[max(0, split - 1)]

    cohorts = {
        "pre_early_dd_2_to_8": audit(frame, train_end, 0.02, 0.08),
        "early_dd_5_to_12": audit(frame, train_end, 0.05, 0.12),
        "mid_dd_8_to_18": audit(frame, train_end, 0.08, 0.18),
        "deep_dd_12_to_24": audit(frame, train_end, 0.12, 0.24),
    }

    out = {
        "study": "V99 R62 realized asset-damage precursor audit",
        "status": "DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION",
        "objective": (
            "identify whether causal trailing realized PnL damage, especially concentration of losses in BTC/ETH or "
            "one dominant losing asset, predicts further drawdown deepening earlier than exposure-only gates in the "
            "R55 hedge-0.15 parent"
        ),
        "parent_fixed": PARENT,
        "parent_summary": r36.stats(parent.equity),
        "train_end": train_end.isoformat(),
        "cohorts": cohorts,
        "disclosure": (
            "Diagnostic only. Every feature uses modeled realized asset PnL, fees and funding available through t. "
            "Future data is used only to construct continuation labels. Any guard must be tested separately."
        ),
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({
        "study": out["study"],
        "parent_summary": out["parent_summary"],
        "top": {
            k: {
                lab: v["feature_rankings"][lab][:15]
                for lab in ("deepen_7d_5pp", "deepen_14d_8pp")
            }
            for k, v in cohorts.items()
        },
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
