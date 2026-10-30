# V98 MC — immutable source-pass / economic-rejection receipt (2026-10-29)

**TERMINAL REJECTION. NO RETUNING, NO MODULE TRANSPLANT, NO PROMOTION.** MC preregistered in commit `0a89f87371cbfbc2a6e0309dfa5e71af166e765d` before source code, source gate or PnL. Seven slots: Growth Core, Opportunity, Relative Value (48h contrarian liquidity dislocation), Stress/Recovery, Regime Router, Dynamic Allocator, Risk Governor. Independent of all benchmarks.

## Source-only gate — PASS
[Original authenticated source run 40952056953](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40952056953). Clean-4 2022-12 warmup + 2023–24 training only, 18,288 hourly bars per asset, 9,144 signed native funding events. Independent entry replay mismatches **0**, invalid entries **0**, silent updates **0**, authenticated and synthetic future-mutation tests PASS, intended gross max 0.88 NAV. 2023 Opportunity/RV/Stress activations **18/37/26**; 2024 **16/52/29**, all >=8. No 2025+, XRP, Phase083, V14/V15/V99, Frozen, paper or future holdout accessed.

## Original full-hour 30-cell physical training — REJECT
[Original physical run 40952206298](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40952206298) ran 5 books × 3 cost tiers × 2 funding orderings = **30 actual full-hour cells** with no physical invariant failures. Exit code 2 = economic rejection. Receipt artifact `v98-mc-physical-40952206298`.

[Independent read-only receipt audit 40952313097](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40952313097) reconciled **30/30 cells, zero arithmetic mismatches**, including costs, turnover, margins and rejection. It does NOT independently replay all-hour PnL.

| Full MC, 2023–24 training only | Base | Severe | Supersevere |
| --- | ---: | ---: | ---: |
| CAGR | +53.5223% | +46.7937% | +39.9009% |
| Turnover per USD10k initial | **USD1,080,798.88 FAIL** | **USD1,026,973.83 FAIL** | USD972,832.25 |
| Max drawdown | -27.5197% | -29.5160% | -31.6570% |
| 2023 return | +102.4004% | +94.6351% | +86.6361% |
| 2024 return | +16.5162% | +10.7699% | +4.9167% |
| Opportunity marginal log growth | +0.094803 | +0.083529 | +0.071428 |
| Relative Value marginal log growth | **-0.012860 FAIL** | **-0.044616 FAIL** | -0.078693 |
| Stress/Recovery marginal log growth | +0.070251 | +0.054938 | +0.038499 |

Original preregistered gates: base CAGR >50%, severe >30%, positive severe annual returns, severe DD <45%, turnover <=USD600,000 at base/severe, each sleeve full-minus-ablation marginal >0.02 base/severe, annual marginal >-0.03. **Eight failures** (two funding orderings × turnover base/severe and RV marginal base/severe). No post-result parameter/sign/gross/cost adjustment permitted.

## What is and is not proven
Original run and independent arithmetic audit support a TRAINING diagnostic only. No independent all-hour PnL oracle or 2025 validation was run because MC failed economic gates. The provisional-only hourly JSONL exporter and independent replay gate were implemented for a future eligible engine but intentionally not activated on rejected MC. Funding uses SHA-authenticated native rates with official worst-side 1h mark OHLC envelope, **not exact tick mark** (exact mark endpoint previously HTTP 451). Slippage is modeled, not exchange fill evidence. No validated future CAGR or real-trading authorization.

**Mechanistic outcome:** unlike MB's momentum relative-value pair, MC's contrarian liquidity-dislocation pair still subtracts net compounded growth while generating prohibitive turnover. Opportunity and Stress had positive marginal contribution but cannot rescue a rejected full engine. Next hypothesis must alter portfolio economics structurally, not tune MC.

**Decision: REJECT_EARLY_TRAINING permanently.** Holdout, Frozen and paper preserved.
