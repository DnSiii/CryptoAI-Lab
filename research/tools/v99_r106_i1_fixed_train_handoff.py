"""Fixed 90-week I1 original-signal / exact-contract lifecycle handoff.

Necessary source-only join, never a backtest, fill, option selector or promotion.
Preregistered before implementation in
research/V99_R106_I1_FIXED_90W_SIGNAL_TO_LIFECYCLE_HANDOFF_PREREG_20261027.md
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from research.tools.v99_r106_i1_lifecycle_daily_tape import audit, FIXED_SCHEMA
from research.verification.independent_v99_r106_i1_lifecycle_daily_oracle import verify
from research.tools.v99_r106_i1_full_archive_intake import eligible
from research.tools.v99_r106_d1_real_train_source_join import FOLD_EDGES

SIGNAL_SCHEMA = "V99_I1_ORIGINAL_TRAIN_CAUSAL_30D_SIGNAL_V1"
REPORT_SCHEMA = "V99_I1_FIXED_90W_ORIGINAL_SIGNAL_LIFECYCLE_HANDOFF_V1"
SIGNALS = ("POSITIVE_EX_ANTE_PREMIUM", "NO_PREMIUM", "NO_30D_HISTORY")
FLAGS = dict(economic_train_executed=False, historical_option_fills_certified=False,
             native_fee_tier_authenticated=False, native_margin_authenticated=False,
             certified_complete_option_lifecycles=0, validation_opened=False,
             holdout_opened=False, orders_enabled=False, promotion_authorized=False)


def _expected():
    return [(int(d.timestamp() * 1000), asset) for d in eligible(True)
            for asset in ("BTC", "ETH")]


def join_reports(signal: dict, source: dict, *, signal_sha256: str,
                 source_manifest_sha256: str) -> dict:
    """Reconcile immutable signal and fixed-tenor source grids, fail closed.

    Caller must independently replay original signal receipts and source bytes.
    """
    if (signal.get("schema") != SIGNAL_SCHEMA or signal.get("source_original") is not True
            or signal.get("observations") != 182 or signal.get("eligible_weeks") != 91
            or signal.get("economic_train_executed") is not False
            or signal.get("promotion_authorized") is not False):
        raise ValueError("UNVERIFIED_OR_NONORIGINAL_SIGNAL")
    if (source.get("schema") != "V99_I1_661_DAY_LIFECYCLE_DAILY_PRESENCE_REPORT_V1"
            or source.get("source_scope") != "FIXED_28_35D"
            or source.get("days") != 661 or source.get("asset_weeks") != 180
            or source.get("certified_complete_option_lifecycles") != 0
            or source.get("source_manifest_self_declared_not_vendor_certified") is not True
            or source.get("same_contract_pair_still_not_executable_or_settlement_certified") is not True):
        raise ValueError("UNVERIFIED_OR_NONFIXED_LIFECYCLE_SOURCE")
    for k in FLAGS:
        if k in source and source[k] is not FLAGS[k]:
            raise ValueError("FORGED_SOURCE_ECONOMIC_STATUS")
    rows = signal.get("rows")
    if not isinstance(rows, list) or len(rows) != 182:
        raise ValueError("MISSING_91_WEEK_ORIGINAL_SIGNAL")
    # The original signal has exactly 91 maturity-eligible 21-day Mondays;
    # fixed 28-day I1 contracts have exactly 90. The final two signal rows
    # must be excluded as RIGHT CENSORED, not counted as losing trades.
    from research.tools.v99_r106_i1_full_archive_intake import eligible as dates
    original_grid = [(int(d.timestamp()*1000), a) for d in dates(False)
                     for a in ("BTC", "ETH")]
    if [(r.get("decision_ms"), r.get("asset")) for r in rows] != original_grid:
        raise ValueError("FORGED_OR_REORDERED_SIGNAL_GRID")
    fixed_grid = _expected()
    if [(r.get("decision_ms"), r.get("asset")) for r in rows[:180]] != fixed_grid:
        raise ValueError("RIGHT_CENSORING_MISMATCH")
    if (source.get("fixture") not in (True, False)
            or type(source["fixture"]) is not bool):
        raise ValueError("UNBOUND_SOURCE_FIXTURE")
    weekly = source.get("weekly")
    if not isinstance(weekly, list) or len(weekly) != 180:
        raise ValueError("MISSING_FIXED_180_SOURCE_WEEKS")
    observed = []
    folds = {str(i): {"positive_signal": 0, "necessary_source": 0,
                      "intersection": 0} for i in range(1, 6)}
    for row, day, key in zip(rows[:180], weekly, fixed_grid):
        at, asset = key
        d = datetime.fromtimestamp(at / 1000, timezone.utc)
        fold = next((i for i in range(1, 6)
                     if FOLD_EDGES[i-1] <= at < FOLD_EDGES[i]), None)
        if (fold is None or row.get("fold") != fold
                or row.get("signal") not in SIGNALS
                or day.get("decision_utc") != d.date().isoformat()
                or day.get("asset") != asset):
            raise ValueError("FOLD_OR_SOURCE_DECISION_MISMATCH")
        necessary = day.get("causal_entry_and_same_contract_pair_presence")
        if type(necessary) is not bool:
            raise ValueError("UNVERIFIED_CAUSAL_SOURCE_FLAG")
        positive = row["signal"] == "POSITIVE_EX_ANTE_PREMIUM"
        both = positive and necessary
        bucket = folds[str(fold)]
        bucket["positive_signal"] += int(positive)
        bucket["necessary_source"] += int(necessary)
        bucket["intersection"] += int(both)
        observed.append({"decision_ms": at, "asset": asset, "fold": fold,
                         "positive_causal_signal": positive,
                         "necessary_same_contract_source": necessary,
                         "source_intersection_not_execution": both})
    if any(row.get("fold") != next((i for i in range(1, 6)
                  if FOLD_EDGES[i-1] <= row["decision_ms"] < FOLD_EDGES[i]), None)
           or row.get("signal") not in SIGNALS for row in rows[180:]):
        raise ValueError("FORGED_RIGHT_CENSORED_SIGNAL")
    return {"schema": REPORT_SCHEMA,
            "status": ("BLOCKED_FIXTURE_SOURCE_NOT_ORIGINAL"
                       if source["fixture"] else
                       "ORIGINAL_SOURCE_NECESSARY_ONLY_NOT_ECONOMICS"),
            "source_fixture": source["fixture"],
            "signal_sha256": signal_sha256,
            "source_manifest_sha256": source_manifest_sha256,
            "original_signal_asset_weeks": 182,
            "fixed_maturity_eligible_asset_weeks": 180,
            "right_censored_signal_asset_weeks": 2,
            "positive_signal_fixed_weeks": sum(v["positive_signal"] for v in folds.values()),
            "necessary_source_asset_weeks": sum(v["necessary_source"] for v in folds.values()),
            "signal_and_necessary_source_asset_weeks": sum(v["intersection"] for v in folds.values()),
            "source_manifest_vendor_certified": False,
            "fixed_selector_strikes_and_executable_quotes_verified": False,
            "native_economics_verified": False,
            "folds": folds, "rows": observed, **FLAGS}


def run(signal_path: str, archive_root: str, output_path: str,
        spot_root: str | None = None, dvol_root: str | None = None):
    signal_file, root, out = Path(signal_path), Path(archive_root), Path(output_path)
    if not signal_file.is_file():
        raise ValueError("ORIGINAL_CAUSAL_SIGNAL_MISSING")
    signal_bytes = signal_file.read_bytes()
    signal = json.loads(signal_bytes)
    if not (root / "manifest.json").is_file():
        raise ValueError("BLOCKED_ORIGINAL_LIFECYCLE_ARCHIVE_MISSING")
    manifest_bytes = (root / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest.get("schema") != FIXED_SCHEMA:
        raise ValueError("WRONG_FIXED_TENOR_SOURCE_MANIFEST")
    # A source_original boolean and a caller-provided SHA do NOT prove the
    # 182 decisions came from first-party OKX/DVOL receipts. The workflow's
    # upstream replay must not be the only line of defense: enforce it here.
    if type(manifest.get("fixture")) is not bool:
        raise ValueError("UNVERIFIED_SOURCE_FIXTURE_FLAG")
    if manifest["fixture"] is False:
        if not spot_root or not dvol_root:
            raise ValueError("ORIGINAL_SIGNAL_REPLAY_RECEIPTS_REQUIRED")
        from research.tools.v99_r106_e1_spot_engine import load_original_spot
        from research.tools.v99_r106_h1_dvol_spot_engine import load_original_dvol
        from research.verification.independent_v99_r106_i1_causal_signal_oracle import (
            verify as verify_original_signal,
        )
        try:
            prices = load_original_spot(Path(spot_root))
            dvol = load_original_dvol(Path(dvol_root))
            verify_original_signal(prices, dvol, signal)
        except (AssertionError, ValueError, KeyError, OSError) as exc:
            raise ValueError("ORIGINAL_SIGNAL_REPLAY_FAILED") from exc
    source = audit(root)
    verify(root, source)  # separate original-byte, 661-day oracle
    result = join_reports(signal, source,
                          signal_sha256=hashlib.sha256(signal_bytes).hexdigest(),
                          source_manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest())
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in
        ("status", "fixed_maturity_eligible_asset_weeks",
         "right_censored_signal_asset_weeks", "positive_signal_fixed_weeks",
         "signal_and_necessary_source_asset_weeks", "economic_train_executed",
         "promotion_authorized")}, sort_keys=True))
    return result


if __name__ == "__main__":
    if len(sys.argv) not in (4, 6):
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_fixed_train_handoff SIGNAL_JSON FULL_TRAIN_ARCHIVE_DIR OUT_JSON [ORIGINAL_OKX_ROOT ORIGINAL_DVOL_ROOT]")
    run(*sys.argv[1:])
