# V98 Independent BK — frozen historical rejection (2026-10-24)

**Decision: REJECT_BK_HISTORICAL_GROWTH_OR_MARGINAL.** BK is permanently rejected, including all ablations. No post-result threshold, window, sign, budget, fee or leverage changes; no cosmetic rescue.

**Official preregistered, algebraically corrected, full Clean-4 run:** https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40067550721 (commit `d7b5fe0f4a03c5a6c62420081adee16caaffdd3c`). A prior run https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40067516520 used the original sign error in the stress short's causal evidence and is **invalid as economic selection evidence**. The short-sign algebra was corrected with a falling-tape invariant before any historical PnL from either run was inspected.

**Mechanics:** 90/90 official historical training scenarios physically survived; 90 cross-OS pairs reconciled with zero discrepancies; independent artifact-only arithmetic audit checked 180/180 receipts with zero errors. Native funding is source-authenticated and signed, but the independent audit does not independently reconstruct every native event or intrabar trajectory.

**USD 10k full BK base, carried-before-fill, 2023–2024 training only:** two-year CAGR **+45.17045%**; 2023 **+22.45879%**, 2024 **+72.01432%**; maximum drawdown **17.23481%**; turnover **$1,289,817.67**, fees **$644.91**, slippage **$644.91**, native funding **−$742.84**. Hourly net Profit Factor **1.05997**, payoff **1.02925**, win rate **50.7351%**. Positive UTC days: 2023 **50/365**, 2024 approximately **131/366**. The 2023 and 2024 full-system base/severe annual growth gates passed in both native funding settlement orders.

**Full-minus-ablation marginal annual net log growth (2023, 2024), USD 10k carried-before-fill:**
- Opportunity: base **[+0.162582,+0.064104]**; severe **[+0.115484,+0.076892]** — PASS all required annual/cost/order marginal gates.
- Relative Value: base **[−0.131273,−0.020029]**; severe **[−0.025522,−0.005851]** — FAIL.
- Stress/Recovery: base **[+0.042125,+0.119092]**; severe **[−0.018701,+0.039721]** — FAIL under severe 2023.

**Structural diagnosis:** BK's opportunity sleeve was genuinely additive to the complete executed portfolio across both training years and both fee levels, but its pair and crisis-short sleeves failed the strict complete-engine marginal requirement. Under severe friction the crisis short had negative marginal contribution in 2023. A successful isolated sleeve or ablated portfolio is NOT a qualified engine. No historical PnL here is an independent future validation, external superiority claim or authorization to trade.

**Firewalls:** all writes limited to `research/v98_independent/bk_*` and `.github/workflows/v98-independent-bk-*` on `research/v98-independent-zero`; 2025 holdout never loaded, 2026+ never used, XRP quarantined, old Phase083 excluded, V14/V15/V99 not used. V16/V99 Frozen, V99 research/workflows/reports and V99 paper untouched.

**Next critical path:** an original composed architecture must earn genuinely positive portfolio-level marginal growth from three complementary sleeves under severe costs, while retaining the validated physical execution and source integrity. Do not tune or resurrect BK.
