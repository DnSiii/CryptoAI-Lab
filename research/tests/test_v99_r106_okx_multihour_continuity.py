"""Native two-hour source witnesses; synthetic independent provenance samples only."""
from __future__ import annotations
import copy
import hashlib
import json
import tempfile
import unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from research.tools import v99_r106_okx_multihour_continuity as witness
from research.tools import v99_r106_okx_prospective_receipt as okx

UTC=timezone.utc

def hour(h):
    return datetime(2026,10,14,h,tzinfo=UTC)

def fake(root, observation=20, revised=False):
    root=Path(root)
    root.mkdir(parents=True,exist_ok=True)
    received=okx.iso(hour(observation)+timedelta(minutes=15))
    manifest={
        "schema":"V99_R106_OKX_PROSPECTIVE_ASOF_V1",
        "mode":"DATA_ONLY",
        "paper_publication_authorized":False,
        "promotion_authorized":False,
        "real_orders_enabled":False,
        "last_received_utc":received,
        "instruments":{},
    }
    for instrument in okx.INSTS:
        rows=[]
        for h in range(observation-1,observation-6,-1):
            begin=hour(h)
            if revised and h==observation-3:
                price="104"
            else:price="103"
            row=[str(int(begin.timestamp()*1000)),"100",price,"99",
                 "102","250","25000","25500","1"]
            rows.append(row)
        curr=hour(observation)
        rows.insert(0,[str(int(curr.timestamp()*1000)),"100","103","99",
                       "102","250","25000","25500","0"])
        data={"code":"0","msg":"","data":rows}
        raw=json.dumps(data,separators=(",",":")).encode()
        (root/(instrument+".raw.json")).write_bytes(raw)
        manifest["instruments"][instrument]={
            "received_utc":received,
            "source_http_url":okx.HOST+okx.candle_path(instrument),
            "source_raw_sha256":hashlib.sha256(raw).hexdigest(),
            "latest_confirmed_close_utc":okx.iso(curr),
        }
    (root/"manifest.json").write_text(json.dumps(manifest,sort_keys=True))
    return root


class TestDualHour(unittest.TestCase):
    def roots(self,old=20,new=21,revised=False):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        folder=Path(tmp.name)
        return fake(folder/"prior",old),fake(folder/"current",new,revised)

    def test_distinct_adjacent_prospective_hours(self):
        prior,current=self.roots()
        report=witness.evaluate(witness.load(prior),witness.load(current))
        self.assertEqual(report["status"],"SOURCE_CONTINUITY_OBSERVED_ONLY")
        self.assertEqual(report["elapsed_source_hours"],1)
        self.assertEqual(report["overlap_observations"],20)
        self.assertEqual(report["revised_confirmed_hours"],0)
        self.assertEqual(report["issues"],[])
        for k in ("paper_publication_authorized","promotion_authorized",
                  "holdout_accessed","binance_to_okx_strategy_transfer_authorized",
                  "source_independently_exchange_signed"):
            self.assertFalse(report[k],k)
        self.assertEqual(report["economic_trials"],0)

    def test_missing_hours_forces_hold(self):
        prior,current=self.roots(old=20,new=23)
        result=witness.evaluate(witness.load(prior),witness.load(current))
        self.assertEqual(result["status"],"DATA_ONLY_HOLD_CONTINUITY")
        self.assertIn("UNATTESTED_HOURLY_GAP:3h",result["issues"])

    def test_no_bar_overlap_fails_to_claim_continuity(self):
        prior,current=self.roots(old=12,new=20)
        result=witness.evaluate(witness.load(prior),witness.load(current))
        self.assertIn("NO_IDENTICAL_BAR_OBSERVATION_WINDOW",result["issues"])
        self.assertFalse(result["paper_publication_authorized"])

    def test_confirmed_source_revision_quarantined(self):
        prior,current=self.roots(old=20,new=21,revised=True)
        result=witness.evaluate(witness.load(prior),witness.load(current))
        self.assertEqual(result["status"],"DATA_ONLY_HOLD_CONTINUITY")
        self.assertEqual(result["revised_confirmed_hours"],5)

    def test_raw_mutation_breaks_sha(self):
        prior,current=self.roots()
        p=current/(okx.INSTS[0]+".raw.json")
        p.write_bytes(p.read_bytes()+b" ")
        with self.assertRaisesRegex(ValueError,"raw_hash_mismatch"):
            witness.load(current)

    def test_manifest_close_mismatch_fails(self):
        prior,current=self.roots()
        p=current/"manifest.json";m=json.loads(p.read_text())
        m["instruments"][okx.INSTS[0]]["latest_confirmed_close_utc"]=okx.iso(hour(19))
        p.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError,"manifest_vs_raw_close_mismatch"):
            witness.load(current)

    def test_wrong_source_url_fails(self):
        prior,current=self.roots()
        p=current/"manifest.json";m=json.loads(p.read_text())
        m["instruments"][okx.INSTS[1]]["source_http_url"]="https://mirror.test/candles"
        p.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError,"source_url_not_authorized"):
            witness.load(current)

    def test_promoted_manifest_rejected(self):
        prior,current=self.roots()
        p=current/"manifest.json";m=json.loads(p.read_text())
        m["paper_publication_authorized"]=True;p.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError,"unapproved_asof_manifest"):
            witness.load(current)

    def test_same_snapshot_is_not_second_hour(self):
        prior,current=self.roots(old=20,new=20)
        with self.assertRaisesRegex(ValueError,"repeated_or_reversed"):
            witness.evaluate(witness.load(prior),witness.load(current))

    def test_second_capture_same_closed_hour_remains_hold(self):
        prior,current=self.roots(old=20,new=20)
        p=current/"manifest.json";m=json.loads(p.read_text())
        later=okx.iso(hour(20)+timedelta(minutes=20))
        m["last_received_utc"]=later
        for inst in okx.INSTS:
            m["instruments"][inst]["received_utc"]=later
        p.write_text(json.dumps(m))
        result=witness.evaluate(witness.load(prior),witness.load(current))
        self.assertEqual(result["status"],"DATA_ONLY_HOLD_SAME_CONFIRMED_HOUR")
        self.assertEqual(result["elapsed_source_hours"],0)
        self.assertFalse(result["publication_authorized"] if "publication_authorized" in result else result["paper_publication_authorized"])
        self.assertIn("REPEAT_SAME_CONFIRMED_HOUR_NOT_INDEPENDENT_EVIDENCE",result["issues"])

    def test_reverse_chronology_rejected(self):
        prior,current=self.roots(old=21,new=20)
        with self.assertRaisesRegex(ValueError,"repeated_or_reversed"):
            witness.evaluate(witness.load(prior),witness.load(current))

    def test_missing_raw_file_fails_closed(self):
        prior,current=self.roots()
        (current/(okx.INSTS[0]+".raw.json")).unlink()
        with self.assertRaises(FileNotFoundError):witness.load(current)

    def test_duplicate_manifest_key_rejected(self):
        prior,current=self.roots()
        (current/"manifest.json").write_text('{"mode":"DATA_ONLY","mode":"PAPER_ONLY"}')
        with self.assertRaisesRegex(ValueError,"duplicate_json_key"):witness.load(current)

if __name__=="__main__":unittest.main()
