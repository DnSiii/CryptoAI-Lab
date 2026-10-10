"""V99 R106 Phase195-BJ: fail-closed prepublication integrity gate.

Read-only comparison against durable paper-results HEAD. This never authorizes
promotion or trades; the five historical and forward tracks remain distinct.
"""
from __future__ import annotations

import json
import math
import subprocess
from datetime import datetime, timedelta

NAMES = ("r98", "f1", "f3", "f7", "f12")
LEDGER_PATH = "reports/paper_v99_research_ledger.json"
MAX_OPERATIONS = 1500


def strict_json(raw):
    def reject(value):
        raise ValueError("nonfinite JSON constant " + value)
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result
    result = json.loads(raw, parse_constant=reject, object_pairs_hook=unique)
    def walk(value):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("nonfinite numeric value")
        if isinstance(value, dict):
            for child in value.values():
                walk(child)
        if isinstance(value, list):
            for child in value:
                walk(child)
    walk(result)
    if not isinstance(result, dict):
        raise ValueError("ledger object required")
    return result


def utc(value):
    if not isinstance(value, str):
        raise ValueError("timestamp string required")
    t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if t.tzinfo is None or t.utcoffset() != timedelta(0):
        raise ValueError("explicit UTC required")
    return t


def indexed(rows, hourly=False):
    if not isinstance(rows, list) or not rows:
        raise ValueError("empty series")
    result, last = {}, None
    for row in rows:
        t = utc(row["timestamp"])
        if last is not None and (t <= last or (hourly and t-last != timedelta(hours=1))):
            raise ValueError("duplicate, unordered or gapped timestamps")
        if hourly and (t.minute or t.second or t.microsecond):
            raise ValueError("whole-hour paper timestamps required")
        result[t] = row
        last = t
    return result


def operations(rows):
    if not isinstance(rows, list):
        raise ValueError("missing operations")
    last, seen = None, set()
    for row in rows:
        t = utc(row["timestamp"])
        key = (t, str(row["symbol"]))
        if (last is not None and t < last) or key in seen:
            raise ValueError("unordered or duplicate symbol-hour operations")
        seen.add(key)
        last = t
    return rows


def audit(old, new):
    for item in (old, new):
        if item.get("mode") != "PAPER_ONLY" or item.get("real_orders_enabled") is not False:
            raise ValueError("paper-only, no real orders required")
        if item.get("same_boundary_for_all_variants") is not True:
            raise ValueError("shared boundary required")
        if set(item.get("variants", {})) != set(NAMES) or set(item.get("backtest_reference", {})) != set(NAMES):
            raise ValueError("five preregistered variants required")
    boundary = utc(old["paper_start_after_timestamp"])
    if utc(new["paper_start_after_timestamp"]) != boundary:
        raise ValueError("paper boundary moved")
    old_latest, new_latest = utc(old["latest_data_timestamp"]), utc(new["latest_data_timestamp"])
    if new_latest < old_latest:
        raise ValueError("latest data regressed")
    issues = {}
    for name in NAMES:
        before, after = old["variants"][name], new["variants"][name]
        if before.get("real_orders_enabled") is not False or after.get("real_orders_enabled") is not False:
            raise ValueError(name + ": real-order flag invalid")
        if utc(before["paper_start_after_timestamp"]) != boundary or utc(after["paper_start_after_timestamp"]) != boundary:
            raise ValueError(name + ": variant boundary moved")
        p, q = indexed(before["equity_curve"], True), indexed(after["equity_curve"], True)
        if next(iter(p)) != boundary or next(iter(q)) != boundary:
            raise ValueError(name + ": paper must start at boundary")
        faults = []
        stable_fields = ("track", "label", "name", "status", "base_capital_brl",
                         "paper_start_after_timestamp", "effective_base_timestamp")
        if any(before.get(field) != after.get(field) for field in stable_fields):
            faults.append("variant_identity_or_status_changed")
        missing = set(p)-set(q)
        changed = [t for t in p.keys() & q.keys() if p[t] != q[t]]
        if missing:
            faults.append("missing_published_hours:" + str(len(missing)))
        if changed:
            faults.append("rewritten_published_hours:" + str(len(changed)) + ";first=" + min(changed).isoformat())
        if max(q) != new_latest:
            faults.append("latest_paper_hour_mismatch")
        h, k = indexed(old["backtest_reference"][name]["curve"]), indexed(new["backtest_reference"][name]["curve"])
        after_boundary = sum(t >= boundary for t in h) + sum(t >= boundary for t in k)
        if after_boundary:
            faults.append("forward_mislabeled_as_backtest:" + str(after_boundary))
        if old["backtest_reference"][name] != new["backtest_reference"][name]:
            faults.append("historical_backtest_or_metrics_changed")
        op, oq = operations(before.get("operations", [])), operations(after.get("operations", []))
        if len(op) >= MAX_OPERATIONS or len(oq) >= MAX_OPERATIONS:
            faults.append("operations_capped_unverifiable")
        elif oq[:len(op)] != op:
            faults.append("operations_prefix_rewritten")
        issues[name] = faults
    passed = all(not v for v in issues.values())
    return {
        "status": "PREFIX_PASS_NOT_PROMOTION" if passed else "DATA_ONLY_HOLD",
        "publication_authorized": passed,
        "promotion_authorized": False,
        "boundary": boundary.isoformat(),
        "published_latest": old_latest.isoformat(),
        "candidate_latest": new_latest.isoformat(),
        "variants": issues,
    }


def load_published_from_git():
    # An explicit fetch avoids reliance on a stale local ref or a reused FETCH_HEAD.
    subprocess.run(["git", "fetch", "--no-tags", "origin", "paper-results"],
                   check=True, capture_output=True, timeout=90)
    sha = subprocess.run(["git", "rev-parse", "FETCH_HEAD"], check=True,
                         capture_output=True, text=True, timeout=10).stdout.strip()
    raw = subprocess.run(["git", "show", sha + ":" + LEDGER_PATH], check=True,
                         capture_output=True, text=True, timeout=20).stdout
    return strict_json(raw), sha


def enforce_published(candidate):
    baseline, sha = load_published_from_git()
    report = audit(baseline, candidate)
    report["published_commit"] = sha
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    if not report["publication_authorized"]:
        raise RuntimeError("V99 research paper publication BLOCKED: DATA_ONLY/HOLD")
    return report


if __name__ == "__main__":
    import sys
    from pathlib import Path
    a = strict_json(Path(sys.argv[1]).read_text(encoding="utf-8"))
    b = strict_json(Path(sys.argv[2]).read_text(encoding="utf-8"))
    verdict = audit(a, b)
    print(json.dumps(verdict, ensure_ascii=False, indent=2))
    sys.exit(0 if verdict["publication_authorized"] else 2)
