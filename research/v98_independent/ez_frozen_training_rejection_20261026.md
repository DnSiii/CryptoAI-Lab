# V98 Independent EZ — immutable training rejection (2026-10-26)

Preregistered before economic PnL in commit `d799c06f2a3523c4251fec24f888c24485bba7e3`. Only authenticated Clean-4 2023–2024 training; 2025 holdout, 2026+, XRP, Phase083, V14/V15/V99, Frozen and paper excluded.

- Causal source-only future-mutation and four-sleeve activation gates PASS. Source job in https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40272473861.
- 30/30 physically settled USD10k cells PASS, numerical reproduction across ubuntu-22.04/24.04 PASS, artifact-only audit errors [], all four annual full-growth gates PASS.
- Independent five-book all-hour signed settlement oracles PASS. Each checks 105,258 settled hours and 13,152 funding hours (five books total 526,290 and 65,760).
- Full base 2023–2024 CAGR **84.928900%**, severe **78.095899%**. Base 2023 net return **173.757174%**, 2024 **25.028659%**; severe 2023 **163.355005%**, 2024 **20.533950%**. Base max drawdown **35.207832%**, severe **36.003118%**. Funding PnL base **-USD2,178.73**, severe **-USD2,052.65** (signed native receipt).
- Locked annual positive marginal log-growth gates **FAIL** for Opportunity, Relative Value and Stress/Recovery under base/severe and both funding orderings. `REJECT_EZ_HISTORICAL_GROWTH_OR_MARGINAL` is the definitive audit result. A passing CI run is **not** economic acceptance.
- The EZ workflow copied two non-economic metadata labels from EW: its push path includes `v98-independent-ew-seven-slot.yml` instead of EZ, and independent ledger artifact names start with `ew-`. They do not change numerical results; repair metadata separately if needed, never alter EZ parameters/signs/windows/thresholds/gross or relabel failed results.

**FINAL: REJECT_EZ_HISTORICAL_GROWTH_OR_MARGINAL.** No 2025 validation, external benchmark comparison, paper or live trading. Do not cosmetically rescue rejected EZ.
