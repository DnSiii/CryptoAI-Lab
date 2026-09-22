# V98 Independent Phase112 — stablecoin confidence regime

CONDITIONAL PRE-REGISTRATION, created while corrected Phase111 remains DATA_ONLY and before any Phase111 price descriptives or Phase112 PnL are inspected.

Activation condition: Phase111 must finish PASS_DATA_ONLY under the already frozen USDT/USDC source and coverage rules. Otherwise Phase112 is void and must not run.

Economic hypothesis: a material deviation of a major USD stablecoin from its $1 peg is a systemic crypto liquidity/credit-stress event. A simple market-direction regime should therefore be risk-on when both major stablecoins are tightly pegged and risk-off when either completed prior UTC day shows a clear peg break.

Frozen design:
- source: exactly the Phase111 DefiLlama stablecoin metadata/history endpoints;
- frozen stablecoins: USDT and USDC only;
- stablecoin daily observation: deterministic last observation of each completed UTC day;
- strict information lag: trading day D uses only stablecoin prices through D-1;
- stress statistic: max(abs(USDT - 1.0), abs(USDC - 1.0));
- single threshold: 0.005 (50 bps), chosen ex ante as a material peg deviation rather than normal tracking noise;
- no alternate threshold, sign, smoothing, hysteresis, duration requirement or stablecoin subset;
- fixed crypto basket: BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT;
- healthy regime (stress <= 0.005): equal-weight LONG basket, total gross 0.75;
- stress regime (stress > 0.005): equal-weight SHORT basket, total gross 0.75;
- rebalance/re-evaluate once daily at 00:00 UTC;
- no leverage search, stop, regime mask, asset subset, weighting search or rescue.

Training: frozen 2023/2024/2025 folds only. Validation remains closed. Phase083/opened holdout and the reserved 2026-09-16→2026-10-15 forward holdout are forbidden. V16/V99 excluded.

Mandatory gates:
1. aggregate BASE return > 0;
2. aggregate BASE daily PF > 1.10;
3. aggregate max DD >= -35%;
4. worst day >= -12%;
5. every 2023/24/25 fold return > 0 and daily PF > 1.02;
6. severe and supersevere return > 0 and daily PF > 1.00;
7. largest absolute asset contribution share <= 45%;
8. top-10 absolute daily return concentration <= 60%;
9. max open gross <= 0.750000001;
10. both healthy and stress observations must exist in training; otherwise the regime hypothesis is not actually identified and is REJECT_NO_RESCUE.

Report an equal-weight always-long 0.75 benchmark under identical execution/cost/funding assumptions as context only; it must not be used to retune the rule after results.

Any failed mandatory gate => REJECT_NO_RESCUE. PASS_TRAINING may authorize only a separately preregistered validation.
