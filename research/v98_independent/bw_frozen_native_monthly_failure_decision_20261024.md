# BW frozen 2023–24 monthly native attribution — decision, 2026-10-24

This is **post-rejection diagnosis**, not candidate selection or a model change. Original rejected BW remains rejected. The preregistered diagnostic `bw_frozen_monthly_forensics_prereg_20261024.md` was committed **before** the results. The workflow `v98-independent-bw-frozen-monthly-attribution.yml` ran successfully in GitHub Actions run **40091390355** after correcting an executable-calendar assertion (the first trade is 2023-02-23, not January). It processed 10 immutable cases, 16,272 executed hours each, using original pinned Clean-4 bytes and native funding. All 10 reconstructed NAV, fees, slippage, funding, turnover and month/year identities against the frozen engine receipts. The previous independent 81-corner source-event replay is run **40090466805**. Neither workflow read 2025 or external engines.

## Root-cause evidence, NOT a rescue

1. **Opportunity marginal loss in April 2024 is largely portfolio interaction, not a standalone SOL loss.** At US$10k/base, BW_full started April at US$18,893.74 and ended US$17,145.36, while BW_minus_opportunity was flat at US$13,258.34 for the entire month. The full portfolio lost **US$726.41 BTC + US$1,020.49 ETH + US$1.49 SOL** that month. Hence April Opportunity marginal log growth was **−0.097103** (severe **−0.100534**), mostly because the **full system retained core BTC/ETH exposure** while its counterfactual did not. Do not mislabel this as direct SOL Opportunity trading loss. This interaction can arise from path-dependent portfolio risk authorization/ratcheting and requires a genuinely new structural architecture, not post-hoc threshold changes to rejected BW.

2. **Relative Value did not contribute in 2024.** The 2024 full-vs-minus-RV marginal log growth is approximately **0 within 1e-14 numerical tolerance**, in both base and severe. The material positive effect was concentrated in **October 2023 (+0.0441 log)**, with 2023 aggregate **+0.047759 log** base. A sleeve with no measurable 2024 marginal benefit cannot satisfy the frozen year-by-year marginal gate.

3. **Stress/Recovery hurt August 2023 directly on BNB.** At US$10k/base, the BW_full BNB position lost **US$29.67** that month (native funding **−US$10.25**, price **−US$15.32**, fees+slippage **US$4.10**); BW_minus_stress had no BNB exposure in August. Under severe costs, BNB lost **US$44.60** (funding **−US$9.92**, price **−US$14.83**, friction **US$19.85**). August marginal log growth: **−0.002617** base / **−0.004067** severe.

4. **Native friction and funding are real, not a bookkeeping mismatch.** BW_full US$10k base: native funding **−US$986.14**, fees+slippage **US$477.97**; severe: funding **−US$922.51**, friction **US$2,213.60**. Both exactly reconcile to original frozen training receipts. The official economic gate remains **REJECT_BW_HISTORICAL_GROWTH_OR_MARGINAL**.

5. **Scaling remains unresolved.** BW_full base CAGR: **39.39% at US$10k**, **39.42% at US$1m**, **3.72% at US$10m** under actual historical participation and exit limits. The separate six-architecture cross-scale audit documents similar high-capital constraints. Do not invent liquidity or relax constraints to inflate growth.

## Consequence for subsequent preregistration

A future candidate needs a **genuinely distinct economic mechanism** with a causal allocator/governor that makes module/core interactions explicit and preserves real liquidity at large capital. Require portfolio-level leave-one-sleeve-out marginal tests **and** attribution of changed core positions so that a module's purported edge is not confused with induced core exposure. Any new design must be preregistered before its returns; rejected BW, its parameters and its gate are frozen. No 2025 holdout, V16/V99 or paper access, and no live-trading authorization.

**Decision:** no V98 approved; frozen BW not rescued. This report documents why further near-duplicate seven-slot variants are not a substitute for fixing the actual growth and causal-coupling bottlenecks.
