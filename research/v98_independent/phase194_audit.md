# V98 Independent — Phase194 independent audit

Decision: **REJECT_FAMILY_NO_RESCUE**.

The harvested training-only report declares `final_holdout: null`, grid size 8, no winner, and family rejection. The inspected specification `v2_m075_h3` is economically negative in aggregate (total return -32.75%, CAGR -12.39%, daily PF 0.627, MDD -40.12%) and is negative in every chronological fold: 2023 -11.81% / PF 0.646, 2024 -12.16% / PF 0.682, 2025 -13.18% / PF 0.528. Its failures include base edge/drawdown, fold inconsistency, severe and supersevere edge/drawdown, and tails.

Mechanism audit: bull regime contribution is materially negative while bear and sideways contributions are only small positives for the inspected spec. Bottom-10 negative contribution share is ~40.3% and top-10 positive share ~59.8%; therefore the failure cannot reasonably be rescued by deleting a single adverse tail. Mean/p95 top-1 share is 0.5, reflecting the two-leg construction rather than diversified breadth. Activity is sparse (564 active hours, 178 episodes over 1095 days), while turnover remains meaningful, making cost robustness especially important.

Scientific conclusion: abnormal-volume reversal has no robust training evidence worth further parameter rescue. Do not invert the failed signal, cherry-pick years, loosen costs, or alter gates. Phase195 is preregistered as a distinct liquidity-adjusted trend-persistence hypothesis instead.

Isolation: this audit uses only V98 Independent Phase194 evidence on `research/v98-independent-zero`; validation/final holdout and V16/V99 state remain outside the decision process.
