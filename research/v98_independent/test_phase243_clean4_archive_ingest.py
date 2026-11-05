"""Regression tests for V98 Clean-4 source-only archive assembler (synthetic, no PnL)."""
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import phase243_clean4_archive_ingest as module


def _fake_month(path, asset, month):
    assert asset in module.CLEAN4
    assert month in module.MONTHS
    assert str(path).endswith(f"{asset}-1h-{month}.zip")
    start = pd.Timestamp(f"{month}-01", tz="UTC")
    end = start + pd.offsets.MonthBegin(1)
    hours = pd.date_range(start, end - pd.Timedelta(hours=1), freq="h")
    base = {"BTCUSDT": 100., "ETHUSDT": 200., "BNBUSDT": 300., "SOLUSDT": 400.}[asset]
    frame = pd.DataFrame({"open_time": hours, "open": base, "high": base + 1,
                          "low": base - 1, "close": base + 0.5,
                          "volume": 10., "quote_volume": base * 10.})
    return frame, {"synthetic_test_only": True}


def test_clean4_full_calendar_and_no_xrp_or_holdout(monkeypatch, tmp_path):
    monkeypatch.setattr(module, "_parse_month", _fake_month)
    root = tmp_path / "v98_independent" / "archives"
    dest = tmp_path / "v98_independent" / "output"
    result = module.assemble_clean4(root, dest, write=True)
    assert set(result["assets"]) == set(module.CLEAN4)
    assert "XRPUSDT" not in result["assets"]
    assert result["training_cut_exclusive"] == "2026-01-01T00:00:00+00:00"
    assert result["promotion_eligible"] is False
    assert result["holdout_accessed"] is False
    assert set(p.name for p in dest.iterdir()) == {
        "BTCUSDT_1h.csv", "ETHUSDT_1h.csv", "BNBUSDT_1h.csv",
        "SOLUSDT_1h.csv", "source_manifest.json"}
    assert all(v["rows"] == 27024 for v in result["assets"].values())
    with pytest.raises(FileExistsError, match="OUTPUT_EXISTS_REFUSED"):
        module.assemble_clean4(root, dest, write=True)


def test_missing_hour_fails_without_publication(monkeypatch, tmp_path):
    def missing_hour(path, asset, month):
        frame, receipt = _fake_month(path, asset, month)
        if asset == "BNBUSDT" and month == "2024-06":
            frame = frame.iloc[1:].copy()
        return frame, receipt
    monkeypatch.setattr(module, "_parse_month", missing_hour)
    root = tmp_path / "v98_independent" / "archives"
    dest = tmp_path / "v98_independent" / "output"
    with pytest.raises(ValueError, match="CLEAN4_CONTINUITY_FAILURE_BNBUSDT"):
        module.assemble_clean4(root, dest, write=True)
    assert not dest.exists()


def test_identical_cross_asset_panel_rejected(monkeypatch, tmp_path):
    def identical(path, asset, month):
        return _fake_month(path, "BTCUSDT", month)
    monkeypatch.setattr(module, "_parse_month", identical)
    root = tmp_path / "v98_independent" / "archives"
    dest = tmp_path / "v98_independent" / "output"
    with pytest.raises(ValueError, match="DUPLICATED_CROSS_ASSET_PANEL"):
        module.assemble_clean4(root, dest, write=True)
    assert not dest.exists()
