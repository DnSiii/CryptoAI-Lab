# V98 Independent — Phase284 funding-source replay (2026-10-15, 07:49 BRT)

Scope: read-only analysis of four V98-native Phase206 funding CSVs on `research/v98-independent-zero`, training window Dec-2022 through Dec-2025 only. No XRP, 2026+, holdout, V14/V15/V99, or system PnL.

## Native source integrity

All four files have 3,381 training-window 8-hour funding settlements, no missing 8-hour slots, no duplicate slot in the selected interval, and no nonfinite rates. Exact BNB zero rates: 1,852/3,381 = 54.78%, with a maximum 77 consecutive settlements (2024-07-03 16:00 UTC through 2024-07-29 00:00 UTC). BTC, ETH and SOL have zero exact-zero settlements. Yearly BNB zero counts: Dec-2022 52/93, 2023 507/1,095, 2024 582/1,098, 2025 711/1,095.

## Independent Phase252 feature replay

Reconstructed the frozen daily 23:00 UTC trailing 168-hour funding-mean sign from the four CSVs, using settlement timestamps floored to 8h and excluding 2026+. Compared all 1,097 chronological decisions to the frozen V98 Phase252 bitset: **0 mismatches** and **0 missing settlement slots**.

Original 275 ON decisions (2022 1; 2023 128; 2024 57; 2025 89). Without BNB in the diagnostic funding-mean calculation (NOT a replacement signal, NOT a tradable test): 101 ON decisions (2022 1; 2023 59; 2024 9; 2025 32). There are 183 BNB-dependent ON decisions and 9 BNB-dependent OFF decisions. The counterfactual is solely a source-sensitivity audit, not a proposal to remove BNB or tune the frozen candidate.

## Decision

Internal replay passes, but external source provenance for BNB exact-zero streaks remains unresolved. Preserve Phase252 as partial candidate; no new PnL, promotion, validation or external benchmark. Require independently authenticated BNB funding provenance and native funded A/B/C matched-cap Phase269/271/278 before promotion. Do not substitute a reconstructed or imputed BNB feed.
