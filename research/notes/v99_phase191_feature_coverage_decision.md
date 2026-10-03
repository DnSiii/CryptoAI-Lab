# V99 Phase191 — feature coverage decision

Scope: DATA_ONLY. Economic trials opened: **0**.

Immutable source evidence: Phase191 snapshot SHA-256 `a83bb6ba52e22a33d0e3551cf915a7a0b3d6cb4894a0c66eb28c5ab444cd23af`, produced by the fixed TRAIN windows 17,000,000–17,000,199; 18,000,000–18,000,199; 19,000,000–19,000,199 for USDC and USDT. Offline replay was byte-identical twice before this audit.

## Feature-only coverage audit

The immutable snapshot contains 15,539 unique logs after deterministic identity deduplication. The observed issuer-native coverage is insufficient for an economic trial:

- USDC 17M: 0 native Mint/Burn logs.
- USDC 18M: 14 native logs (8 Mint, 6 Burn); zero-address Transfer reconciliation matches native Mint/Burn amounts.
- USDC 19M: 7 native logs (2 Mint, 5 Burn); zero-address Transfer reconciliation matches native Mint/Burn amounts.
- USDT 17M/18M/19M: 0 non-Transfer/non-Approval event logs in all three fixed windows, so the intended issuer-native Issue/Redeem component has no observed variation in this snapshot.

Decision: **REJECT BEFORE ECONOMIC TRIAL — insufficient issuer-native event coverage.** This is a data/feature identifiability rejection, not a PnL rejection. No price, return, benchmark, regime label, cost model, or holdout outcome was consulted.

## Additional causal caution

The current cumulative `t-1` feature resets running net flow to zero at each fixed window boundary. That is causal but it is a window-local level, not a chain-history cumulative level. It must not be silently interpreted as a globally identified cumulative issuance state. Any future level formulation requires preregistered warm-up/history; alternatively a strictly lagged impulse/rate formulation can be preregistered without an unknown initial level.

## Preregistered next step

Stay DATA_ONLY. Before any economic trial, test a scientifically distinct **issuer-native lagged impulse/rate** representation on broader, fixed TRAIN-only acquisition windows chosen without market outcomes. Require non-zero native coverage in each token/window intended for a combined USDC+USDT feature, immutable provenance, duplicate-identity=0, deterministic replay, and strict `t-1`. If those data gates fail, reject again without opening PnL. Holdout remains untouched.
