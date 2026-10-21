# V98 Independent Phase865 — Preregistered K composed growth architecture

Time: 2026-10-21 19:45 BRT. Scope: research/v98-independent-zero; only V98 Independent files. No external benchmark reads, XRP, 2025+ data, Phase083 holdout, or historical PnL.

K is a distinct seven-slot **trend persistence / breakout / relative-strength / post-stress reacceleration** architecture, not a sign/window/threshold rescue of frozen J. North star: maximize long-run compounded net wealth under hard survival/causality constraints. Hypothesis: persistent exposure with causal low-turnover allocation can improve net compounding after realistic fees and liquidity costs. No economic performance of K has been observed before this preregistration.

Fixed slots:
1. Growth Core: positive 168h log momentum scaled by trailing 72h realized volatility.
2. Opportunity: close breaks the prior 48h high, with positive core momentum, event remains active up to 24h.
3. Relative Value: positive 72h log return residual vs equal-weight Clean-4 market.
4. Stress/Recovery: after a >=8% market drawdown in the past 168h, activate only when closed-bar 24h market return >0 and positive-breadth improves.
5. Regime Router: positive-trend breadth and trailing 72h market vol vs 336h historical 75th percentile. Risk-on: breadth>=3 and volatility below threshold; neutral: breadth>=2; otherwise risk-off.
6. Dynamic Allocator: fixed sleeve shares core .55/opportunity .20/relative .15/recovery .10, renormalize only among active sleeves. Gross targets 1.50 risk-on, 1.00 neutral, .35 risk-off; rebalance on weekly UTC Monday 00:00 or L1 desired-vs-last target drift > .15. Inactive sleeves contribute zero. No optimization grid.
7. Risk Governor: long-only; per-asset cap .70, gross cap 1.75; no hidden leverage; fee-inclusive NAV; 5% of prior fully closed 1h quote-volume capacity, sell-first; t-1 execution; reject overnight/intrabar breaches without risk waiver.

The four paths K_full, K_minus_opportunity, K_minus_relative_value, K_minus_recovery and a fixed internal baseline must be frozen before any economic evaluation. No parameter retuning, post-result rescue, cherry-picking, or accessing external engines. Economic matrix 5 paths x 3 fixed fee tiers (7/12/20 bps) x 2 funding settlement conventions x (immediate + USD1m and USD10m capacity) = 90 cases, with both 2023 and 2024 chronological folds. Require fresh same-run authenticated official OHLC+native funding+conservative mark source receipts before PnL. Preserve drawdown, tails, concentration, PF, payoff, win rate, positive days, log wealth/CAGR, fees/funding and all failures. The 2025 future validation remains untouched until K training gates pass and K is frozen. J is not modified or rescued.

Source-only structural tests can freeze K's code and target hashes but cannot promote it economically. Reject permanently if gates fail.
