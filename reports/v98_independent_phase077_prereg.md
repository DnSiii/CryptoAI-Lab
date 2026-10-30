# V98 Independent Phase077 — pre-registration

## Hypothesis
Cross-sectional **return-sign entropy** may identify structurally persistent versus directionally noisy assets without using return magnitude, funding, validation feedback, or Phase075 diagnostics. Over a lagged 28-day hourly window, estimate the fraction of positive hourly returns p and binary sign entropy H = -p ln(p) - (1-p) ln(1-p). Lower H means more persistent directional structure; higher H means noisier sign switching. Hypothesis: long the lowest-entropy asset and short the highest-entropy asset.

## Frozen specification before any Phase077 PnL
- V98 Independent namespace only.
- Universe: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT.
- Training only through 2025-12-31; validation and final holdout closed.
- Lookback: 672 hours (28 days), fixed ex ante.
- Information: hourly log-return signs through t-1 only.
- p = rolling fraction(return > 0); H = -p ln(p) - (1-p) ln(1-p), with numerical clipping only at 1e-12 for log safety.
- Direction: long minimum H, short maximum H.
- Rebalance: 00:00 UTC daily; hold to next rebalance.
- Gross 0.75, 0.375 long / 0.375 short.
- Existing V98 exact cost/funding engine; BASE, severe, supersevere unchanged.
- No parameter search, threshold sweep, direction flip, validation feedback, or rescue.

## Mandatory training diagnostics / frozen gate
Report aggregate plus chronological 2023/2024/2025 folds: return, max drawdown, daily Profit Factor, payoff, win rate, positive days; BASE/severe/supersevere; regimes; concentration/tails; asset contribution; activation; reproducibility hashes.

PASS requires aggregate return > 0, PF > 1.05, max drawdown >= -35%, every fold return > 0 and PF > 1.00, severe return > 0, supersevere return > 0, and no ruin. Any failure => REJECT_NO_RESCUE. Only full PASS can open separately frozen validation. Final holdout remains untouched.

## Independence declaration
Phase077 was specified only after Phase075/076 had been permanently rejected, but its construction does not use their validation losses, regimes, asset contributions, or any V99/V16 evidence. It is a magnitude-free sign-distribution hypothesis and is not a rescue of downside asymmetry.