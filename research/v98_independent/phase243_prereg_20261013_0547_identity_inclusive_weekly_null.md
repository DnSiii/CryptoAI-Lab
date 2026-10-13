# V98 Independent Phase243 — identity-inclusive weekly rotation null (independent falsification preregistration)

Date 2026-10-13 05:47 America/Sao_Paulo. Branch `research/v98-independent-zero`; only V98 Phase206 canonical training funding 2023-01-01..2025-12-31 UTC and existing sparse event replay. **No V16, V99, holdout, trades, PnL, parameter selection or promotion.**

## Why test
The frozen weekly-regime null draws offsets from 1..D-1 for each non-BTC asset in each D-day block, excluding the identity rotation (0 days). The full cyclic rotation group has D elements, including identity. Omitting identity can make a purported uniform phase-randomization null anti-conservative or otherwise distort the distribution, especially for short blocks. This is a distinct **null-calibration/inference audit** prompted by code inspection, not a new alpha hypothesis. The original preregistered weekly result (primary p=0.0689862) must remain frozen and the failed primary gate cannot be overturned post hoc.

## Frozen independent test
Use the existing V98 five-asset sparse event masks at |funding|>=7bp, with the exact original 158 ISO-Monday week blocks and 3 native 8h slots per UTC day. Hold BTC fixed; independently rotate each of the other four assets by a *uniform random integer offset from 0 through D-1 days*, including identity. D=1 => 0. Preserve each asset-week tail count, intraweek pattern, 8h clock and chronological boundaries. No interpolation, funding adjustment, calendar tuning, cross-year spill or access to holdout.

Run 20,000 deterministic Monte Carlo replicates with Python random.Random(202610130547), compute observed >=2 and >=3 co-tail slot counts, null means, p95, max, exceedances, empirical one-sided p=(1+k)/(N+1), and Wilson 95% interval for the exceedance probability. Compare to the *already frozen* nonzero-offset weekly null (5,000 draws p=0.0689862; 10,000-draw repeats ~0.067–0.069). Report shift-induced differences as sensitivity, not as a new significance test or confirmatory finding. Additional 2,000-rep reference-versus-fast draw-for-draw equivalence, seeded 202610130548. All masks must be V98-only, source identity frozen, no new data.

## Interpretation
If primary remains p>=0.05: week-conditioned co-tail association remains unsupported. If p<0.05: report instability in randomization specification; **do not rescue** the previously failed confirmatory primary or promote a strategy. Secondary >=3 is descriptive, not a substitute primary. Explicitly discuss exchange-source uncertainty (BNB zero funding, SOL variable settlement, XRP impossible 1h VWAP) and the null's inability to preserve contemporaneous macro shocks.

Keep Phase240 REJECTED, Phase243 BLOCKED_SOURCE, champion NONE. Require independently authenticated original sources, chronological folds, untouched holdout, realistic funding and 7/14/28 bp costs, severe/supersevere, regimes, concentration/tails, MDD, PF, payoff, win rate, positive days and reproducibility before any promotion.
