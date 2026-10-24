"""G1 fixed-rule original TRAIN entry feasibility; no PnL, orders, validation or holdout.

Uses original OKX spot 1H CLOSE receipts and independently audited G1 original
dated-futures hourly derived tapes. An absent futures trade bar is UNKNOWN,
never zero basis. Preregistered 2026-10-23 rules are not optimized.
"""
from __future__ import annotations
import hashlib
import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from research.tools.v99_r106_d1_real_train_source_join import START, END, HOUR, FOLD_EDGES
from research.tools.v99_r106_g1_full_train_original_monthly import EXPIRIES, MONTHS
from research.verification.independent_d1_native_train_receipts import verify, distinct

UTC = timezone.utc
ASSETS = ("BTC", "ETH")
SEVERE_ENTRY_MIN = Decimal("0.0073")  # 0.48% round trip + 0.25% reserve
SUPERSEVERE_ENTRY_MIN = Decimal("0.0121")  # 0.96% round trip + 0.25% reserve
ANNUAL_MIN = Decimal("0.10")
FLAGS = dict(roi_computed=False, economic_train_executed=False, orders_enabled=False,
             validation_opened=False, holdout_opened=False, promotion_authorized=False)

def read(path):
    return json.loads(Path(path).read_bytes(), object_pairs_hook=distinct)

def spot_closes(root, asset):
    folder = Path(root) / (asset + "-USDT")
    manifest = read(Path(root) / "manifest.json")
    pages = manifest["instruments"][asset + "-USDT"]["pages"]
    closes = {}
    for meta in pages:
        raw = (folder / meta["file"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != meta["sha256"]:
            raise ValueError("SPOT_ORIGINAL_RECEIPT_SHA_MISMATCH")
        obj = json.loads(raw, object_pairs_hook=distinct)
        if obj.get("code") != "0":
            raise ValueError("SPOT_ORIGINAL_SOURCE_REJECTED")
        for row in obj["data"]:
            if len(row) < 9 or row[8] != "1":
                raise ValueError("SPOT_UNCONFIRMED_HOUR")
            t = int(row[0])
            if START <= t < END:
                price = Decimal(row[4])
                if not price.is_finite() or price <= 0:
                    raise ValueError("SPOT_INVALID_CLOSE")
                if t in closes and closes[t] != price:
                    raise ValueError("SPOT_CONFLICTING_CLOSE")
                closes[t] = price
    if len(closes) != (END - START) // HOUR:
        raise ValueError("SPOT_TRAIN_COVERAGE_INCOMPLETE")
    return closes

def futures_closes(root):
    out = defaultdict(dict)
    seen = set()
    manifests = sorted(Path(root).glob("batch*/manifest.json"))
    if len(manifests) != 5:
        raise ValueError("G1_SOURCE_BATCH_COUNT_MISMATCH")
    for manifest_path in manifests:
        manifest = read(manifest_path)
        if manifest.get("economic_train_executed") is not False:
            raise ValueError("G1_SOURCE_UNSAFE")
        folder = manifest_path.parent
        for rec in manifest["records"]:
            key = (rec["asset"], rec["month"])
            if key in seen:
                raise ValueError("G1_DUPLICATE_SOURCE_MONTH")
            seen.add(key)
            if rec["status"] == "NO_PREREG_WEEKLY_ELIGIBILITY":
                continue
            if rec["status"] != "SOURCE_COLLECTED":
                raise ValueError("G1_SOURCE_BATCH_BLOCKED")
            prefix = rec["asset"] + "_" + rec["month"]
            sources = [("candle", prefix + ".hourly.json", "hourly_sha256")]
            if "trade_zip_filename" in rec:
                sources.append(("trade", prefix + ".trades.json", "trade_hourly_sha256"))
            for kind, filename, digest_key in sources:
                raw = (folder / filename).read_bytes()
                if hashlib.sha256(raw).hexdigest() != rec[digest_key]:
                    raise ValueError("G1_DERIVED_SHA_MISMATCH")
                obj = json.loads(raw, object_pairs_hook=distinct)
                for inst, data in obj.items():
                    if inst not in rec["targets"]:
                        raise ValueError("G1_NON_PREREG_INSTRUMENT")
                    for bar in data["complete_hours"]:
                        t = bar["hour_ms"]
                        # Original UTC+8 monthly ZIPs can overlap the day before
                        # TRAIN_START; exclude pre-TRAIN boundary rows, never
                        # allow a sealed validation/holdout timestamp.
                        if t < START:
                            continue
                        if t >= END or t % HOUR:
                            raise ValueError("G1_SEALED_OR_OFFGRID_HOUR")
                        p = Decimal(bar["close"])
                        if not p.is_finite() or p <= 0:
                            raise ValueError("G1_BAD_FUTURE_CLOSE")
                        old = out[inst].get(t)
                        # Prefer original confirmed minute candles when available.
                        # Same-kind overlap must be identical; cross-kind difference is
                        # retained as a separate source disagreement, not averaged.
                        if old is None:
                            out[inst][t] = (p, kind)
                        elif old[1] == kind and old[0] != p:
                            raise ValueError("G1_SAME_SOURCE_CONFLICTING_CLOSE")
                        elif kind == "candle" and old[1] == "trade":
                            out[inst][t] = (p, kind)
    if seen != {(a,m) for a in ASSETS for m in MONTHS}:
        raise ValueError("G1_MISSING_SOURCE_MONTH")
    return out

def candidates():
    day = datetime.fromtimestamp(START/1000, UTC)
    end = datetime.fromtimestamp(END/1000, UTC)
    while day < end:
        if day.weekday() == 0 and day.hour == 0:
            eligible = [datetime.fromisoformat(e).replace(tzinfo=UTC)
                        for e in EXPIRIES if 30 <= (datetime.fromisoformat(e).replace(tzinfo=UTC)-day).total_seconds()/86400 <= 110]
            if eligible:
                yield day, min(eligible)
        day += timedelta(days=1)

def main(spot_root, future_root, out_dir):
    if verify(spot_root)["status"] != "INDEPENDENT_FOUR_LEG_TRAIN_SOURCE_COMPLETE_NO_ECONOMICS":
        raise ValueError("ORIGINAL_SPOT_INDEPENDENT_ORACLE_FAILED")
    spot = {asset: spot_closes(spot_root, asset) for asset in ASSETS}
    futures = futures_closes(future_root)
    events = []
    for day, expiry in candidates():
        t = int(day.timestamp()*1000)
        signal_hour = t - HOUR  # last COMPLETED 1H bar at Monday 00:00
        remaining = Decimal(str((expiry-day).total_seconds()/86400))
        for asset in ASSETS:
            inst = asset + "-USDT-" + expiry.strftime("%y%m%d")
            f = futures.get(inst, {}).get(signal_hour)
            s = spot[asset].get(signal_hour)
            fold = next((i+1 for i,(a,b) in enumerate(zip(FOLD_EDGES,FOLD_EDGES[1:]))
                         if a <= t < b), None)
            if fold is None or t >= END:
                raise ValueError("NONTRAIN_OR_NONFOLD_SIGNAL")
            row = dict(asset=asset, contract=inst, decision_ms=t,
                       signal_hour_ms=signal_hour, fold=fold,
                       days_to_expiry=str(remaining),
                       available=f is not None and s is not None,
                       source=f[1] if f else None)
            if row["available"]:
                premium = f[0] / s - 1
                annualized = premium * Decimal("365") / remaining
                row.update(premium=str(premium), annualized=str(annualized),
                           severe_entry=annualized > ANNUAL_MIN and premium > SEVERE_ENTRY_MIN,
                           supersevere_cost_envelope=annualized > ANNUAL_MIN and premium > SUPERSEVERE_ENTRY_MIN)
            events.append(row)
    stats = {}
    for asset in ASSETS:
        rows = [r for r in events if r["asset"] == asset]
        stats[asset] = dict(mondays=len(rows), known=sum(r["available"] for r in rows),
                            unknown=sum(not r["available"] for r in rows),
                            severe_signals=sum(r.get("severe_entry",False) for r in rows),
                            supersevere_signals=sum(r.get("supersevere_cost_envelope",False) for r in rows),
                            fold_known=[sum(r["available"] and r["fold"] == f for r in rows) for f in range(1,6)],
                            fold_severe_signals=[sum(r.get("severe_entry",False) and r["fold"] == f for r in rows) for f in range(1,6)])
    all_known = all(x["unknown"] == 0 for x in stats.values())
    any_signal = any(x["severe_signals"] for x in stats.values())
    # Conservative upper bound: an UNKNOWN original t-1 signal MAY have
    # entered, but only until its already-preregistered contractual expiry.
    # A fold with no possible open G1 pair cannot have positive G1 trading PnL.
    possible_exposure_folds = set()
    for event in events:
        if not event.get("severe_entry", False) and event["available"]:
            continue
        start = event["decision_ms"]
        expiry = datetime.strptime(event["contract"][-6:], "%y%m%d").replace(tzinfo=UTC)
        end = int((expiry + timedelta(hours=8)).timestamp()*1000)
        for fold,(a,b) in enumerate(zip(FOLD_EDGES,FOLD_EDGES[1:]),1):
            if start < b and end > a:
                possible_exposure_folds.add(fold)
    impossible_four_positive_folds = len(possible_exposure_folds) < 4
    status = ("PERMANENT_TRAIN_STRUCTURAL_REJECT_NO_RETUNE"
              if impossible_four_positive_folds
              else "ENTRY_SIGNAL_PRESENT_ECONOMIC_TRAIN_STILL_BLOCKED" if any_signal
              else "ENTRY_GATE_INCOMPLETE_ORIGINAL_SIGNAL_HOURS")
    report = dict(schema="G1_ORIGINAL_TRAIN_PREREG_ENTRY_GATE_V1",
                  possible_exposure_folds=sorted(possible_exposure_folds),
                  max_possible_positive_trading_folds=len(possible_exposure_folds),
                  severe_four_positive_folds_structurally_impossible=impossible_four_positive_folds,
                  unknown_signal_hours_conservatively_counted_as_possible_entries=True,
                  preregistration="research/V99_R106_G1_DATED_FUTURES_PREREG_20261023.md",
                  original_futures_audit_run=40052913340,
                  original_spot_receipt_run=40019588739,
                  status=status, stats=stats,
                  events=events, **FLAGS)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out/"g1_entry_gate.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k != "events"},sort_keys=True))
    return report

if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python -m research.tools.v99_r106_g1_original_train_entry_gate SPOT FUTURES OUT")
    main(*sys.argv[1:])
