# V98 Independent BC — permanent 90-cell economic rejection (2026-10-23)

**Decision: REJECT_BC_HISTORICAL_GROWTH_OR_MARGINAL.** BC was preregistered before PnL in `bc_breakout_funding_recovery_prereg_20261023.md`, then implemented and executed with the exact frozen seven-slot hypothesis. No post-result strategy modification or ablation rescue.

Official two-OS run: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40055698743
Official economic summary artifact: `bc90-official-economic-summary`, ID `12544799899`. Independent audit used the **10 original per-path/per-OS JSON artifacts**, rather than trusting the summary. Source manifest SHA256 `833013a2e18836a203afd267ca698175907cff8f4c153c919a7811f14cb80752`.

## Historical training, USD10k, base, carried-before-fill
- 90/90 distinct mechanical scenarios survived; 180/180 receipts across Ubuntu 22.04/24.04. Independent original-receipt comparison had **zero structural/numeric errors** (maximum absolute numeric difference `1.862645149230957e-09`); independently checked annual/total wealth identities and fee/slippage vs turnover.
- **Two-year CAGR -4.4211%**, final NAV **USD9,134.76**, 2023 annualized **-0.8355%**, 2024 annualized **-7.8678%**. Maximum drawdown **14.3702%**; hourly net PF **0.95777**, payoff **0.95276**, win rate **50.13%**, positive UTC days **205/731**.
- Turnover **USD141,550.97**, fees **USD70.78**, slippage **USD70.78**, native funding **+USD11.55**; maximum single-asset gross concentration **100%**.
- All four mandatory full-growth gates (2023/2024, base/severe, two funding orders) fail. Base annual log wealth `[-0.00838478, -0.08211343]`; severe `[-0.03760186, -0.11105275]` for carried-before-fill.
- Marginal base carried-before-fill annual log wealth: Opportunity `[+0.00294923, -0.00065275]`; RV `[+0.00095260, +0.00137829]`; Stress/Recovery `[-0.00325090, +0.00381426]`. Severe RV is negative in both years; all three required sleeve gates fail.

## Interpretation and integrity
Physical execution/cost pipeline passed for this candidate, but the **portfolio lost money in both training years** and did not deliver robust positive complementary sleeve contribution. This is an economic failure, not a CI failure. BC and its leave-one-out paths remain permanently rejected; do not adjust windows, signs, budgets, costs, gross exposure or gates after seeing this result.

Independent audit rederived receipt arithmetic and checked cross-OS numeric identity, **not individual native funding events from trade-level fills**; native source manifest is pinned by the official source loader. This distinction must not be misrepresented as full independent trade-level replay.

Only authenticated Dec2022-Dec2024 Clean-4 training and native funding were used; sealed 2025 holdout, quarantined XRP, 2026+, Phase083 and V14/V15/V99 benchmark inputs were not read. No V16/V99 Frozen, V99 research/workflow/report/paper mutation. No V98 engine has passed internal growth+marginal gates; no independent future validation or live authorization.

**Next critical path:** design a genuinely different preregistered complete portfolio hypothesis that targets persistent *net* compound wealth and causal sleeve value, rather than repairing BC or inflating test counts.