"""Independent raw-byte replay of Deribit I1 original instrument registry.
Does not import the primary collector. Source-only; no trades or ROI.
"""
import gzip
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

START, END = 1639008000000, 1696118400000
KEYS = ("instrument_name","creation_timestamp","expiration_timestamp","strike",
        "option_type","settlement_currency","contract_size","min_trade_amount","tick_size")


def audit(folder):
    root = Path(folder)
    report = json.loads((root / "native_instrument_registry.json").read_text())
    assert report["schema"] == "V99_I1_DERIBIT_HISTORICAL_INSTRUMENT_REGISTRY_V1"
    assert report["train_start_ms"] == START and report["train_end_exclusive_ms"] == END
    assert set(report["sources"]) == set(report["registry"]) == {"BTC", "ETH"}
    for asset in ("BTC", "ETH"):
        src = report["sources"][asset]
        assert src["endpoint"] == "https://history.deribit.com/api/v2/public/get_instruments"
        assert src["not_asof_fee_or_margin_attestation"] is True
        original = gzip.decompress((root / src["original_gzip"]).read_bytes())
        assert hashlib.sha256(original).hexdigest() == src["original_raw_sha256"]
        assert len(original) == src["original_response_bytes"]
        payload = json.loads(original)
        assert not payload.get("error") and isinstance(payload["result"], list)
        rows = payload["result"]
        assert len(rows) == src["original_instruments"]
        chosen, dropped = [], {"nonput":0,"out_of_train":0,"invalid_metadata":0}
        for row in rows:
            assert isinstance(row,dict)
            if row.get("kind") != "option" or row.get("option_type") != "put":
                dropped["nonput"] += 1
                continue
            try:
                t = int(row["expiration_timestamp"])
                created = int(row["creation_timestamp"])
                name = row["instrument_name"]
            except (ValueError, KeyError, TypeError):
                dropped["invalid_metadata"] += 1
                continue
            if t < START or t >= END:
                dropped["out_of_train"] += 1
                continue
            bits = name.split("-")
            assert len(bits) == 4 and bits[0] == asset and bits[3] == "P"
            stamp = datetime.strptime(bits[1], "%d%b%y").replace(tzinfo=timezone.utc)
            strike = float(bits[2])
            assert stamp.date() == datetime.fromtimestamp(t/1000,timezone.utc).date()
            assert math.isfinite(strike) and strike > 0 and strike == float(row["strike"])
            assert created <= t
            chosen.append({key:row.get(key) for key in KEYS})
        chosen.sort(key=lambda r:r["instrument_name"])
        assert len({r["instrument_name"] for r in chosen}) == len(chosen)
        assert chosen == report["registry"][asset]
        assert dropped == src["skipped"]
        assert len(chosen) == src["train_puts"] and len(chosen) > 0
        assert {key:sum(r[key] is None for r in chosen) for key in KEYS} == src["missing_native_fields"]
        print(json.dumps({"asset":asset,"original_instruments":len(rows),
                          "original_train_puts":len(chosen),"independent":True}),flush=True)
    for flag in ("economic_train_executed","historical_fee_authenticated",
                 "native_margin_liquidation_authenticated","historical_executable_quotes_authenticated",
                 "validation_opened","holdout_opened","promotion_authorized","orders_enabled"):
        assert report[flag] is False
    return True


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_historical_instruments OUT_DIR")
    assert audit(sys.argv[1])
    print("INDEPENDENT ORIGINAL BYTES VERIFIED / NO PNL / NO PROMOTION")
