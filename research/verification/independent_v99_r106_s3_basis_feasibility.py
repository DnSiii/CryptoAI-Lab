"""Independent S3 feasibility oracle: original first-party TRAIN, NO economic strategy."""
import hashlib
import json
import math
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

from research.verification.independent_d1_native_train_receipts import verify

HOUR = 3600000
START = int(datetime(2021, 12, 9, tzinfo=timezone.utc).timestamp() * 1000)
END = int(datetime(2023, 10, 1, tzinfo=timezone.utc).timestamp() * 1000)
N = (END - START) // HOUR
EDGES = [int(datetime.fromisoformat(d).replace(tzinfo=timezone.utc).timestamp() * 1000)
         for d in ("2021-12-09T00:00:00", "2022-04-20T04:00:00",
                   "2022-08-30T09:00:00", "2023-01-09T14:00:00",
                   "2023-05-21T19:00:00", "2023-10-01T00:00:00")]
INSTRUMENTS = ("BTC-USDT", "BTC-USDT-SWAP", "ETH-USDT", "ETH-USDT-SWAP")
LIMIT = 0.024 + 0.005


def audit(source_root: Path, result_path: Path) -> dict:
    if verify(source_root)["status"] != "INDEPENDENT_FOUR_LEG_TRAIN_SOURCE_COMPLETE_NO_ECONOMICS":
        raise ValueError("S3_ORACLE_ORIGINAL_SOURCE_VETO")
    result = json.loads(result_path.read_text())
    if result.get("schema") != "V99_R106_S3_ORIGINAL_BASIS_SOURCE_FEASIBILITY_V1":
        raise ValueError("S3_ORACLE_SCHEMA")
    for flag in ("economic_trial_run", "native_funding_authenticated",
                 "native_fee_tier_authenticated", "historical_fills_authenticated",
                 "validation_opened", "final_holdout_opened", "promotion_authorized",
                 "paper_publication_authorized", "orders_enabled"):
        if result.get(flag) is not False:
            raise ValueError("S3_ORACLE_UNAUTHORIZED_PROMOTION_" + flag)
    if result.get("train_start_ms") != START or result.get("train_end_exclusive_ms") != END:
        raise ValueError("S3_ORACLE_SEALED_SCOPE")
    if result.get("threshold_premium") != LIMIT:
        raise ValueError("S3_ORACLE_THRESHOLD_CHANGED")
    prices = {}
    for instrument in INSTRUMENTS:
        rows = json.loads((source_root / instrument / "train_opens.json").read_bytes())
        if len(rows) != N:
            raise ValueError("S3_ORACLE_MISSING_HOURS")
        values = []
        for i, row in enumerate(rows):
            if type(row.get("ts")) is not int or row["ts"] != START + i * HOUR:
                raise ValueError("S3_ORACLE_INVALID_GRID")
            price = float(row["open"])
            if not math.isfinite(price) or price <= 0:
                raise ValueError("S3_ORACLE_INVALID_PRICE")
            values.append(price)
        prices[instrument] = values
    counts = {"BTC": 0, "ETH": 0}
    folds = [0] * 5
    by_fold_coin = {"BTC": [0] * 5, "ETH": [0] * 5}
    regimes = {f"{a}_{b}": {"eligible_days": 0, "daily_observations": 0}
               for a in ("bull", "bear", "sideways") for b in ("low", "high")}
    maxima = {"BTC": -float("inf"), "ETH": -float("inf")}
    sha = hashlib.sha256()
    days = 0
    eligible = 0
    btc = prices["BTC-USDT"]
    for t in range(720, N, 24):
        timestamp = START + t * HOUR
        # Independent implementation, no strategy function imported.
        f = {}
        for coin in ("BTC", "ETH"):
            spot = prices[coin + "-USDT"][t - 1]
            swap = prices[coin + "-USDT-SWAP"][t - 1]
            spread = (swap - spot) / spot
            maxima[coin] = max(maxima[coin], spread)
            f[coin] = spread >= LIMIT
        sha.update(f"{timestamp},{1 if f['BTC'] else 0},{1 if f['ETH'] else 0}\n".encode())
        trailing = (btc[t - 1] - btc[t - 720]) / btc[t - 720]
        vol = statistics.pstdev(
            [math.log(btc[k] / btc[k - 1]) for k in range(t - 72, t)]
        ) * math.sqrt(24)
        key = ("bull" if trailing > .05 else "bear" if trailing < -.05 else "sideways") + (
            "_high" if vol >= .04 else "_low")
        regimes[key]["daily_observations"] += 1
        fold = next((i for i in range(5) if EDGES[i] <= timestamp < EDGES[i + 1]), None)
        if fold is None:
            raise ValueError("S3_ORACLE_FOLD_OUTSIDE_TRAIN")
        days += 1
        if f["BTC"] or f["ETH"]:
            eligible += 1
            folds[fold] += 1
            regimes[key]["eligible_days"] += 1
        for coin in ("BTC", "ETH"):
            if f[coin]:
                counts[coin] += 1
                by_fold_coin[coin][fold] += 1
    expected = {
        "daily_observations": days, "eligible_unique_days": eligible,
        "eligible_by_coin": counts, "eligible_by_fold": folds,
        "eligible_by_fold_coin": by_fold_coin,
        "eligible_by_regime": regimes,
        "folds_with_eligibility": sum(x > 0 for x in folds),
        "eligibility_trace_sha256": sha.hexdigest(),
    }
    for key, value in expected.items():
        if result.get(key) != value:
            raise ValueError("S3_ORACLE_MISMATCH_" + key)
    for coin in ("BTC", "ETH"):
        if not math.isclose(maxima[coin], result["maximum_indicative_premium"][coin],
                            rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError("S3_ORACLE_MAX_PREMIUM_" + coin)
    status = ("FEASIBILITY_ONLY_NO_PROMOTION" if expected["folds_with_eligibility"] >= 4
              else "OPPORTUNITY_VETO_NO_ECONOMIC_TRIAL")
    if result.get("status") != status:
        raise ValueError("S3_ORACLE_STATUS")
    print(json.dumps({"status": "INDEPENDENT_ORIGINAL_TRAIN_FEASIBILITY_REPLAY_PASS",
                      "decision_days": days, "eligible_days": eligible,
                      "eligible_by_fold": folds, "economic_trial_run": False,
                      "promotion_authorized": False}, sort_keys=True))
    return expected


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_s3_basis_feasibility PRICE_ROOT REPORT")
    audit(Path(sys.argv[1]), Path(sys.argv[2]))
