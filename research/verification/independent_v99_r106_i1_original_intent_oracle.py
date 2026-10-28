"""Independent read-only oracle for original 182-to-180 intent handoff.

Does not import the production binding implementation. NO option economics.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from research.tools.v99_r106_i1_full_archive_intake import eligible
from research.tools.v99_r106_d1_real_train_source_join import FOLD_EDGES

SIGNALS = {"POSITIVE_EX_ANTE_PREMIUM", "NO_PREMIUM", "NO_30D_HISTORY"}


def verify(original_path, manifest_path):
    raw = Path(original_path).read_bytes()
    source = json.loads(raw)
    result = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if source.get("schema") != "V99_I1_ORIGINAL_TRAIN_CAUSAL_30D_SIGNAL_V1":
        raise ValueError("WRONG_ORIGINAL_SIGNAL_SCHEMA")
    if source.get("source_original") is not True or source.get("observations") != 182:
        raise ValueError("ORIGINAL_SIGNAL_PROVENANCE_NOT_DECLARED")
    if result.get("schema") != "V99_I1_ORIGINAL_180_CAUSAL_INTENTS_V1":
        raise ValueError("WRONG_INTENT_SCHEMA")
    if result.get("source_original_signal_sha256") != hashlib.sha256(raw).hexdigest():
        raise ValueError("ORIGINAL_SOURCE_SHA_MISMATCH")
    full = [(int(d.timestamp() * 1000), asset)
            for d in eligible() for asset in ("BTC", "ETH")]
    fixed = [(int(d.timestamp() * 1000), asset)
             for d in eligible(True) for asset in ("BTC", "ETH")]
    if len(full) != 182 or len(fixed) != 180 or full[:180] != fixed:
        raise ValueError("FIXED_GRID_CHANGED")
    observed = source.get("rows")
    intents = result.get("intents")
    if not isinstance(observed, list) or len(observed) != 182 or not isinstance(intents, list) or len(intents) != 180:
        raise ValueError("INCOMPLETE_INTENT_OR_SOURCE_GRID")
    positives = 0
    for i, (clock, asset) in enumerate(full):
        fold = next((f for f in range(1, 6)
                     if FOLD_EDGES[f-1] <= clock < FOLD_EDGES[f]), None)
        row = observed[i]
        if (not isinstance(row, dict) or row.get("decision_ms") != clock
                or row.get("asset") != asset or row.get("fold") != fold
                or row.get("signal") not in SIGNALS):
            raise ValueError("ORIGINAL_SIGNAL_GRID_MISMATCH")
        if i < 180:
            expected = {"decision_ms": clock, "asset": asset,
                        "fold": fold, "signal": row["signal"]}
            if intents[i] != expected:
                raise ValueError("ORIGINAL_INTENT_FIDELITY_FAILURE")
            positives += row["signal"] == "POSITIVE_EX_ANTE_PREMIUM"
    digest = hashlib.sha256(json.dumps(intents, sort_keys=True, separators=(",", ":"),
                                      allow_nan=False).encode("utf-8")).hexdigest()
    if result.get("canonical_intents_sha256") != digest:
        raise ValueError("CANONICAL_INTENT_DIGEST_MISMATCH")
    if (result.get("positive_fixed_intents") != positives
            or result.get("fixed_asset_week_intents") != 180
            or result.get("original_signal_observations") != 182
            or result.get("right_censored_excluded_asset_weeks") != 2):
        raise ValueError("FORGED_INTENT_COUNTS")
    for k in ("options_source_authenticated", "historical_native_fees_authenticated",
              "original_historical_economic_train_executed", "actions_or_cash_veto_certified",
              "validation_opened", "holdout_opened", "orders_enabled",
              "promotion_authorized"):
        if result.get(k) is not False:
            raise ValueError("FORGED_OR_UNSAFE_ECONOMIC_CERTIFICATION")
    return {"original_intents_verified": 180, "positive_fixed_intents": positives,
            "original_options_lifecycles_certified": 0, "promotion_authorized": False}


def main(original, output):
    report = verify(original, output)
    # Falsify changed intent and forged source digest, without changing original files.
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        doc = json.loads(Path(output).read_text(encoding="utf-8"))
        doc["intents"][0]["signal"] = (
            "NO_PREMIUM" if doc["intents"][0]["signal"] != "NO_PREMIUM"
            else "POSITIVE_EX_ANTE_PREMIUM")
        p = Path(tmp) / "forged.json"
        p.write_text(json.dumps(doc), encoding="utf-8")
        try:
            verify(original, p)
        except ValueError as e:
            assert str(e) == "ORIGINAL_INTENT_FIDELITY_FAILURE"
        else:
            raise AssertionError("FORGED_ORIGINAL_INTENT_ACCEPTED")
        doc = json.loads(Path(output).read_text(encoding="utf-8"))
        doc["source_original_signal_sha256"] = "0"*64
        p.write_text(json.dumps(doc), encoding="utf-8")
        try:
            verify(original, p)
        except ValueError as e:
            assert str(e) == "ORIGINAL_SOURCE_SHA_MISMATCH"
        else:
            raise AssertionError("FORGED_ORIGINAL_SOURCE_SHA_ACCEPTED")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_original_intent_oracle ORIGINAL_JSON MANIFEST_JSON")
    main(*sys.argv[1:])
