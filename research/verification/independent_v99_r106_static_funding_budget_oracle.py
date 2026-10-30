"""Independent ORIGINAL-BYTE funding-budget verifier. Does not import primary source/engine."""
import csv
import hashlib
import io
import json
import math
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

START = 1639008000000
END = 1696118400000
STEP = 8 * 3600 * 1000
EDGES = [START + h*3600000 for h in (0, 3172, 6345, 9518, 12691, 15864)]
MONTHS = [f"{y}-{m:02d}" for y in (2021, 2022, 2023) for m in range(1, 13)
          if (y, m) >= (2021, 12) and (y, m) <= (2023, 9)]
ASSETS = ("BTCUSDT", "ETHUSDT")
COST = {"severe": .0028, "supersevere": .0056}

def independent_verify(root):
    root = Path(root)
    report = json.loads((root / "static_funding_budget_source_only.json").read_text())
    if report["schema"] != "V99_R106_ORIGINAL_FUNDING_STATIC_BUDGET_NOT_ROI_V1":
        raise ValueError("wrong_preregistered_budget_schema")
    original_events = {}
    zip_digests = {}
    for symbol in ASSETS:
        observed = {}
        for month in MONTHS:
            name = f"{symbol}-fundingRate-{month}.zip"
            z = (root / "raw_ephemeral" / name).read_bytes()
            chk = (root / "raw_ephemeral" / (name + ".CHECKSUM")).read_bytes()
            match = re.search(rb"\b([a-fA-F0-9]{64})\b", chk)
            sha = hashlib.sha256(z).hexdigest()
            if match is None or sha != match.group(1).decode().lower():
                raise ValueError("independent_publisher_digest_mismatch")
            zip_digests[name] = sha
            with zipfile.ZipFile(io.BytesIO(z)) as zf:
                files = [x for x in zf.infolist() if not x.is_dir()]
                if len(files) != 1 or files[0].file_size > 24*1024*1024:
                    raise ValueError("independent_archive_structure")
                rows = csv.DictReader(io.StringIO(zf.read(files[0]).decode("utf-8-sig")))
                if not {"calc_time","funding_interval_hours","last_funding_rate"}.issubset(rows.fieldnames or []):
                    raise ValueError("independent_native_header")
                last = None
                for row in rows:
                    ts = int(row["calc_time"])
                    rate = float(row["last_funding_rate"])
                    interval = float(row["funding_interval_hours"])
                    if not math.isfinite(rate) or interval != 8:
                        raise ValueError("independent_native_row")
                    if datetime.fromtimestamp(ts/1000,timezone.utc).strftime("%Y-%m") != month:
                        raise ValueError("independent_archive_month")
                    if last is not None and ts <= last:
                        raise ValueError("independent_month_nonmonotone")
                    last = ts
                    nominal = (ts // STEP) * STEP
                    if not 0 <= ts - nominal <= 31:
                        raise ValueError("independent_native_clock")
                    if START <= nominal < END:
                        if nominal in observed:
                            raise ValueError("independent_duplicate_native_slot")
                        observed[nominal] = rate
        required = set(range(START, END, STEP))
        if set(observed) != required or len(observed) != 1983:
            raise ValueError("independent_original_train_missing_slots")
        original_events[symbol] = observed
    fold_stats = []
    asset_folds = {symbol: [] for symbol in ASSETS}
    for k in range(5):
        a,b = EDGES[k:k+2]
        n = sum(a <= t < b for t in range(START, END, STEP))
        if n != [397,397,396,397,396][k]:
            raise ValueError("independent_fold_grid")
        sums = {}
        for symbol in ASSETS:
            rates = [v for t,v in original_events[symbol].items() if a <= t < b]
            if len(rates) != n:
                raise ValueError("independent_fold_missing")
            total = math.fsum(rates)
            sums[symbol] = total
            f = report["assets"][symbol][k]
            for key, actual in (("rate_sum",total),("event_count",n),
                                ("positive_events",sum(x>0 for x in rates)),
                                ("negative_events",sum(x<0 for x in rates)),
                                ("zero_events",sum(x==0 for x in rates)),
                                ("min_rate",min(rates)),("max_rate",max(rates))):
                observed = f[key]
                if not math.isclose(observed,actual,rel_tol=0.,abs_tol=1e-12):
                    raise ValueError("independent_asset_fold_mismatch_"+key)
            asset_folds[symbol].append(total)
        budget = math.fsum((sums["BTCUSDT"]*.5,sums["ETHUSDT"]*.5))
        primary = report["folds"][k]
        if primary["fold"] != k+1 or primary["events_per_asset"] != n:
            raise ValueError("independent_fold_identity")
        for key,actual in (("btc_signed_rate_sum",sums["BTCUSDT"]),
                           ("eth_signed_rate_sum",sums["ETHUSDT"]),
                           ("static_50_50_signed_funding_rate_budget_NOT_ROI",budget)):
            if not math.isclose(primary[key],actual,rel_tol=0.,abs_tol=1e-12):
                raise ValueError("independent_budget_mismatch_"+key)
        for name,cost in COST.items():
            if not math.isclose(primary["illustrative_budget_minus_four_side_cost_NOT_ROI"][name],
                                budget-cost,rel_tol=0.,abs_tol=1e-12):
                raise ValueError("independent_fee_budget_mismatch")
        fold_stats.append(budget)
    positive = {name:sum(b-cost>0 for b in fold_stats) for name,cost in COST.items()}
    if report["positive_budget_folds"] != positive:
        raise ValueError("independent_fivefold_decision_mismatch")
    if not math.isclose(report["whole_train_signed_rate_budget_NOT_ROI"],
                        math.fsum(fold_stats),rel_tol=0.,abs_tol=1e-12):
        raise ValueError("independent_whole_train_mismatch")
    expected_status = ("FUNDING_BUDGET_UNFALSIFIED_SOURCE_ONLY" if positive["severe"]>=4
                       else "FUNDING_BUDGET_FAIL_4_OF_5_SOURCE_ONLY")
    if report["status"] != expected_status:
        raise ValueError("independent_mechanism_decision_mismatch")
    if not all(report[k] is False for k in ("economic_train_executed","promotion_authorized",
                 "orders_enabled","validation_opened","holdout_opened","paper_modified","frozen_modified")):
        raise ValueError("unsafe_source_only_claim")
    if not all(report[k] is True for k in ("rate_budget_is_not_nav_or_roi",
                   "public_funding_is_not_account_settlement","no_basis_or_fills_or_margin_certified")):
        raise ValueError("unjustified_native_economics_claim")
    result = {"status":"INDEPENDENT_44_ORIGINAL_PUBLISHER_ZIPS_FIVEFOLD_BUDGET_REEXECUTED",
              "original_zip_sha256_manifest_sha256":hashlib.sha256(
                  json.dumps(zip_digests,sort_keys=True).encode()).hexdigest(),
              "original_files":len(zip_digests),"events_per_asset":1983,
              "fold_signed_rate_budgets_NOT_ROI":fold_stats,
              "positive_illustrative_budget_folds":positive,
              "mechanism_status":expected_status,
              "promotion_authorized":False,"economic_train_executed":False}
    (root/"static_funding_budget_independent_oracle.json").write_text(
        json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
    return result

if __name__ == "__main__":
    if len(sys.argv)!=2:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_static_funding_budget_oracle OUTDIR")
    independent_verify(sys.argv[1])
