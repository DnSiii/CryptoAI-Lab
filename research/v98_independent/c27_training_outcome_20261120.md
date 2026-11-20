# C27 Clean-4 training outcome — 2026-11-20 (research only)

Immutable evidence: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/44786341472
Commit: 49c6b30b2d8c624f95690a32e08fea9c4e0de460
Branch: research/v98-independent-zero

## Completed
- Authenticated Binance USD-M Clean-4 hourly 2022-12 through 2025-12, 27,048 hours; 27,047 ledger rows per cost scenario.
- Native V98 funding and 1x/2x/4x transaction costs.
- Independent arithmetic ledger audit and causal queued-order/clock audit: passed.
- Preregistered C27 *training-only* economic gate: passed; NOT a validation or promotion.
- C27 deterministic governor CI: passed (run 44786341474).
- No XRP, no 2026+ training data, no Phase083 holdout, no V14/V15/V99 benchmark access.

## Audited training results (initial USD 10,000)
| Cost | Final USD | Max drawdown | Positive days / 1127 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|
| 1x | 15,169.21 | 13.44% | 369 | +19.7667% | +11.9846% | +13.1016% |
| 2x | 15,041.86 | 13.50% | 364 | +19.5167% | +11.5292% | +12.8455% |
| 4x | 14,904.88 | 13.60% | 361 | +19.0183% | +11.4807% | +12.3350% |

Maximum audited per-asset exposure: 0.323446 (all three scenarios). The deterministic buffer is 0.307692 pre-gap per asset and 0.882353 gross; gap protection is conditional on the preregistered envelope, not unconditional.
Funding return sum: -0.0332359 (1x/2x), -0.0330311 (4x); total turnover 14.0483 (1x/2x), 13.9568 (4x).

## Decision
C27 is **training-gate pass, NOT a validated champion**. Absolute returns remain modest against the V98 north-star objective, and no separate chronological validation, future untouched holdout, external benchmark, or paper validation has occurred. No PnL is claimed as live or forward-tested.

Do not retune C27 based on its observed results, nor compare it with V14/V15/V99 before an independently frozen and validated complete candidate. Keep this run as a reproducible training baseline only. Next critical-path work: independent chronological validation of a fully specified complete seven-slot candidate and preregistration of a genuinely distinct *whole-portfolio* growth hypothesis, without altering C27 post hoc or accessing untouched holdout.
