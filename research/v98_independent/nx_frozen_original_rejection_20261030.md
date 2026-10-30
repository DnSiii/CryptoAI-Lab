# V98 NX — original frozen economic rejection (2026-10-30)

**PERMANENT REJECTION; NO POST-RESULT RESCUE.** Distinct trend/carry/volatility seven-slot hypothesis preregistered at `781cdce9e0f776b011b3447c7f03310c694e2a86`, physical implementation at `f5d4070b6237fc27b5d5b9dbe7f8ffc3fc0e54d9`. Original execution: [GitHub Actions 41146373747](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41146373747). Workflow failure is intended binding economic rejection after all physical and accounting steps passed, not a source/CI infrastructure failure.

**2023–2024 Clean-4 development, carried-before-fill, per USD10k:**
- Base CAGR **-15.0192%**, max DD **-51.9354%**, turnover **$373,165.38**. Annual 2023 **-21.7353%**, 2024 **-7.7474%**.
- Severe CAGR **-18.1616%**, max DD **-53.1328%**, turnover **$359,921.26**. Annual 2023 **-24.6182%**, 2024 **-11.1764%**.
- Supersevere CAGR **-21.4141%**, max DD **-54.3896%**, turnover **$346,372.10**.
- Base marginal net log-growth Opportunity **+0.094917**, Relative Value **-0.003075**, Stress/Recovery **+0.012480**; severe **+0.090811, -0.010816, +0.010775**. Opportunity passes marginal floor; RV negative; Stress below floor. **16 binding economic gate failures** across two funding orders.
- Raw source decisions (2023/2024): Opportunity **6/7**, RV **27/26**, Stress **14/12**. All three are active, so failure is economic rather than missing activity.

**Independent evidence:** authenticated 18,288 Clean-4 hours; 53/53 independently recomputed source decisions, zero mismatches; 9,144 native 8h funding events; 30/30 physical cells passed invariants; 17,543 hourly signed settlement rows independently reconciled; 17,543 strategy-to-fill hours independently replayed, 413 rebalance events, zero quantity mismatches, tamper detected; 30-cell arithmetic/economic audit independently reproduced binding rejection. This is integrity of a rejected engine, not a validated profitable strategy.

**Source limitation:** exact historical event `markPrice` remains missing (4 authenticated per-symbol 2,286-row files, 9,144 total), signed worst-side official hourly envelope used as conservative proxy. This is not why NX failed. 2025 already consumed by earlier research, not a fresh validation set. 2026+ untouched, XRP quarantined, V14/V15/V99 internals not consulted, Frozen/paper unchanged, no live authorization.

**Artifact naming caveat:** the NX workflow inherited the historical `v98-nv-original-` artifact *label* from a template, but all seven payload filenames are `nx_*` and run SHA is the NX implementation; label alone is not evidence of NV data reuse.
