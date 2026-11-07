import unittest
from research.v98_independent.phase243_economic_accounting import account

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
H=3600000
def grid(target=0,pre=0,close=100,fill=100):
    return [{"asset":a,"hour_open_ms":t,"pre_trade_notional_usd":pre if t else 0,
             "target_notional_usd":target,"close_price":close,"fill_price":fill}
            for t in (0,H) for a in ASSETS]
def funding(rate=0):
    return {a:{H:rate} for a in ASSETS}
class EconomicAccountingTests(unittest.TestCase):
    def test_flat_zero(self):
        out=account(grid(),funding(),initial_equity_usd=10000,taker_fee_bps=5,slippage_bps=2)
        self.assertEqual(out[-1]["ending_equity_usd"],10000)
    def test_funding_signed_and_costs(self):
        rows=grid(target=100,pre=100)
        out=account(rows,funding(.01),initial_equity_usd=10000,taker_fee_bps=5,slippage_bps=5)
        self.assertAlmostEqual(out[0]["execution_cost_usd"],.4)
        self.assertAlmostEqual(out[1]["funding_cashflow_usd"],-4)
        self.assertAlmostEqual(out[1]["ending_equity_usd"],9995.6)
    def test_missing_hour_fails(self):
        with self.assertRaisesRegex(ValueError,"INCOMPLETE_CLEAN4_INVENTORY"):
            account(grid()[:-1],funding(),initial_equity_usd=10000,taker_fee_bps=5,slippage_bps=2)
    def test_pretrade_mismatch_fails(self):
        with self.assertRaisesRegex(ValueError,"PRE_TRADE_INVENTORY_MISMATCH"):
            account(grid(target=100,pre=0),funding(),initial_equity_usd=10000,taker_fee_bps=5,slippage_bps=2)
    def test_cost_stress_monotonic(self):
        a=account(grid(target=100,pre=100),funding(),initial_equity_usd=10000,taker_fee_bps=5,slippage_bps=5)
        b=account(grid(target=100,pre=100),funding(),initial_equity_usd=10000,taker_fee_bps=5,slippage_bps=5,cost_multiplier=3)
        self.assertLess(b[-1]["ending_equity_usd"],a[-1]["ending_equity_usd"])
    def test_closing_leverage_after_adverse_move(self):
        # Entry gross 1.6x passes; a 30% adverse mark leaves 2.15x.
        with self.assertRaisesRegex(ValueError,"CLOSING_GROSS_LEVERAGE_LIMIT"):
            account(grid(target=4000,close=70,fill=100),funding(),
                    initial_equity_usd=10000,taker_fee_bps=0,slippage_bps=0)
    def test_entry_leverage_uses_post_gap_equity(self):
        rows = grid(target=4000, pre=4000)
        for r in rows:
            if r["hour_open_ms"] == H:
                r["fill_price"] = 70
                r["pre_trade_notional_usd"] = 2800
                r["close_price"] = 70
                r["target_notional_usd"] = 4000
        # Prior inventory of 16k loses 4.8k at the next open. 16k target
        # must be rejected against 5.2k available equity, even if it passed
        # the obsolete check against 10k starting equity.
        with self.assertRaisesRegex(ValueError,"ENTRY_GROSS_LEVERAGE_LIMIT"):
            account(rows,funding(),initial_equity_usd=10000,taker_fee_bps=0,slippage_bps=0)
    def test_gap_revalues_units_without_double_counting(self):
        rows = grid(target=100,pre=100)
        for r in rows:
            if r["hour_open_ms"] == H:
                r["fill_price"] = 110
                r["pre_trade_notional_usd"] = 110
                r["close_price"] = 110
                r["target_notional_usd"] = 110
        out=account(rows,funding(),initial_equity_usd=10000,taker_fee_bps=0,slippage_bps=0)
        self.assertAlmostEqual(out[-1]["price_pnl_usd"],40)
        self.assertAlmostEqual(out[-1]["ending_equity_usd"],10040)

    def test_stale_pretrade_usd_rejected_on_gap(self):
        rows = grid(target=100,pre=100)
        for r in rows:
            if r["hour_open_ms"] == H:
                r["fill_price"] = 110
                r["close_price"] = 110
        with self.assertRaisesRegex(ValueError,"PRE_TRADE_INVENTORY_MISMATCH"):
            account(rows,funding(),initial_equity_usd=10000,taker_fee_bps=0,slippage_bps=0)

    def test_leverage_gate(self):
        with self.assertRaisesRegex(ValueError,"ENTRY_GROSS_LEVERAGE_LIMIT"):
            account(grid(target=10000),funding(),initial_equity_usd=10000,taker_fee_bps=5,slippage_bps=5)
if __name__=="__main__": unittest.main()
