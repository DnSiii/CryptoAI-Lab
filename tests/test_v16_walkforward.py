from dataclasses import replace
from importlib.util import find_spec
import unittest
import numpy as np
import pandas as pd
from test_v16_rebuild import sample
from cryptoai_v13.data import FuturesData
from cryptoai_v13.v16_walkforward import (
    ForecastSpec,feature_panel,forward_labels,purged_train_rows,
    walkforward_forecasts,forecasts_to_targets)
from cryptoai_v13.v16_relative import RelativeSpec,balance_sides,relative_targets,worthwhile_rebalance


class WalkforwardTests(unittest.TestCase):
    def test_purge_excludes_every_unfinished_trade(self):
        index=pd.date_range("2025-01-01",periods=24*100,freq="h",tz="UTC")
        spec=ForecastSpec(horizon_hours=24,decision_every_hours=12,train_days=60)
        asof=index[-1].floor("D")
        chosen=index[purged_train_rows(index,asof,spec)]
        self.assertTrue(((chosen+pd.Timedelta(hours=25))<asof).all())
        self.assertTrue((chosen>=asof-pd.Timedelta(days=60)).all())
        self.assertTrue((chosen.hour%12==0).all())

    def test_labels_use_next_open_and_charge_funding_after_entry(self):
        d=sample(80,2); h=12; t=20
        actual=forward_labels(d,h).iloc[t,0]
        expected=d.frames['open'].iloc[t+h+1,0]/d.frames['open'].iloc[t+1,0]-1
        expected-=d.funding.iloc[t+2:t+h+2,0].sum()
        self.assertAlmostEqual(actual,expected)
        for frame in d.frames.values(): frame.iloc[t+5,0]=np.nan
        self.assertTrue(np.isnan(forward_labels(d,h).iloc[t,0]))
        self.assertTrue(forward_labels(d,h).iloc[-h-1:].isna().all().all())

    def test_features_ignore_future_and_missing_ratios(self):
        d=sample(1400,8)
        prefix=FuturesData({k:v.iloc[:1100] for k,v in d.frames.items()},d.funding.iloc[:1100],d.symbols)
        full,names,_=feature_panel(d); part,_,_=feature_panel(prefix)
        np.testing.assert_allclose(full[:1100],part,equal_nan=True)
        d.frames['quote_volume'].iloc[700:1100]=0
        broken,_,_=feature_panel(d)
        self.assertFalse(np.isinf(broken).any())
        self.assertTrue(np.isnan(broken[1000,:,names.index('volume_surge')]).all())

    @unittest.skipUnless(find_spec('sklearn') and find_spec('threadpoolctl'),
                         'install requirements-v16-research.txt for model training tests')
    def test_fitted_models_cannot_change_predictions_before_future_mutation(self):
        d=sample(24*140,20); cutoff=24*130
        changed=FuturesData({k:v.copy() for k,v in d.frames.items()},d.funding.copy(),d.symbols)
        for frame in changed.frames.values(): frame.iloc[cutoff:]*=5
        changed.funding.iloc[cutoff:]+=.2
        for model in ('ridge','boosting'):
            spec=ForecastSpec(model=model,horizon_hours=12,decision_every_hours=12)
            a,folds=walkforward_forecasts(d,spec)
            b,_=walkforward_forecasts(changed,spec)
            self.assertGreater(len(folds),0)
            self.assertGreater(a.notna().sum().sum(),100)
            pd.testing.assert_frame_equal(a.iloc[:cutoff],b.iloc[:cutoff],atol=1e-11,rtol=1e-11)
            for f in folds:
                self.assertLess(pd.Timestamp(f['last_training_label_matured_at']),pd.Timestamp(f['fit_at']))

    def test_forecast_targets_are_causal_and_bounded(self):
        d=sample(1400,8); rng=np.random.default_rng(16)
        f=pd.DataFrame(rng.normal(0,.015,d.close.shape),index=d.close.index,columns=d.symbols)
        old=forecasts_to_targets(d,f,ForecastSpec())
        f.iloc[1100:]*=-100
        new=forecasts_to_targets(d,f,ForecastSpec())
        pd.testing.assert_frame_equal(old.iloc[:1100],new.iloc[:1100])
        self.assertLessEqual(old.abs().sum(axis=1).max(),1.6+1e-12)
        self.assertLessEqual(old.abs().max().max(),.2+1e-12)


class RelativeTests(unittest.TestCase):
    def test_rebalance_requires_incremental_forecast_to_cover_costs(self):
        spec=RelativeSpec(trading_cost_hurdle=2)
        # A profitable existing portfolio does not justify a useless adjustment.
        self.assertFalse(worthwhile_rebalance([.2,-.2],[.2,-.2],[.2,-.2],spec))
        self.assertFalse(worthwhile_rebalance([.1,-.1],[.2,-.2],[.001,-.001],spec))
        self.assertTrue(worthwhile_rebalance([.1,-.1],[.2,-.2],[.02,-.02],spec))

    def test_neutral_sizing_preserves_constraint_after_cap(self):
        long=np.array([1.,4.,0,0]); short=np.array([0.,0.,3.,1.]); beta=np.array([1.,2.,.5,1.])
        for mode in ('beta','dollar'):
            spec=RelativeSpec(balance=mode)
            weight=balance_sides(long,short,beta,spec)
            self.assertAlmostEqual(float(weight@beta if mode=='beta' else weight.sum()),0)
            self.assertLessEqual(abs(weight).max(),.2+1e-12)
            self.assertLessEqual(abs(weight).sum(),1.6+1e-12)
        np.testing.assert_array_equal(balance_sides(long,short*0,beta,spec),np.zeros(4))

    def test_relative_book_causal_and_invalid_leg_closes_both_sides(self):
        d=sample(1600,10)
        names=('BTCUSDT',*d.symbols[1:])
        frames={k:v.set_axis(names,axis=1) for k,v in d.frames.items()}
        # Correlated series permit positive, estimable BTC betas.
        for key in ('open','high','low','close'):
            frames[key]=frames[key].mul(frames[key].BTCUSDT,axis=0)
        d=FuturesData(frames,d.funding.set_axis(names,axis=1),names)
        pred=pd.DataFrame(np.tile(np.linspace(-.03,.03,10),(1600,1)),index=d.close.index,columns=names)
        spec=RelativeSpec(balance='dollar')
        a,_=relative_targets(d,pred,spec)
        self.assertGreater(a.abs().sum().sum(),0)
        self.assertLess(a.sum(axis=1).abs().max(),1e-10)
        cut=1301
        held=np.flatnonzero(a.iloc[cut-1].abs().gt(1e-12))
        self.assertGreater(len(held),0)
        for frame in d.frames.values(): frame.iloc[cut,held[0]]=np.nan
        b,_=relative_targets(d,pred,spec)
        pd.testing.assert_frame_equal(a.iloc[:cut],b.iloc[:cut])
        self.assertEqual(b.iloc[cut].abs().sum(),0)

    def test_cost_gate_cannot_rewrite_past_with_future_forecasts(self):
        d=sample(1600,10); names=('BTCUSDT',*d.symbols[1:])
        frames={k:v.set_axis(names,axis=1) for k,v in d.frames.items()}
        for k in ('open','high','low','close'): frames[k]=frames[k].mul(frames[k].BTCUSDT,axis=0)
        d=FuturesData(frames,d.funding.set_axis(names,axis=1),names)
        f=pd.DataFrame(np.tile(np.linspace(-.03,.03,10),(1600,1)),index=d.close.index,columns=names)
        spec=RelativeSpec(trading_cost_hurdle=2,retain_rank_buffer=True)
        original,diag=relative_targets(d,f,spec)
        self.assertGreater(diag.cost_gate_skipped.sum(),0)
        f.iloc[1300:]*=-100
        changed,_=relative_targets(d,f,spec)
        pd.testing.assert_frame_equal(original.iloc[:1300],changed.iloc[:1300])


if __name__=='__main__': unittest.main()
