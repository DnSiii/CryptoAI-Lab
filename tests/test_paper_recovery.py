import copy
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from recover_paper_runtime import classify_run, heartbeat_stale
from verify_published_paper_history import verify

NOW = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)


def test_old_queue_never_blocks_recovery():
    run = {"status": "queued", "created_at": "2026-09-13T09:05:49Z"}
    assert classify_run(run, NOW) == "expired"
    run["created_at"] = (NOW - timedelta(minutes=10)).isoformat()
    assert classify_run(run, NOW) == "active"


def test_long_running_job_expires_only_after_job_timeout():
    run = {"status": "in_progress", "created_at": (NOW - timedelta(minutes=179)).isoformat()}
    assert classify_run(run, NOW) == "active"
    run["created_at"] = (NOW - timedelta(minutes=191)).isoformat()
    assert classify_run(run, NOW) == "expired"


def test_new_heartbeat_cannot_hide_stale_data():
    payload = {"heartbeat_at_utc": NOW.isoformat(), "latest_official_timestamps": {
        v: "2026-09-16T14:00:00Z" for v in ("v13", "v14", "v15", "v16", "v99")}}
    assert heartbeat_stale(payload, NOW)
    payload["latest_official_timestamps"] = {v: (NOW - timedelta(minutes=60)).isoformat()
                                            for v in payload["latest_official_timestamps"]}
    assert not heartbeat_stale(payload, NOW)


def test_publication_allows_append_but_rejects_rewrites():
    old = {"latest_data_timestamp": "2026-09-16", "equity_curve": [{"capital_brl": 10000}], "decisions": []}
    new = copy.deepcopy(old)
    new["latest_data_timestamp"] = "2026-10-01"
    new["equity_curve"].append({"capital_brl": 10100})
    verify(old, new)
    new["equity_curve"][0]["capital_brl"] = 9999
    with pytest.raises(RuntimeError, match="rewritten"):
        verify(old, new)
