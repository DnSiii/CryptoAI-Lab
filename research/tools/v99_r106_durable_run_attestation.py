"""GitHub-origin receipt run/artifact attestation; does NOT authenticate exchange data.
All evidence is DATA_ONLY. Never issues orders, selects strategy or accesses holdout.
"""
import argparse
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

REPO_PATTERN = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
RUN_ID = re.compile(r"[0-9]{8,15}\Z")
UTC = timezone.utc


def utc(value):
    if not isinstance(value, str):
        raise ValueError("utc_timestamp_required")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None or dt.utcoffset() != timedelta(0):
        raise ValueError("explicit_utc_required")
    return dt.astimezone(UTC)


def attest(report, repository, fetcher):
    if not REPO_PATTERN.fullmatch(repository):
        raise ValueError("invalid_github_repository")
    if (report.get("schema") != "V99_R106_DURABLE_PAIRED_SOURCE_CHAIN_V1"
            or report.get("economic_trials") != 0
            or report.get("promotion_authorized") is not False
            or report.get("paper_publication_authorized") is not False):
        raise ValueError("non_data_only_chain")
    results = []
    for label, ids, prefix in (
        ("market", report["market_recorded_run_ids"], "v99-r106-okx-firstparty-"),
        ("terms", report["terms_recorded_run_ids"], "v99-r106-okx-terms-"),
    ):
        for bucket, run_id in sorted(ids.items()):
            if not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d", bucket) or not RUN_ID.fullmatch(str(run_id)):
                raise ValueError("invalid_evidence_bucket_or_run_id")
            run = fetcher("repos/" + repository + "/actions/runs/" + str(run_id))
            if (run.get("id") != int(run_id) or run.get("status") != "completed"
                    or run.get("conclusion") != "success"
                    or run.get("event") not in ("schedule", "push", "workflow_dispatch")
                    or run.get("repository", {}).get("full_name") != repository):
                raise ValueError("unverified_github_action_run:" + str(run_id))
            acquired_slot = utc(bucket + ":00:00+00:00")
            start = utc(run["created_at"])
            finish = utc(run["updated_at"])
            if not (acquired_slot - timedelta(hours=1) < finish
                    and acquired_slot + timedelta(hours=1) >= start
                    and start <= finish):
                raise ValueError("run_outside_claimed_capture_hour:" + str(run_id))
            artifacts = fetcher("repos/" + repository + "/actions/runs/" + str(run_id) + "/artifacts?per_page=100")
            match = [a for a in artifacts.get("artifacts", [])
                     if a.get("name") == prefix + str(run_id)
                     and a.get("expired") is False
                     and a.get("workflow_run", {}).get("id", int(run_id)) == int(run_id)]
            if len(match) != 1:
                raise ValueError("missing_or_ambiguous_github_source_artifact:" + str(run_id))
            artifact = match[0]
            results.append({"type": label, "bucket": bucket, "run_id": str(run_id),
                            "run_html_url": run.get("html_url"),
                            "artifact_id": artifact["id"],
                            "run_conclusion": "success", "original_bytes_separately_sha256_verified": True})
    return {
        "schema": "V99_R106_GITHUB_RUN_PROVENANCE_V1",
        "status": "DATA_ONLY_GITHUB_RUN_AND_ARTIFACT_METADATA_ATTESTED",
        "verified": len(results), "results": results,
        "authenticates_exchange_signed_source_or_first_seen": False,
        "historical_backfill_authorized": False,
        "economic_trials": 0, "paper_publication_authorized": False,
        "promotion_authorized": False, "holdout_accessed": False,
    }


def make_fetcher(token):
    if not token:
        raise ValueError("read_only_github_token_required")

    def fetch(path):
        req = Request("https://api.github.com/" + path,
                      headers={"Accept": "application/vnd.github+json",
                               "Authorization": "Bearer " + token,
                               "X-GitHub-Api-Version": "2022-11-28",
                               "User-Agent": "CryptoAI-R106-DATA_ONLY-RunAttestation"})
        with urlopen(req, timeout=25) as response:
            data = response.read(300000)
        return json.loads(data)
    return fetch


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    result = attest(report, args.repository, make_fetcher(os.environ.get("GH_TOKEN")))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "verified": result["verified"],
                      "economic_trials": 0, "promotion_authorized": False}))


if __name__ == "__main__":
    main()
