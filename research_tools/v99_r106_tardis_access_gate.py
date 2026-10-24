#!/usr/bin/env python3
"""Check anonymous non-sample historical options quote entitlement via HEAD only."""
import json
import pathlib
import urllib.error
import urllib.request

out = pathlib.Path("tardis_quote_probe")
out.mkdir(exist_ok=True)
results = []
for day in ("2022-01-02", "2023-01-02"):
    url = "https://datasets.tardis.dev/v1/deribit/quotes/" + day.replace("-", "/") + "/OPTIONS.csv.gz"
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "V99-research-entitlement-check/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            status = response.status
            reason = "HEAD response (does not prove a complete download)"
    except urllib.error.HTTPError as error:
        status = error.code
        reason = str(error.reason)
    results.append({"date": day, "http_head_status": status, "reason": reason,
                    "entitlement_confirmed": False, "full_train_download_confirmed": False})
(out / "anonymous_entitlement.json").write_text(json.dumps(results, indent=2) + "\n")
print(json.dumps(results, indent=2))
if any(r["http_head_status"] not in (200, 401, 402, 403, 405) for r in results):
    raise RuntimeError("unexpected HTTP status; inspect provider response before claiming access")
