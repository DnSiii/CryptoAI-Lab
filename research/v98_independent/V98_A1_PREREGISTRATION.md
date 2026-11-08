# V98 Independent A1 — preregistration (2026-11-08, before A1 economic results)

Status: **unvalidated research hypothesis; not approved for paper or live trading**.

## Hypothesis and architecture
A0 is rejected and must not be rescued by sign, window or threshold changes. A1 is a distinct long-only slow-trend/breakout composition, not a retune of A0. The seven slots are Growth Core (720-hour slow trend and 720-hour mean), Opportunity Sleeve (168-hour high breakout), Relative-Value Sleeve (positive 168-hour asset momentum; this is *not* market-neutral relative value), Stress/Recovery Sleeve (drawdown recovery conditional on long-term trend), Regime Router (168-hour realized volatility), Dynamic Allocator (portfolio gross budget 0.8), and Risk Governor (per-asset ceiling 0.3). All constants are frozen in `v98_sevenslot_preregistered_a1.py` before observing A1 outcomes. This candidate is architecturally incomplete in the strict relative-value sense: the relative-value sleeve is a positive-momentum proxy and must not be described as a fully validated RV strategy.

## Evidence gates
Source: only authenticated Phase243 Clean-4 hourly BTC/ETH/BNB/SOL USD-M, December 2022 warmup through December 2025; V98 native funding, causal t-1 decision execution, fees and slippage, 1x/2x/4x cost stress. XRP and Phase083 contaminated holdout excluded. No 2026+ access during research.

First verify complete 27,048-hour ledger, 108,192 decisions, source manifests, deterministic replay and valid costs/funding. Independently inspect chronological 2023, 2024, 2025 results and rolling drawdown, tail concentration, turnover, PF, payoff, win rate and positive days. Calendar slices are descriptive, **not** independent train/validation. No promotion without separately designed chronological training/validation gates, reproducibility, robust marginal contribution of all sleeves, and future untouched holdout. In particular, a positive full-sample CAGR is insufficient for approval. If normal cost CAGR <= 0, reject A1 outright; if severe/supersevere stress collapses, do not promote. Do not change A1 after results to rescue it.

No V14/V15/V99 inspection until an internally frozen candidate passes independent chronological validation.
