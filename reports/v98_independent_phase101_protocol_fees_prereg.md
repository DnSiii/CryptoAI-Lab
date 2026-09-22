# V98 Independent Phase101 — Aggregate protocol-fees regime preregistration

Status: **PREREGISTERED / TRAINING ONLY / FROZEN BEFORE PNL**.

Phase100 passed DATA_ONLY with complete 2023-2025 coverage. Phase101 is the one allowed alpha test for this source/schema. No parameter search or rescue is allowed.

Frozen source: DefiLlama aggregate protocol fees `overview/fees.totalDataChart`. Frozen signal: daily aggregate protocol-fee sum, strict prior UTC day availability; compare the most recent completed 7 calendar days with the immediately preceding non-overlapping 7 days. At 00:00 UTC, long the fixed equal-weight BTCUSDT/ETHUSDT/BNBUSDT/SOLUSDT/XRPUSDT basket when recent fees are greater than prior fees; short the same basket when lower; flat only when unavailable/equal. Gross exposure 0.75; daily rebalance. The signal is causal via a mandatory one-day lag.

Frozen training window/folds and cost/funding definitions come unchanged from `config/v98_independent.json`. Evaluate BASE plus severe and supersevere friction, chronological folds, regime metrics, concentration/tails, max drawdown, daily Profit Factor, payoff, win rate and positive days. Reproducibility must include raw-source, targets and preregistration SHA-256.

Frozen training gates: aggregate return > 0; aggregate daily PF > 1.10; max drawdown >= -35%; every chronological training fold return > 0; severe and supersevere each return > 0 and daily PF > 1.0; single-asset absolute contribution <=60%; top-10 absolute-day contribution <=60%. Any failure => **REJECT_NO_RESCUE** for this source/schema/direction/window/basket/gross/cadence family.

No Phase083 selection use, validation, final holdout, 2026 selection data, V99/V16 evidence, threshold/window/direction/gross/basket search, or same-family rescue. PASS_TRAINING authorizes only a separately preregistered validation gate.