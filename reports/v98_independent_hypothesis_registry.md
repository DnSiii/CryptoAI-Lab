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

## Phase102 preregistration — decentralized perpetuals volume feasibility only
PRE-REGISTERED before Phase102 payload inspection or alpha/PnL. Frozen source is DefiLlama `overview/derivatives` top-level `totalDataChart`, window 2023-01-01 through 2025-12-31 UTC. Mode is DATA_ONLY_NO_ALPHA_NO_PNL. This family measures decentralized perpetuals risk-taking/activity and is distinct from closed spot DEX-volume, TVL, stablecoin, sentiment, fees, positioning/OI and price-derived families.

PASS_DATA_ONLY requires HTTP/JSON success, >=95% of 1,096 days, first day <=2023-01-07, last >=2025-12-24, finite non-negative values, zero duplicate normalized dates, strict chronological order and raw SHA-256. Any failure closes the exact source/schema without substitution. A pass authorizes only a separately preregistered Phase103; no same-run economic evaluation.

## Gate preservation
Validation remains closed unless a future frozen training candidate passes. Final holdout remains untouched until training and validation pass and a candidate is formally frozen. V99 is excluded from V98 selection. No V16/V99 files/state/workflows/reports may be modified.

## Current decision
No champion exists. Phase101 is REJECT_NO_RESCUE. Phase102 is preregistered DATA_ONLY and execution #266 is pending/queued at registry update time.
