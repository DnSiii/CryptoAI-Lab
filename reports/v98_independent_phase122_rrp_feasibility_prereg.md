# V98 Independent Phase122 — ON RRP DATA_ONLY preregistration

Status: PREREGISTERED / NO ALPHA / NO PNL.

## Scientific family
Federal Reserve overnight reverse-repurchase usage (ON RRP), a money-market liquidity/drain observable distinct from WALCL level, DXY, stablecoin supply, crypto positioning, DeFi/on-chain, sentiment, and prior internal price/derivatives families.

## Frozen source and series
Source: FRED only. Series: `RRPONTSYD` (Overnight Reverse Repurchase Agreements: Treasury Securities Sold by the Federal Reserve in the Temporary Open Market Operations, daily). Frozen research window: 2023-01-01 through 2025-12-31 only.

## DATA_ONLY gate
The feasibility step may inspect only transport/schema/date/value validity and coverage metadata. It MUST NOT print/store individual values, distributional summaries, changes, correlations, returns, direction, thresholds, regimes, alpha, positions or PnL.

PASS requires: source request succeeds reproducibly; schema contains date/value; all retained dates are unique after canonicalization; no retained non-numeric/non-finite values; no retained observations outside the frozen window; observed business-day coverage >= 95% against the US business-day calendar in the frozen window. Missing weekends/holidays are not imputed. No interpolation, forward/back fill, source substitution or series substitution is permitted.

A deterministic SHA-256 over canonical `date,value` rows is allowed as integrity metadata. Row count, min/max date, duplicate/invalid/out-of-window counts and coverage percentage are allowed because they are data-integrity metadata, not economic descriptives.

## Decision rule
Any failed frozen gate => `REJECT_DATA_SOURCE_NO_RESCUE` for this exact family/source/series. PASS_DATA_ONLY authorizes only a later, separately committed economic preregistration. No direction/window/lag/gross/threshold/regime may be chosen from Phase122 values.

## Isolation
Validation and final holdout remain closed. Phase083 is permanently ineligible. V16/V99 evidence, state, workflows and reports are forbidden for selection/tuning. No V99 paper state may be read or modified.
