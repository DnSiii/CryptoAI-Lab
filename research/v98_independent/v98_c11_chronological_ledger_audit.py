"""Fail-closed independent C11 ledger audit; descriptive training evidence, never promotion."""
import argparse
import json
import math
from pathlib import Path

FOLDS = ((744, 9504, "2023"), (9504, 18288, "2024"), (18288, 27048, "2025"))
SCENARIOS = ("1x", "2x", "4x")

def audit(summary_path):
    summary = json.loads(Path(summary_path).read_text())
    if summary.get("holdout_accessed") is not False or summary.get("source") != "AUTHENTICATED_CLEAN4":
        raise ValueError("C11_UNAUTHENTICATED_OR_HOLDOUT")
    report = {"status": "TRAINING_AUDIT_ONLY_NO_PROMOTION", "scenarios": {}}
    for scenario in SCENARIOS:
        s = summary["results"][scenario]
        if s["hours"] != 27048:
            raise ValueError("C11_INCOMPLETE_HISTORY")
        path = Path(summary_path).with_name(Path(summary_path).stem + "_" + scenario + "_ledger.jsonl")
        entries = [json.loads(line) for line in path.open()]
        if len(entries) != 27047 or any(e["index"] != i for i, e in enumerate(entries, 1)):
            raise ValueError("C11_NONCONTIGUOUS_LEDGER")
        previous_equity = 10000.0
        running_peak = previous_equity
        independently_measured_max_dd = 0.0
        for e in entries:
            if not all(math.isfinite(float(e[k])) for k in ("equity", "pre_fill_equity", "turnover", "cost_return", "gross_return", "funding_return")):
                raise ValueError("C11_NONFINITE_LEDGER")
            if e["equity"] <= 0 or e["turnover"] < 0 or e["cost_return"] < 0:
                raise ValueError("C11_INVALID_ACCOUNT")
            if not math.isclose(e["equity"], e["pre_fill_equity"] * (1 - e["cost_return"]), rel_tol=1e-10, abs_tol=1e-7):
                raise ValueError("C11_COST_RECONCILIATION")
            assets = {"BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"}
            if set(e["gross_by_asset"]) != assets or set(e["funding_by_asset"]) != assets:
                raise ValueError("C11_ASSET_LEDGER_INCOMPLETE")
            if not math.isclose(sum(e["gross_by_asset"].values()), e["gross_return"], rel_tol=1e-10, abs_tol=1e-10):
                raise ValueError("C11_GROSS_ASSET_RECONCILIATION")
            if not math.isclose(sum(e["funding_by_asset"].values()), e["funding_return"], rel_tol=1e-10, abs_tol=1e-10):
                raise ValueError("C11_FUNDING_ASSET_RECONCILIATION")
            expected_pre_fill = previous_equity * (1 + e["gross_return"] + e["funding_return"])
            if not math.isclose(expected_pre_fill, e["pre_fill_equity"], rel_tol=1e-10, abs_tol=1e-7):
                raise ValueError("C11_HOURLY_EQUITY_CHAIN")
            if not math.isclose(e["cost_return"], e["turnover"] * .0006 * float(scenario[0]), rel_tol=1e-10, abs_tol=1e-10):
                raise ValueError("C11_COST_SCALE_MISMATCH")
            if set(e["weights_before_fill"]) != assets or set(e["weights_after_fill"]) != assets:
                raise ValueError("C11_WEIGHTS_INCOMPLETE")
            expected_turnover = sum(abs(e["weights_after_fill"][a] - e["weights_before_fill"][a]) for a in assets)
            if not math.isclose(expected_turnover, e["turnover"], rel_tol=1e-10, abs_tol=1e-10):
                raise ValueError("C11_TURNOVER_RECONCILIATION")
            running_peak = max(running_peak, e["pre_fill_equity"], e["equity"])
            independently_measured_max_dd = max(
                independently_measured_max_dd,
                1 - e["pre_fill_equity"] / running_peak,
                1 - e["equity"] / running_peak,
            )
            previous_equity = e["equity"]
            w = e["weights_after_fill"]
            if set(w) != {"BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"} or any(not 0 <= v <= .42000001 for v in w.values()) or sum(w.values()) > .78000001:
                raise ValueError("C11_EXPOSURE_LIMIT")
        final_equity = entries[-1]["equity"] * s["last_mark_factor"]
        running_peak = max(running_peak, final_equity)
        independently_measured_max_dd = max(independently_measured_max_dd, 1 - final_equity / running_peak)
        if not math.isclose(independently_measured_max_dd, s["max_drawdown"], rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError("C11_MAX_DRAWDOWN_RECONCILIATION")
        if not math.isclose(sum(e["turnover"] for e in entries), s["total_turnover"], rel_tol=1e-9, abs_tol=1e-7):
            raise ValueError("C11_TURNOVER_MISMATCH")
        if not math.isclose(sum(e["funding_return"] for e in entries), s["funding_return_sum"], rel_tol=1e-9, abs_tol=1e-7):
            raise ValueError("C11_FUNDING_MISMATCH")
        if not math.isclose(entries[-1]["equity"] * s["last_mark_factor"], s["final_equity"], rel_tol=1e-10, abs_tol=1e-6):
            raise ValueError("C11_FINAL_EQUITY_MISMATCH")
        # Fold returns are equity changes, not independent starting-capital backtests.
        folds = {}
        for start, stop, label in FOLDS:
            section = entries[start-1:stop-1]
            if len(section) != stop-start:
                raise ValueError("C11_FOLD_LENGTH")
            base = entries[start-2]["equity"]
            end = section[-1]["equity"]
            changes = [section[0]["equity"]/base-1] + [b["equity"]/a["equity"]-1 for a,b in zip(section, section[1:])]
            gains = sum(max(x,0) for x in changes)
            losses = -sum(min(x,0) for x in changes)
            peak = base
            dd = 0.
            for e in section:
                peak = max(peak,e["equity"])
                dd = max(dd,1-e["equity"]/peak)
            days = [section[j:j+24] for j in range(0,len(section),24)]
            positive_days = sum(day[-1]["equity"] > (base if j==0 else days[j-1][-1]["equity"]) for j,day in enumerate(days))
            folds[label] = {"net_return":end/base-1, "max_drawdown_sampled":dd,
                            "hourly_profit_factor":gains/losses if losses else None,
                            "positive_hours":sum(x>0 for x in changes),
                            "win_rate_hourly":sum(x>0 for x in changes)/len(changes),
                            "positive_days":positive_days, "total_days":len(days),
                            "turnover":sum(e["turnover"] for e in section)}
        report["scenarios"][scenario] = {"final_equity_reported":s["final_equity"], "folds":folds,
                                         "max_drawdown_independently_reconciled":independently_measured_max_dd,
                                         "gross_exposure_peak":max(sum(e["weights_after_fill"].values()) for e in entries)}
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--summary",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    if "v98_independent" not in args.output.absolute().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    report=audit(args.summary)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print("C11_TRAINING_FOLDS_AUDITED_NO_PROMOTION")

if __name__ == "__main__":
    main()
