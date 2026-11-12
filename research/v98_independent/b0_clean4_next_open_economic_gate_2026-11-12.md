# V98 Independent B0 — authenticated Clean-4 economic gate (2026-11-12)

Evidence: GitHub Actions run 43157337577, commit fa7a5e27264c79447f6b8f51f6b0e4c0fb59e59f, artifact 13916258579 (SHA256 c609116a6e2eeb42be10e3fd3a8955523ff879fc3022ee2f17edd437eed3d5be). This is research evidence, not a validated champion.

The workflow completed successfully with 23 unit tests, downloaded pinned Clean-4 price artifact 13444665313 and native funding artifact 13464271018, and replayed 27,048 hourly observations using next-open fills. The artifact states holdout_accessed=false. Price manifest SHA256 01e7bdeb8bcaf34ee898e322cf20f4479c0e25a9066b40f8cd2446286259f8a8; funding manifest SHA256 f33094dfc065aa862a529d46f36e15f8a418ab085780214a0423488d2ff49622.

| Cost scenario | Final equity (from 10,000) | Total return | Approx annualized geometric return* | Max drawdown reported | Turnover |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1x | 14,562.0085 | +45.6201% | +12.9438% | 22.3763% | 86.4474 |
| 2x | 14,263.1573 | +42.6316% | +12.1878% | 22.2480% | 84.6910 |
| 4x | 12,762.2273 | +27.6223% | +8.2197% | 23.6613% | 73.3911 |

*Calculated as (final_equity / 10000)^(8760 / 27048) - 1. The 27,048 count includes warmup and is not an independently established invested-duration denominator. These annualized figures are descriptive approximations, not certified CAGR.

## Gate decision

**DO NOT PROMOTE B0.** Positive nominal equity in this replay is not proof of robust compounded wealth or superiority. Under 4x costs the final equity declines materially versus 1x; 1x approximate annualization is modest relative to the project's deliberately high-growth objective. No tuning based on these results is authorized. B0 stays an experimental system integration baseline, not a frozen complete-engine champion. A3 and all external frozen engines remain untouched.

## Outstanding independent gates

1. Audit execution accounting, especially treatment of funding settlement at the opening boundary, post-funding weight drift, and whether price/position convention matches actual Binance USD-M fills; verify fee/slippage assumptions against documented venue evidence.
2. Produce complete chronological equity and trade/position ledger (not only 5 summary fields), and derive exact invested-period CAGR, yearly/fold results, Profit Factor, payoff, win rate, positive days, tails, concentration, and regime attribution. The current artifact cannot support those statistics.
3. Validate the **seven-slot composed portfolio** and marginal sleeve contributions with preregistered hypotheses, separate chronological training/validation and untouched future holdout. Do not access 2026+ during training or reuse contaminated Phase083.
4. Only after an internally frozen V98 candidate passes its own gates may external V14/V15/V99 benchmarks be opened.

This report is a post-run economic disposition of an already preregistered B0 candidate, **not** a parameter-selection or rescue instruction.
