"""Read-only, fail-closed audit of durable paired OKX market and terms receipts.
No PnL, strategy, holdout, real orders, cross-venue transfers or historical backfill.
Original first-party HTTP hashes are not independently exchange-signed evidence.
"""
import argparse
import hashlib
import json
import re
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from research.tools import v99_r106_okx_multihour_continuity as continuity
from research.tools import v99_r106_okx_prospective_receipt as okx
from research.tools import v99_r106_okx_terms_asof as terms
from research.tools import v99_r106_receipt_append as market_store
from research.tools import v99_r106_terms_append as terms_store

MARKET = Path("receipts/v99_r106_okx")
TERMS = Path("receipts/v99_r106_okx_terms")
PROOF = "receipt_commit_provenance.json"
UTC = timezone.utc


def parse_bucket(value):
    if not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d", value):
        raise ValueError("invalid_bucket_name")
    dt = datetime.strptime(value, "%Y-%m-%dT%H").replace(tzinfo=UTC)
    if dt.strftime("%Y-%m-%dT%H") != value:
        raise ValueError("noncanonical_bucket")
    return dt


def scan(root):
    if not root.is_dir():
        raise ValueError("missing_receipt_root:" + str(root))
    out = {}
    for p in sorted(root.iterdir()):
        if p.is_file() and p.name == "README.md":
            continue
        if not p.is_dir():
            raise ValueError("unexpected_receipt_file:" + p.name)
        parse_bucket(p.name)
        out[p.name] = p
    return out


def verify_original(folder, expected, verifier):
    if {p.name for p in folder.iterdir()} != set(expected) | {PROOF}:
        raise ValueError("missing_or_extra_source_files:" + str(folder))
    # Existing independent source validators expect raw-only directories.
    # Copy bytes into an isolated temp directory; never mutate the durable tree.
    with tempfile.TemporaryDirectory(prefix="v99-verify-") as tmp:
        root = Path(tmp)
        for name in expected:
            shutil.copyfile(folder / name, root / name)
        return verifier(root)


def verify_proof(folder, manifest, bucket, kind):
    proof = market_store.strict((folder / PROOF).read_bytes())
    if not re.fullmatch(r"\d{8,15}", str(proof.get("run_id", ""))):
        raise ValueError("unrecorded_run_id")
    if kind == "market":
        acquired = manifest["last_received_utc"]
        if proof.get("acquired_utc") != acquired or proof.get("immutable_bucket_utc") != bucket:
            raise ValueError("market_receipt_provenance_mismatch")
        digest = proof.get("manifest_sha256")
    else:
        acquired = manifest["acquisition_last_utc"]
        if proof.get("observed_utc") != acquired or proof.get("bucket") != bucket:
            raise ValueError("terms_receipt_provenance_mismatch")
        if proof.get("native_fee_and_settled_funding_verified") is not False:
            raise ValueError("false_settled_funding_claim")
        digest = proof.get("sha256_manifest")
    actual = hashlib.sha256((folder / "manifest.json").read_bytes()).hexdigest()
    if actual != digest or proof.get("paper_or_model_changes_allowed") is not False:
        raise ValueError("provenance_digest_or_permissions_tampered")
    if market_store.utc(acquired).strftime("%Y-%m-%dT%H") != bucket:
        raise ValueError("manifest_acquisition_outside_utc_bucket")
    if manifest.get("economic_trials") != 0 or manifest.get("holdout_accessed") is not False:
        raise ValueError("economic_or_holdout_access_in_source")
    return {"claimed_run_id": str(proof["run_id"]), "acquired_utc": acquired,
            "manifest_sha256": actual}


def verify_market(folder, bucket):
    manifest = verify_original(folder, market_store.EXPECTED, market_store.verify_source)
    for field in ("paper_publication_authorized", "promotion_authorized",
                  "real_orders_enabled", "holdout_accessed",
                  "original_r106_binance_fee_and_funding_model_transfer_authorized"):
        if manifest.get(field) is not False:
            raise ValueError("market_source_permission_mismatch:" + field)
    info = verify_proof(folder, manifest, bucket, "market")
    verified = continuity.load(folder)  # raw candle hashes and semantics independently checked
    return {**info, "verified": verified}


def verify_terms(folder, bucket):
    manifest = verify_original(folder, terms_store.FILES, terms_store.validate)
    info = verify_proof(folder, manifest, bucket, "terms")
    for inst in okx.INSTS:
        record = manifest["contracts"][inst]
        observed = {"raw": (folder / ("metadata_" + inst + ".raw.json")).read_bytes(),
                    "received_utc": record["contract_received_utc"]}
        notice = {"raw": (folder / ("funding_" + inst + ".raw.json")).read_bytes(),
                  "received_utc": record["funding_received_utc"]}
        if terms.verify_contract(observed, inst) != record["contract"]:
            raise ValueError("original_contract_does_not_match_manifest:" + inst)
        if terms.verify_current_funding(notice, inst) != record["funding_notice"]:
            raise ValueError("original_funding_notice_does_not_match_manifest:" + inst)
    return info


def summarize(market, native_terms):
    all_buckets = sorted(set(market) | set(native_terms))
    if not all_buckets:
        raise ValueError("empty_durable_evidence_chain")
    pair = sorted(set(market) & set(native_terms))
    beginning, end = parse_bucket(all_buckets[0]), parse_bucket(all_buckets[-1])
    span = int((end-beginning).total_seconds()//3600) + 1
    expected = [(beginning + timedelta(hours=n)).strftime("%Y-%m-%dT%H") for n in range(span)]
    links = []
    valid = 0
    for left, right in zip(pair, pair[1:]):
        if parse_bucket(right)-parse_bucket(left) != timedelta(hours=1):
            continue
        result = continuity.evaluate(market[left]["verified"], market[right]["verified"])
        passed = result["status"] == "SOURCE_CONTINUITY_OBSERVED_ONLY"
        valid += int(passed)
        links.append({"from": left, "to": right, "status": result["status"],
                      "issues": result["issues"], "revisions": result["revised_confirmed_hours"],
                      "overlap_observations": result["overlap_observations"]})
    return {"schema": "V99_R106_DURABLE_PAIRED_SOURCE_CHAIN_V1",
            "status": ("DATA_ONLY_SOURCE_CONTINUITY_OBSERVED_ONLY" if valid
                       else "DATA_ONLY_HOLD_NO_CONSECUTIVE_PAIRS"),
            "market_utc_buckets": sorted(market), "terms_utc_buckets": sorted(native_terms),
            "paired_utc_buckets": pair, "total_utc_hours": span,
            "paired_hours": len(pair),
            "missing_paired_hours": [x for x in expected if x not in pair],
            "market_only_hours": sorted(set(market)-set(native_terms)),
            "terms_only_hours": sorted(set(native_terms)-set(market)),
            "verified_adjacent_links": valid, "adjacent_audits": links,
            "claimed_run_ids_not_independently_github_authenticated": True,
            "retroactive_missing_hour_backfill": False,
            "exchange_signed_receipts": False, "native_fee_tier_authenticated": False,
            "position_funding_settlements_authenticated": False,
            "paper_publication_authorized": False, "promotion_authorized": False,
            "cross_venue_economic_transfer_authorized": False,
            "real_orders_enabled": False, "holdout_accessed": False, "economic_trials": 0}


def audit(root):
    market = {name: verify_market(path, name) for name, path in scan(root / MARKET).items()}
    terms_ = {name: verify_terms(path, name) for name, path in scan(root / TERMS).items()}
    for group in (market, terms_):
        ids = [value["claimed_run_id"] for value in group.values()]
        if len(ids) != len(set(ids)):
            raise ValueError("same_run_id_recorded_for_multiple_hours")
    return summarize(market, terms_)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "paired_hours": result["paired_hours"],
                      "missing": len(result["missing_paired_hours"]),
                      "adjacent_verified": result["verified_adjacent_links"],
                      "economic_trials": 0, "promotion_authorized": False}))


if __name__ == "__main__":
    main()
