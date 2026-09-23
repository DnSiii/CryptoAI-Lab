# V98 Independent Phase114 — Fear & Greed extremes regime

CONDITIONAL PRE-REGISTRATION, created after Phase113 PASS_DATA_ONLY and before inspecting any Phase113 value descriptives or any Phase114 PnL.

Activation condition: Phase113 must remain PASS_DATA_ONLY under the frozen Alternative.me Fear & Greed source/coverage rules. Otherwise Phase114 is void.

Economic hypothesis: sentiment extremes can proxy crowded positioning and forced-risk behavior. Extreme Fear should have positive subsequent contrarian expectancy, Extreme Greed negative subsequent expectancy, while the broad middle is intentionally untraded to avoid converting this into generic crypto beta.

Frozen design:
- source: exactly Phase113 Alternative.me Fear & Greed endpoint;
- daily observation: deterministic last valid observation of each completed UTC day;
- strict lag: trading day D uses only the value from D-1;
- thresholds: <=25 Extreme Fear; >=75 Extreme Greed; 26..74 neutral. These are conventional semantic boundaries, frozen ex ante; no threshold search;
- fixed basket: BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT;
- Extreme Fear: equal-weight LONG basket, total gross 0.75;
- Extreme Greed: equal-weight SHORT basket, total gross 0.75;
- neutral: flat;
- rebalance/re-evaluate once daily at 00:00 UTC;
- no smoothing, hysteresis, duration rule, leverage search, stop, asset subset, weighting search, combination with Phase112, or rescue.

Training: frozen 2023/2024/2025 folds only. Validation remains closed. Phase083/opened holdout and reserved 2026-09-16→2026-10-15 forward holdout are forbidden. V16/V99 excluded.

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
10. all three states (fear, neutral, greed) must occur in training; otherwise the hypothesis is not identified.

Report equal-weight always-long 0.75 under identical execution/cost/funding assumptions as context only. It must not be used to retune the rule.

Any failed mandatory gate => REJECT_NO_RESCUE. PASS_TRAINING may authorize only a separately preregistered validation.