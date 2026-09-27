# V99 R106 Phase165 — Open-Interest DATA-only audit

Status: **PREREGISTERED BEFORE ANY Phase165 PnL**.

## Scientific reason
Phase159–164 exhaust the preregistered funding-only mechanisms tested so far and all TRAIN alpha variants were rejected. Phase165 therefore changes the information source rather than rescuing funding parameters: futures **open interest (OI)**, a positioning/crowding quantity orthogonal to funding-rate level/breadth.

## Scope and contamination firewall
- DATA ONLY. This phase MUST NOT compute returns, PnL, PF, drawdown, alpha selection, direction selection, thresholds, or inspect holdout outcomes.
- TRAIN interval is inherited exactly from the Phase159 data contract (`START`, `END`). No post-TRAIN observations may participate in feature construction or source selection.
- Frozen V16 and Frozen V99 are read-only and must not be modified.
- Symbols fixed ex ante: BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, DOGEUSDT.

## Source contract
Primary source: Binance public futures historical data (deterministic archive/static source where available), not an endpoint requiring geographic API access. Native timestamps and native OI values are retained; no interpolation across missing source records.

## DATA gates
For each symbol report: first/last native timestamp, row count, duplicate timestamps, monotonicity, non-finite/non-positive OI count, and TRAIN-only coverage on the source's native cadence. Cross-symbol aligned coverage must also be reported.

PASS_DATA_ONLY requires all five symbols to have monotonic unique timestamps, zero invalid/non-positive OI after parsing, and >=90% individual TRAIN coverage plus >=85% cross-symbol coverage at the declared native cadence. If the public archive cannot satisfy this without changing source semantics, return FAIL_DATA_ONLY and do not compute PnL.

## Future hypothesis (not authorized in this phase)
Only after PASS_DATA_ONLY may a later separately preregistered phase test whether causal OI expansion/contraction contains incremental information. Direction, normalization, execution lag, costs, temporal folds and downstream gates must be frozen in that later preregistration before any PnL is observed.
