"""G1 dated-futures first-party source feasibility only. No alpha, no PnL, no orders.

Preregistered in research/V99_R106_G1_DATED_FUTURES_PREREG_20261023.md
at commit 5ff7194efde234309d52be64042f2af06cf2f8b8.
"""
from __future__ import annotations
import hashlib
import json
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

PREREG = "5ff7194efde234309d52be64042f2af06cf2f8b8"
ASSETS = ("BTC", "ETH")
EXPIRIES = ("2022-03-25", "2022-12-30", "2023-09-29")
END_TRAIN = datetime(2023, 10, 1, tzinfo=timezone.utc)
HOST = "https://www.okx.com/api/v5/market/history-candles"


def utc(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def run(outdir: str):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    probes = []
    for expiry in EXPIRIES:
        # Public 1H bars strictly prior to each preregistered expiry.
        before_expiry = utc(expiry) + timedelta(hours=8)
        after = int((before_expiry - timedelta(days=1)).timestamp() * 1000)
        for asset in ASSETS:
            instrument = f"{asset}-USDT-{expiry[2:].replace('-', '')}"
            params = urlencode({"instId": instrument, "bar": "1H", "after": str(after), "limit": "30"})
            url = f"{HOST}?{params}"
            raw = b""
            http_status = None
            error = None
            try:
                request = Request(url, headers={"User-Agent": "V99-G1-source-only/1.0", "Accept": "application/json"})
                with urlopen(request, timeout=25) as response:
                    http_status = response.status
                    raw = response.read(2_000_000)
            except HTTPError as exc:
                http_status = exc.code
                raw = exc.read(2_000_000)
                error = f"HTTP_{exc.code}"
            except (URLError, TimeoutError, OSError) as exc:
                error = type(exc).__name__
            filename = f"{instrument}.json"
            (out / filename).write_bytes(raw)
            decoded = None
            rows = []
            if raw:
                try:
                    decoded = json.loads(raw)
                    if isinstance(decoded, dict) and isinstance(decoded.get("data"), list):
                        rows = decoded["data"]
                except (ValueError, UnicodeDecodeError):
                    error = "NON_JSON_FIRST_PARTY_RESPONSE"
            observed = []
            for row in rows:
                if isinstance(row, list) and len(row) >= 5:
                    try:
                        ts = int(row[0])
                        price = float(row[1])
                        if 0 < price < float("inf"):
                            observed.append(ts)
                    except (ValueError, TypeError):
                        pass
            # Source feasibility is not a certification of instrument listing/delivery.
            near = [ts for ts in observed if int((before_expiry-timedelta(days=10)).timestamp()*1000)
                    <= ts < int(before_expiry.timestamp()*1000)]
            accepted = (http_status == 200 and isinstance(decoded, dict)
                        and decoded.get("code") == "0" and bool(near))
            probes.append({
                "instrument": instrument, "expiry": expiry, "request_url": url,
                "http_status": http_status, "error": error,
                "okx_code": decoded.get("code") if isinstance(decoded, dict) else None,
                "okx_message": decoded.get("msg") if isinstance(decoded, dict) else None,
                "raw_filename": filename, "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "raw_bytes": len(raw), "returned_rows": len(rows),
                "near_expiry_valid_open_rows": len(near),
                "source_retrievable": bool(accepted)
            })
            print(json.dumps({k: probes[-1][k] for k in (
                "instrument", "http_status", "okx_code", "returned_rows",
                "near_expiry_valid_open_rows", "source_retrievable", "error"
            )}, sort_keys=True), flush=True)
            time.sleep(.25)
    all_found = all(p["source_retrievable"] for p in probes)
    report = {
        "schema": "G1_EXPIRED_QUARTERLY_FUTURES_SOURCE_GATE_V1",
        "preregistration_commit": PREREG,
        "status": "SOURCE_SAMPLES_AVAILABLE_NOT_FULL_TRAIN" if all_found
                  else "BLOCKED_ORIGINAL_EXPIRED_FUTURES_SOURCE",
        "probes": probes,
        "train_end_exclusive": END_TRAIN.isoformat(),
        "all_six_samples_retrievable": all_found,
        "economic_train_executed": False,
        "roi_computed": False,
        "native_contract_metadata_authenticated": False,
        "settlement_cash_authenticated": False,
        "historical_account_fills_authenticated": False,
        "validation_opened": False, "holdout_opened": False,
        "orders_enabled": False, "promotion_authorized": False,
    }
    (out / "g1_source_gate.json").write_text(json.dumps(report, sort_keys=True, indent=2)+"\n")
    return report


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.tools.v99_r106_g1_dated_futures_source_gate OUT_DIR")
    run(sys.argv[1])
