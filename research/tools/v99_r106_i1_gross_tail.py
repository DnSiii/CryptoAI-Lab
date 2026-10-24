"""I1 post-screen gross variance stress, NOT executable PnL or an alpha gate."""
from __future__ import annotations
import hashlib
import json
import math
import statistics
import sys
from collections import Counter
from pathlib import Path

MULTIPLIERS = (1.0, 1.25, 1.5)
ASSETS = ("BTC", "ETH")
FORBIDDEN = ("promotion_authorized", "validation_opened", "holdout_opened",
             "orders_enabled", "paper_publication_authorized",
             "trading_engine_evaluated", "economic_backtest_executed")


def validate_original(doc):
    if doc.get("schema") != "I1_FIRSTPARTY_VARIANCE_PREMIUM_NONOVERLAP_STRUCTURAL_V1":
        raise ValueError("I1_TAIL_BAD_SOURCE_SCHEMA")
    if doc.get("train_start_ms") != 1639008000000 or doc.get("train_end_exclusive_ms") != 1696118400000:
        raise ValueError("I1_TAIL_FUTURE_PARTITION")
    if any(doc.get(k) is not False for k in FORBIDDEN):
        raise ValueError("I1_TAIL_FORBIDDEN_FLAG")
    rows = doc.get("rows", [])
    if len(rows) != 30 or doc.get("windows") != 15:
        raise ValueError("I1_TAIL_WINDOW_COUNT")
    for asset in ASSETS:
        for fold in range(1, 6):
            x = [r for r in rows if r.get("asset") == asset and r.get("fold") == fold]
            if len(x) != 3 or len({r["decision_ms"] for r in x}) != 3:
                raise ValueError("I1_TAIL_FOLD_WINDOW_COUNT")
    by_pair = {}
    for r in rows:
        key = (r["fold"], r["decision_ms"])
        by_pair.setdefault(key, []).append(r)
        if not (math.isfinite(r["implied_variance"]) and r["implied_variance"] > 0
                and math.isfinite(r["realized_variance"]) and r["realized_variance"] >= 0):
            raise ValueError("I1_TAIL_NONFINITE_VARIANCE")
        if not math.isclose(r["premium"], r["implied_variance"] - r["realized_variance"],
                            rel_tol=1e-11, abs_tol=1e-12):
            raise ValueError("I1_TAIL_PREMIUM_TAMPER")
    if len(by_pair) != 15 or any(sorted(r["asset"] for r in pair) != list(ASSETS)
                                or len({r["regime"] for r in pair}) != 1
                                for pair in by_pair.values()):
        raise ValueError("I1_TAIL_PAIR_IDENTITY")
    return rows, by_pair


def summary(observations):
    values = [x["value"] for x in observations]
    positive = sorted((v for v in values if v > 0), reverse=True)
    negative = [-v for v in values if v < 0]
    positive_total = math.fsum(positive)
    negative_total = math.fsum(negative)
    fold_means = [statistics.fmean(x["value"] for x in observations if x["fold"] == f)
                  for f in range(1, 6)]
    return dict(observations=len(values), mean=statistics.fmean(values),
                positive_windows=len(positive),
                positive_folds=sum(v > 0 for v in fold_means),
                fold_means=fold_means, worst_window=min(values),
                total_positive=positive_total, total_negative_magnitude=negative_total,
                top_two_positive_share=(math.fsum(positive[:2])/positive_total
                                        if positive_total else None),
                largest_loss_to_total_positive=(max(negative)/positive_total
                                                if positive_total and negative else None))


def calculate(doc):
    rows, pairs = validate_original(doc)
    output = {}
    for multiplier in MULTIPLIERS:
        k = str(multiplier)
        asset_results = {}
        for asset in ASSETS:
            observations = [dict(fold=r["fold"],
                                 value=r["implied_variance"]-multiplier*r["realized_variance"])
                            for r in rows if r["asset"] == asset]
            asset_results[asset] = summary(observations)
        paired = []
        for (fold, _), pair in sorted(pairs.items()):
            vals = [r["implied_variance"]-multiplier*r["realized_variance"] for r in pair]
            paired.append(dict(fold=fold, value=math.fsum(vals)/2.0))
        output[k] = dict(assets=asset_results, paired_equal_weight_nonportfolio=summary(paired))
    regimes = dict(sorted(Counter(r["regime"] for r in rows if r["asset"] == "BTC").items()))
    return dict(schema="V99_I1_POST_SCREEN_GROSS_TAIL_SENSITIVITY_V1",
                source_i1_run=40087572354, status="POST_SCREEN_GROSS_RISK_ONLY_NO_EXECUTABLE_OPTIONS",
                multipliers=output, regime_window_counts=regimes,
                worst_realized_to_implied={asset:max(r["realized_to_implied"]
                     for r in rows if r["asset"] == asset) for asset in ASSETS},
                **{k: False for k in FORBIDDEN})


def main(input_path, output_dir):
    raw = Path(input_path).read_bytes()
    doc = json.loads(raw)
    result = calculate(doc)
    result["source_report_sha256"] = hashlib.sha256(raw).hexdigest()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out/"i1_gross_tail_sensitivity.json").write_text(
        json.dumps(result, sort_keys=True, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"status":result["status"], "stress":{
        k:{a:{"mean":m["mean"],"positive_folds":m["positive_folds"],
              "worst_window":m["worst_window"]}
           for a,m in v["assets"].items()} for k,v in result["multipliers"].items()},
        "no_promotion":True},sort_keys=True))
    return result


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_gross_tail I1_REPORT_JSON OUTPUT_DIR")
    main(*sys.argv[1:])
