# V98 Independent — Phase227 postmortem

Decision: **REJECT_FAMILY_NO_RESCUE**.

Evidence source: deterministic Phase227 payload SHA256 `794e8ecd820487c4adca38a640dc86cf14bee14874f6daf33eb3015299e72675`; untouched holdout remains `<2026-01-01` only.

## Independent failure audit

The preregistered cross-sectional idiosyncratic residual reversal family produced zero survivors across the frozen 8-spec grid. This is not a near-miss suitable for rescue.

Representative preregistered spec `w24_q0.010_h4`, 2023 base: return -48.8431%, PF 0.96885, payoff 0.99576, win rate 47.2603%, positive days 51.5068%, max DD -60.2168%, 3,613 trades. Severe cost: return -79.7681%, PF 0.91480, DD -81.6387%. Supersevere: return -96.8404%, PF 0.81799, DD -97.0128%.

Regime decomposition for that 2023 base slice shows the weakness is not a single-regime artifact: bear was +6.74% / PF 1.036, but bull was -12.37% / PF 0.989 and sideways -45.31% / PF 0.928. Under severe and supersevere costs all three regimes become negative.

Concentration/tails are also unacceptable as a rescue argument: max asset concentration is 61.36% in the representative 2023 base slice, SOL contributes -46.67 percentage points, median trade is slightly negative, p01 is -2.92%, and worst trade -17.62%. 2024 base deteriorates further to -86.59%, PF 0.9076 and DD -87.42%, with negative bear/bull/sideways returns.

## Scientific decision

No parameter narrowing, asset exclusion, regime filtering, tail clipping, or cost relaxation is permitted after observing these results. Phase227 is closed as a failed family. Champion is unchanged. V16 Frozen, V99 Frozen/research/workflows/reports/paper state and the 2026+ holdout are untouched.

Next work must be a genuinely orthogonal preregistered hypothesis rather than a rescue of residual reversal/persistence.