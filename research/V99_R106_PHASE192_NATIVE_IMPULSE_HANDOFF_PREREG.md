# V99 R106 Phase192 — native impulse post-coverage handoff preregistration

Status: PREREGISTERED / DATA_ONLY. This document is written while Phase192 acquisition is incomplete and before any economic result from this data family is inspected.

## Immutable boundary

- V16 Frozen and V99 Frozen remain immutable.
- Phase192 remains `economic_trials = 0` until native-event coverage and deterministic replay pass.
- The three chain-position windows and four issuer-native event topics already frozen in `research/tools/v99_phase192_native_impulse_coverage.py` are not changed by this handoff.
- No holdout, price, PnL, regime outcome, benchmark result, cost result, direction, threshold, or trading-rule selection may influence source acceptance or the feature-only audit below.

## Why this step is scientifically distinct

Phase192 asks only whether issuer-native USDC mint/burn and USDT issue/redeem events have sufficient TRAIN-only source coverage. If coverage passes, the next question is not whether the events make money. It is whether a causal, reproducible event-flow feature can be constructed without hidden timing, concentration, or missingness pathologies.

## Mandatory feature-only audit after source acceptance

Build an issuer-specific event table from the immutable accepted snapshot and report, before any economic trial:

1. canonical event identity and deterministic ordering;
2. event counts and signed native-flow counts by token, event type, preregistered window, and chronological subfold;
3. inter-event-time distribution and burst/tail concentration;
4. concentration of observations by block interval and transaction identity;
5. missing/zero-activity intervals under a fixed clock aggregation declared before price is joined;
6. availability lag: a feature used for decision bar `t` must contain only events demonstrably available by the causal `t-1` cutoff;
7. sensitivity to deterministic aggregation boundaries (clock alignment only, not economic outcomes);
8. byte-identical rebuild from the same snapshot plus persisted snapshot SHA256 and feature-table SHA256.

Any ambiguous timestamp/ordering, unexplained source concentration, nondeterministic rebuild, or inability to enforce `t-1` keeps this family quarantined.

## Preregistered feature family

Only issuer-native net impulse is admitted initially: USDC mint minus burn and USDT issue minus redeem, with token-level components retained for attribution. Aggregation/lookback candidates must be fixed from TRAIN-only source cadence diagnostics before any holdout or economic result is opened. Transfer/approval traffic is excluded. No post-hoc event family expansion is allowed inside this trial.

## Economic hypothesis gate — remains closed

Only after the feature-only audit passes may one preregister a single economic hypothesis. That later hypothesis must use chronological TRAIN-only selection, temporal folds, causal `t-1` execution, untouched holdout, severe and supersevere costs, the full BULL/BEAR/SIDEWAYS × HIGH/LOW volatility matrix, benchmark-envelope comparison, reproducibility checks, and concentration/tail diagnostics.

The intended scientific question is whether issuer-native stablecoin supply impulse adds orthogonal information to the rebuilt all-regime architecture, especially the Carry/Positioning sleeve. This is a hypothesis direction, not a promotion claim. Failure at any gate rejects or quarantines the feature; thresholds must never be changed because of holdout behavior.

## Current transport failure mechanism

Repeated Phase192 attempts have progressed through append-only checkpoints but terminate on HTTP 429 from the public source. This is a transport limitation, not evidence for or against the economic hypothesis. Partial snapshots may only reduce future network work; they cannot be treated as accepted evidence until acquisition completes and deterministic zero-network replay passes.
