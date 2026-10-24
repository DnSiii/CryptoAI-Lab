"""Deterministic synthetic 91-Sunday fixture and negative controls (NO PNL)."""
from __future__ import annotations
import csv
import hashlib
import json
import tempfile
import unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path

from research.tools.v99_r106_i1_full_archive_intake import evaluate
from research.verification.independent_v99_r106_i1_full_archive_intake import audit

FIELDS=("exchange","symbol","timestamp","local_timestamp",
        "bid_price","ask_price","bid_amount","ask_amount")


def make_fixture(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    ds=[]
    first=datetime(2021,12,13,tzinfo=timezone.utc)
    for i in range(91):
        d=first+timedelta(days=7*i)
        sunday=d-timedelta(days=1)
        stamp=int((d-timedelta(seconds=80)).timestamp()*1_000_000)
        expiry=(d+timedelta(days=21)).strftime("%d%b%y").upper()
        name=sunday.strftime("%Y-%m-%d")+".csv"
        with (root/name).open("w",newline="",encoding="utf-8") as f:
            writer=csv.DictWriter(f,fieldnames=FIELDS)
            writer.writeheader()
            for asset in ("BTC","ETH"):
                for strike in ("100","110"):
                    writer.writerow({"exchange":"deribit",
                        "symbol":f"{asset}-{expiry}-{strike}-P",
                        "timestamp":stamp,"local_timestamp":stamp+200,
                        "bid_price":"0.04","ask_price":"0.05",
                        "bid_amount":"1.0","ask_amount":"1.0"})
        b=(root/name).read_bytes()
        ds.append({"date":sunday.strftime("%Y-%m-%d"),
                   "file":name,"sha256":hashlib.sha256(b).hexdigest(),
                   "rows":4,"complete_capture":True})
    (root/"manifest.json").write_text(json.dumps({
        "schema":"I1_FULL_TRAIN_SUNDAY_ARCHIVE_V1",
        "venue":"deribit","fixture":True,"days":ds},indent=2)+"\n")
    return ds


class FullArchiveIntakeTests(unittest.TestCase):
    def test_all_91_weeks_independent_oracle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"source"
            make_fixture(root)
            result=evaluate(root)
            self.assertEqual(result["two_strike_asset_weeks"],182)
            self.assertEqual(result["maturity_eligible_weeks"],91)
            self.assertFalse(result["economic_train_executed"])
            path=Path(tmp)/"report.json"
            path.write_text(json.dumps(result))
            audit(root,path)

    def test_byte_mutation_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            ds=make_fixture(root)
            with (root/ds[0]["file"]).open("ab") as f: f.write(b"\n")
            with self.assertRaisesRegex(ValueError,"ARCHIVE_SHA256_MISMATCH"):
                evaluate(root)

    def test_missing_week_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            ds=make_fixture(root)
            (root/ds[4]["file"]).unlink()
            with self.assertRaisesRegex(ValueError,"ARCHIVE_MISSING_OR_SYMLINK"):
                evaluate(root)

    def test_latest_invalid_quote_cancels_old_valid_quote(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            ds=make_fixture(root)
            first=root/ds[0]["file"]
            with first.open("r",newline="") as f:
                rows=list(csv.DictReader(f))
            bad=dict(rows[1])
            bad["local_timestamp"]=str(int(bad["local_timestamp"])+1000)
            bad["timestamp"]=str(int(bad["timestamp"])+1000)
            bad["ask_amount"]="0"
            with first.open("w",newline="") as f:
                w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader()
                w.writerows(rows+[bad])
            manifest=json.loads((root/"manifest.json").read_text())
            manifest["days"][0]["rows"]=5
            manifest["days"][0]["sha256"]=hashlib.sha256(first.read_bytes()).hexdigest()
            (root/"manifest.json").write_text(json.dumps(manifest))
            result=evaluate(root)
            self.assertEqual(result["two_strike_asset_weeks"],181)
            path=Path(tmp)/"report.json";path.write_text(json.dumps(result))
            audit(root,path)


if __name__=="__main__":
    unittest.main()
