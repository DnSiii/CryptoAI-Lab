# V98 WG — frozen exposed-training survival rejection (2026-11-02)

**FINAL: REJECT_WG_EXPOSED_TRAINING_SURVIVAL. NO V98 CHAMPION. NO RETUNE OR RESCUE.**

Preregistered before implementation, source read or PnL at commit `2d0ed31a08947a0bfc62d8390c1d190cb2744803`. Source module `wg_funding_inventory.py`, independent oracle `wg_funding_inventory_oracle.py`, physical ledger `wg_funding_inventory_physical.py`, and WG-only workflow `v98-independent-wg-funding-inventory.yml`. Final run [GitHub Actions 41465942169](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41465942169), immutable artifact `13153020730` (ZIP SHA256 `350a15a914e068734b5a2e236803f76a739ee0b79d1b1d5abf1a9efbd2ac50b8`). Red CI is **real survival rejection**; independent oracle could not approve a failed full-book base ledger. No benchmarks or holdout inspected.

## Source and complete composed-engine gate

Authenticated Clean-4 1h Dec-2022 warmup through Dec-2025 exposed training, 27,048 source hours, 13,524 native funding events. 157 weekly causal decisions; all four slots active 157/157, pre-PnL incidence threshold 16. Synthetic future-source mutation and source-integrity gates passed. The weekly holding design reduced scheduled rebalance frequency by construction but does not guarantee the gross exposure remains <=cash between fills.

**30 preregistered physical scenarios attempted** (five books x three illustrative 10/20/35bps cost tiers x two funding orders). **24 completed; six full-book scenarios failed** the non-negotiable close gross<=cash survival gate at identical hour **19748 (2025-03-02 20:00 UTC)**. Failure: `CLOSE_HIDDEN_LEVERAGE` in all three tiers and both funding orders. Therefore full WG CAGR, PF, max drawdown, annual return and optional marginal log growth are **undefined/not eligible**; do not extrapolate or publish partial full-book CAGR. This is a genuine system-level failure, not a GitHub runner/tool failure.

## Independent survival witness using official source and frozen partial ledger

The base full-book ledger contains exactly hours 0..19747. Independently read the last position/cash from `wg_base_full_hourly_ledger.csv` in the immutable artifact and the four exchange-authenticated 2025 hourly candle CSVs from the pinned 2025 official-source artifact `12987237544`. At hour 19748, no weekly rebalance is scheduled and `19748 % 8 = 4`, so no funding settlement occurs. Independently recompute `cash_after = cash_before + sum(q*(open_t-prev_close)) + sum(q*(close_t-open_t))`, and `gross_close = sum(abs(q)*close_t)`.

- Last prior cash/equity: USD **17,440.8496479164**.
- Next-hour gap PnL: USD **+0.6388900751**; intrahour PnL: USD **-274.9773775896**.
- Independently reconstructed next-hour equity: USD **17,166.5111604020**.
- Independently reconstructed gross exposure: USD **17,386.2353278674**.
- Gross/equity = **1.0127995820**, excess gross **USD219.7241674654**; survival condition gross<=cash is false. This independently corroborates the full-book physical rejection without importing WG strategy signals, using only a frozen position and original exchange candles. Do not claim an independent 30-cell oracle PASS.

## Diagnostic ablations (not candidates)

Base core-only CAGR +36.38%; base minus-stress CAGR +46.45%; severe core-only CAGR +33.13%; severe minus-stress CAGR +41.83%. These are *diagnostic sub-books*, NOT a WG complete-engine approval, independent validation, or permission to transplant a partial sleeve. The full composed system is rejected and cannot be repaired by deleting stress, changing gross, holding period, fees, or thresholds after seeing this result. None of these sub-books clears the predeclared full-book CAGR hurdle as a complete V98.

## External evidence and strict next step

Even if survival had passed, account-executable returns remain unverified: independently attested exact exchange funding-tick `markPrice` for all 13,524 events, dated account fee tier, historical spread/depth/impact and collateral/liquidation policy are missing. Official API HTTP451 is not bypassed; lawful exchange-origin export with verifiable custody is the alternative. 1h worst-side official mark envelopes and illustrative cost tiers are explicitly not exact execution proof. Future research must use a **genuinely different preregistered complete architecture with endogenous between-rebalance survival**, not rescue WG. No 2026+, quarantined XRP, contaminated Phase083 holdout, V14/V15/V99, Frozen or paper touched. No live trading.
