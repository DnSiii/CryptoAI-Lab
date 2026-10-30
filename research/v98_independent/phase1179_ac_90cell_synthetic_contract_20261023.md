# V98 Independent Phase1179 — AC 90-cell synthetic integration preregistration

Date 2026-10-23, before any integrated AC synthetic result or official historical system PnL. AC source has independently passed and frozen 15/15 hashes (Phase1178); economic code is not frozen.

## Fixed fixture and procedure
- Use the deterministic **1,300-hour** synthetic Clean-4 fixture in `test_phase1174_ac_discrete_intents.sample`. Simulate exactly **96 hourly transitions t=900..995 inclusive**, including the preregistered t=930 volume/close-location impulse and subsequent open/close discontinuity. No official OHLC price history or future validation.
- Five source paths (AC_core_only, AC_full, AC_minus_opportunity, AC_minus_relative_value, AC_minus_stress), three starting cash modes ($10k/$1m/$10m), three fees (base .0007/severe .0012/supersevere .002), two native funding timing orders (carried-before-fill/new-after-fill) = exactly 90 cells.
- At hour t, use **source intent[t-1]**, previous completed close, quote and trailing 336h minimum quote. Covariance from previous 336 completed 1h log returns, scaled by 24h plus 1e-8 PSD ridge. Precommitted risk envelope down=.25, up=.30 per asset and adverse funding bound=.001. Rebalance every 12 hours; all other hours carry actual units unless the governor fails closed.
- Synthetic native funding event every eighth hour t%8==0 for each asset, alternating signed rate +/-0.0001 by hour and asset, with mark bounds [0.99*close[t],1.01*close[t]]. Actual fill at open[t] with 0.002 slippage. No PnL outside this synthetic fixture.
- Require **90/90** independent executable self-financing survival and no negative/nonfinite NAV. Report all 90 decisions, turnover, fees, funding, gap events and final synthetic NAV for diagnostic purposes **only**. No synthetic CAGR is promoted to historical CAGR.
- A failed cell is a preregistered AC integration gate failure; do not alter thresholds, dates, fixture, fees, sign, leverage, or code to rescue. Any accounting bug must be separately classified and fixed only under a new, prospective preregistration if the candidate remains eligible under the protocol.

## Next
If the gate passes, freeze full executable code and run official chronological 2023/2024 economic training. If it fails, reject AC and preregister a genuinely distinct complete engine.
