from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r47_band_rebalanced_crash_shield as r47

BANDS = (0.01, 0.02, 0.03)
SUMMARY = PROJECT / "reports" / "candidate_v99_r52_band_sweep.json"


def main() -> None:
    runs = []
    for band in BANDS:
        pp = int(round(band * 100))
        report_path = PROJECT / "reports" / f"candidate_v99_r52_band_{pp}pp.json"
        r47.BAND = band
        r47.REPORT = report_path
        r47.main()

        report = json.loads(report_path.read_text())
        report["study"] = f"V99 R52 {pp}pp band-rebalanced crash shield"
        report["status"] = "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER"
        report["parent"] = "R37 exact signal/grid; only maintenance-band width differs"
        report["objective"] = (
            "calibrate the minimum maintenance needed to recover R37 tail protection without returning "
            "to hourly sleeve rebalancing; detector, safe-weight grid, destinations, timing, costs and "
            "benchmarks remain unchanged"
        )
        report["maintenance_band"] = band
        report["grid_policy"] = (
            "same predeclared R37 27-combination signal grid; R52 tests only three structural execution "
            "bands fixed before this run: 1pp, 2pp and 3pp"
        )
        if report.get("selected"):
            routing = report["selected"].get("routing", {})
            routing["band_absolute"] = band
            routing["execution_policy"] = (
                f"entry/exit rebalance plus maintenance only when realized safe allocation deviates "
                f"by more than {pp} percentage point(s)"
            )
        report_path.write_text(json.dumps(report, indent=2) + "\n")
        runs.append({
            "band": band,
            "report": str(report_path.relative_to(PROJECT)),
            "selected": report.get("selected"),
            "full_envelope": report.get("full_envelope"),
            "severe_envelope": report.get("severe_envelope"),
        })

    def rank_key(item: dict):
        sel = item.get("selected") or {}
        routing = sel.get("routing") or {}
        summary = sel.get("summary") or {}
        isolated = sel.get("isolated") or {}
        y1 = isolated.get("365") or {}
        return (
            bool(sel.get("dominant_gate_passed", False)),
            float(sel.get("score", -1e18)),
            float(summary.get("return", -1e18)),
            -abs(float(summary.get("max_drawdown", -1e9))),
            -abs(float(summary.get("worst_day", -1e9))),
            float(y1.get("return", -1e18)),
            -int(routing.get("route_changes", 10**9)),
        )

    ranked = sorted(runs, key=rank_key, reverse=True)
    out = {
        "study": "V99 R52 narrow maintenance-band sweep",
        "status": "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective": "find whether 1pp/2pp/3pp maintenance bands recover meaningful R37 tail protection while preserving most of R46 turnover reduction",
        "bands_predeclared": list(BANDS),
        "runs": runs,
        "best_by_existing_r37_score": ranked[0] if ranked else None,
        "disclosure": "No detector or portfolio parameter was retuned. R52 changes only execution-band width. Frozen V99 and paper are untouched.",
    }
    SUMMARY.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2), flush=True)


if __name__ == "__main__":
    main()
