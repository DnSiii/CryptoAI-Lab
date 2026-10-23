# V98 Independent Phase1192 — AD covariance-neutral dispersion sleeve preregistration (2026-10-23)

This is AD's **Relative-Value Sleeve**, distinct from rejected AC's 72h rank reversal and AB's beta/cointegration spread. It is evaluated **only as marginal log-wealth contribution to frozen AD_full**, not as a standalone return champion. No historical AD system PnL, 2025+, XRP or external benchmarks.

## Fixed economic hypothesis and causal estimator
Extreme **one-hour** cross-sectional price innovation after a sudden dispersion shock is partially transient. At completed t, calculate four Clean-4 hourly log returns and subtract their equal-weight mean; trade **against** the contemporaneous residual innovation for a bounded eight-hour unwind. Do not flip signs after outcomes.

- Previous 168 completed hourly log-return vectors (strictly through t-1) estimate 4x4 covariance with population normalization. Shrink covariance to **70% sample + 30% diagonal**, add diagonal ridge 1e-8.
- Define BTC beta vector b_j = covariance[j,BTC]/covariance[BTC,BTC]. Enforce both sum_j w_j=0 and b^T w=0 by the **covariance-metric projection** of negative one-hour demeaned innovation: raw = Sigma^-1 [s - A(A^T Sigma^-1 A)^+ A^T Sigma^-1 s], A=[ones,b]. Normalize to sum(abs(w))=1. If singular/nonfinite, fail closed; if near-zero projected vector, stay flat.
- Dispersion gate: current cross-sectional population variance of one-hour demeaned log returns must exceed **2x median** of prior 168 cross-sectional variances, with floor 1e-8. Current t observation is allowed only for a decision executable at t+1.
- Start only at t>=336; signal active t..t+7 inclusive, then flat. Minimum 24 hours between triggers. No future smoothing, no AC 72h relative ranks, no funding carry, no post-result sign/window/threshold/gross rescue.
- Output dimensionless four-asset signed sleeve weights, not executable positions. Actual portfolio NAV, funding, capacity, fees, 81 corners and liquidation handled by AD allocator/governor only after complete seven-slot freeze.
- Synthetic tests must prove signed dollar neutrality, estimated BTC-beta neutrality, gross normalization, chronology, no lookahead, expiry/cooldown, no 2025, and no PnL. Dual-OS tests before vendor-authenticated source composition.
