# V98 Independent Phase113 — Fear & Greed data feasibility

PRE-REGISTRATION created after Phase112 was permanently rejected and before Phase113 values, descriptives, alpha or PnL are inspected.

Purpose: test only whether a genuinely external daily sentiment series is technically suitable for a later, separately preregistered V98 hypothesis. This phase is DATA_ONLY and cannot promote a trading candidate.

Frozen source: Alternative.me public Crypto Fear & Greed Index API (`https://api.alternative.me/fng/?limit=0&format=json`). This is independent of V99/V16 and distinct from the Phase111/112 stablecoin-peg family.

Frozen window: 2023-01-01 through 2025-12-31 only. Validation, Phase083/opened holdout, and reserved 2026-09-16→2026-10-15 forward holdout are forbidden.

Data-only checks:
1. HTTP 200 and JSON object with `data` list;
2. each usable record has timestamp and integer value in [0,100];
3. canonicalize timestamp to UTC date, sort ascending, keep last observation per UTC day;
4. >=95% coverage of the 1,096 calendar days;
5. first usable date <= 2023-01-07 and last >= 2025-12-24;
6. no duplicate UTC dates after canonicalization;
7. record source payload SHA256 for reproducibility.

Anti-leakage: report coverage/schema/integrity only. Do not expose value distribution, mean, quantiles, classifications, correlations, returns, alpha or PnL. Do not choose thresholds, sign, smoothing, duration, lag or trading rule in Phase113.

PASS_DATA_ONLY authorizes only a new conditional preregistration written before any sentiment descriptives or PnL are inspected. FAIL_DATA_NO_ALPHA rejects this source without rescue in this phase.
