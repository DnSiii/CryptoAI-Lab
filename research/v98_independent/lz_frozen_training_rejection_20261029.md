# V98 LZ — permanently rejected after authenticated source and 30-cell training (2026-10-29)

**TERMINAL REJECTION — NO RETUNING, NO PROMOTION, NO HOLDOUT.** Architecture preregistered in commit `807aafae75ef4b907199008d2737539e0e5fcab9` **before** LZ implementation and results. All subsequent writes confined to `research/v98_independent/lz_*` and `.github/workflows/v98-independent-lz-*` on `research/v98-independent-zero`.

## Authenticated source gate
[GitHub Actions source run 40924148219](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40924148219) passed. Original SHA-pinned BTC/ETH/BNB/SOL Dec-2022 warmup through Dec-2024 training only: 18,288 hourly rows per asset, 9,144 native signed funding events. Independent entry replay mismatch **0**, invalid entries **0**, silent updates **0**, causal future-prefix mutation PASS, intended gross peak **0.93**. 2023 Opportunity/RV/Stress activations **31/31/41**; 2024 **33/31/49**. All >=8/year.

## Physical training (diagnostic, not independent performance validation)
[GitHub Actions physical run 40924160975](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40924160975) completed 5 books x 3 cost tiers x 2 funding orders = **30** actual hourly physical training cases, including native signed funding and independently SHA-pinned official worst-case mark envelope. All reported full-book CAGR and turnover are **training-only**, not paper/holdout/live PnL.

| LZ full book, 2023–2024 | Base | Severe | Supersevere |
| --- | ---: | ---: | ---: |
| Annualized CAGR | +57.413% | +51.290% | +45.264% |
| Turnover / initial USD10k | **USD928,586 FAIL** | **USD886,432 FAIL** | USD846,005 |
| Opportunity marginal log-growth | +0.092956 | +0.076038 | +0.061735 |
| Relative Value marginal log-growth | **-0.010716 FAIL** | **-0.027270 FAIL** | -0.041182 |
| Stress/Recovery marginal log-growth | +0.046797 | +0.027494 | +0.006233 |

Both funding settlement orders yielded the same rounded results. **Two independent, preregistered hard failures**: base/severe turnover > USD600,000 and RV marginal <= +0.02. Even though Opportunity and Stress marginals passed base/severe, they do not justify rescuing the rejected portfolio or transplanting its components without new independent hypotheses.

**Receipt labeling caveat:** an accidental case-sensitive text substitution in the copied diagnostic produced `REJECT_EARLZ_TRAINING_ECONOMIC` rather than the intended `REJECT_EARLY_TRAINING_ECONOMIC`. The accompanying eight explicit gate failures and numeric outcomes are unambiguous; this note records the semantic rejection without changing historical receipts or rerunning to cosmetically alter them.

**External data limitation unchanged:** exact historical exchange funding-tick mark remains unavailable after HTTP 451; official independently attested two-sided OHLC worst-case envelope is the conservative alternative, not exact native mark. Account-specific fee tier and actual order-book slippage are not evidenced. No independent all-hour PnL oracle, 81-corner, cross-OS, 2025 validation, future holdout, benchmark comparison, paper or live trading was attempted for LZ.

**Next structural hypothesis should be genuinely different:** reduce frequent 72h cross-sectional RV reversal turnover and pursue a portfolio-level relative-value contribution that is robust after funding and costs, without copying LZ sleeve signs/windows/weights or retuning a rejected result. Preserve growth/CAGR as objective; risk/tails/costs as survival constraints.

## Final fail-closed CI verification (same immutable LZ hypothesis)
Reproducible triggering-SHA checkout source run [40924298444](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40924298444) PASS. Corrected gate-only runner [40924450925](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40924450925) reran the **same frozen LZ** 30 physical cells, reproduced base CAGR **57.413%**, severe CAGR **51.290%**, turnovers **USD928,586/886,432**, and emitted the eight explicit hard failures. Its workflow now exits **code 2 / GitHub Actions FAILURE** when the economic gate rejects, while the full diagnostic JSON artifact is still uploaded (artifact ID `12919498269`). This changes only CI failure signaling and a misspelled decision label; **no signal, weight, window, threshold, cost, historical data or gate was changed**, and LZ remains permanently rejected.
