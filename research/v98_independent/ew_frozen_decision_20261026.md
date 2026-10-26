# V98 Independent EW — immutable pre-PnL rejection (2026-10-26)
Pre-registered before system PnL at commit 27e902e587bebd4ca5a586519c40c1b20d6a494b. Authenticated Clean-4 2023–2024 training only; no 2025 holdout or external benchmarks.

- Source-only causal future-mutation static PASS.
- Preregistered >=4 active epochs per sleeve/year FAIL. Opportunity 0/53 in 2023, 0/52 in 2024; Relative Value 6/53 in 2023 but only 2/52 in 2024. Stress 18/53 and 12/52.
- Source-first economic workflow rejected and skipped both 30-cell system PnL and economic audit: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40266595085
- Separate independent ledger workflow launched concurrently and reported physical cell failure in each book: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40266567293. Because EW failed the preregistered source gate, its ledger attempt is **ineligible for economic selection** and does not justify rescue or holdout access.

**FINAL: REJECT_EW_SOURCE_INACTIVE.** Do not modify EW signals/thresholds/parameters/gates or reuse results for selecting another candidate. No holdout unlock, benchmarks, paper or live authorization.
