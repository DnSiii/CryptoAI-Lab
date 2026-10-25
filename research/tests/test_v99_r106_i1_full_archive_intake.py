"""Deterministic synthetic 91-Sunday fixture and negative controls (NO PNL)."""
from __future__ import annotations
import csv
import gzip
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


def attach_synthetic_native_bytes(root, late_first_btc=False):
    """TEST ONLY: self-generated fake venue bytes, never historical provenance."""
    root=Path(root)
    manifest=json.loads((root/"manifest.json").read_text())
    manifest["fixture"]=False  # adversarially exercise non-fixture fail-closed path
    (root/"manifest.json").write_text(json.dumps(manifest))
    fields=("instrument_name","creation_timestamp","expiration_timestamp","strike",
            "option_type","settlement_currency","contract_size","min_trade_amount","tick_size")
    sources,registry={},{}
    for asset in ("BTC","ETH"):
        rows=[]
        for i in range(91):
            decision=datetime(2021,12,13,tzinfo=timezone.utc)+timedelta(weeks=i)
            expiry=decision+timedelta(days=21,hours=8)
            for strike in (100,110):
                created=decision-timedelta(days=1)
                if late_first_btc and asset=="BTC" and i==0 and strike==110:
                    created=decision+timedelta(days=1)
                rows.append({"kind":"option","instrument_name":
                    f"{asset}-{expiry.strftime('%d%b%y').upper()}-{strike}-P",
                    "creation_timestamp":int(created.timestamp()*1000),
                    "expiration_timestamp":int(expiry.timestamp()*1000),
                    "strike":float(strike),"option_type":"put",
                    "settlement_currency":asset,"contract_size":1.0,
                    "min_trade_amount":0.1,
                    "tick_size":(0.0005 if decision.date() < datetime(2023,7,6).date() else 0.0001),
                    "tick_size_steps":([] if decision.date() < datetime(2023,7,6).date()
                        else [{"above_price":0.005,"tick_size":0.0005}])})
        raw=json.dumps({"result":rows},sort_keys=True).encode()
        name=f"deribit_{asset.lower()}_original_instruments.json.gz"
        (root/name).write_bytes(gzip.compress(raw))
        sources[asset]={"endpoint":"https://history.deribit.com/api/v2/public/get_instruments",
            "original_raw_sha256":hashlib.sha256(raw).hexdigest(),
            "original_response_bytes":len(raw),"original_instruments":len(rows),
            "train_puts":len(rows),"missing_native_fields":{k:0 for k in fields},
            "skipped":{"nonput":0,"out_of_train":0,"invalid_metadata":0},
            "original_gzip":name,"not_asof_fee_or_margin_attestation":True}
        registry[asset]=[{k:r.get(k) for k in fields} for r in
                         sorted(rows,key=lambda r:r["instrument_name"])]
    report={"schema":"V99_I1_DERIBIT_HISTORICAL_INSTRUMENT_REGISTRY_V1",
        "source_classification":"FIRST_PARTY_ARCHIVED_METADATA_NOT_ASOF_TRADABILITY",
        "train_start_ms":1639008000000,"train_end_exclusive_ms":1696118400000,
        "sources":sources,"registry":registry}
    report.update({k:False for k in ("economic_train_executed",
        "historical_fee_authenticated","native_margin_liquidation_authenticated",
        "historical_executable_quotes_authenticated","validation_opened",
        "holdout_opened","promotion_authorized","orders_enabled")})
    (root/"native_instrument_registry.json").write_text(json.dumps(report))
    return report


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


    def test_nonfixture_without_original_native_bytes_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            make_fixture(root)
            manifest=json.loads((root/"manifest.json").read_text())
            manifest["fixture"]=False
            (root/"manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError,"NATIVE_ORIGINAL_REGISTRY_REQUIRED"):
                evaluate(root)

    def test_nonfixture_native_asof_creation_rejects_unlisted_quote(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            make_fixture(root)
            attach_synthetic_native_bytes(root,late_first_btc=True)
            result=evaluate(root)
            self.assertTrue(result["native_registry_verified"])
            self.assertEqual(result["two_strike_asset_weeks"],181)
            self.assertFalse(result["economic_train_executed"])
            report=Path(tmp)/"native_asof.json"
            report.write_text(json.dumps(result))
            audit(root,report)

    def test_nonfixture_forged_native_metadata_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            make_fixture(root)
            report=attach_synthetic_native_bytes(root)
            report["registry"]["BTC"][0]["strike"]+=1
            (root/"native_instrument_registry.json").write_text(json.dumps(report))
            with self.assertRaisesRegex(ValueError,"NATIVE_ORIGINAL_REGISTRY_UNVERIFIED"):
                evaluate(root)

    def test_original_native_2022_offgrid_bid_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            make_fixture(root)
            attach_synthetic_native_bytes(root)
            path=root/"2021-12-12.csv"
            with path.open(newline="",encoding="utf-8") as fp:
                rows=list(csv.DictReader(fp))
            rows[1]["bid_price"]="0.0401"  # invalid pre-2023 0.0005 grid
            with path.open("w",newline="",encoding="utf-8") as fp:
                w=csv.DictWriter(fp,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
            manifest=json.loads((root/"manifest.json").read_text())
            manifest["days"][0]["sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
            (root/"manifest.json").write_text(json.dumps(manifest))
            result=evaluate(root)
            self.assertEqual(result["two_strike_asset_weeks"],181)
            out=root/"audit.json";out.write_text(json.dumps(result))
            audit(root,out)

    def test_original_native_2023_postchange_above_threshold_offgrid_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            make_fixture(root)
            attach_synthetic_native_bytes(root)
            target=datetime(2023,7,10,tzinfo=timezone.utc)
            week=(target-datetime(2021,12,13,tzinfo=timezone.utc)).days//7
            path=root/(target-timedelta(days=1)).strftime("%Y-%m-%d")
            path=Path(str(path)+".csv")
            with path.open(newline="",encoding="utf-8") as fp:
                rows=list(csv.DictReader(fp))
            rows[1]["bid_price"]="0.0040"
            rows[1]["ask_price"]="0.0051"  # >0.005 requires 0.0005, not 0.0001
            with path.open("w",newline="",encoding="utf-8") as fp:
                w=csv.DictWriter(fp,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
            manifest=json.loads((root/"manifest.json").read_text())
            manifest["days"][week]["sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
            (root/"manifest.json").write_text(json.dumps(manifest))
            result=evaluate(root)
            self.assertEqual(result["two_strike_asset_weeks"],181)
            out=root/"audit.json";out.write_text(json.dumps(result))
            audit(root,out)

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


    def test_latest_malformed_price_cancels_prior_quote(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            ds=make_fixture(root)
            first=root/ds[0]["file"]
            with first.open("r",newline="") as f:
                rows=list(csv.DictReader(f))
            bad=dict(rows[1])
            bad["local_timestamp"]=str(int(bad["local_timestamp"])+1000)
            bad["timestamp"]=str(int(bad["timestamp"])+1000)
            bad["ask_price"]="NOT_A_NUMBER"
            with first.open("w",newline="") as f:
                w=csv.DictWriter(f,fieldnames=FIELDS)
                w.writeheader();w.writerows(rows+[bad])
            manifest=json.loads((root/"manifest.json").read_text())
            manifest["days"][0]["rows"]=5
            manifest["days"][0]["sha256"]=hashlib.sha256(first.read_bytes()).hexdigest()
            (root/"manifest.json").write_text(json.dumps(manifest))
            result=evaluate(root)
            self.assertEqual(result["two_strike_asset_weeks"],181)
            path=Path(tmp)/"report.json";path.write_text(json.dumps(result))
            audit(root,path)



    def test_recent_arrival_with_six_minute_old_exchange_event_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            ds=make_fixture(root)
            path=root/ds[0]["file"]
            with path.open(newline="",encoding="utf-8") as f:
                rows=list(csv.DictReader(f))
            rows[1]["timestamp"]=str(int(rows[1]["local_timestamp"])-360_000_000)
            with path.open("w",newline="",encoding="utf-8") as f:
                writer=csv.DictWriter(f,fieldnames=FIELDS)
                writer.writeheader();writer.writerows(rows)
            manifest=json.loads((root/"manifest.json").read_text())
            manifest["days"][0]["sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
            (root/"manifest.json").write_text(json.dumps(manifest))
            result=evaluate(root)
            self.assertEqual(result["two_strike_asset_weeks"],181)
            report=Path(tmp)/"result.json";report.write_text(json.dumps(result))
            audit(root,report)

    def test_newer_stale_exchange_event_revokes_prior_valid_book(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            ds=make_fixture(root)
            path=root/ds[0]["file"]
            with path.open(newline="",encoding="utf-8") as f:
                rows=list(csv.DictReader(f))
            newer=dict(rows[1])
            newer["local_timestamp"]=str(int(newer["local_timestamp"])+1000)
            newer["timestamp"]=str(int(newer["local_timestamp"])-360_000_000)
            with path.open("w",newline="",encoding="utf-8") as f:
                writer=csv.DictWriter(f,fieldnames=FIELDS)
                writer.writeheader();writer.writerows(rows+[newer])
            manifest=json.loads((root/"manifest.json").read_text())
            manifest["days"][0]["rows"]=5
            manifest["days"][0]["sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
            (root/"manifest.json").write_text(json.dumps(manifest))
            result=evaluate(root)
            self.assertEqual(result["two_strike_asset_weeks"],181)
            report=Path(tmp)/"result.json";report.write_text(json.dumps(result))
            audit(root,report)


    def test_same_arrival_last_capture_row_revokes_higher_exchange_timestamp(self):
        """The last physical CSV row wins even when its venue event is older."""
        from research.tools.v99_r106_i1_entry_book_export import export_books
        from research.verification.independent_v99_r106_i1_entry_book_export import audit as audit_books
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"source"
            ds=make_fixture(root)
            path=root/ds[0]["file"]
            with path.open(newline="",encoding="utf-8") as fp:
                rows=list(csv.DictReader(fp))
            last=dict(rows[1])  # same arrival as earlier valid BTC strike
            last["timestamp"]=str(int(last["timestamp"])-1000)
            last["ask_amount"]="0"  # final captured book is not executable
            with path.open("w",newline="",encoding="utf-8") as fp:
                writer=csv.DictWriter(fp,fieldnames=FIELDS)
                writer.writeheader();writer.writerows(rows+[last])
            manifest=json.loads((root/"manifest.json").read_text())
            manifest["days"][0]["rows"]=5
            manifest["days"][0]["sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
            (root/"manifest.json").write_text(json.dumps(manifest))
            result=evaluate(root)
            self.assertEqual(result["two_strike_asset_weeks"],181)
            report=root/"intake.json";report.write_text(json.dumps(result))
            audit(root,report)
            export=export_books(root)
            self.assertEqual(export["source_pairs"],181)
            self.assertEqual(len(export["quotes"]),363)
            out=root/"books.json";out.write_text(json.dumps(export))
            self.assertEqual(audit_books(root,out),363)

    def test_reversed_local_arrival_original_capture_fails_closed(self):
        """An out-of-order source capture must never be silently re-sorted."""
        from research.tools.v99_r106_i1_entry_book_export import export_books
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            ds=make_fixture(root)
            path=root/ds[0]["file"]
            with path.open(newline="",encoding="utf-8") as fp:
                rows=list(csv.DictReader(fp))
            reversed_row=dict(rows[1])
            reversed_row["local_timestamp"]=str(int(reversed_row["local_timestamp"])-1)
            reversed_row["timestamp"]=str(int(reversed_row["timestamp"])-1)
            with path.open("w",newline="",encoding="utf-8") as fp:
                writer=csv.DictWriter(fp,fieldnames=FIELDS)
                writer.writeheader();writer.writerows(rows+[reversed_row])
            manifest=json.loads((root/"manifest.json").read_text())
            manifest["days"][0]["rows"]=5
            manifest["days"][0]["sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
            (root/"manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError,"OUT_OF_ORDER_ORIGINAL_CAPTURE"):
                evaluate(root)
            with self.assertRaisesRegex(ValueError,"OUT_OF_ORDER_ORIGINAL_CAPTURE"):
                export_books(root)


if __name__=="__main__":
    unittest.main()
