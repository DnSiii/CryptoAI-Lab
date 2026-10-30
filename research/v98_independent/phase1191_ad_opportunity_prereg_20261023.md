# V98 Independent Phase1191 — AD funding-event opportunity sleeve preregistration (2026-10-23)

**Status:** AD is the distinct Phase1186 seven-slot portfolio. This is the **Opportunity Sleeve only**, not a standalone alpha promotion and not a rescue of any AC/AB/Y/Z rejection. No AD system PnL, no 2025, no external benchmarks, no XRP.

## Economic hypothesis fixed before testing
A native USD-M funding settlement with **abnormally positive** funding relative to the asset's own prior 90 settlement observations, accompanied by **positive** asset-specific 24h price divergence versus equal-weight Clean-4, signals overcrowded long exposure; short the asset for a bounded post-event unwind. Mirror case: abnormally negative funding surprise **and** negative relative price divergence signals overcrowded short exposure; long for the unwind. Do not flip the sign if historical PnL disappoints. This is conditional post-settlement crowding dislocation, **not** unconditional funding carry.

## Deterministic causal rules
- For each asset at settlement t, baseline mean/std uses the **previous 90 native funding events**, excluding t. std floor 0.00005 (absolute funding fraction); z=(rate_t - prior_mean)/max(prior_std, floor).
- Asset divergence at completed t = log(close_t/close_{t-24}) - mean over Clean-4 of the same 24h log return. Trigger only if |z| >=2, |divergence| >=0.015, and z*divergence>0. Direction is **-sign(z)**. No signal at non-settlement hours, even when price divergence alone is large.
- Trigger at completed t, intent may first execute at **t+1 open**; hold the signed opportunity intent for **16 completed hours** (t..t+15), then flat. Minimum **48 hours** between triggers for the same asset. No future lookahead and no instant settlement fill.
- Opportunity intent is dimensionless -1/0/+1. Actual capital, fees, 81-corner governor, funding, exit capacity and marginal log-wealth allocation are deferred to the **full AD composed engine**. A sleeve may survive standalone weakness only if preregistered positive marginal contribution to frozen AD_full is demonstrated.
- Warmup >=720h from 2022-12-01; 2023/2024 separate chronological training only. Exactly Clean-4 native funding event mask. Invalid clock, missing event history, NaNs, 2025+ or invalid OHLC fail closed.
- Synthetic tests must check event causality, sign, 90-event lookback excluding current, 16h expiry, 48h cooldown, no overlap, no future leakage, funding clock and no historical PnL. Two independent OS runners before fresh official source hash work.
