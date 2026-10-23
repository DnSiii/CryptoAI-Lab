#!/usr/bin/env python3
"""V98 AE stateful prior-actual-NAV convex stress; targets only for next open."""
from __future__ import annotations
import numpy as np

DRAWDOWN_TRIGGER = -.12
MARKET_LOG_TRIGGER = -.03
RECOVERY_DRAWDOWN = -.05
RECOVERY_HOURS = 48
HEDGE_GROSS = .24
ASSETS = 4


class AEStressMachine:
    def __init__(self):
        self.peak = None
        self.active = False
        self.recovery_hours = 0
        self.completed_hours = 0

    def step(self, completed_nav, completed_market_log_return):
        nav = float(completed_nav)
        market = float(completed_market_log_return)
        if not np.isfinite(nav) or nav <= 0 or not np.isfinite(market):
            raise ValueError('AE1206_NONFINITE_OR_INSOLVENT_NAV')
        if self.peak is None:
            self.peak = nav
        self.peak = max(self.peak, nav)
        dd = nav / self.peak - 1.
        shock = dd <= DRAWDOWN_TRIGGER or market <= MARKET_LOG_TRIGGER
        if shock:
            self.active = True
            self.recovery_hours = 0
        elif self.active:
            if dd > RECOVERY_DRAWDOWN and market >= 0:
                self.recovery_hours += 1
                if self.recovery_hours >= RECOVERY_HOURS:
                    self.active = False
                    self.recovery_hours = 0
            else:
                self.recovery_hours = 0
        self.completed_hours += 1
        # Caller may submit this target at t+1 open, never retroactively at t.
        return np.full(ASSETS, -HEDGE_GROSS / ASSETS if self.active else 0.,
                       dtype=np.float64)

    def diagnostic(self):
        return {'phase':1206, 'active':self.active,
                'recovery_hours':self.recovery_hours,
                'completed_hours':self.completed_hours,
                'actual_nav_required':True,
                'historical_system_pnl_computed':False,
                'validation_2025_read':False,
                'external_benchmarks_used':False}
