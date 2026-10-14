"""First-party OKX native terms source-branch append regression, no trades."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from research.tools import v99_r106_terms_append as x

RECEIVED="2026-10-14T20:21:28+00:00"
ELIGIBLE="2026-10-14T22:00:00+00:00"

def prepare(root):
    src=Path(root);src.mkdir(parents=True,exist_ok=True)
    files={}
    for name in x.FILES:
        if name!="manifest.json":
            data=(name+"-OKX-synthetic").encode()
            (src/name).write_bytes(data)
            files[name]=hashlib.sha256(data).hexdigest()
    manifest={
      "schema":"V99_R106_OKX_NATIVE_TERMS_ASOF_V1",
      "mode":"DATA_ONLY",
      "acquisition_last_utc":RECEIVED,
      "earliest_safe_decision_utc":ELIGIBLE,
      "fee_schedule_independently_proven":False,
      "funding_cashflows_settled_and_pit_authenticated":False,
      "binance_r106_parameters_crossvenue_transfer_authorized":False,
      "paper_publication_authorized":False,
      "promotion_authorized":False,
      "real_orders_enabled":False,
      "holdout_accessed":False,
      "first_party_clock_receipts":[files["clock_before.raw.json"],files["clock_after.raw.json"]],
      "contracts":{
        inst:{
          "contract":{
            "instId":inst,"ctType":"linear","state":"live","settleCcy":"USDT",
            "ctVal":"0.1","ctValCcy":"BTC","lotSz":"1","minSz":"1","tickSz":"0.1"},
          "funding_notice":{"instId":inst,"observed_rate_not_settled":"0.0001",
                             "settled_cashflow_authenticated":False},
          "contract_received_utc":RECEIVED,
          "funding_received_utc":RECEIVED,
          "contract_raw_sha256":files["metadata_"+inst+".raw.json"],
          "funding_raw_sha256":files["funding_"+inst+".raw.json"]
        }
        for inst in x.INSTRUMENTS
      }
    }
    (src/"manifest.json").write_text(json.dumps(manifest))
    return manifest

class TestFundingTermsStorage(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.src=self.root/"source"
        self.manifest=prepare(self.src)
        self.dst=self.root/"receipts"
    def write(self,manifest):
        (self.src/"manifest.json").write_text(json.dumps(manifest))
    def test_verified_source_stages_no_economic_claim(self):
        result=x.append(self.src,self.dst,"38631347210")
        self.assertEqual(result["status"],"APPENDED_FIRST_PARTY_NATIVE_TERMS_ONLY")
        self.assertEqual(result["bucket"],"2026-10-14T20")
        stored=self.dst/result["bucket"]
        self.assertTrue((stored/"metadata_BTC-USDT-SWAP.raw.json").exists())
        provenance=json.loads((stored/"receipt_commit_provenance.json").read_text())
        self.assertFalse(provenance["native_fee_and_settled_funding_verified"])
        self.assertFalse(provenance["paper_or_model_changes_allowed"])
    def test_existing_hour_must_never_be_replaced(self):
        first=x.append(self.src,self.dst,"38631347210")
        last=(self.dst/first["bucket"]/"manifest.json").read_bytes()
        result=x.append(self.src,self.dst,"38631347211")
        self.assertEqual(result["status"],"ALREADY_PRESENT_IMMUTABLE")
        self.assertEqual(last,(self.dst/first["bucket"]/"manifest.json").read_bytes())
    def test_tampered_funding_bytes_rejected(self):
        (self.src/"funding_ETH-USDT-SWAP.raw.json").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError,"SHA256"):
            x.validate(self.src)
    def test_wrong_contract_semantics_rejected(self):
        a=copy.deepcopy(self.manifest)
        a["contracts"]["BTC-USDT-SWAP"]["contract"]["ctType"]="inverse"
        self.write(a)
        with self.assertRaisesRegex(ValueError,"semantics"):
            x.validate(self.src)
    def test_funding_notice_not_a_settled_cashflow(self):
        a=copy.deepcopy(self.manifest)
        a["contracts"]["DOGE-USDT-SWAP"]["funding_notice"]["settled_cashflow_authenticated"]=True
        self.write(a)
        with self.assertRaisesRegex(ValueError,"semantics"):
            x.validate(self.src)
    def test_missing_native_terms_rejected(self):
        (self.src/"metadata_SOL-USDT-SWAP.raw.json").unlink()
        with self.assertRaisesRegex(ValueError,"incomplete"):
            x.validate(self.src)
    def test_fee_auth_cannot_be_claimed_from_public_endpoint(self):
        a=copy.deepcopy(self.manifest);a["fee_schedule_independently_proven"]=True
        self.write(a)
        with self.assertRaisesRegex(ValueError,"cannot confer"):
            x.validate(self.src)
    def test_tminus1_clock_violation_rejected(self):
        a=copy.deepcopy(self.manifest);a["earliest_safe_decision_utc"]=RECEIVED
        self.write(a)
        with self.assertRaisesRegex(ValueError,"t-1"):
            x.validate(self.src)
    def test_missing_instrument_rejected(self):
        a=copy.deepcopy(self.manifest);del a["contracts"]["ETH-USDT-SWAP"]
        self.write(a)
        with self.assertRaisesRegex(ValueError,"schema or instruments"):
            x.validate(self.src)
    def test_invalid_run_id_rejected(self):
        with self.assertRaisesRegex(ValueError,"run ID"):
            x.append(self.src,self.dst,"test-only")
    def test_future_receipt_after_manifest_rejected(self):
        a=copy.deepcopy(self.manifest)
        a["contracts"]["SOL-USDT-SWAP"]["contract_received_utc"]="2026-10-14T20:22:28+00:00"
        self.write(a)
        with self.assertRaisesRegex(ValueError,"after manifest"):
            x.validate(self.src)

if __name__=="__main__":
    unittest.main()
