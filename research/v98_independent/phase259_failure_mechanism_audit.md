# V98 Independent Phase259 — failure-mechanism audit

Status: **POST-RESULT AUDIT / REJECTED FAMILY REMAINS CLOSED**.

This audit does not change the Phase259 decision, parameters or gates.

## What improved

Relative to frozen Phase252:

- BASE terminal return: +550.57% -> +626.52% (+75.96 percentage points).
- CAGR: 86.66% -> 93.65%.
- SEVERE: +493.66% -> +551.70%.
- SUPERSEVERE: +408.80% -> +442.77%.
- 2023 marginal return: +46.53pp.
- 2024 marginal return: +21.95pp.
- asset concentration remained acceptable (largest absolute contribution share 38.86%).
- top-10 absolute-day concentration remained low (5.41%).
- no ruin.

## What failed

- daily PF fell from 1.2169 to 1.2084;
- max DD worsened from -52.64% to -60.23% (7.59pp deeper);
- 2025 fell from -8.36% to -18.72% (10.37pp marginal loss), just beyond the frozen -10pp tolerance;
- the sleeve was active on 874 decisions / 79.74% of training hours.

Regime attribution also shows broad amplification rather than sufficiently selective alpha:
- Phase259 bear classified-hour return: +193.84%;
- bull: +368.32%;
- sideways: -47.31%.

For comparison, the frozen Phase252 diagnostic previously recorded approximately:
- bear +156.31%;
- bull +305.68%;
- sideways -37.56%.

Thus the exact hashrate-expansion rule amplified favorable regimes, but also amplified the structurally weak sideways state and deepened the 2025 path.

## Scientific interpretation

The gain is not dismissed: the Phase258 hashrate source is a valid new information class and the Phase259 rule materially increased wealth under BASE/SEVERE/SUPERSEVERE costs.

However, the 79.7% activation rate means the exact 30d-vs-prior30d / +0.25 gross construction behaves too much like persistent extra beta. The rejected result does **not** authorize:
- reducing +0.25 to a smaller sleeve;
- changing 30d windows;
- adding a 2025-specific or sideways filter;
- changing the sign;
- combining a rejected governor/router to rescue it.

Any future network-security work must have a materially different causal economic mechanism, not a tuned version of Phase259.

Phase252 remains the frozen partial architecture and current leader.
