# V98 Independent Phase202 — independent audit

Decision: **REJECT_FAMILY_NO_RESCUE**.

Evidence harvested from the preregistered 8-spec range-position reversal family. No spec passed. The representative w24_q05_h3 is catastrophically negative in every chronological fold: 2023 return -96.19%, PF 0.541; 2024 -97.59%, PF 0.663; 2025 -97.96%, PF 0.642. Full-period base PF is 0.686 with ~-100% return/MDD; severe PF 0.533 and supersevere PF 0.400. Bear/bull/sideways PFs are all <1 under base costs, so the failure is not isolated to one regime. Positive-day fraction is only 30.7% base and deteriorates to 19.6% severe / 10.9% supersevere.

Concentration/tails do not rescue the mechanism: max symbol absolute loss share is ~28.4%, all five symbols lose money, and top/bottom tail shares are small relative to the persistent broad loss. The mechanism is therefore broadly negative rather than a single-symbol or rare-tail accident. High turnover (~11,058 notional units in the representative spec) makes cost stress worse, but base-cost PF is already decisively below 1.

Integrity/reproducibility audit: training-only canonical data ends 2025-12-31; temporal firewall passed for all five assets; deterministic run hashes were byte-identical (b038b00c1e7f9401228420166abfac1ecd02a374c8d1244e0287d1f629d3d3d9). Validation/final holdout remain untouched. No rescue, inversion, threshold expansion, or post-hoc parameter search is permitted.

Scientific interpretation: simple reversal from trailing-range extremes has no robust edge in this universe under realistic implementation. Phase202 is closed as negative evidence.