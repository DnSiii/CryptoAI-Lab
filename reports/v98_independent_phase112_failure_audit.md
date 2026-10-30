# V98 Independent Phase112 — independent failure audit

Decision: **REJECT_NO_RESCUE**. This audit is post-decision and may not be used to retune Phase112.

## Evidence
- Aggregate BASE was strong (+278.43%, daily PF 1.208), but the frozen mandatory gates were conjunctive.
- Max drawdown was -35.349%, narrowly beyond the preregistered -35% floor.
- 2025 failed independently: return -7.00%, daily PF 0.9995, versus frozen requirements return > 0 and PF > 1.02.
- 2023 and 2024 were positive (+70.22%, +136.55%; PF 1.281 and 1.366), so the failure is temporal instability, not absence of historical profitability.
- Severe/supersevere remained profitable (+252.85% / +212.10%, PF 1.198 / 1.181), so friction is not the primary failure mechanism.
- Stress state occurred on only 15 daily observations versus 1,077 healthy observations. The hypothesized peg-stress switch is therefore extremely sparse; in 2025 turnover was only 0.0356 and the strategy behaved almost entirely as a long risk basket.
- Asset contribution was not pathologically concentrated: largest absolute share SOL 34.77% < 45% gate. Top-10 absolute-day share 5.89% < 60% gate.
- Tail risk remained material: worst day -11.29%, CVaR5 -4.79%, and aggregate DD breached the gate despite acceptable concentration.
- The always-long context benchmark returned +59.81% with -41.07% DD. Phase112 improved aggregate return and DD, but failed the frozen robustness requirement because its benefit did not persist through 2025.

## Causal interpretation
The stablecoin peg signal is too sparse to identify a reliable all-regime directional edge. Most exposure is effectively persistent long crypto beta, and the rare stress reversals do not repair the 2025 regime. Changing threshold, duration, stablecoin subset, sign, smoothing, gross, or basket after seeing this result would be rescue tuning and is forbidden.

## Integrity
Validation and final holdout remain unopened. V16/V99 were not used. No parameter search or rescue is authorized. Phase112 is permanently rejected under this specification.
