"""C8 training-only chronological diagnostics. No selection, no promotion, no holdout."""
import argparse
import json
import math
from pathlib import Path
from .v98_b0_chronological_evidence import audit

SCENARIOS = ("1x", "2x", "4x")

def run(directory):
    directory = Path(directory)
    if "v98_independent" not in directory.resolve().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    summary = json.loads((directory / "c8_composed_summary.json").read_text())
    if summary.get("holdout_accessed") is not False or summary.get("source") != "AUTHENTICATED_CLEAN4":
        raise ValueError("INVALID_SOURCE_BOUNDARY")
    if set(summary.get("results", {})) != set(SCENARIOS):
        raise ValueError("INCOMPLETE_SCENARIOS")
    output = {}
    for scenario in SCENARIOS:
        ledger_path = directory / ("c8_composed_summary_" + scenario + "_ledger.jsonl")
        with ledger_path.open() as handle:
            entries = [json.loads(line) for line in handle]
        final_equity = float(summary["results"][scenario]["final_equity"])
        evidence = audit(entries, final_equity)
        annual = evidence["utc_annual_returns_including_warmup"]
        monthly = evidence["utc_monthly_returns_including_warmup"]
        if not all(math.isfinite(x) for x in [*annual.values(), *monthly.values()]):
            raise ValueError("NONFINITE_CHRONOLOGY")
        output[scenario] = evidence
    result = {"status": "C8_CHRONOLOGICAL_TRAINING_ONLY_NOT_VALIDATION",
              "holdout_accessed": False, "source": "AUTHENTICATED_CLEAN4",
              "price_manifest_sha256": summary["price_manifest_sha256"],
              "funding_manifest_sha256": summary["funding_manifest_sha256"],
              "results": output}
    (directory / "c8_chronological_evidence.json").write_text(
        json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n")
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.directory)
    print(json.dumps({k: {"annual": v["utc_annual_returns_including_warmup"],
                           "negative_months": v["negative_months"],
                           "months": v["months"]}
                      for k, v in result["results"].items()}, sort_keys=True))

if __name__ == "__main__":
    main()
