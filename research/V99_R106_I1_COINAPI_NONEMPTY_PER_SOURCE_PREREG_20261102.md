# V99 I1 CoinAPI derived-day nonempty-per-source invariant — preregistration (2026-11-02)

**Scope:** Software provenance integrity only. Does not change trading strategy, signals, economic gates, historical data, paper, Frozen, validation or holdout.

**Observed defect (before implementation):** The derived-only daily converter accepts a source descriptor for BTC and ETH even when one gzip contains only the valid CSV header. The combined daily file is nonempty, so the independent byte oracle can replay and accept a day that contains no observations for one advertised source. A fake two-asset day must not be published.

**Fixed ex-ante rule:** Every independently hashed, declared original per-symbol gzip must contain >=1 actual original quote row. A header-only or otherwise empty gzip is rejected *before any derived day or sidecar is published*. This is a necessary transport condition, not evidence of liquidity, fills, market completeness, licensed provenance or economic viability. Zero-sided and crossed rows are still retained as non-executable source observations.

**Independent verification:** The separate oracle must enforce the same >=1 per-source invariant from the original gzips, independently of the production report, and reject an already-published legacy derived day if a source was empty. Tests must cover BTC-empty, ETH-empty, and nonempty zero-size rows; failed conversion leaves the output directory empty. Preserve exact original hashes and conservative 100ns clock handling.

**Acceptance:** GitHub CI executes the synthetic/adversarial tests. Even if green: SOURCE HOLD, 0 original economic lifecycles certified, NO TRAIN/ROI/PROMOTION/ORDERS. No changes to sealed validation >=2023-10-01, final holdout >=2024-01-18, V16/V99 Frozen, legacy champion or paper.
