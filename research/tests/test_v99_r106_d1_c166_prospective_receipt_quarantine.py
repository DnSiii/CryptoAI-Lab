"""C166 adversarial receipt quarantine tests; no market download or orders."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from research.verification.independent_d1_c166_prospective_receipt_quarantine import (
    quarantine_prospective_receipts,
)

OBS = "2026-10-23T18:43:00+00:00"
LATEST = "2026-10-23T17:00:00+00:00"


class ReceiptQuarantine(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.market = Path(self.tmp.name) / "market"
        self.terms = Path(self.tmp.name) / "terms"
        self.market.mkdir()
        self.terms.mkdir()
        self.m = dict(schema="V99_R106_OKX_PROSPECTIVE_ASOF_V1",
                      provider="OKX", mode="DATA_ONLY", economic_trials=0,
                      promotion_authorized=False, real_orders_enabled=False,
                      paper_publication_authorized=False,
                      first_party_observation_only_not_venue_signed=True,
                      first_received_utc=OBS, instruments={})
        self.t = dict(schema="V99_R106_OKX_NATIVE_TERMS_ASOF_V1",
                      provider="OKX", mode="DATA_ONLY", economic_trials=0,
                      promotion_authorized=False, real_orders_enabled=False,
                      paper_publication_authorized=False,
                      fee_schedule_independently_proven=False,
                      funding_cashflows_settled_and_pit_authenticated=False,
                      historical_first_seen_authenticated=False,
                      acquisition_last_utc=OBS, contracts={})
        for asset, value in (("BTC", "0.01"), ("ETH", "0.1")):
            inst = asset + "-USDT-SWAP"
            raw = ("market-" + inst).encode()
            (self.market / (inst + ".raw.json")).write_bytes(raw)
            self.m["instruments"][inst] = dict(
                instrument=inst, first_observed_now=True, confirmed_candles=5,
                latest_confirmed_open_utc=LATEST, received_utc=OBS,
                source_raw_sha256=hashlib.sha256(raw).hexdigest())
            hashes = {}
            for kind in ("metadata", "funding"):
                raw = (kind + "-" + inst).encode()
                (self.terms / (kind + "_" + inst + ".raw.json")).write_bytes(raw)
                hashes[kind] = hashlib.sha256(raw).hexdigest()
            self.t["contracts"][inst] = dict(
                contract=dict(instId=inst, ctType="linear", ctVal=value,
                              ctValCcy=asset, lotSz="0.01", minSz="0.01",
                              settleCcy="USDT", state="live"),
                funding_notice=dict(instId=inst, settled_cashflow_authenticated=False),
                contract_received_utc=OBS, funding_received_utc=OBS,
                contract_raw_sha256=hashes["metadata"],
                funding_raw_sha256=hashes["funding"])
        self.write()

    def write(self):
        (self.market / "manifest.json").write_text(json.dumps(self.m), encoding="utf-8")
        (self.terms / "manifest.json").write_text(json.dumps(self.t), encoding="utf-8")

    def proof(self):
        self.write()
        return quarantine_prospective_receipts(self.market, self.terms)

    def test_six_raw_receipts_verified_but_train_denied(self):
        p = self.proof()
        self.assertEqual(p["raw_receipts_sha256_verified"], 6)
        self.assertEqual(p["observed_2026_min_swap_base_by_asset_not_historical"],
                         {"BTC": "0.0001", "ETH": "0.001"})
        self.assertEqual(len(p["missing_for_historical_train"]), 5)
        self.assertFalse(any(p[k] for k in (
            "train_market_economics_authorized", "exchange_account_history_authenticated",
            "validation_opened", "final_holdout_opened", "promotion_authorized",
            "orders_enabled")))

    def test_raw_receipt_mutation_rejected(self):
        (self.market / "BTC-USDT-SWAP.raw.json").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "TAMPERED"):
            self.proof()

    def test_terms_receipt_mutation_rejected(self):
        (self.terms / "funding_ETH-USDT-SWAP.raw.json").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "TAMPERED"):
            self.proof()

    def test_missing_spot_perp_pair_rejected(self):
        del self.m["instruments"]["BTC-USDT-SWAP"]
        with self.assertRaisesRegex(ValueError, "MISSING_BTC_ETH_SWAP"):
            self.proof()

    def test_prospective_receipt_cannot_be_backdated(self):
        self.m["first_received_utc"] = "2022-01-01T00:00:00+00:00"
        with self.assertRaisesRegex(ValueError, "BACKDATED"):
            self.proof()

    def test_2026_candle_cannot_be_claimed_as_train(self):
        self.m["instruments"]["ETH-USDT-SWAP"]["latest_confirmed_open_utc"] = "2022-01-01T00:00:00+00:00"
        with self.assertRaisesRegex(ValueError, "TIME_TRAVEL"):
            self.proof()

    def test_public_funding_notice_is_not_settlement(self):
        self.t["contracts"]["BTC-USDT-SWAP"]["funding_notice"]["settled_cashflow_authenticated"] = True
        with self.assertRaisesRegex(ValueError, "FUNDING_NOTICE"):
            self.proof()

    def test_no_fee_tier_proof_from_public_metadata(self):
        self.t["fee_schedule_independently_proven"] = True
        with self.assertRaisesRegex(ValueError, "MISREPRESENTED_PROVENANCE"):
            self.proof()

    def test_no_unauthorized_economic_claim(self):
        self.m["promotion_authorized"] = True
        with self.assertRaisesRegex(ValueError, "UNAUTHORIZED_ECONOMIC_CLAIM"):
            self.proof()

    def test_minimum_order_quantity_above_lot_step(self):
        self.t["contracts"]["BTC-USDT-SWAP"]["contract"]["minSz"] = "0.03"
        self.assertEqual(self.proof()["observed_2026_min_swap_base_by_asset_not_historical"]["BTC"], "0.0003")

    def test_missing_native_minimum_rejected(self):
        del self.t["contracts"]["ETH-USDT-SWAP"]["contract"]["minSz"]
        with self.assertRaisesRegex(ValueError, "BAD_CONTRACT_QUANTITY"):
            self.proof()

    def test_invalid_contract_currency_rejected(self):
        self.t["contracts"]["BTC-USDT-SWAP"]["contract"]["ctValCcy"] = "USDT"
        with self.assertRaisesRegex(ValueError, "INVALID_NATIVE_CONTRACT"):
            self.proof()


if __name__ == "__main__":
    unittest.main()
