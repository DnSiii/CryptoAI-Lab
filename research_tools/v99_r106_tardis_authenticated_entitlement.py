#!/usr/bin/env python3
"""Bounded Tardis non-sample entitlement probe. No credentials or paid bytes logged."""
from __future__ import annotations
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DATES = ("2021/12/10", "2022/06/15", "2023/09/29")
OUT = Path("research_evidence/v99_options_entitlement")
OUT.mkdir(parents=True, exist_ok=True)

def probe(date: str, key: str) -> dict:
    url = f"https://datasets.tardis.dev/v1/deribit/quotes/{date}/OPTIONS.csv.gz"
    # Authorization is carried ONLY in the HTTP header, never a URL or printed value.
    request = Request(url, headers={
        "Authorization": "Bearer " + key,
        "Range": "bytes=0-0",
        "User-Agent": "V99-entitlement-minimal-byte-probe/1.0",
    }, method="GET")
    try:
        with urlopen(request, timeout=25) as response:
            status = response.status
            response.read(1)
            return {"date": date.replace("/", "-"), "http_status": status,
                    "single_request_read_bytes": 1,
                    "accessible_sampled_day": status in (200, 206),
                    "full_day_integrity_proven": False}
    except HTTPError as exc:
        return {"date": date.replace("/", "-"), "http_status": exc.code,
                "single_request_read_bytes": 0,
                "accessible_sampled_day": False, "full_day_integrity_proven": False}
    except (URLError, TimeoutError, OSError):
        return {"date": date.replace("/", "-"), "http_status": "TRANSPORT_UNVERIFIED",
                "single_request_read_bytes": 0,
                "accessible_sampled_day": False, "full_day_integrity_proven": False}

def main() -> None:
    key = os.environ.get("TARDIS_API_KEY", "").strip()
    if not key:
        rows = []
        state = "BLOCKED_NO_AUTHENTICATED_ARCHIVE_ENTITLEMENT_CONFIGURED"
    else:
        rows = [probe(day, key) for day in DATES]
        state = ("SAMPLED_NONFIRST_DAY_ACCESS_CONFIRMED_FULL_COVERAGE_UNVERIFIED"
                 if all(r["accessible_sampled_day"] for r in rows)
                 else "BLOCKED_OR_INCOMPLETE_HISTORICAL_ENTITLEMENT")
    report = {"schema": "V99_R106_TARDIS_BOUNDED_ENTITLEMENT_V1",
              "status": state, "requested_dates": list(DATES), "observations": rows,
              "original_train_end_exclusive": "2023-10-01T00:00:00Z",
              "validation_opened": False, "holdout_opened": False,
              "native_fills_authenticated": False, "options_engine_evaluated": False,
              "promotion_authorized": False, "orders_enabled": False,
              "complete_five_fold_quote_coverage_proven": False,
              "external_dependency": "Authenticated 2021-12-09..2023-09-30 BTC/ETH option BBO+sizes, arrival timestamps, complete gap manifest, historical contracts/fees/margins"}
    (OUT / "entitlement_status.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True))
    assert not any(report[k] for k in ("validation_opened", "holdout_opened",
                                      "native_fills_authenticated", "promotion_authorized",
                                      "orders_enabled", "complete_five_fold_quote_coverage_proven"))
if __name__ == "__main__":
    main()
