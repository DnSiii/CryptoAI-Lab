from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r59_h15_mild_crash as r59
import run_v99_r61_core_asset_whipsaw_audit as r61

r36 = r59.r36
r37 = r59.r37
REPORT = PROJECT / "reports" / "v99_r63_medium_event_severity_audit.json"
PARENT = r59.PARENT
MEDIUM = r59.CRASH_PRESETS[0]


def future_min(series: pd.Series, hours: int) -> pd.Series:
    shifted = series.shift(-1)
    return shifted.iloc[::-1].rolling(hours, min_periods=hours).min().iloc[::-1]


def event_frame(parent, targets: pd.DataFrame, close: pd.DataFrame, hedge_active: pd.Series) -> pd.DataFrame:
    eq = parent.equity.astype(float)
    idx = eq.index.intersection(targets.index).intersection(close.index)
    eq = eq.reindex(idx)
    t = targets.reindex(index=idx, columns=close.columns).fillna(0.0)
    c = close.reindex(index=idx, columns=close.columns)

    r3 = eq.pct_change(3, fill_method=None)
    r6 = eq.pct_change(6, fill_method=None)
    r12 = eq.pct_change(12, fill_method=None)
    r24 = eq.pct_change(24, fill_method=None)
    r72 = eq.pct_change(72, fill_method=None)
    dd = eq / eq.cummax() - 1.0
    dd6 = dd - dd.shift(6)
    dd24 = dd - dd.shift(24)

    b3 = c["BTCUSDT"].pct_change(3, fill_method=None)
    b6 = c["BTCUSDT"].pct_change(6, fill_method=None)
    b24 = c["BTCUSDT"].pct_change(24, fill_method=None)
    b72 = c["BTCUSDT"].pct_change(72, fill_method=None)
    e6 = c["ETHUSDT"].pct_change(6, fill_method=None)
    e24 = c["ETHUSDT"].pct_change(24, fill_method=None)
    e72 = c["ETHUSDT"].pct_change(72, fill_method=None)

    fast = r6 <= MEDIUM["r6_trigger"]
    accel = (dd <= MEDIUM["dd_trigger"]) & (r24 <= MEDIUM["r24_trigger"])
    conflict = ((b24 <= MEDIUM["btc24_trigger"]) | (b72 <= MEDIUM["btc72_trigger"])) & (r6 < 0.0)
    instant = (fast | accel | conflict).fillna(False)
    active = instant.astype(float).rolling(int(MEDIUM["cooldown"]), min_periods=1).max().gt(0.0)
    entry = active & ~active.shift(1, fill_value=False)

    abs_t = t.abs()
    gross = abs_t.sum(axis=1)
    long_gross = t.clip(lower=0.0).sum(axis=1)
    short_gross = (-t.clip(upper=0.0)).sum(axis=1)
    dominant = pd.concat([long_gross, short_gross], axis=1).max(axis=1)
    net_abs = t.sum(axis=1).abs()
    btc_w = t["BTCUSDT"]
    eth_w = t["ETHUSDT"]
    core_gross = btc_w.abs() + eth_w.abs()
    core_net_abs = (btc_w + eth_w).abs()
    share = abs_t.div(gross.replace(0.0, np.nan), axis=0).fillna(0.0)
    top1 = share.max(axis=1)

    hourly = c.pct_change(fill_method=None)
    r6m = c.pct_change(6, fill_method=None)
    r24m = c.pct_change(24, fill_method=None)
    breadth_neg_6 = (r6m < 0.0).mean(axis=1)
    breadth_neg_24 = (r24m < 0.0).mean(axis=1)
    median_r6 = r6m.median(axis=1)
    median_r24 = r24m.median(axis=1)
    cross_vol = hourly.std(axis=1)

    peak = eq.cummax()
    f7 = future_min(eq, 168)
    f14 = future_min(eq, 336)
    fdd7 = f7 / peak - 1.0
    fdd14 = f14 / peak - 1.0

    out = pd.DataFrame(index=idx)
    out["entry"] = entry
    out["fast_loss_component"] = fast.astype(float)
    out["drawdown_accel_component"] = accel.astype(float)
    out["market_conflict_component"] = conflict.astype(float)
    out["component_count"] = fast.astype(int) + accel.astype(int) + conflict.astype(int)
    out["fast_loss_excess"] = (-r6 - abs(MEDIUM["r6_trigger"])).clip(lower=0.0)
    out["dd_depth"] = (-dd).clip(lower=0.0)
    out["dd_worsen_6h"] = (-dd6).clip(lower=0.0)
    out["dd_worsen_24h"] = (-dd24).clip(lower=0.0)
    out["equity_loss_3h"] = (-r3).clip(lower=0.0)
    out["equity_loss_6h"] = (-r6).clip(lower=0.0)
    out["equity_loss_12h"] = (-r12).clip(lower=0.0)
    out["equity_loss_24h"] = (-r24).clip(lower=0.0)
    out["equity_loss_72h"] = (-r72).clip(lower=0.0)
    out["btc_loss_3h"] = (-b3).clip(lower=0.0)
    out["btc_loss_6h"] = (-b6).clip(lower=0.0)
    out["btc_loss_24h"] = (-b24).clip(lower=0.0)
    out["btc_loss_72h"] = (-b72).clip(lower=0.0)
    out["eth_loss_6h"] = (-e6).clip(lower=0.0)
    out["eth_loss_24h"] = (-e24).clip(lower=0.0)
    out["eth_loss_72h"] = (-e72).clip(lower=0.0)
    out["gross"] = gross
    out["dominant_side_gross"] = dominant
    out["net_abs"] = net_abs
    out["core_gross"] = core_gross
    out["core_net_abs"] = core_net_abs
    out["btc_abs_weight"] = btc_w.abs()
    out["eth_abs_weight"] = eth_w.abs()
    out["top1_share"] = top1
    out["breadth_negative_6h"] = breadth_neg_6
    out["breadth_negative_24h"] = breadth_neg_24
    out["market_median_loss_6h"] = (-median_r6).clip(lower=0.0)
    out["market_median_loss_24h"] = (-median_r24).clip(lower=0.0)
    out["cross_section_vol_1h"] = cross_vol
    out["parent_hedge_active"] = hedge_active.reindex(idx).fillna(False).astype(float)
    out["current_dd"] = dd
    out["future_dd7"] = fdd7
    out["future_dd14"] = fdd14
    out["deepen_7d_5pp"] = fdd7 <= (dd - 0.05)
    out["deepen_14d_8pp"] = fdd14 <= (dd - 0.08)
    out["hit_20pct_dd_14d"] = fdd14 <= -0.20
    return out.loc[entry].replace([np.inf, -np.inf], np.nan).dropna(subset=["future_dd7", "future_dd14"])


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
        "auc": r61.auc(sample[feature], y),
    }


def threshold_rows(train: pd.DataFrame, hold: pd.DataFrame, feature: str, label: str):
    rows=[]
    for q in (0.70,0.80,0.90):
        th=float(train[feature].quantile(q))
        row={"quantile":q,"threshold":th}
        for name,sample in (("train",train),("holdout",hold)):
            gate=sample[feature]>=th; y=sample[label].astype(bool)
            base=float(y.mean()) if len(sample) else 0.0
            gated=float(sample.loc[gate,label].mean()) if gate.any() else 0.0
            row[name]={"coverage":float(gate.mean()) if len(sample) else 0.0,
                       "event_capture":float((gate&y).sum()/max(1,int(y.sum()))),
                       "base_rate":base,"gated_rate":gated,"lift":float(gated/max(base,1e-12))}
        rows.append(row)
    return rows


def main():
    cand,data,raw,ex,guard,gross,quarantined,metadata=r36.v15_setup()
    cost=float(ex["base_cost_per_side"])
    parent,shadow,targets,hedge_active=r59.build_parent(data,raw,ex,guard,gross,cost)
    events=event_frame(parent,targets,data.close,hedge_active)
    if len(events) < 20:
        raise RuntimeError(f"Too few medium entry events: {len(events)}")
    split=max(1,min(len(events)-1,int(len(events)*0.60)))
    train=events.iloc[:split].copy(); hold=events.iloc[split:].copy(); train_end=train.index[-1]
    labels=("deepen_7d_5pp","deepen_14d_8pp","hit_20pct_dd_14d")
    exclude={"entry","current_dd","future_dd7","future_dd14",*labels}
    features=[c for c in events.columns if c not in exclude]
    rankings={}; thresholds={}
    for label in labels:
        ranked=[]
        for f in features:
            tr=split_stats(train,f,label); ho=split_stats(hold,f,label)
            ranked.append({"feature":f,"train":tr,"holdout":ho,
                           "stable_auc":float(min(tr["auc"],ho["auc"])),
                           "mean_auc":float((tr["auc"]+ho["auc"])/2.0)})
        ranked.sort(key=lambda x:(x["stable_auc"],x["mean_auc"]),reverse=True)
        rankings[label]=ranked
        for row in ranked[:15]:
            if row["stable_auc"]>=0.56:
                thresholds[f"{label}:{row['feature']}"]=threshold_rows(train,hold,row["feature"],label)

    component_tests={}
    for label in labels:
        ytr=train[label].astype(bool); yho=hold[label].astype(bool)
        tests=[]
        for name,gate_tr,gate_ho in (
            ("fast_loss",train["fast_loss_component"]>0,hold["fast_loss_component"]>0),
            ("drawdown_accel",train["drawdown_accel_component"]>0,hold["drawdown_accel_component"]>0),
            ("market_conflict",train["market_conflict_component"]>0,hold["market_conflict_component"]>0),
            ("two_or_more_components",train["component_count"]>=2,hold["component_count"]>=2),
            ("all_three_components",train["component_count"]>=3,hold["component_count"]>=3),
        ):
            row={"name":name}
            for split_name,sample,y,gate in (("train",train,ytr,gate_tr),("holdout",hold,yho,gate_ho)):
                base=float(y.mean()) if len(sample) else 0.0
                rate=float(y.loc[gate].mean()) if gate.any() else 0.0
                row[split_name]={"coverage":float(gate.mean()),"base_rate":base,"gated_rate":rate,
                                 "lift":float(rate/max(base,1e-12)),"events":int(gate.sum())}
            tests.append(row)
        component_tests[label]=tests

    out={
        "study":"V99 R63 medium-entry event severity audit",
        "status":"DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION",
        "objective":"classify discrete entries into the validated R37 medium crash state and identify causal event-time features that separate truly dangerous warnings from benign warnings, using a chronological 60/40 event split",
        "parent_fixed":PARENT,"medium_fixed":MEDIUM,"parent_summary":r36.stats(parent.equity),
        "event_count":int(len(events)),"train_events":int(len(train)),"holdout_events":int(len(hold)),"train_end":train_end.isoformat(),
        "event_rates":{lab:{"train":float(train[lab].mean()),"holdout":float(hold[lab].mean())} for lab in labels},
        "feature_rankings":rankings,"threshold_stability":thresholds,"component_tests":component_tests,
        "disclosure":"Diagnostic only. Every feature is known at the medium-state entry timestamp. Future equity is used only for event labels. Any defensive action must be tested prospectively in a separate revision.",
        "funding_quarantined_symbols":quarantined,"v15_metadata":metadata,
    }
    REPORT.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps({"study":out["study"],"event_count":out["event_count"],"event_rates":out["event_rates"],
                      "top":{lab:rankings[lab][:12] for lab in labels},"component_tests":component_tests},indent=2),flush=True)

if __name__=="__main__":
    main()
