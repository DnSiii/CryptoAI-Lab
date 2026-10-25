# V98 Independent DP — frozen historical training rejection (2026-10-25)

**Decision: REJECT_DP_HISTORICAL_GROWTH_OR_MARGINAL.** No promotion or threshold/sign/gross rescue. Frozen run [40186440175](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40186440175), source commit `1e2879e6121425b34deb2696897c3276efa21ca0`. DP source/preregistration untouched after the official economic result.

- Pinned authenticated Clean-4 Dec-2022–Dec-2024, 1440h warmup, next actual open, signed native funding, two funding orderings and three friction levels. 2025 future holdout never opened.
- Source-only activity passed 2023 and 2024: core 48/53, Opportunity 8/7, Relative Value 31/37, Stress/Recovery 4/7.
- **30/30 physical cells survived**, Ubuntu 22.04 vs 24.04 numeric reproduction passed; independent receipt audit `errors=[]`.
- Full USD10k, carried-before-fill base: two-year CAGR **+51.8766%**, 2023 net **+47.7611%**, 2024 net **+56.1960%**, max DD **28.1009%**, native funding **-USD 1,911.30**.
- Severe: two-year CAGR **+50.0559%**, 2023 **+46.0242%**, 2024 **+54.2847%**, max DD **28.1519%**, native funding **-USD 1,867.96**.
- Annual growth, CAGR and severe drawdown gates passed. **All three satellite modules failed** positive marginal annual net log-growth requirements across base/severe and both funding orderings. Therefore complete DP engine is rejected despite passing aggregate growth thresholds.
- These are **training-only historical results**, not an approved candidate, validation or live forecast. V14/V15/V99 benchmarks unopened; V16/V99 Frozen, V99 paper and 2025 holdout untouched.

Next: analyze frozen capital displacement and each sleeve's signed contribution from independent receipts; pursue a genuinely different *system-level* capital allocation hypothesis, not DP post-result rescue.
