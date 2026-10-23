"""Independent raw-ZIP D1 funding threshold impossibility oracle (NO PNL).

Does not import the signal probe, its JSON parser, or its strategy decisions.
Recomputes original monthly ZIP rates and optimistic 3-fix envelopes in Decimal.
"""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

START = int(datetime(2021, 12, 9, tzinfo=timezone.utc).timestamp() * 1000)
END = int(datetime(2023, 10, 1, tzinfo=timezone.utc).timestamp() * 1000)
EDGES = [int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp() * 1000)
         for s in ("2021-12-09T00:00:00", "2022-04-20T04:00:00",
                   "2022-08-30T09:00:00", "2023-01-09T14:00:00",
                   "2023-05-21T19:00:00", "2023-10-01T00:00:00")]
THRESHOLDS = {"severe_model_only": Decimal("0.0056"),
              "supersevere_model_only": Decimal("0.0112")}


def verify_raw(root, result):
    root = Path(root)
    report = json.loads(Path(result).read_text())
    manifest = json.loads((root / "manifest.json").read_text())
    if report["historical_economic_trial_run"] or report["promotion_authorized"]:
        raise ValueError("UNAUTHORIZED_ECONOMIC_PROMOTION")
    if {k: Decimal(v) for k, v in report["fee_thresholds_four_leg_round_trip_x2"].items()} != THRESHOLDS:
        raise ValueError("CHANGED_PREREGISTERED_THRESHOLD")
    for asset in ("BTC", "ETH"):
        inst = asset + "-USDT-SWAP"
        receipts = {}
        for file in manifest["instruments"][inst]["archives"]:
            raw = (root / inst / file["file"]).read_bytes()
            if hashlib.sha256(raw).hexdigest() != file["sha256"]:
                raise ValueError("RAW_ZIP_HASH_MISMATCH")
            with zipfile.ZipFile(root / inst / file["file"]) as archive:
                csv_names = [n for n in archive.namelist() if n.endswith(".csv")]
                if len(csv_names) != 1:
                    raise ValueError("AMBIGUOUS_ORIGINAL_ZIP")
                for line in archive.read(csv_names[0]).decode("utf-8-sig").splitlines():
                    fields = line.strip().split(",")
                    if len(fields) < 3 or fields[0] != inst:
                        continue
                    t = int(fields[2])
                    if not START <= t < END:
                        raise ValueError("SEALED_OR_UNEXPECTED_FUNDING_TIME")
                    rate = Decimal(fields[1])
                    if not rate.is_finite() or abs(rate) > Decimal("0.1"):
                        raise ValueError("INVALID_RAW_RATE")
                    if t in receipts and receipts[t] != rate:
                        raise ValueError("CONFLICTING_ORIGINAL_RATE")
                    receipts[t] = rate
        stamps = sorted(receipts)
        for fold in range(1, 6):
            triples = []
            for j in range(2, len(stamps)):
                if EDGES[fold-1] <= stamps[j] < EDGES[fold]:
                    triples.append(receipts[stamps[j-2]] +
                                   receipts[stamps[j-1]] + receipts[stamps[j]])
            d = report["optimistic_observed_funding_envelope"][str(fold)][asset]
            if len(triples) != d["observed_settlement_triples"]:
                raise ValueError("INDEPENDENT_TRIPLE_COUNT_MISMATCH")
            maximum = max(triples) if triples else None
            if (None if maximum is None else maximum) != (
                None if d["max_optimistic_projected_24h"] is None
                else Decimal(d["max_optimistic_projected_24h"])
            ):
                raise ValueError("INDEPENDENT_MAX_FUNDING_MISMATCH")
            for name, threshold in THRESHOLDS.items():
                key = "triples_above_" + ("severe" if name == "severe_model_only"
                       else "supersevere") + "_threshold"
                if sum(value > threshold for value in triples) != d[key]:
                    raise ValueError("INDEPENDENT_THRESHOLD_CROSSING_MISMATCH")
    # Four later folds have original first-party rates, and even the
    # optimistic no-basis/no-cadence envelope never reaches entry threshold.
    if report["folds_2_to_5_without_even_optimistic_severe_funding_threshold"] != [2, 3, 4, 5]:
        raise ValueError("NO_DECISIVE_FOUR_FOLD_FALSIFICATION")
    print("INDEPENDENT_ORIGINAL_ZIP_FOUR_FOLD_D1_NO_ENTRY_PROOF / "
          "PRE-MARCH_UNKNOWN / NO ECONOMICS / NO PROMOTION", flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m research.verification.independent_d1_actual_train_signal_falsification FUND_ROOT REPORT")
    verify_raw(sys.argv[1], sys.argv[2])
