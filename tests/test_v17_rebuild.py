from __future__ import annotations
import sys
import unittest
from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(PROJECT/"src"),str(PROJECT/"scripts")]
from cryptoai_v13.data import FuturesData
from cryptoai_v13.v17_rebuild import GrowthSpec, eligibility, growth_targets, hold_on_clock, online_mix, research_menu
from evaluate_v17_recent import metrics, windows


def sample(n=800, assets=8):
    rng=np.random.default_rng(1605)
    index=pd.date_range("2025-01-01",periods=n,freq="h",tz="UTC")
    names=tuple(f"ASSET{j:02}USDT" for j in range(assets))
    close=pd.DataFrame(100*np.exp(np.cumsum(rng.normal(0,0.006,(n,assets))+
         np.linspace(-.0007,.0007,assets),axis=0)),index=index,columns=names)
    opened=close.shift(1).fillna(close.iloc[0])
    frames={"open":opened,"close":close,"high":np.maximum(opened,close)*1.002,
        "low":np.minimum(opened,close)*.998,
        "quote_volume":pd.DataFrame(1e8,index=index,columns=names),
        "volume":pd.DataFrame(1e6,index=index,columns=names),
        "trades":pd.DataFrame(1000,index=index,columns=names)}
    funding=pd.DataFrame(0.,index=index,columns=names)
    funding.iloc[::8,:]=np.linspace(-.0003,.0003,assets)
    return FuturesData(frames,funding,names)


class V17RebuildTests(unittest.TestCase):
    def spec(self,**kw):
        return GrowthSpec(fast_hours=24,slow_hours=96,volatility_hours=96,
            liquidity_hours=96,minimum_history_hours=96,**kw)

    def test_invalid_parameters_fail(self):
        for kwargs in ({"maximum_gross":3},{"maximum_asset_weight":0},
            {"family":"mock"},{"slow_hours":1},{"hourly_shock_limit":-1}):
            with self.assertRaises(ValueError): GrowthSpec(**kwargs)

    def test_menu_is_bounded_and_not_evaluation_generated(self):
        self.assertEqual(len(research_menu()),11)
        self.assertEqual(set(s.family for s in research_menu().values()),
                         {"trend","relative_momentum","relative_reversal","carry","breakout"})

    def test_every_family_is_prefix_causal_and_does_not_mutate_inputs(self):
        data=sample()
        before={k:v.copy() for k,v in data.frames.items()}
        cutoff=600
        prefix=FuturesData({k:v.iloc[:cutoff].copy() for k,v in data.frames.items()},
                           data.funding.iloc[:cutoff].copy(),data.symbols)
        for family in {s.family for s in research_menu().values()}:
            spec=self.spec(family=family)
            full,_=growth_targets(data,spec)
            short,_=growth_targets(prefix,spec)
            pd.testing.assert_frame_equal(full.iloc[:cutoff],short,atol=1e-12,rtol=1e-12)
            self.assertLessEqual(full.abs().max().max(),spec.maximum_asset_weight+1e-12)
            self.assertLessEqual(full.abs().sum(axis=1).max(),spec.maximum_gross+1e-12)
        for k,v in before.items(): pd.testing.assert_frame_equal(data.frames[k],v)

    def test_future_market_mutation_cannot_rewrite_past(self):
        data=sample()
        changed=FuturesData({k:v.copy() for k,v in data.frames.items()},data.funding.copy(),data.symbols)
        for k,v in changed.frames.items(): v.iloc[600:]*=10
        changed.funding.iloc[600:]*=-100
        for family in ("trend","relative_reversal","carry","breakout"):
            old,_=growth_targets(data,self.spec(family=family))
            new,_=growth_targets(changed,self.spec(family=family))
            pd.testing.assert_frame_equal(old.iloc[:600],new.iloc[:600])

    def test_future_eligible_coin_cannot_change_earlier_ranking_or_sizing(self):
        data=sample()
        boundaries={s:data.close.index[0].isoformat() for s in data.symbols}
        target,_=growth_targets(data,self.spec(),boundaries)
        frames={k:v.assign(FUTUREUSDT=v.iloc[:,0]*1000) for k,v in data.frames.items()}
        expanded=FuturesData(frames,data.funding.assign(FUTUREUSDT=-.1),(*data.symbols,"FUTUREUSDT"))
        boundaries["FUTUREUSDT"]=data.close.index[700].isoformat()
        larger,_=growth_targets(expanded,self.spec(),boundaries)
        pd.testing.assert_frame_equal(target.iloc[:700],larger.loc[:,list(data.symbols)].iloc[:700])
        self.assertEqual(larger.FUTUREUSDT.iloc[:700].abs().sum(),0)

    def test_missing_data_resets_eligibility_and_never_fills_a_price(self):
        data=sample()
        for v in data.frames.values(): v.iloc[500,0]=np.nan
        mask=eligibility(data,self.spec())
        self.assertFalse(mask.iloc[500:596,0].any())
        targets,_=growth_targets(data,self.spec())
        self.assertEqual(targets.iloc[500:596,0].abs().sum(),0)
        self.assertTrue(pd.isna(data.close.iloc[500,0]))

    def test_extreme_hour_enters_causal_quarantine(self):
        data=sample()
        for field in ("open","high","low","close"):
            data.frames[field].iloc[500:,0]*=.70
        mask=eligibility(data,self.spec())
        self.assertFalse(mask.iloc[500:524,0].any())

    def test_clock_alignment_independent_of_history_length(self):
        idx=pd.date_range("2025-01-01",periods=60,freq="h",tz="UTC")
        raw=pd.DataFrame({"x":np.arange(60)},index=idx)
        full=hold_on_clock(raw,12)
        sliced=hold_on_clock(raw.iloc[13:],12)
        pd.testing.assert_frame_equal(full.iloc[24:],sliced.iloc[11:])

    def test_online_allocation_is_causal_bounded_and_allows_cash(self):
        data=sample()
        targets={f"s{i}":data.close*0+.1 for i in range(4)}
        returns=pd.DataFrame({f"s{i}":np.sin(np.arange(800)/7)*.002 + i*.00001 for i in range(4)},index=data.close.index)
        mixed,w=online_mix(targets,returns,windows_days=(3,7))
        altered=returns.copy(); altered.iloc[600:]=1
        new,nw=online_mix(targets,altered,windows_days=(3,7))
        pd.testing.assert_frame_equal(mixed.iloc[:600],new.iloc[:600])
        self.assertLessEqual(w.sum(axis=1).max(),1+1e-12)
        self.assertLessEqual(w.max().max(),.35+1e-12)
        _,cash=online_mix(targets,returns*0-.001,windows_days=(3,7))
        self.assertEqual(cash.abs().sum().sum(),0)

    def test_metrics_include_first_day_and_boundary_drawdown(self):
        index=pd.date_range("2025-01-01 23:00",periods=3,freq="D",tz="UTC")
        equity=pd.Series([100,90,99],index=index)
        m=metrics(equity,"2025-01-02T00:00Z","2025-01-03T23:00Z")
        self.assertAlmostEqual(m["return"],-.01)
        self.assertAlmostEqual(m["max_drawdown"],-.10)
        self.assertEqual(m["days"],2)
        self.assertAlmostEqual(m["without_best_day"],-.10)

    def test_five_windows_have_true_calendar_boundaries(self):
        index=pd.date_range("2024-12-31 23:00",end="2026-08-31 23:00",freq="h",tz="UTC")
        eq=pd.Series(np.exp(np.arange(len(index))*.00001),index=index)
        result=windows(eq,index[-1])
        self.assertEqual({k:v["days"] for k,v in result.items()},
                         {"1Y":365,"6M":184,"3M":92,"30D":30,"7D":7})

if __name__=="__main__": unittest.main()

