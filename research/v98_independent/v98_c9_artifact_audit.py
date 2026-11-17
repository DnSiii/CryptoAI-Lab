"""Independent C9 artifact gate: training-only, never promotes or opens holdout."""
import argparse
import json
import math
import zipfile
from pathlib import Path

ASSETS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")
SCENARIOS = ("1x", "2x", "4x")

def audit(archive):
    with zipfile.ZipFile(archive) as z:
        names = set(z.namelist())
        summary = json.loads(z.read("c9_composed_summary.json"))
        assert summary["source"] == "AUTHENTICATED_CLEAN4"
        assert summary["holdout_accessed"] is False
        assert summary["status"] == "C9_PREREGISTERED_TRAINING_ONLY_NO_PROMOTION"
        assert set(summary["results"]) == set(SCENARIOS)
        result = {}
        for scenario in SCENARIOS:
            name = f"c9_composed_summary_{scenario}_ledger.jsonl"
            assert name in names
            entries = [json.loads(line) for line in z.open(name)]
            assert len(entries) == 27047
            assert [r["index"] for r in entries] == list(range(1, 27048))
            assert summary["results"][scenario]["hours"] == 27048
            prev = 10000.
            positive, negative, wins, losses = 0., 0., 0, 0
            asset_gross = {a: 0. for a in ASSETS}
            max_exposure = 0.
            for r in entries:
                equity = float(r["equity"])
                assert math.isfinite(equity) and equity > 0
                change = equity / prev - 1
                if change > 0:
                    positive += change
                    wins += 1
                elif change < 0:
                    negative -= change
                    losses += 1
                for a in ASSETS:
                    asset_gross[a] += r["gross_by_asset"][a]
                max_exposure = max(max_exposure, sum(abs(v) for v in r["weights_after_fill"].values()))
                prev = equity
            assert max_exposure <= 0.750000001
            assert math.isfinite(summary["results"][scenario]["final_equity"])
            result[scenario] = {
                "final_equity_official": summary["results"][scenario]["final_equity"],
                "last_fill_equity": prev,
                "hourly_profit_factor_excluding_final_mark": positive / negative if negative else None,
                "hourly_win_rate_excluding_final_mark": wins / (wins + losses) if wins + losses else None,
                "max_gross_exposure": max_exposure,
                "gross_return_contribution_by_asset": asset_gross,
                "final_mark_not_in_ledger": True,
            }
        return {"status": "C9_TRAINING_AUDITED_NOT_VALIDATED", "results": result}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("artifact_zip", type=Path)
    args = p.parse_args()
    print(json.dumps(audit(args.artifact_zip), indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
