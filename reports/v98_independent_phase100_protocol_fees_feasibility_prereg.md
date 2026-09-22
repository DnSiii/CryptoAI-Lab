# V98 Independent Phase100 — Aggregate protocol-fees feasibility preregistration

Status: **PREREGISTERED / DATA ONLY / NO ALPHA / NO PNL**.

Phase099 is **REJECT_NO_RESCUE**. It produced +86.08% aggregate, PF 1.1104 and positive severe/supersevere returns, but violated the frozen max-drawdown gate (-53.16%) and the 2025 chronological fold (-35.36%). The DEX-volume family is closed: no sign/window/threshold/basket/gross/cadence/regime/source/cost rescue.

Phase100 opens a new data-feasibility class: aggregate DeFi protocol fees, representing realized user-paid on-chain economic activity rather than TVL capital stock, stablecoin supply, DEX notional volume, sentiment, price or derivatives positioning. No alpha/PnL/crypto-price join is allowed in Phase100.

Frozen source: DefiLlama public API endpoint `https://api.llama.fi/overview/fees?excludeTotalDataChartBreakdown=true&excludeTotalDataChart=false`. Frozen dataset: aggregate fees `totalDataChart`. Frozen window: 2023-01-01 through 2025-12-31 UTC.

PASS_DATA_ONLY requires HTTP success; parseable daily observations; >=95% of 1,096 calendar days; first <=2023-01-07; last >=2025-12-24; finite non-negative values; zero duplicate UTC dates after deterministic normalization; strictly increasing dates; raw SHA-256. Any failure => FAIL_DATA_NO_ALPHA and exact source/schema closed without endpoint/provider/schema rescue.

PASS_DATA_ONLY authorizes only a separately preregistered later hypothesis. No V99/V16 evidence, Phase083 selection, validation, holdout, 2026 selection data, or same-run direction/window/threshold/gross search.