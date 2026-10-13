"""Recover the official paper only; never treat an expired queue as progress."""
from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

WORKFLOW = "v13-paper.yml"
QUEUE_TIMEOUT_MINUTES = 30
RUN_TIMEOUT_MINUTES = 190  # official job timeout (180) plus finalization margin


def timestamp(raw: str) -> datetime:
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def classify_run(run: dict, now: datetime) -> str:
    status = run["status"]
    if status == "completed":
        return "completed"
    age = (now - timestamp(run["created_at"])).total_seconds() / 60
    limit = RUN_TIMEOUT_MINUTES if status == "in_progress" else QUEUE_TIMEOUT_MINUTES
    return "expired" if age > limit else "active"


def heartbeat_stale(payload: dict, now: datetime) -> bool:
    age = (now - timestamp(payload["heartbeat_at_utc"])).total_seconds() / 60
    points = payload.get("latest_official_timestamps", {})
    if set(points) != {"v13", "v14", "v15", "v16", "v99"}:
        return True
    data_age = max((now - timestamp(value)).total_seconds() / 60 - 60 for value in points.values())
    print(f"heartbeat_age_minutes={age:.1f}; oldest_official_data_age_minutes={data_age:.1f}")
    return age > 25 or data_age > 90


def gh(*args: str) -> str:
    return subprocess.check_output(["gh", *args], text=True, timeout=60, stderr=subprocess.STDOUT)


def main(continue_chain: bool = False) -> None:
    repo = os.environ["GITHUB_REPOSITORY"]
    now = datetime.now(timezone.utc)
    publication_age = None
    try:
        envelope = json.loads(gh("api", f"repos/{repo}/contents/reports/paper_runtime_status.json?ref=paper-results"))
        payload = json.loads(base64.b64decode(envelope["content"]))
        stale = heartbeat_stale(payload, now)
        ages = [(now-timestamp(payload["heartbeat_at_utc"])).total_seconds()/60]
        ages += [(now-timestamp(t)).total_seconds()/60-60 for t in payload.get("latest_official_timestamps", {}).values()]
        publication_age = max(ages)
    except (KeyError, ValueError, subprocess.SubprocessError) as error:
        print(f"heartbeat_unavailable={error}; recovery required")
        stale = True

    def runs() -> list[dict]:
        # Paginate: one ancient queued run may be hidden behind completed runs.
        result = []
        for status in ("queued", "in_progress", "waiting", "pending", "requested"):
            pages = json.loads(gh("api", "--paginate", "--slurp", f"repos/{repo}/actions/workflows/{WORKFLOW}/runs?status={status}&per_page=100"))
            result.extend(run for page in pages for run in page["workflow_runs"])
        return [run for run in result if str(run["id"]) != os.environ.get("GITHUB_RUN_ID")]

    current = runs()
    runtime_paths = ("src/cryptoai_v13/paper_execution.py", "scripts/paper_continuation.py", "scripts/paper_once_v13_incremental.py")
    def signature(ref):
        parts = []
        for path in runtime_paths:
            try:
                parts.append(json.loads(gh("api", f"repos/{repo}/contents/{path}?ref={ref}"))["sha"])
            except subprocess.CalledProcessError as error:
                if "HTTP 404" not in error.output:
                    raise
                parts.append("missing")
        return tuple(parts)
    obsolete = []
    if any(run.get("head_sha") for run in current):
        latest_signature = signature("main")
        signatures = {}
        for run in current:
            head = run.get("head_sha")
            if not head:
                continue
            if head not in signatures:
                signatures[head] = signature(head)
            if signatures[head] != latest_signature:
                # Publication is short and must finish atomically before cancellation.
                jobs = json.loads(gh("api", f"repos/{repo}/actions/runs/{run['id']}/jobs"))["jobs"]
                publishing = any(step.get("name") == "Publish durable paper results" and step.get("status") == "in_progress"
                                 for job in jobs for step in job.get("steps", []))
                if not publishing:
                    obsolete.append(run)
    expired = [run for run in current if classify_run(run, now) == "expired" or run in obsolete]
    for run in expired:
        print(f"Cancelling expired or obsolete official paper run {run['id']} ({run['status']}, created {run['created_at']})")
        try:
            gh("api", "--method", "POST", f"repos/{repo}/actions/runs/{run['id']}/cancel")
        except subprocess.CalledProcessError as error:
            if "HTTP 409" not in error.output:
                raise
            try:
                gh("api", "--method", "POST", f"repos/{repo}/actions/runs/{run['id']}/force-cancel")
            except subprocess.CalledProcessError as force_error:
                if "HTTP 409" not in force_error.output:
                    raise
                print(f"WARNING: GitHub refuses cancellation of phantom run {run['id']}; expired run is excluded from active count.")
    if expired:
        for attempt in range(3):
            time.sleep(2)
            current = runs()
            pending = [run for run in current if classify_run(run, datetime.now(timezone.utc)) == "expired"]
            if not pending:
                break
        else:
            print("WARNING: Expired runs remain in GitHub metadata; they cannot block recovery.")

    active = [run for run in current if classify_run(run, datetime.now(timezone.utc)) == "active"]
    if active:
        print(f"Paper recovery deferred: {len(active)} recent active run(s); data_stale={stale}")
    elif stale or continue_chain:
        gh("workflow", "run", WORKFLOW, "--repo", repo, "--ref", "main")
        print("Dispatched official paper recovery. Publication freshness is not yet confirmed.")
    else:
        print("Official paper heartbeat and data are fresh.")

    if not continue_chain and publication_age is not None and publication_age > 180:
        raise RuntimeError(f"Official paper publication has been stale for {publication_age:.0f} minutes. An active retry is not evidence of healthy publication.")


if __name__ == "__main__":
    main(continue_chain="--continue-chain" in sys.argv)
