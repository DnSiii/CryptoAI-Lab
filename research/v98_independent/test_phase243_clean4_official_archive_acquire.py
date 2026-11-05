"""Offline integrity regressions for the V98 official Clean-4 archive acquirer."""
import hashlib
import pytest
import phase243_clean4_official_archive_acquire as acq

def test_provider_checksum_and_atomic_archive(monkeypatch, tmp_path):
    data = b"synthetic zip placeholder; integrity only"
    digest = hashlib.sha256(data).hexdigest()
    def fake_fetch(url, cap):
        name = "BTCUSDT-1h-2022-12.zip"
        assert name in url
        return (f"{digest}  {name}\n".encode() if url.endswith(".CHECKSUM") else data)
    monkeypatch.setattr(acq, "_fetch", fake_fetch)
    root = tmp_path / "v98_independent" / "source"
    result = acq.acquire(root, limit=1)
    assert result["verified_archives"] == 1
    assert not result["promotion_eligible"]
    assert (root / "klines/BTCUSDT/1h/BTCUSDT-1h-2022-12.zip").read_bytes() == data
    assert acq.acquire(root, limit=1)["verified_archives"] == 1

def test_provider_mismatch_does_not_publish(monkeypatch, tmp_path):
    name = "BTCUSDT-1h-2022-12.zip"
    def fake_fetch(url, cap):
        return (f"{'0'*64}  {name}\n".encode() if url.endswith(".CHECKSUM") else b"wrong")
    monkeypatch.setattr(acq, "_fetch", fake_fetch)
    root = tmp_path / "v98_independent" / "source"
    with pytest.raises(ValueError, match="PROVIDER_SHA256_MISMATCH"):
        acq.acquire(root, limit=1)
    assert not (root / f"klines/BTCUSDT/1h/{name}").exists()

def test_quarantine_and_training_calendar():
    assert acq.ASSETS == ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")
    assert len(acq.MONTHS) == 37
    assert acq.MONTHS[0] == "2022-12" and acq.MONTHS[-1] == "2025-12"
