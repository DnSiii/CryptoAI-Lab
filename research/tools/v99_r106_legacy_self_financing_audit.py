"""Read-only C1/C2 legacy TRAIN accounting audit. No candidate, retune, or orders.

Uses frozen target-weight journals; their cost-dependent policies are NOT re-simulated.
This synthetic derivatives variation-margin model has no native funding/fills.
"""
import csv
import hashlib
import json
import math
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from research.tools import v99_r106_c1_core as c1core
from research.tools import v99_r106_c1_accounting as c1acc
from research.tools import v99_r106_c1_journal_oracle as c1oracle
from research.tools import v99_r106_c1_train_gate as c1gate
from research.tools import v99_r106_c2_engine as c2
from research.tools import v99_r106_c2_oracle as c2oracle

SCENARIOS = (("severe", 0.0007), ("supersevere", 0.0014))
# Published 2026-10-16 rejected TRAIN economics; coarse tolerance is for
# archived report rounding only. This is an integrity check, NOT an alpha gate.
ARCHIVED_ROI = {
    "C1": {"severe": -0.207856, "supersevere": -0.034081},
    "C2": {"severe": -0.297475, "supersevere": -0.306009},
}
OUT = Path("research_evidence/v99_r106_legacy_self_financing_audit.json")


def check_cost(cost):
    # Model input guard only: passing does not authenticate historical fee tiers.
    if not math.isfinite(cost) or not 0 <= cost <= .01:
        raise ValueError("invalid_model_cost")


def check_hourly_utc(rows):
    previous = None
    for row in rows:
        try:
            stamp = datetime.fromisoformat(row["time"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid_utc_journal_timestamp") from exc
        if stamp.tzinfo is None or stamp.utcoffset() != timedelta(0):
            raise ValueError("non_utc_journal_timestamp")
        if previous is not None and stamp - previous != timedelta(hours=1):
            raise ValueError("nonhourly_journal_grid")
        previous = stamp




def close(a, b, label, tol=1e-10):
    if not (math.isfinite(a) and math.isfinite(b)) or abs(a-b) > tol * max(1., abs(a), abs(b)):
        raise ValueError("self_financing_mismatch_" + label)


def fee_solution(nav_pre, q_old, prices, target, cost):
    """Unique nonnegative fee satisfying post-fee target notional identity."""
    if (not math.isfinite(nav_pre) or nav_pre <= 0 or
        not math.isfinite(cost) or not 0 <= cost <= 0.01 or
        any(not math.isfinite(x) or x <= 0 for x in prices) or
        any(not math.isfinite(x) for x in (*q_old, *target)) or
        sum(map(abs, target)) > 1.3 + 1e-10):
        raise ValueError("invalid_self_financing_input")

    def required(fee):
        nav_after = nav_pre - fee
        return cost * sum(abs(target[j] * nav_after - q_old[j] * prices[j])
                          for j in range(2))

    if required(nav_pre) >= nav_pre:
        raise ValueError("insufficient_equity_for_rebalance")
    lo, hi = 0., nav_pre
    for _ in range(80):
        mid = (lo + hi) / 2.
        if mid < required(mid):
            lo = mid
        else:
            hi = mid
    fee = (lo + hi) / 2.
    close(fee, required(fee), "implicit_fee", 1e-12)
    return fee


def replay_targets(target_rows, opens, cost):
    """Rebalance at OPEN, mark carried signed contracts at NEXT OPEN."""
    if not target_rows or len(target_rows) != len(opens):
        raise ValueError("target_price_coverage")
    check_cost(cost)
    check_hourly_utc(target_rows)
    q_prev = (0., 0.)
    prev_prices = None
    nav_post_fee = 1.
    trace = []
    for k, (row, prices) in enumerate(zip(target_rows, opens)):
        prices = tuple(map(float, prices))
        nxt = opens[k+1] if k+1 < len(opens) else row["next_prices"]
        nxt = tuple(map(float, nxt))
        w = tuple(float(row[key]) for key in ("btc_weight", "eth_weight"))
        if any(not math.isfinite(x) or x <= 0 for x in (*prices, *nxt)):
            raise ValueError("invalid_market_price")
        nav_pre = nav_post_fee
        if prev_prices is not None:
            nav_pre += sum(q_prev[j] * (prices[j] - prev_prices[j]) for j in range(2))
        fee = fee_solution(nav_pre, q_prev, prices, w, cost)
        nav_post_fee = nav_pre - fee
        q_new = tuple(w[j] * nav_post_fee / prices[j] for j in range(2))
        notional_turn = sum(abs(q_new[j] - q_prev[j]) * prices[j] for j in range(2))
        close(fee, cost * notional_turn, "trade_fee")
        nav_next = nav_post_fee + sum(q_new[j] * (nxt[j] - prices[j]) for j in range(2))
        if not math.isfinite(nav_next) or nav_next <= 0:
            raise ValueError("liquidated_diagnostic_nav")
        trace.append({
            "time": row["time"], "prices": prices, "next_prices": nxt,
            "weights": w, "q_old": q_prev, "q_new": q_new,
            "nav_pre": nav_pre, "fee": fee, "nav_post_fee": nav_post_fee,
            "nav_next": nav_next, "notional_turn": notional_turn,
            "legacy_turn": float(row["turnover"]),
            "legacy_fee_fraction": float(row["fee"]),
        })
        prev_prices = prices
        q_prev = q_new
    verify_trace(trace, cost)
    return trace


def verify_trace(trace, cost):
    """Independent conservation oracle: never invokes the fee solver."""
    if not trace:
        raise ValueError("empty_trace")
    check_cost(cost)
    check_hourly_utc(trace)
    prev_q = (0., 0.)
    prev_prices = None
    prev_nav_post = 1.
    for k, r in enumerate(trace):
        p = r["prices"]
        nxt = r["next_prices"]
        q = r["q_new"]
        w = r["weights"]
        if any(not math.isfinite(x) for x in (*p, *nxt, *q, *w,
                                             r["nav_pre"], r["nav_post_fee"],
                                             r["nav_next"], r["fee"], r["notional_turn"])):
            raise ValueError("nonfinite_trace")
        if sum(abs(x) for x in w) > 1.3 + 1e-10:
            raise ValueError("independent_oracle_overgross_target")
        if (r["nav_pre"] <= 0 or r["nav_post_fee"] <= 0 or
            r["nav_next"] <= 0 or r["fee"] < 0 or r["notional_turn"] < 0):
            raise ValueError("independent_oracle_invalid_nav_or_cost")
        if any(x <= 0 for x in (*p, *nxt)):
            raise ValueError("invalid_price")
        for j in range(2):
            close(r["q_old"][j], prev_q[j], "carried_contracts")
        pre = prev_nav_post + (sum(prev_q[j] * (p[j] - prev_prices[j])
                                   for j in range(2)) if prev_prices else 0.)
        close(r["nav_pre"], pre, "pretrade_nav")
        turn = sum(abs(q[j] - prev_q[j]) * p[j] for j in range(2))
        close(r["notional_turn"], turn, "notional_turnover")
        close(r["fee"], cost * turn, "fee")
        post = pre - cost * turn
        if post <= 0:
            raise ValueError("nonpositive_nav")
        close(r["nav_post_fee"], post, "post_fee_nav")
        for j in range(2):
            close(q[j] * p[j], w[j] * post, "post_fee_target")
        next_nav = post + sum(q[j] * (nxt[j] - p[j]) for j in range(2))
        if next_nav <= 0:
            raise ValueError("independent_oracle_nonpositive_next_nav")
        close(r["nav_next"], next_nav, "next_open_nav")
        if k+1 < len(trace):
            if trace[k+1]["time"] <= r["time"]:
                raise ValueError("noncausal_journal_order")
            for j in range(2):
                close(nxt[j], trace[k+1]["prices"][j], "next_open_alignment")
        prev_q, prev_prices, prev_nav_post = q, p, post
    return True


def read_journal(path, fields, indices, b):
    with path.open(newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        if rd.fieldnames != list(fields):
            raise ValueError("legacy_journal_schema")
        rows = list(rd)
    if len(rows) != len(indices):
        raise ValueError("legacy_journal_coverage")
    for i, row in zip(indices, rows):
        if row["time"] != b[i][0].isoformat():
            raise ValueError("legacy_journal_time")
    return rows


def forensic_summary(trace, legacy_report, cost):
    return {
        "original_legacy_roi_archived_diagnostic": legacy_report["roi"],
        "conditional_self_financing_nav_change_NOT_STRATEGY_ROI": trace[-1]["nav_next"] - 1.,
        "legacy_weight_delta_turnover_sum": sum(r["legacy_turn"] for r in trace),
        "quantity_based_turnover_over_pretrade_nav_sum": sum(r["notional_turn"] / r["nav_pre"] for r in trace),
        "original_legacy_fee_fraction_sum": sum(r["legacy_fee_fraction"] for r in trace),
        "quantity_based_fee_paid_initial_nav_units": sum(r["fee"] for r in trace),
        "legacy_zero_turnover_but_quantity_rebalance_hours": sum(
            r["legacy_turn"] < 1e-12 and r["notional_turn"] > 1e-10 for r in trace),
        "rows": len(trace),
        "cost_per_side": cost,
        "trace_sha256": hashlib.sha256(
            json.dumps(trace, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "independent_conservation_verified": True,
        "exchange_native_fee_funding_fills_verified": False,
        "promotable": False,
    }


def run(out=OUT):
    btc = Path("data/canonical/BTCUSDT_1h.csv")
    eth = Path("data/canonical/ETHUSDT_1h.csv")
    if not btc.is_file() or not eth.is_file():
        raise ValueError("ORIGINAL_TRAIN_CANONICAL_SOURCE_ABSENT")
    b, bh = c1core.load_train(btc)
    e, eh = c1core.load_train(eth)
    c1core.assert_train_coverage(b)
    c1core.assert_train_coverage(e)
    if len(b) != len(e) or any(x[0] != y[0] for x, y in zip(b, e)):
        raise ValueError("unaligned_original_sources")
    if b[-1][0] >= c1core.END:
        raise ValueError("sealed_partition_access")
    indices = [i for i in range(721, len(b)-1) if b[i][0] >= c1core.START]
    opens = [(b[i][1], e[i][1]) for i in indices]
    next_last = (b[indices[-1]+1][1], e[indices[-1]+1][1])
    result = {
        "status": "READ_ONLY_LEGACY_ACCOUNTING_DIAGNOSTIC_NO_PROMOTION",
        "prereg": "research/V99_R106_LEGACY_SELF_FINANCING_ACCOUNTING_AUDIT_PREREG_20261030.md",
        "btc_original_train_sha256": bh, "eth_original_train_sha256": eh,
        "train_end_exclusive": c1core.END.isoformat(),
        "sealed_validation_parsed": False, "final_holdout_parsed": False,
        "frozen_modified": False, "paper_modified": False, "real_orders_enabled": False,
        "new_economic_candidate": False, "promotion_authorized": False,
        "funding_or_native_fills_verified": False, "systems": {},
    }
    with tempfile.TemporaryDirectory(prefix="v99_legacy_accounting_") as td:
        root = Path(td)
        c1_results, c2_results = {}, {}
        legacy_c1, legacy_c2 = {}, {}
        for name, cost in SCENARIOS:
            p1 = root / ("c1_" + name + ".csv")
            r1 = c1acc.simulate(b, e, cost, p1)
            legacy_c1[name] = r1
            close(r1["roi"], ARCHIVED_ROI["C1"][name], "archived_c1_roi", 1e-5)
            original1 = c1oracle.verify(b, e, p1, cost)
            close(original1["independent_net_roi"], r1["roi"], "legacy_c1_oracle")
            rows1 = read_journal(p1, c1oracle.FIELDS, indices, b)
            rows1[-1]["next_prices"] = next_last
            trace1 = replay_targets(rows1, opens, cost)
            c1_results[name] = forensic_summary(trace1, r1, cost)

            p2 = root / ("c2_" + name + ".csv")
            # Only unchanged archived C2 targets; no optimization.
            if name == "severe":
                targets2 = c2.path_targets(b, e)
                if len(targets2) != len(indices):
                    raise ValueError("c2_train_scope_mismatch")
            r2 = c2.simulate(b, e, targets2, cost, p2)
            legacy_c2[name] = r2
            close(r2["roi"], ARCHIVED_ROI["C2"][name], "archived_c2_roi", 1e-5)
            original2 = c2oracle.verify(b, e, p2, cost)
            close(original2["roi"], r2["roi"], "legacy_c2_oracle")
            rows2 = read_journal(p2, c2.JOURNAL_FIELDS, indices, b)
            rows2[-1]["next_prices"] = next_last
            trace2 = replay_targets(rows2, opens, cost)
            c2_results[name] = forensic_summary(trace2, r2, cost)

        if all(c1gate.gates(legacy_c1["severe"], legacy_c1["supersevere"]).values()):
            raise ValueError("archived_c1_rejection_not_reproduced")
        if all(c2.gates(legacy_c2["severe"], legacy_c2["supersevere"], True).values()):
            raise ValueError("archived_c2_rejection_not_reproduced")
        result["historical_C1_C2_rejections_reconfirmed"] = True
        result["systems"]["C1_PERMANENTLY_REJECTED"] = c1_results
        result["systems"]["C2_PERMANENTLY_REJECTED"] = c2_results
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"],
                      "systems": {k: {s: {"rows": v["rows"],
                            "legacy_turnover": v["legacy_weight_delta_turnover_sum"],
                            "quantity_turnover": v["quantity_based_turnover_over_pretrade_nav_sum"],
                            "missing_rebalances": v["legacy_zero_turnover_but_quantity_rebalance_hours"]}
                          for s, v in ss.items()} for k, ss in result["systems"].items()},
                      "promotion_authorized": False}, sort_keys=True))
    return result


if __name__ == "__main__":
    run()
