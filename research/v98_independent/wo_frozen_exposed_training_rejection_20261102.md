# V98 Independent WO — frozen multiscale seven-slot exposed-training rejection (2026-11-02)

**Decision: REJECT_WO_EXPOSED_TRAINING. NO RETUNING, SIGN/WINDOW/THRESHOLD/GROSS RESCUE.** WO asynchronous monthly/weekly/daily inventory was preregistered **before** implementation and PnL at commit `d26cdfa56383cacf54791ae583f6def41bbd3e13`. It is not a continuation or cosmetic modification of rejected WN/WL/WG.

## Complete measured physical experiment
[GitHub Actions run 41531790519](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41531790519), code commit `6c7e84343abc7904c06a7b814c946d7e6c46787d`, immutable artifact **13182432598**, artifact ZIP SHA256 **662054d351ce01cd082ddf045a6b832f6579e7e0bf0949620bacf21c934df66c**. Source: official SHA-pinned Clean-4 USD-M 1h prices and native funding, 27,048 hours, Dec-2022 warmup plus 2023–2025 exposed training, 13,524 native funding events. All four assets only; 1,096 daily decisions. Sleeve incidence: Growth 1,096, Opportunity 644, Relative Value 819, Stress/Recovery 30. Causal synthetic future mutation passed.

**30/30** five-book x three illustrative one-way cost tiers 10/20/35bps x two funding/fill orders completed the physical history without simulated gross, cash, or intrahour survival breaches. These are **simulated exposed-training returns**, not authenticated account-executable returns.

| Tier, carried-before-fill | Simulated CAGR | Max drawdown | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| Base 10bps | **+14.3333%** | -41.79% | +11.22% | **-6.11%** | +43.12% |
| Severe 20bps | **+11.3145%** | -42.87% | +8.60% | **-8.69%** | +39.10% |
| Supersevere 35bps | **+6.9320%** | -44.45% | +4.78% | **-12.44%** | +33.28% |

**Ten preregistered economic gates failed**: four CAGR targets, two negative-year gates, and four Stress/Recovery negative marginal contribution gates. The Stress/Recovery sleeve reduced complete-portfolio log growth in base and severe under both funding/fill orders. Opportunity and Relative Value contributed positively in base and severe; they are **diagnostic ablations only** and are not approved standalone or salvage candidates. No module tuning after seeing PnL. All WO candidates rejected, no V98 champion.

## Independent accounting and physical governor
Separate read-only hourly cash/funding replay reconciled **27,048** hourly ledger rows; base carried-before-fill terminal cash/equity **USD 14,945.78377589842** from USD 10,000, illustrative fees/spread/impact **USD 800.8816156527067**, signed native funding under conservative mark envelope **-USD 814.5697918634542**, maximum arithmetic difference **1.1e-11**. Deliberate cash tampering **detected**. The funding-buffer governor actually trimmed **three** times in the full historical base simulation. This demonstrates internal arithmetic and exercised simulated risk controls, not independent economic validation or exact exchange liquidation safety.

## Remaining delivery blockers and preserved boundaries
Original 13,524 exchange-origin settlement `markPrice` events with independently auditable raw transport/custody are absent. Prior official Binance USD-M historical `/fapi/v1/fundingRate` calls from hosted Linux and macOS runners returned HTTP 451, and alternate official transports returned empty HTTP 202. Obtain an **authorized exchange-origin export** with `symbol,fundingTime,fundingRate,markPrice`, raw response bodies, original URLs/headers, UTC retrieval times and SHA256; reconcile independently to the pinned rates. Additionally need account-dated maker/taker fees, historical executable bid/ask/depth/impact at intended size, collateral/liquidation rules, untouched chronological validation and clean future holdout. The conservative hourly mark envelopes and 10/20/35bps tiers are proxies, not execution proof.

No 2026+ training, quarantined XRP, Phase083, external V14/V15/V99 benchmark internals, V16/V99 Frozen, paper or live state touched. No real trading authorized. **Next:** pursue a genuinely distinct high-growth seven-slot economic mechanism; do not reuse WO parameters/ablation results to select or rescue a new candidate.
