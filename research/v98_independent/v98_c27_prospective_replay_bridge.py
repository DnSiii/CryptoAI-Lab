"""Read-only, source-verified prospective replay bridge for frozen C27.

This module NEVER trains, selects, or executes C27. Its output is a validated
hour-indexed input package; economic replay requires an independently audited
carry-in state and a frozen executor that accepts variable horizons.
"""
import csv
import json
from pathlib import Path
from .v98_c27_prospective_source_preflight import ASSETS, HOUR, stamp_ms, validate

def prepare(root, receipt_path):
    root = Path(root).resolve()
    receipt_path = Path(receipt_path).resolve()
    gate = validate(root, receipt_path)  # fail closed before reading any bars
    receipt = json.loads(receipt_path.read_text())
    start = stamp_ms(receipt["start_utc"])
    bars, funding = {}, {}
    for asset in ASSETS:
        entry = receipt["assets"][asset]
        with (root / entry["price_file"]).open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        if len(rows) != gate["hours"]:
            raise ValueError("PROSPECTIVE_BRIDGE_HOUR_MISMATCH")
        bars[asset] = []
        for i, row in enumerate(rows):
            if stamp_ms(row["open_time"]) != start + i * HOUR:
                raise ValueError("PROSPECTIVE_BRIDGE_CLOCK_MISMATCH")
            bars[asset].append(tuple(float(row[k]) for k in
                ("open", "high", "low", "close", "quote_volume")))
        funding[asset] = {}
        with (root / entry["funding_file"]).open(newline="") as stream:
            for row in csv.DictReader(stream):
                offset = stamp_ms(row["timestamp_utc"]) - start
                if offset % HOUR or not 0 <= offset // HOUR < gate["hours"]:
                    raise ValueError("PROSPECTIVE_BRIDGE_FUNDING_CLOCK")
                funding[asset][offset // HOUR] = float(row["funding_rate"])
    return {"status": "VERIFIED_INPUT_ONLY_NOT_PNL", "source_gate": gate,
            "bars": bars, "funding_by_hour": funding,
            "economic_replay_allowed": False,
            "reason": "Frozen C27 requires audited pre-window histories, equity, weights, queue, peak and decision clock; existing replay hardcodes 27048 training hours."}
