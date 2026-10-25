"""Independent raw-first-party-byte oracle for V99 I1 retrospective tick metadata.

Never imports the primary aggregator; asserts every original expired TRAIN put
contributes exactly once. No market data, economic TRAIN, or orders.
"""
import gzip
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

START = 1639008000000
END = 1696118400000
CUT = int(datetime(2023, 7, 6, tzinfo=timezone.utc).timestamp() * 1000)


def verify(root, output):
    root = Path(root)
    result = json.loads(Path(output).read_text())
    manifest = json.loads((root / "native_instrument_registry.json").read_text())
    assert result["schema"] == "V99_I1_RETROSPECTIVE_TICK_METADATA_SCREEN_V1"
    assert result["source_asof_classification"] == "RETROSPECTIVE_API_NOT_ASOF_TERMS"
    assert result["historical_tick_grid_certified"] is False
    assert result["historical_native_lot_certified"] is False
    assert result["historical_fee_margin_certified"] is False
    assert result["change_day_utc"] == "2023-07-06"
    assert result["change_notice"].startswith("https://support.deribit.com/")
    for asset in ("BTC", "ETH"):
        src = manifest["sources"][asset]
        original = gzip.decompress((root / src["original_gzip"]).read_bytes())
        sha = hashlib.sha256(original).hexdigest()
        assert sha == src["original_raw_sha256"]
        payload = json.loads(original)
        assert isinstance(payload["result"], list)
        assert result["original_sources"][asset] == {
            "sha256": sha, "original_rows": len(payload["result"])}
        expected = {b: {"count": 0, "tick_size_steps_present": 0,
                        "tick_0_0001": 0, "tick_0_0005": 0,
                        "tick_histogram": defaultdict(int)}
                    for b in ("before_change", "change_day_uncertain", "after_change")}
        selected = 0
        for item in payload["result"]:
            if item.get("kind") != "option" or item.get("option_type") != "put":
                continue
            t = int(item["expiration_timestamp"])
            if not START <= t < END:
                continue
            assert item["instrument_name"].startswith(asset + "-")
            selected += 1
            period = ("before_change" if t < CUT
                      else "change_day_uncertain" if t < CUT + 86400000
                      else "after_change")
            tick = ("MISSING" if item.get("tick_size") is None
                    else format(Decimal(str(item["tick_size"])).normalize(), "f"))
            x = expected[period]
            x["count"] += 1
            x["tick_histogram"][tick] += 1
            x["tick_size_steps_present"] += int(bool(item.get("tick_size_steps")))
            x["tick_0_0001"] += int(tick == "0.0001")
            x["tick_0_0005"] += int(tick == "0.0005")
        assert selected == src["train_puts"]
        for period, x in expected.items():
            assert dict(x) == result["assets"][asset][period], (asset, period)
    for key in ("economic_train_executed", "validation_opened", "holdout_opened",
                "promotion_authorized", "orders_enabled"):
        assert result[key] is False
    return True


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_asof_tick_metadata ROOT OUTPUT")
    assert verify(sys.argv[1], sys.argv[2])
    print("INDEPENDENT ORIGINAL DERIBIT TICK SOURCE VERIFIED / NO ASOF CERTIFICATION / NO PROMOTION")
