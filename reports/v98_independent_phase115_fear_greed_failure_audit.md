# V98 Independent Phase115 — Phase114 failure audit and next-family preregistration

## Phase114 decision

Phase114 is frozen as `REJECT_NO_RESCUE`. No threshold, direction, gross, basket, duration, smoothing, hysteresis, or combination rescue is permitted.

Observed training evidence from the preregistered Phase114 rule:
- aggregate return +5.87%, daily PF 1.0656, max drawdown -40.16%;
- 2023 +6.36%, PF 8.58, but only 7 non-zero days;
- 2024 -29.88%, PF 0.7463;
- 2025 +41.94%, PF 1.6449;
- severe +0.34%, PF 1.0363; supersevere -7.24%, PF 0.9948;
- SOL accounts for 44.77% of absolute asset-contribution proxy, immediately below the frozen 45% concentration ceiling;
- top-10 absolute-day share 17.60%, so daily-tail concentration itself was not the binding failure;
- regime return-sum proxy: bear +0.200, sideways +0.271, bull -0.337.

Mandatory failures were aggregate PF, max DD, 2024 return/PF, and supersevere stress. The failure mechanism is therefore broad temporal/regime instability plus friction sensitivity, not a single isolated tail. The very sparse 2023 activation and near-limit SOL contribution add fragility. No validation or holdout is authorized.

## Scientific disposition

The Fear & Greed threshold family is closed for V98 selection after this rejection. Phase114 values may be used only to understand why that exact preregistered candidate failed; they must not be used to tune another Fear & Greed threshold/direction variant.

## Next orthogonal family — Phase116 DATA_ONLY preregistration

Before any values, descriptives, alpha, or PnL are inspected, test feasibility of a genuinely orthogonal external macro-liquidity feature: daily U.S. Dollar Index (DXY) observations from a public authoritative/traceable source, restricted to completed UTC dates in training 2023-01-01 through 2025-12-31.

Phase116 is DATA_ONLY. It may report only source/schema/integrity metadata, coverage, first/last usable date, duplicate/missing/invalid counts, canonicalization rule, and payload/file SHA256. It must not expose DXY values or value descriptives, compute returns/changes/correlations, join crypto prices, compute alpha/PnL, inspect validation/holdout, or perform parameter search.

Required activation gate: deterministic source access; >=95% coverage of expected business-day observations over 2023-2025; no invalid/non-finite records after canonicalization; no post-canonical duplicate date; source and payload hash recorded. Failure => `REJECT_DATA_SOURCE` and move to a different orthogonal family, with no source-shape rescue that changes economic meaning.

If and only if Phase116 passes DATA_ONLY, a directional trading hypothesis must be separately preregistered before inspecting any DXY value distribution or any crypto PnL. V16 and V99 remain excluded. Validation and all holdouts remain closed.