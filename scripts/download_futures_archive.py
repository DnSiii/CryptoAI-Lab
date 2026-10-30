from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import time
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
BASE = "https://data.binance.vision/data/futures/um/monthly"


@dataclass(frozen=True)
class Job:
    kind: str
    symbol: str
    month: str

    @property
    def stem(self) -> str:
        if self.kind == "klines":
            return f"{self.symbol}-1h-{self.month}"
        return f"{self.symbol}-fundingRate-{self.month}"

    @property
    def url(self) -> str:
        if self.kind == "klines":
            return f"{BASE}/klines/{self.symbol}/1h/{self.stem}.zip"
        return f"{BASE}/fundingRate/{self.symbol}/{self.stem}.zip"

    @property
    def directory(self) -> Path:
        return PROJECT / "data" / "raw" / self.kind / self.symbol


def months(start: str, end: str) -> list[str]:
    sy, sm = map(int, start.split("-"))
    ey, em = map(int, end.split("-"))
    result = []
    year, month = sy, sm
    while (year, month) <= (ey, em):
        result.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            year += 1
            month = 1
    return result


def fetch(url: str, attempts: int = 4) -> bytes | None:
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "CryptoAI-research/13"})
            with urllib.request.urlopen(request, timeout=45) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            if attempt == attempts - 1:
                raise
        except (TimeoutError, urllib.error.URLError):
            if attempt == attempts - 1:
                raise
        time.sleep(1.5 * (attempt + 1))
    return None


def download(job: Job) -> dict:
    job.directory.mkdir(parents=True, exist_ok=True)
    target = job.directory / f"{job.stem}.zip"
    checksum_target = target.with_suffix(".zip.CHECKSUM")
    if target.exists() and checksum_target.exists():
        checksum = checksum_target.read_text().split()[0]
        if hashlib.sha256(target.read_bytes()).hexdigest() == checksum:
            return {"status": "cached", "job": job.__dict__, "bytes": target.stat().st_size}

    payload = fetch(job.url)
    if payload is None:
        return {"status": "missing", "job": job.__dict__}
    checksum_payload = fetch(job.url + ".CHECKSUM")
    if checksum_payload is None:
        raise RuntimeError(f"checksum ausente para {job.url}")
    expected = checksum_payload.decode().split()[0]
    actual = hashlib.sha256(payload).hexdigest()
    if actual != expected:
        raise RuntimeError(f"checksum inválido para {job.url}: {actual} != {expected}")

    # Testa o CRC antes de preservar o arquivo.
    import io
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        if archive.testzip() is not None:
            raise RuntimeError(f"CRC inválido em {job.url}")
    target.write_bytes(payload)
    checksum_target.write_bytes(checksum_payload)
    return {"status": "downloaded", "job": job.__dict__, "bytes": len(payload), "sha256": actual}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=40)
    parser.add_argument("--config", default="research.json")
    args = parser.parse_args()
    config = json.loads((PROJECT / "config" / args.config).read_text())
    jobs = [
        Job(kind, symbol, month)
        for symbol, start in config["symbols"].items()
        for month in months(start, config["cutoff_month"])
        for kind in ("klines", "fundingRate")
    ]
    results: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(download, job): job for job in jobs}
        for number, future in enumerate(concurrent.futures.as_completed(futures), 1):
            results.append(future.result())
            if number % 100 == 0 or number == len(jobs):
                counts = {key: sum(item["status"] == key for item in results)
                          for key in ("downloaded", "cached", "missing")}
                print(f"{number}/{len(jobs)} {counts}", flush=True)
    results.sort(key=lambda item: (item["job"]["symbol"], item["job"]["month"], item["job"]["kind"]))
    manifest = {
        "source": BASE,
        "jobs": len(jobs),
        "downloaded": sum(item["status"] == "downloaded" for item in results),
        "cached": sum(item["status"] == "cached" for item in results),
        "missing": sum(item["status"] == "missing" for item in results),
        "results": results,
    }
    stem = Path(args.config).stem.upper()
    suffix = "" if args.config == "research.json" else f"_{stem}"
    output = PROJECT / "data" / f"RAW_DOWNLOAD_MANIFEST{suffix}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2) + "\n")
    print(output)


if __name__ == "__main__":
    main()
