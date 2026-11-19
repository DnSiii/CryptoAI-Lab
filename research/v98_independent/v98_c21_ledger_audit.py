"""Independent V98 ledger arithmetic audit; training-only, never selects candidates.

Usage: python -m research.v98_independent.v98_c21_ledger_audit --summary result.json
The sibling *_1x_ledger.jsonl, *_2x_ledger.jsonl, *_4x_ledger.jsonl
must be downloaded from the SAME authenticated workflow artifact.
"""
import argparse
import json
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path

ASSETS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")
SCALES = ("1x", "2x", "4x")
TOL = 1e-9

def close(a, b):
    return math.isclose(a, b, rel_tol=TOL, abs_tol=TOL)

def audit(summary_path):
    summary_path = Path(summary_path)
    summary = json.loads(summary_path.read_text())
    if summary.get("source") != "AUTHENTICATED_CLEAN4" or summary.get("holdout_accessed") is not False:
        raise ValueError("SOURCE_OR_HOLDOUT_CONTRACT")
    if set(summary["results"]) != set(SCALES):
        raise ValueError("SCENARIOS_MISSING")
    report = {}
    for scenario in SCALES:
        path = summary_path.with_name(summary_path.stem + "_" + scenario + "_ledger.jsonl")
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        result = summary["results"][scenario]
        if len(rows) != result["hours"] - 1 or result["hours"] != 27048:
            raise ValueError("INCOMPLETE_HISTORY_" + scenario)
        prior_equity = 10000.
        prior_weights = dict.fromkeys(ASSETS, 0.)
        peak = prior_equity
        max_dd = 0.
        turnovers = []
        funding_sum = 0.
        day_end = {}
        year_end = {}
        year_start = {}
        year_hours = {}
        epoch = datetime(2022, 12, 1, tzinfo=timezone.utc)
        asset_gross = dict.fromkeys(ASSETS, 0.)
        asset_funding = dict.fromkeys(ASSETS, 0.)
        max_concentration = 0.
        for i, e in enumerate(rows, 1):
            if e["index"] != i or set(e["weights_before_fill"]) != set(ASSETS) or set(e["weights_after_fill"]) != set(ASSETS):
                raise ValueError("ROW_SCHEMA_OR_SEQUENCE")
            for field in ("gross_by_asset", "funding_by_asset"):
                if set(e[field]) != set(ASSETS):
                    raise ValueError("ASSET_ATTRIBUTION_SCHEMA")
            vals = [e[k] for k in ("equity","pre_fill_equity","turnover","cost_return","drawdown","gross_return","funding_return")]
            vals += list(e["weights_before_fill"].values()) + list(e["weights_after_fill"].values())
            vals += list(e["gross_by_asset"].values()) + list(e["funding_by_asset"].values())
            if not all(math.isfinite(float(v)) for v in vals):
                raise ValueError("NONFINITE_LEDGER")
            if e["equity"] <= 0 or e["pre_fill_equity"] <= 0 or e["turnover"] < -TOL or e["cost_return"] < -TOL:
                raise ValueError("NONPOSITIVE_EQUITY_OR_NEGATIVE_TRADING_COST")
            if not close(sum(e["gross_by_asset"].values()),e["gross_return"]) or not close(sum(e["funding_by_asset"].values()),e["funding_return"]):
                raise ValueError("ASSET_ATTRIBUTION_MISMATCH")
            expected_pre = prior_equity * (1 + e["gross_return"] + e["funding_return"])
            if not close(expected_pre, e["pre_fill_equity"]):
                raise ValueError("OPEN_MARK_RECONCILIATION")
            # Reconstruct drifted holdings independently of the runner's weights.
            factor = 1 + e["gross_return"] + e["funding_return"]
            if factor <= 0:
                raise ValueError("NONPOSITIVE_MARK_FACTOR")
            for a in ASSETS:
                if abs(prior_weights[a]) <= TOL and (abs(e["gross_by_asset"][a]) > TOL or abs(e["funding_by_asset"][a]) > TOL):
                    raise ValueError("UNHELD_ASSET_PNL")
                expected_weight = (prior_weights[a] + e["gross_by_asset"][a]) / factor
                if not close(expected_weight, e["weights_before_fill"][a]):
                    raise ValueError("PRE_FILL_WEIGHT_DRIFT_MISMATCH")
            turnover = sum(abs(e["weights_after_fill"][a]-e["weights_before_fill"][a]) for a in ASSETS)
            if not close(turnover,e["turnover"]):
                raise ValueError("TURNOVER_RECONCILIATION")
            expected_cost = turnover * .0006 * int(scenario[0])
            if not close(expected_cost,e["cost_return"]):
                raise ValueError("NATIVE_COST_RECONCILIATION")
            if not close(e["pre_fill_equity"]*(1-e["cost_return"]),e["equity"]):
                raise ValueError("FILL_EQUITY_RECONCILIATION")
            if any(e["weights_after_fill"][a] < -TOL for a in ASSETS):
                raise ValueError("UNREGISTERED_SHORT")
            gross_exposure = sum(abs(e["weights_after_fill"][a]) for a in ASSETS)
            if gross_exposure > .90 + TOL or max(e["weights_after_fill"].values()) > .40 + TOL:
                raise ValueError("EXPOSURE_CAP_VIOLATION")
            max_concentration = max(max_concentration,max(e["weights_after_fill"].values()))
            peak = max(peak,e["pre_fill_equity"],e["equity"])
            max_dd = max(max_dd,1-e["pre_fill_equity"]/peak,1-e["equity"]/peak)
            if not close(1-e["equity"]/peak,e["drawdown"]):
                raise ValueError("DRAWDOWN_RECONCILIATION")
            for a in ASSETS:
                asset_gross[a] += e["gross_by_asset"][a]
                asset_funding[a] += e["funding_by_asset"][a]
            turnovers.append(turnover)
            funding_sum += e["funding_return"]
            stamp = epoch + timedelta(hours=i)
            day_end[stamp.date().isoformat()] = e["equity"]
            yr = str(stamp.year)
            if yr not in year_start:
                year_start[yr] = 10000. if i == 1 else equity_before_year
            year_end[yr] = e["equity"]
            year_hours[yr] = year_hours.get(yr, 0) + 1
            equity_before_year = e["equity"]
            prior_equity = e["equity"]
            prior_weights = e["weights_after_fill"]
        final_equity = prior_equity * result["last_mark_factor"]
        if not close(final_equity,result["final_equity"]) or not close(sum(turnovers),result["total_turnover"]) or not close(funding_sum,result["funding_return_sum"]):
            raise ValueError("SUMMARY_RECONCILIATION")
        peak = max(peak,final_equity)
        max_dd = max(max_dd,1-final_equity/peak)
        if not close(max_dd,result["max_drawdown"]):
            raise ValueError("MAX_DRAWDOWN_RECONCILIATION")
        # Last mark is the final 2025-12-31 hourly mark, not another trade.
        year_end['2025'] = final_equity
        daily = [10000.] + [day_end[k] for k in sorted(day_end)]
        daily[-1] = final_equity
        annual = {y: {'start_equity': year_start[y], 'end_equity': year_end[y],
                      'return': year_end[y] / year_start[y] - 1,
                      'ledger_hours': year_hours[y]}
                  for y in sorted(year_end)}
        if not close(math.prod(1 + annual[y]['return'] for y in annual), final_equity / 10000.):
            raise ValueError('YEARLY_COMPOUND_RECONCILIATION')
        day_returns = [daily[i]/daily[i-1]-1 for i in range(1,len(daily))]
        report[scenario] = dict(rows=len(rows),final_equity=final_equity,
            max_drawdown=max_dd,positive_days=sum(r>0 for r in day_returns),
            total_days=len(day_returns),max_asset_weight=max_concentration,
            asset_gross_return_sum=asset_gross,asset_funding_return_sum=asset_funding,
            annual_training_only=annual,arithmetic_reconciled=True)
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--summary",type=Path,required=True)
    args=p.parse_args()
    if "v98_independent" not in args.summary.resolve().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    print(json.dumps(audit(args.summary),indent=2,sort_keys=True))

if __name__ == "__main__":
    main()
