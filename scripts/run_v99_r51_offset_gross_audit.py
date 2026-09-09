from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r48_dd_continuation_audit as r48

r36 = r48.r36
r37 = r48.r37
REPORT = PROJECT / "reports" / "v99_r51_offset_gross_audit.json"


def offset_features(targets: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
    idx = targets.index.intersection(close.index)
    t = targets.reindex(index=idx, columns=close.columns).fillna(0.0)
    c = close.reindex(index=idx, columns=close.columns)

    abs_t = t.abs()
    gross = abs_t.sum(axis=1)
    net_abs = t.sum(axis=1).abs()
    long_gross = t.clip(lower=0.0).sum(axis=1)
    short_gross = (-t.clip(upper=0.0)).sum(axis=1)
    offset = (gross - net_abs).clip(lower=0.0)

    out = pd.DataFrame(index=idx)
    out["gross"] = gross
    out["net_abs"] = net_abs
    out["offset_gross"] = offset
    out["offset_fraction"] = (offset / gross.replace(0.0, np.nan)).fillna(0.0)
    out["balanced_side_gross"] = 2.0 * pd.concat([long_gross, short_gross], axis=1).min(axis=1)
    out["dominant_side_gross"] = pd.concat([long_gross, short_gross], axis=1).max(axis=1)

    btc = t["BTCUSDT"]
    eth = t["ETHUSDT"] if "ETHUSDT" in t.columns else pd.Series(0.0, index=idx)
    pair_gross = btc.abs() + eth.abs()
    pair_net = (btc + eth).abs()
    pair_offset = (pair_gross - pair_net).clip(lower=0.0)
    out["btc_eth_pair_gross"] = pair_gross
    out["btc_eth_pair_offset"] = pair_offset
    out["btc_eth_offset_fraction"] = (pair_offset / pair_gross.replace(0.0, np.nan)).fillna(0.0)
    out["btc_eth_opposed"] = ((btc * eth) < 0.0).astype(float)
    out["btc_abs_weight"] = btc.abs()
    out["eth_abs_weight"] = eth.abs()

    # Requested-book churn: all causal, based only on target changes through t.
    hourly_turn = t.diff().abs().sum(axis=1).fillna(0.0)
    out["target_turnover_6h"] = hourly_turn.rolling(6, min_periods=1).sum()
    out["target_turnover_24h"] = hourly_turn.rolling(24, min_periods=1).sum()
    out["target_turnover_72h"] = hourly_turn.rolling(72, min_periods=1).sum()

    sign = np.sign(t)
    flips = ((sign != sign.shift(1)) & (t.abs() >= 0.05) & (t.shift(1).abs() >= 0.05)).sum(axis=1).astype(float)
    out["material_sign_flips_24h"] = flips.rolling(24, min_periods=1).sum()
    out["material_sign_flips_72h"] = flips.rolling(72, min_periods=1).sum()

    hourly = c.pct_change(fill_method=None)
    out["cross_section_vol_1h"] = hourly.std(axis=1).fillna(0.0)
    out["btc_abs_3h"] = c["BTCUSDT"].pct_change(3, fill_method=None).abs().fillna(0.0)
    out["btc_abs_24h"] = c["BTCUSDT"].pct_change(24, fill_method=None).abs().fillna(0.0)
    return out.replace([np.inf, -np.inf], np.nan).fillna(0.0)


def split_stats(sample: pd.DataFrame, feature: str, label: str) -> dict:
    if sample.empty:
        return {"n": 0, "events": 0, "event_rate": 0.0, "auc": 0.5}
    y = sample[label].astype(bool)
    return {
        "n": int(len(sample)),
        "events": int(y.sum()),
        "event_rate": float(y.mean()),
        "event_median": float(sample.loc[y, feature].median()) if y.any() else 0.0,
        "normal_median": float(sample.loc[~y, feature].median()) if (~y).any() else 0.0,
        "auc": r48.auc(sample[feature], y),
    }


def threshold_rows(train: pd.DataFrame, hold: pd.DataFrame, feature: str, label: str) -> list[dict]:
    out=[]
    for q in (0.80,0.90,0.95):
        threshold=float(train[feature].quantile(q))
        row={"quantile":q,"threshold":threshold}
        for name,sample in (("train",train),("holdout",hold)):
            gate=sample[feature]>=threshold
            y=sample[label].astype(bool)
            base=float(y.mean()) if len(sample) else 0.0
            gated=float(sample.loc[gate,label].mean()) if gate.any() else 0.0
            row[name]={
                "coverage":float(gate.mean()) if len(sample) else 0.0,
                "event_capture":float((gate & y).sum()/max(1,int(y.sum()))),
                "base_rate":base,
                "gated_rate":gated,
                "lift":float(gated/max(base,1e-12)),
            }
        out.append(row)
    return out


def pair_row(train: pd.DataFrame, hold: pd.DataFrame, f1: str, f2: str, label: str) -> dict:
    t1=float(train[f1].quantile(.80)); t2=float(train[f2].quantile(.80))
    out={"features":[f1,f2],"thresholds":[t1,t2],"label":label}
    for name,sample in (("train",train),("holdout",hold)):
        gate=(sample[f1]>=t1)&(sample[f2]>=t2)
        y=sample[label].astype(bool); base=float(y.mean()) if len(sample) else 0.0
        gated=float(sample.loc[gate,label].mean()) if gate.any() else 0.0
        out[name]={"coverage":float(gate.mean()) if len(sample) else 0.0,
                   "event_capture":float((gate&y).sum()/max(1,int(y.sum()))),
                   "base_rate":base,"gated_rate":gated,"lift":float(gated/max(base,1e-12))}
    return out


def audit(frame: pd.DataFrame, train_end: pd.Timestamp, lo: float, hi: float) -> dict:
    cohort=frame.loc[(frame["dd_depth"]>=lo)&(frame["dd_depth"]<hi)].copy()
    train=cohort.loc[cohort.index<=train_end]; hold=cohort.loc[cohort.index>train_end]
    labels=("deepen_7d_5pp","deepen_14d_8pp")
    features=[c for c in frame.columns if c not in {"dd_depth",*labels,"current_dd","future_dd7","future_dd14"}]
    rankings={}; thresholds={}
    for label in labels:
        rows=[]
        for f in features:
            tr=split_stats(train,f,label); ho=split_stats(hold,f,label)
            rows.append({"feature":f,"train":tr,"holdout":ho,
                         "stable_auc":float(min(tr["auc"],ho["auc"])),
                         "mean_auc":float((tr["auc"]+ho["auc"])/2.0)})
        rows.sort(key=lambda x:(x["stable_auc"],x["mean_auc"]),reverse=True)
        rankings[label]=rows
        for r in rows[:12]:
            if r["stable_auc"]>=.56:
                thresholds[f"{label}:{r['feature']}"]=threshold_rows(train,hold,r["feature"],label)
    pairs=[]
    fixed=(
        ("offset_gross","cross_section_vol_1h"),
        ("offset_gross","target_turnover_24h"),
        ("offset_fraction","gross"),
        ("btc_eth_pair_offset","target_turnover_24h"),
        ("btc_eth_pair_offset","cross_section_vol_1h"),
        ("target_turnover_24h","gross"),
    )
    for label in labels:
        for f1,f2 in fixed:
            pairs.append(pair_row(train,hold,f1,f2,label))
    return {"depth_range":[lo,hi],"rows":int(len(cohort)),"train_rows":int(len(train)),"holdout_rows":int(len(hold)),
            "feature_rankings":rankings,"threshold_stability":thresholds,"predeclared_pair_tests":pairs}


def main():
    cand,data,raw,ex,guard,gross,quarantined,metadata=r36.v15_setup()
    cost=float(ex["base_cost_per_side"])
    r30,r30_targets,hedge_active=r37.build_r30(data,raw,ex,guard,gross,cost)
    base=r48.build_risk_features(r30_targets,data.close,r30.equity,hedge_active)
    extra=offset_features(r30_targets,data.close)
    labels=r48.continuation_labels(r30.equity)
    frame=base[["dd_depth"]].join(extra).join(labels).dropna(subset=["future_dd7","future_dd14"])
    split=int(len(frame)*.60); train_end=frame.index[max(0,split-1)]
    cohorts={
        "early_dd_5_to_12":audit(frame,train_end,.05,.12),
        "mid_dd_8_to_18":audit(frame,train_end,.08,.18),
    }
    out={
        "study":"V99 R51 offset-gross / dispersion continuation audit",
        "status":"DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION",
        "objective":"test whether two-sided offsetting gross, BTC/ETH opposing exposure, and target-book churn explain drawdown continuation beyond net exposure, using the same causal labels and fixed chronological 60/40 split as R48",
        "r30_fixed_base":r37.R30_BASE,
        "r30_summary":r36.stats(r30.equity),
        "train_end":train_end.isoformat(),
        "cohorts":cohorts,
        "disclosure":"Diagnostic only. All exposure/churn features use targets through t only; future data is used solely for continuation labels. Thresholds come from train and are unchanged in holdout.",
        "funding_quarantined_symbols":quarantined,
        "v15_metadata":metadata,
    }
    REPORT.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps({"study":out["study"],"top":{k:{lab:v["feature_rankings"][lab][:8] for lab in ("deepen_7d_5pp","deepen_14d_8pp")} for k,v in cohorts.items()}},indent=2),flush=True)

if __name__=="__main__":
    main()
