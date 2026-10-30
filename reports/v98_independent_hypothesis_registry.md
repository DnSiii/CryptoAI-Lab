# V98 Independent — Hypothesis Family Registry

Status: no champion. Validation and final holdout remain closed.

Purpose: prevent renamed repeats, rescue tuning, and pseudo-diversification. This registry is selection hygiene only; it does not inspect validation/final holdout and does not use V99 evidence.

## Historical registry through Phase062
003-050 as previously recorded. Phase051 liquidation-data feasibility failed with no alpha. Phase052 no-alpha probe passed, Phase053 spot-perp candidate failed. Phase054 no-alpha COIN-M/USD-M probe passed, Phase055 candidate failed. Phase056 listed-options feasibility failed cross-fold coverage before alpha. Phase057 on-chain network-activity feasibility failed its frozen metric-access gate before alpha. Phase058 macro-risk feasibility passed; Phase059 candidate failed. Phase060 aggregate stablecoin-liquidity feasibility passed; Phase061 candidate failed. Phase062 cross-asset/system-liquidity feasibility failed its frozen reproducibility/source-access gate before alpha.

All families through Phase062 remain closed exactly as previously recorded. No failed family may be revived by sign/window/cadence/gross/threshold/regime/symbol search, subset rescue, source substitution after failure, or recombination.

## Key decisions retained
Phase050 REJECT_NO_RESCUE: training -17.41%, PF 0.9462, DD -35.18%; all 2023/2024/2025 folds negative; severe -45.80%; supersevere -72.36%.
Phase051 FAIL_DATA_NO_ALPHA: Binance public USD-M liquidationSnapshot 0/30 frozen checks.
Phase053 REJECT_NO_RESCUE: base -42.6493%, DD -51.1659%, PF 0.8687; severe -63.0156%; supersevere -81.6734%.
Phase055 REJECT_NO_RESCUE: base -46.50%, PF 0.0080, DD -46.50%; severe -67.05%, supersevere -84.82%.
Phase056 FAIL_DATA_NO_ALPHA: frozen options coverage requirement failed; no partial-era/BVOL-only rescue.
Phase057 FAIL_DATA_NO_ALPHA: frozen FeeTotUSD metric inaccessible while other metrics passed; no metric dropping/substitution.
Phase059 REJECT_NO_RESCUE: aggregate +115.71%, PF 1.331, DD -19.81%, but chronological 2025 fold -2.32%; no rescue.
Phase061 REJECT_NO_RESCUE: aggregate +64.89%, PF 1.0704, DD -48.74%; 2023 and 2025 folds negative; no stablecoin sign/window/subset/source/regime/gross/cadence rescue.
Phase062 FAIL_DATA_NO_ALPHA: frozen FRED system-liquidity source did not complete reproducibly; no alternate-source rescue.

## Later-family continuity
Post-062 V98 evidence is preserved in its namespaced scripts/reports and remains binding. Phase083 is permanently ineligible for reuse/selection. Phase093 Fear & Greed contrarian is REJECT_NO_RESCUE. Phase095 CandleFeed/Bybit liquidation feasibility is FAIL_DATA_NO_ALPHA. Phase096 DeFi TVL feasibility passed; Phase097 relative-TVL candidate is REJECT_NO_RESCUE. Phase098 DEX-volume feasibility passed; Phase099 DEX-volume regime is REJECT_NO_RESCUE. Phase100 protocol-fees feasibility passed.

## Phase101 decision — REJECT_NO_RESCUE
Frozen protocol-fees regime training returned +44.5684% total return and 13.0701% CAGR, but failed four preregistered gates: aggregate PF 1.0774 <= 1.10; max drawdown -54.7761% < -35%; chronological 2025 return -5.1213% <= 0; supersevere return -1.0284% with PF 1.0289 failed the stress gate. 2023 was +41.2122%/PF 1.1804 and 2024 +8.9385%/PF 1.0690, but this does not override the frozen all-gates requirement. Severe remained +24.8980% yet DD was -57.7337%. No sign/window/gross/cadence/regime/basket/source rescue is allowed. Validation and final holdout were not opened.

## Phase102 decision — FAIL_DATA_NO_ALPHA
The frozen DefiLlama `overview/derivatives` / `totalDataChart` feasibility probe returned HTTP 402 with a paid-plan requirement. Per preregistration this closes the exact decentralized-perpetuals-volume source/schema without substitution, source-shopping, partial-data rescue, or alpha/PnL. Expected window remained 2023-01-01 through 2025-12-31 (1,096 days). Validation/final holdout were not opened and V16/V99/Phase083 were not used.

## Phase125 decision — REJECT_NO_RESCUE
The frozen US Economic Policy Uncertainty permission regime failed decisively in training: total return -30.0426%, CAGR -11.2256%, max drawdown -44.7666%, PF 0.9414. Chronological 2023 returned -27.4466%, 2024 +6.7886%, and 2025 -10.4452%. Severe returned -43.0322%; supersevere -59.2071%. Sideways return-sum proxy was -0.40346 and XRP represented 48.2379% of absolute pre-cost contribution, breaching the frozen 45% concentration gate. The always-long context benchmark returned +59.8055%, reinforcing that this exact permission filter destroyed rather than improved training expectancy. No sign inversion, lookback/lag change, XRP removal, threshold/gross/cadence adjustment, or other rescue is permitted. Validation/final holdout remained unopened; V16/V99/Phase083 were not used.

## Phase126 preregistration — DATA_ONLY
After closing Phase125, the next orthogonal family is Chicago Fed National Financial Conditions Index (`NFCI`) feasibility. Phase126 is frozen as DATA_ONLY before values/alpha/PnL: FRED `NFCI` only, native weekly cadence, 2023-01-01 through 2025-12-31, >=150 in-window rows, >=95% finite coverage, zero duplicate/malformed dates, deterministic payload/date-manifest hashes. No source substitution, interpolation, alternate series, partial-era rescue, validation/final-holdout access, V16/V99 use, or parameter search is allowed. PASS_DATA_ONLY authorizes only a separately preregistered later hypothesis; FAIL_DATA_NO_ALPHA permanently closes this exact source/schema family.

## State reconciliation note
`state/v98_independent_state.json` is a legacy snapshot ending at Phase050 and must not be treated as the current research pointer. It is intentionally not rewritten from incomplete reconstructed summaries: the namespaced reports plus this append-only decision registry are authoritative for post-050 continuity until a deterministic state migration can preserve every intervening decision without information loss. This avoids silently erasing Phase051-102 provenance while fixing the stale-state ambiguity.

## Gate preservation
Validation remains closed unless a future frozen training candidate passes. Final holdout remains untouched until training and validation pass and a candidate is formally frozen. V99 is excluded from V98 selection. No V16/V99 files/state/workflows/reports may be modified.

## Current decision
No champion exists. Phase125 is REJECT_NO_RESCUE and permanently closed. Phase126 NFCI is the active preregistered DATA_ONLY feasibility family; no alpha/PnL may be inspected before its gate passes.
