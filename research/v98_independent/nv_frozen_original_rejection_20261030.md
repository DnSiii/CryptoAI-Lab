# V98 NV — permanent original economic rejection (2026-10-30)

**PERMANENT REJECTION; NO POST-RESULT RESCUE.** NV liquidity-rotation/volume-asymmetry seven-slot rules and economic gates were preregistered at commit `05d64bbc071b62a3149f732c1dcc8e93b2f7219b` before code or economic PnL. Original source/oracle broadcast defect was corrected **before any physical PnL** (commit `7f991f1debce432b443c8a2894df5ca9f131e6d4`), without changing source signals, thresholds, windows, gross, fees, signs, or economic gates.

**Original original physical run:** [GitHub Actions 41140930878](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41140930878), head `7f991f1debce432b443c8a2894df5ca9f131e6d4`, artifact `v98-nv-original-41140930878` id `13018059086`. The GitHub workflow status **failure** is intentional: binding `REJECT_EARLY_TRAINING` after 22 preregistered economic gate failures, not an infrastructure failure. Initial pre-PnL workflow `41140879499` failed independent-source broadcasting and did **not** execute any PnL.

**Clean-4 development only, 2023–2024, carried-before-fill:**
- Base: CAGR **+22.8970%**, max DD **-37.4751%**, turnover **USD514,994.80** per USD10k. 2023 **+82.1382%**, 2024 **-17.0523%**. Optional marginal net log-growth: Opportunity **+0.003299**, Relative Value **-0.001150**, Stress/Recovery **0**.
- Severe: CAGR **+19.8562%**, max DD **-37.8289%**, turnover **USD501,824.44**. 2023 **+78.4015%**, 2024 **-19.4565%**. Marginals: Opportunity **+0.002242**, RV **-0.003907**, Stress **0**.
- Supersevere: CAGR **+16.6595%**, max DD **-38.2017%**, turnover **USD488,001.74**. 2023 **+74.4197%**, 2024 **-21.9565%**.
- Failed growth minimum in base/severe, failed positive severe 2024, Opportunity below +0.020 and negative 2024 annual marginal, RV negative, Stress inactive (zero marginal). 22 economic failures across the two funding-order variants. Turnover and physical survival passed but do not override growth failure.

**Independent gates:** pinned Clean-4 18,288 source hours; 53/53 source decisions independently recomputed, zero source mismatches; 9,144 signed native 8h funding events; 30/30 original physical cells passed execution invariants; 17,543 all-hour signed settlement independently reconciled; 17,543 strategy-to-fill hours independently replayed with 141 rebalance events, zero quantity mismatches and injected fill tamper detected; independent 30-cell arithmetic audit reported zero mismatches and independently reproduced the rejection. These establish accounting integrity **of a rejected engine**, not a validated edge.

**Unresolved exact funding evidence:** four authenticated per-symbol official (or independently equivalent) 2,286-row historical `symbol,fundingTime,fundingRate,markPrice` files with source/transport attestation, 9,144 events total, Dec-2022–Dec-2024. Official API transport HTTP451, alternate HTTP202 empty and third-party timeout; conservative official 1h mark envelope remains proxy, not exact event settlement. Missing exact mark is not the reason NV failed its economic gates.

**Next:** pursue genuinely distinct complete high-growth seven-slot economic hypothesis, not NV tuning. 2025 has already been consumed by prior candidates and cannot serve as fresh independent validation; 2026+ holdout untouched. No V14/V15/V99 internal signal use, Frozen or paper changes, or live authorization.
