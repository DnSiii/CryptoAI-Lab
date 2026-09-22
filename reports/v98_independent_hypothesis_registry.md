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
Post-062 V98 evidence is preserved in its namespaced scripts/reports and remains binding even where this compact registry was not updated contemporaneously. In particular, Phase083 is permanently ineligible for reuse/selection; Phase093 Fear & Greed contrarian is REJECT_NO_RESCUE; Phase095 is the frozen CandleFeed/Bybit liquidation data-feasibility family.

## Phase095 decision — FAIL_DATA_NO_ALPHA
ZERO ALPHA/ZERO RETURNS/ZERO CRYPTO PRICE JOIN. Run #252 completed successfully as an execution but the frozen CandleFeed source could not be queried because CANDLEFEED_API_KEY was absent in the runner. The report therefore correctly emitted FAIL_DATA_NO_ALPHA. Source substitution after observing this failure is forbidden for Phase095. This is a data-access result, not economic evidence.

## Phase096 preregistration — DeFi TVL feasibility only
PRE-REGISTERED BEFORE ANY Phase096 alpha/PnL/crypto-price join. This is a new data-feasibility family, not a rescue of Phase060/061 stablecoin liquidity. Frozen source: DefiLlama public API endpoint `https://api.llama.fi/v2/historicalChainTvl/{chain}`. Frozen chains: Ethereum and BSC. Frozen window: 2023-01-01 through 2025-12-31 UTC. Frozen mode: DATA_ONLY_NO_ALPHA_NO_PNL.

Rationale for orthogonality: TVL measures capital locked in DeFi protocols, whereas the closed Phase060/061 family measured aggregate stablecoin circulating liquidity. Phase096 must not use stablecoin supply, crypto returns, prices, V99 evidence, validation, holdout, Phase083, or 2026 selection data.

PASS_DATA_ONLY requires, independently for BOTH frozen chains: HTTP success; parseable daily observations; at least 95% of the 1,096 calendar days in the frozen window; first in-window observation no later than 2023-01-07; last no earlier than 2025-12-24; finite non-negative TVL values; no duplicate UTC dates after deterministic daily normalization; strictly increasing normalized dates; raw-payload SHA-256 recorded. Any failure => FAIL_DATA_NO_ALPHA and the exact Phase096 source/schema/chains are closed without source/chain/subset rescue.

A PASS_DATA_ONLY authorizes only a separately preregistered later hypothesis. It does NOT authorize inspecting same-run crypto returns or selecting sign/window/threshold/cadence/gross from Phase096 data.

## Gate preservation
Validation remains closed unless a future frozen training candidate passes. Final holdout remains untouched until training and validation pass and a candidate is formally frozen. V99 is excluded from V98 selection. No V16/V99 files/state/workflows/reports may be modified.

## Current decision
No champion exists. Phase095 is closed FAIL_DATA_NO_ALPHA. Phase096 is preregistered DATA_ONLY and awaits deterministic execution.