# V98 Independent AR — immutable official 90-cell historical rejection (2026-10-23)

**Decision: REJECT_AR_HISTORICAL_MARGINAL — PERMANENT.** No AR post-result threshold, sign, window, leverage, prior, gate, sleeve or event-clock rescue; no ablation promotion. Final corrected executable and workflow frozen at commit `4f4eab7d8c2950e0b3dc397e6b11c2b855c26d44`. Official dual-OS 90-cell training run: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40042538845, summary artifact `ar90-official-economic-summary` ID `12540206102`.

**Source and execution:** authenticated vendor-pinned Clean-4 Dec2022 warmup + 2023/24 only, native 8h funding and conservative mark bounds, actual next-open event-driven rebalancing and signed margin settlement. Initial run `40042298175` is **excluded** from economic evaluation due to preregistered 168h/72h event-clock execution mismatch identified before inspecting its PnL; the pre-economic correction is documented separately. No 2025/2026+, XRP, Phase083, V14/V15/V99, Frozen or paper.

**Reproducibility:** 90/90 corrected historical funded cells mechanically survived, Ubuntu22.04/24.04 ten jobs, independent numeric reconciliation PASS, worst normalized numeric delta 0.00037748 of permitted tolerance. This is not an economic pass.

**AR_full, USD10k base, carried-before-fill:** 2023 CAGR **+101.3381%**, 2024 **+23.1499%**, two-year CAGR **+57.4106%**; max drawdown **30.9714%**; native funding **-USD2,087.12**, fees **USD550.76**, slippage **USD550.76**, turnover **USD1,101,519.35**, 893 nonzero-turnover hours. Hourly PF **1.03649**, payoff **1.00145**, win rate **50.8597%**, positive days **333/731**, 1% hourly CVaR **-1.9314%**, max gross/NAV **1.00451**, peak single-asset gross concentration **100%** (important tail/concentration concern). All figures TRAINING ONLY; not 2025 validation, not forward PnL.

**Capital scalability diagnostic (base, carried-before-fill, full engine):** USD1m: two-year CAGR **+2.628%**, 2023 **+5.903%**, 2024 **-0.538%**, max DD **9.211%**; USD10m: two-year CAGR **+0.358%**, 2023 **+0.620%**, 2024 **+0.097%**, max DD **0.900%**. At USD10k the same engine returned +57.411% CAGR. The severe capacity collapse under physical liquidity constraints is additional evidence that the system is not yet a high-growth scalable delivery; no leverage or liquidity-cap rescue is authorized. These are training-only receipts from the same frozen official run.\n\n**Annual growth gates:** 2023 and 2024 positive under base and severe, both funding orders: PASS.

**Paired full-minus-ablation annual net log wealth, USD10k base carried-before-fill:**
- Opportunity: 2023 **+0.041989**, 2024 **+0.156614**; severe +0.006030/+0.133233 → PASS.
- Relative Value: 2023 **-0.044325**, 2024 **+0.048144**; severe -0.045706/+0.034756 → FAIL.
- Stress/Recovery: 2023 **-0.084365**, 2024 **-0.047861**; severe -0.114639/-0.087599 → FAIL.

**Mechanism:** event-clock repair enabled a genuinely positive opportunity marginal, but beta-residual RV was unstable across years and short-crash/recovery stress lost net wealth in both years. Turnover/friction remained meaningful and concentration reached 100% in at least one hour. This does NOT authorize salvaging AR's profitable ablation or tweaking its failed sleeves. Future architecture must address jointly the structural sign/holding mismatch of defensive trades and concentration without borrowing rejected AR parameters. No qualified V98, no 2025 release or external benchmarks.
