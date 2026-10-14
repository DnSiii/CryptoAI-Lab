"""Fail-closed tests for read-only R98/R106 epoch auditor."""
import copy
import unittest
from datetime import datetime, timedelta, timezone
from research.tools.v99_phase195gb_paper_epoch_audit import audit, new_epoch_prereg, sha256, utc

T0=datetime(2026,10,10,5,tzinfo=timezone.utc)
def iso(n): return (T0+timedelta(hours=n)).isoformat()
def fixture():
    variants, refs={},{}
    for name in ("r98","f1","f3","f7","f12"):
        curve=[{"timestamp":iso(i),"equity_multiple":1+i*.001} for i in range(3)]
        if name=="f1":curve[1]["equity_multiple"]+=.002
        if name=="f3":curve[1]["equity_multiple"]+=.004
        ops=[{"timestamp":iso(1),"symbol":"ETHUSDT" if name in ("f1","f3") else "BTCUSDT","action":"opened"}]
        variants[name]={"paper_start_after_timestamp":iso(0),"real_orders_enabled":False,
                        "equity_curve":curve,"operations":ops}
        refs[name]={"curve":[{"timestamp":iso(-25),"equity_multiple":1},
                             {"timestamp":iso(-1),"equity_multiple":1.01}]}
    return {"mode":"PAPER_ONLY","real_orders_enabled":False,
            "same_boundary_for_all_variants":True,"version":"v99-research-five-v1",
            "paper_start_after_timestamp":iso(0),"latest_data_timestamp":iso(2),
            "variants":variants,"backtest_reference":refs}

class TestEpochAudit(unittest.TestCase):
    def setUp(self): self.d=fixture()
    def reject(self,mutate):
        mutate(self.d)
        with self.assertRaises(ValueError): audit(self.d,iso(5))
    def test_status(self):
        a=audit(self.d,iso(5));self.assertEqual(a["status"],"DATA_ONLY/HOLD")
        self.assertFalse(a["promotion_authorized"])
    def test_duplicate_traces(self):
        a=audit(self.d,iso(5));self.assertIn(["r98","f7","f12"],a["forward_duplicate_groups"])
        self.assertEqual(a["distinct_forward_traces"],3)
    def test_staleness(self):self.assertEqual(audit(self.d,iso(5))["stale_hours_at_audit"],3)
    def test_financial_missing(self):self.assertEqual(audit(self.d,iso(5))["variants"]["f1"]["missing_financial_component_rows"],3)
    def test_crossing_reference(self):
        self.d["backtest_reference"]["f1"]["curve"].append({"timestamp":iso(1),"equity_multiple":1})
        self.assertEqual(audit(self.d,iso(5))["variants"]["f1"]["reference_points_after_boundary"],1)
    def test_capped_operations(self):
        self.d["variants"]["f1"]["operations"]=[{"timestamp":iso(1),"symbol":f"S{i}"} for i in range(1500)]
        self.assertTrue(audit(self.d,iso(5))["variants"]["f1"]["operations_capped"])
    def test_real_orders(self):self.reject(lambda d:d.update(real_orders_enabled=True))
    def test_shared_boundary(self):self.reject(lambda d:d.update(same_boundary_for_all_variants=False))
    def test_missing_variant(self):self.reject(lambda d:d["variants"].pop("f1"))
    def test_variant_boundary(self):self.reject(lambda d:d["variants"]["f1"].update(paper_start_after_timestamp=iso(1)))
    def test_gap(self):self.reject(lambda d:d["variants"]["f1"]["equity_curve"][1].update(timestamp=iso(4)))
    def test_duplicate_hour(self):self.reject(lambda d:d["variants"]["f1"]["equity_curve"][1].update(timestamp=iso(0)))
    def test_invalid_equity(self):self.reject(lambda d:d["variants"]["f1"]["equity_curve"][1].update(equity_multiple=-1))
    def test_duplicate_operation(self):
        self.reject(lambda d:d["variants"]["f1"]["operations"].append(copy.deepcopy(d["variants"]["f1"]["operations"][0])))
    def test_early_operation(self):self.reject(lambda d:d["variants"]["f1"]["operations"][0].update(timestamp=iso(-1)))
    def test_future_operation(self):self.reject(lambda d:d["variants"]["f1"]["operations"][0].update(timestamp=iso(3)))
    def test_non_utc(self):self.reject(lambda d:d.update(latest_data_timestamp="2026-10-10T07:00:00-03:00"))
    def test_missing_reference(self):self.reject(lambda d:d["backtest_reference"]["f1"].update(curve=[]))
    def test_now_before_latest(self):
        with self.assertRaises(ValueError):audit(self.d,iso(1))
    def test_deterministic_hash(self):self.assertEqual(sha256(self.d),sha256(copy.deepcopy(self.d)))
    def test_no_receipt(self):
        m=new_epoch_prereg(old_audit=audit(self.d,iso(5)),epoch_id="v99-r106-epoch-02",first_new_utc=iso(3))
        self.assertFalse(m["publication_authorized"])
    def test_early_decision(self):
        with self.assertRaises(ValueError):
            new_epoch_prereg(old_audit=audit(self.d,iso(5)),epoch_id="v99-r106-epoch-02",
                             first_new_utc=iso(3),first_receipt_utc=iso(2),input_hash="a"*64)
    def test_safe_receipt_still_hold(self):
        m=new_epoch_prereg(old_audit=audit(self.d,iso(5)),epoch_id="v99-r106-epoch-02",
                            first_new_utc=iso(4),first_receipt_utc=iso(2),input_hash="a"*64)
        self.assertFalse(m["publication_authorized"])
        self.assertFalse(m["receipt_independently_authenticated"])
    def test_no_backfill(self):
        with self.assertRaises(ValueError):
            new_epoch_prereg(old_audit=audit(self.d,iso(5)),epoch_id="v99-r106-epoch-02",first_new_utc=iso(2))
    def test_invalid_hash(self):
        with self.assertRaises(ValueError):
            new_epoch_prereg(old_audit=audit(self.d,iso(5)),epoch_id="v99-r106-epoch-02",
                             first_new_utc=iso(4),first_receipt_utc=iso(2),input_hash="xyz")
    def test_invalid_epoch_id(self):
        with self.assertRaises(ValueError):
            new_epoch_prereg(old_audit=audit(self.d,iso(5)),epoch_id="epoch-02",
                             first_new_utc=iso(4),first_receipt_utc=iso(2),input_hash="a"*64)
    def test_naive_time(self):
        with self.assertRaises(ValueError):utc("2026-10-14T01:00:00")

if __name__=="__main__":unittest.main()
