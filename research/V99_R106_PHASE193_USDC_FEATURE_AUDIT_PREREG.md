# V99 R106 Phase193 USDC native feature audit preregistration

Status: PREREGISTERED, DATA_ONLY, economic_trials=0.

Phase192 rejected the combined USDC and USDT family before economic testing because USDT native coverage was absent in two frozen TRAIN-only windows. Phase193 audits USDC alone without changing windows or using market outcomes.

Immutable rules:
- Do not modify V16 Frozen or V99 Frozen.
- Reuse Phase192 snapshot SHA256 de5a6303170e71e0576a4fe7ec66b7094f131bee3ca7b8aaf3dcc95c65799aaa.
- Keep windows 16950000-17050000, 17950000-18050000, 18950000-19050000.
- Admit only USDC native Mint and Burn events.
- No price, PnL, regime outcome, benchmark, costs, direction, threshold, holdout, or trading-rule input.
- economic_trials remains zero.

Fixed diagnostics:
1. deterministic identity and ordering;
2. Mint/Burn counts and signed amount in four equal block-position subfolds per window;
3. inter-event gap median, p95 and max;
4. amount median, p95, p99, max and top-event share;
5. transaction concentration and same-transaction collisions;
6. fixed UTC clock diagnostics at 1h, 4h and 24h;
7. deterministic rebuild SHA256.

USDC uses six decimals and signed impulse equals Mint amount minus Burn amount. Clock boundaries are source diagnostics only.

Causal handoff: any later decision-bar feature must use only fully closed source intervals available before the decision bar, preserving t-1. Passing this audit is not evidence of alpha and cannot promote V99.
