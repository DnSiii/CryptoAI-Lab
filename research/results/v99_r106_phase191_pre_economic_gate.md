# V99 R106 — Phase191 pre-economic admission gate

Scope: DATA_ONLY. No price, PnL, regime return, benchmark return, or holdout values may be read by this gate.

## Frozen admission criteria

Phase191 remains pre-economic. A stablecoin-flow hypothesis may be preregistered only after all of the following are demonstrated on TRAIN-era finalized Ethereum windows:

1. Canonical contracts only: Ethereum USDC proxy `0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48` and USDT `0xdAC17F958D2ee523a2206206994597C13D831ec7`.
2. Issuer-specific semantics: USDC native Mint/Burn, independently reconciled to zero-address Transfer; USDT native Issue/Redeem, never inferred from zero-address Transfer.
3. Immutable provenance persisted: block number/hash, tx hash, log index, contract, raw amount, event type, block timestamp.
4. Finality fixed ex ante: only finalized blocks are admissible. A reorg/conflicting block hash or duplicate log identity fails closed.
5. Determinism: identical input event set must produce byte-identical normalized output and summary.
6. Historical boundary: Ethereum-native flow only. No claim of global stablecoin supply/liquidity; no current metadata used to decide historical inclusion.
7. Coverage: sampled TRAIN-era windows must contain enough native events to test reconciliation and continuity. Missing archive history, RPC truncation, or ambiguous proxy/implementation history fails closed.

## Anti-overfit firewall

Stablecoin economic trial count remains zero. No threshold, lookback, direction, position size, regime filter, benchmark comparison, or economic gate is chosen until the DATA_ONLY admission evidence passes and one hypothesis is preregistered. Phase190's PIT failure is not reused as an economic observation.

## Next deterministic action

Run the provenance invariant gate plus a real finalized-log coverage collector on multiple separated TRAIN-era windows. If source/proxy/archive coverage is ambiguous, close Phase191 pre-PnL. If it passes, preregister exactly one causal t-1 hypothesis before any economic evaluation.
