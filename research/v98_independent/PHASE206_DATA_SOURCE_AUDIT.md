# V98 Independent — Phase206 funding source audit

Date: 2026-10-01
Scope: V98 Independent only. Validation/final holdout remains unopened.

## Observed failure

Workflow run 36894852391 failed during the first training-only funding acquisition request. GitHub-hosted runner received HTTP 451 from `https://fapi.binance.com/fapi/v1/fundingRate`. No snapshot was produced, no funding observations were inspected, and no Phase206 parameter/result was changed.

This is an infrastructure/geographic-access failure, not scientific evidence for or against Phase206. Retrying the identical Binance endpoint on the same runner is not considered useful research.

## Independent source audit

A scientifically acceptable fallback must provide *realized historical perpetual funding*, timestamped at settlement, without interpolation/imputation, and must support strict cutoff `< 2026-01-01T00:00:00Z`.

Two public exchange families satisfy the semantic requirement in their official documentation:

1. Bybit V5 `GET /v5/market/funding/history`: returns `fundingRate` and `fundingRateTimestamp`, supports linear perpetuals, `endTime`, and up to 200 observations/request.
2. OKX V5 `GET /api/v5/public/funding-rate-history`: returns historical perpetual funding including `fundingTime` and realized-rate semantics; official historical-data catalogue states funding history is available from March 2022.

Exchange substitution is a material data-source change. Therefore it must be frozen before any values are inspected and must not be selected based on Phase206 performance.

## Frozen fallback protocol

Priority is fixed *before data inspection*:

1. Try Bybit linear USDT perpetual realized funding for BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT.
2. If and only if Bybit is inaccessible or lacks the required historical coverage for any frozen symbol, try OKX USDT perpetual funding for the corresponding five assets.
3. If neither source yields complete causal training coverage, Phase206 is marked DATA_UNAVAILABLE and is not backtested. No synthetic funding, forward fill, interpolation, proxy rate, or V99-derived data is permitted.

Required acquisition/audit invariants:

- request only timestamps `< 2026-01-01T00:00:00Z`;
- preserve raw settlement timestamps/rates;
- reject duplicate/non-monotonic timestamps;
- report cadence/gaps rather than imputing them;
- record source/exchange and retrieval timestamp;
- acquire twice independently and require identical canonical data hashes;
- run an independent firewall audit before evaluator execution;
- Phase206 hypothesis/grid/gates remain exactly as preregistered.

## Decision

Binance acquisition path: **INFRASTRUCTURE_REJECTED_HTTP451**.
Phase206 hypothesis: **STILL PREREGISTERED / NOT EVALUATED**.
Champion: unchanged.
Holdout: unopened.
