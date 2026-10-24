#!/usr/bin/env python3
"""Read-only anonymous non-sample quote access check; never assumes 404 means absent market data."""
import json
import pathlib
import urllib.error
import urllib.request

out = pathlib.Path("tardis_quote_probe")
out.mkdir(exist_ok=True)
results = []
for day in ("2022-01-02", "2023-01-02"):
    url = "https://datasets.tardis.dev/v1/deribit/quotes/" + day.replace("-", "/") + "/OPTIONS.csv.gz"
    codes = {}
    for method in ("HEAD", "GET"):
        headers = {"User-Agent": "V99-research-entitlement-check/1.0"}
        if method == "GET":
            headers["Range"] = "bytes=0-0"  # bounded; never read full paid data
        request = urllib.request.Request(url, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=35) as response:
                codes[method] = response.status
                if method == "GET":
                    response.read(1)
        except urllib.error.HTTPError as err:
            codes[method] = err.code
        except (TimeoutError, OSError) as err:
            codes[method] = "TRANSPORT_ERROR:" + type(err).__name__
    results.append({"date": day, "head_status": codes["HEAD"], "get_range_status": codes["GET"],
                    "anonymous_complete_day_access_proven": False,
                    "classification": "ACCESS_PROBE_ONLY; 404 may mean entitlement masking or missing file"})
(out / "anonymous_entitlement.json").write_text(json.dumps(results, indent=2) + "\n")
print(json.dumps(results, indent=2))
print("No complete historical quote entitlement or five-fold coverage established.")
