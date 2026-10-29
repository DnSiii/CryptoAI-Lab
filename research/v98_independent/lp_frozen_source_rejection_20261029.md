# V98 LP — permanent source-only rejection (2026-10-29)

**DECISION: REJECT LP BEFORE PNL. NO RESCUE. NO PROMOTION.** Preregistration SHA `64990cf98783f2e1b2245467fb5dd71bc34cb7ce` preceded source implementation SHA `9e8c15a5a8d7cb0bb5a0711954711af886fb17ae` and independent source gate SHA `72fe3f819b5cdfb29518c4a8ad830d9a3cfc152e`.

Local run read only pinned original Clean-4 artifact 12549265452 (all four SHA256-authenticated 18,288-hour OHLC files, exact pinned native funding SHA256 `f706812b7989666c3efd0b24045a5c31f4d9c79b46d61da7b5e6cde6c6e73f5e`, 9,144 funding events), Dec-2022 warmup and 2023–2024 training. No 2025/2026, XRP, Phase083, V14/V15/V99 internals, Frozen or paper.

Independent expected-entry replay constructed without importing LP event generation: **zero mismatches**. Authenticated future mutation prefix, synthetic future causality, no silent row changes, no invalid-quote entries passed; maximum intended gross 0.90. Counts:

| Year | Opportunity | Relative Value | Stress/Recovery |
|---|---:|---:|---:|
| 2023 | **7 (FAIL <8)** | 16 | 13 |
| 2024 | 9 | 10 | 12 |

The preregistered hard gate requires >=8 entries per optional sleeve in **each** year. **Opportunity 2023 = 7**, so LP is permanently rejected at the source gate. No LP PnL, economic backtest, independent settlement, 2025 validation, benchmark or real trading performed or claimed. No threshold/clock/exposure rescue allowed.

Execution critical-path finding: the authenticated pinned artifact is actually downloadable into the current research runtime; local authenticated replay is feasible without waiting for GitHub workflow dispatch. This does not substitute for an original 30-cell GitHub execution or independent ledger, which remain mandatory for a future source-eligible architecture. Funding conservative marks remain `api_mark_attested=false`, not API-attested.

Next: a genuinely distinct preregistered complete architecture, prioritize high-growth net marginal contribution, and run real full physical cells only after passing independent source gate. No V98 complete champion yet.
