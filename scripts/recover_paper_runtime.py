"""Recover the official paper only; never treat an expired queue as progress."""
from __future__ import annotations

import base64
import json
import os
import subprocess
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
    data_age = max((now - timestamp(value)).total_seconds() / 60 for value in points.values())
    print(f"heartbeat_age_minutes={age:.1f}; oldest_official_data_age_minutes={data_age:.1f}")
    return age > 25 or data_age > 90


def gh(*args: str) -> str:
    return subprocess.check_output(["gh", *args], text=True, timeout=60)


def main() -> None:
    repo = os.environ["GITHUB_REPOSITORY"]
    now = datetime.now(timezone.utc)
    try:
        envelope = json.loads(gh("api", f"repos/{repo}/contents/reports/paper_runtime_status.json?ref=paper-results"))
        payload = json.loads(base64.b64decode(envelope["content"]))
        stale = heartbeat_stale(payload, now)
    except (KeyError, ValueError, subprocess.SubprocessError) as error:
        print(f"heartbeat_unavailable={error}; recovery required")
        stale = True

    def runs() -> list[dict]:
        # Paginate: one ancient queued run may be hidden behind completed runs.
        result = []
        for status in ("queued", "in_progress", "waiting", "pending", "requested"):
            pages = json.loads(gh("api", "--paginate", "--slurp", f"repos/{repo}/actions/workflows/{WORKFLOW}/runs?status={status}&per_page=100"))
            result.extend(run for page in pages for run in page["workflow_runs"])
        return result

    current = runs()
    expired = [run for run in current if classify_run(run, now) == "expired"]
    for run in expired:
        print(f"Cancelling expired official paper run {run['id']} ({run['status']}, created {run['created_at']})")
        gh("api", "--method", "POST", f"repos/{repo}/actions/runs/{run['id']}/cancel")
    if expired:
        for attempt in range(3):
            time.sleep(2)
            current = runs()
            pending = [run for run in current if classify_run(run, datetime.now(timezone.utc)) == "expired"]
            if not pending:
                break
        else:
            raise RuntimeError("Expired paper runs still pending cancellation; refusing to report recovery as successful")

    active = [run for run in current if classify_run(run, datetime.now(timezone.utc)) == "active"]
    if active:
        print(f"Paper recovery deferred: {len(active)} recent active run(s); data_stale={stale}")
    elif stale:
        gh("workflow", "run", WORKFLOW, "--repo", repo, "--ref", "main")
        print("Dispatched official paper recovery. Publication freshness is not yet confirmed.")
    else:
        print("Official paper heartbeat and data are fresh.")


if __name__ == "__main__":
    main()
