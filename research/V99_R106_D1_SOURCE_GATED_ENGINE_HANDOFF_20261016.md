# V99 R106 D1 — source-gated distinct spot/perp carry (2026-10-16)

Status: PRE_ECONOMIC_SOURCE_GATED / DATA_ONLY / HOLD / NO PROMOTION. No D1 historical PnL, validation, holdout, paper, or orders are authorized. C1/C2 and prior R106 candidates remain permanently rejected; their historical accounting is quarantined pending corrected self-financing replay.

Scientific hypothesis: long OKX BTC/ETH spot paired with short same-asset OKX perpetual, earning positive settled funding net of four leg fills, basis risk, borrow/collateral/margin and tail costs. Not a trend/Donchian/C1/C2 retune. Economic benefit remains unknown.

TRAIN: all market observations < 2023-10-01 UTC. Sealed validation [2023-10-01,2024-01-18); final holdout >=2024-01-18. Historical R106 holdout diagnostics were previously accessed; that lineage is not a clean final test. No training on or peeking into either future partition.

Ex-ante fixed design: at 00:00 UTC, use only t-1 or earlier 168 hourly paired bars and 3 already-announced and already-settled OKX funding fixes. Each BTC/ETH pair enters at spot +0.25 NAV / perp -0.25 NAV only if all 3 fixes are positive, projected 24h funding (3 x average fix) > 2 x 4 x stressed per-leg cost, and |perp/spot basis| < 1%; otherwise cash. Severe cost 7 bps/leg and supersevere 14 bps/leg are modeling shocks, NOT exchange-native fees. Basis divergence >=1.5% forces risk exit. Maximum gross two-asset four-leg notional = 1.0 NAV. No parameter tuning after historical economics.

Hard gates before first historical trial: authenticated first-party OKX spot/perp synchronized hourly TRAIN prices and instrument contract specifications; exchange-published funding fixing times and rates; historical native fee tier and tier validity; trade-level fill assumptions, slippage, collateral and liquidation constraints; self-financing share/contract/cash and margin ledger; deterministic independent oracle. Merely labeling fabricated rows 'OKX' is not provenance. Missing proof fails closed; separate modeled funding from actual account-settled receipts.

A complete single D1 TRAIN trial must report 5 chronological folds, 3x2 regimes, 2 cost shocks, true trade and hourly PF, maximum DD, tail concentration, remove-best-day, benchmarks cash/passive BTC/equal BTC-ETH/carry-no-carry, and independent byte-identical replay. Necessary pass gates: positive severe and supersevere ROI, >=4/5 severe and >=3/5 supersevere positive folds, PF>1 both, remove-best-day ROI>0 both, supersevere max DD <=35%, regime/tail diversification and benchmark superiority. Never use synthetic success or Actions green as promotion.

Never alter V16 Frozen, V99 Frozen, paper-results, legacy champion, or prior rejection evidence. No orders. Next: integrate a read-only source-integrity and self-financing test workflow, then obtain native OKX historical paired/funding/fee evidence before running a single economic TRAIN.
