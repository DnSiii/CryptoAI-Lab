#!/usr/bin/env python3
"""V98 AF actual-NAV prefunded cash stress sleeve, next-open targets only."""
from __future__ import annotations
import numpy as np

STRESS_DRAWDOWN=-.15
STRESS_MARKET_LOG=-.05
RECOVERY_DRAWDOWN=-.08
RECOVERY_HOURS=24
NORMAL_CASH=.10
STRESS_CASH=.55


class AFCashStress:
    def __init__(self):
        self.peak=None
        self.stress=False
        self.recovery=0
        self.completed_hours=0

    def step(self,completed_nav,completed_market_log_return):
        nav=float(completed_nav)
        market=float(completed_market_log_return)
        if not np.isfinite(nav) or nav<=0 or not np.isfinite(market):
            raise ValueError('AF1217_NONFINITE_OR_INSOLVENT_NAV')
        if self.peak is None:
            self.peak=nav
        self.peak=max(self.peak,nav)
        dd=nav/self.peak-1
        if dd<=STRESS_DRAWDOWN or market<=STRESS_MARKET_LOG:
            self.stress=True
            self.recovery=0
        elif self.stress:
            if dd>RECOVERY_DRAWDOWN and market>=0:
                self.recovery+=1
                if self.recovery>=RECOVERY_HOURS:
                    self.stress=False
                    self.recovery=0
            else:
                self.recovery=0
        self.completed_hours+=1
        return STRESS_CASH if self.stress else NORMAL_CASH

    def diagnostic(self):
        return {'phase':1217,'actual_nav_required':True,
                'completed_hours':self.completed_hours,
                'stress':self.stress,'recovery_hours':self.recovery,
                'historical_system_pnl_computed':False,
                'validation_2025_read':False,
                'external_benchmarks_used':False}
