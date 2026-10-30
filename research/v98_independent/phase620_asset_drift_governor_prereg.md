# V98 Independent Phase620 — Per-asset close-drift governor contract (preregistered)

Branch: `research/v98-independent-zero`. Scope: V98 Independent only; source-free execution accounting. No V16/V99, external engines, holdout or 2026+ training.

## Defect and causal hypothesis

Phase618 synthetic gap tests demonstrate that an asset with open weight 0.69 can close above the 0.70 asset ceiling while gross exposure remains below 1.45. Phase592/486 currently arm next-open correction only when *gross* close weight exceeds 1.45, leaving an isolated per-asset close breach uncorrected if the signal is unchanged. This is an execution-governor omission, not an alpha signal.

## Frozen, pre-result correction

At each close, record both realized gross and maximum per-asset weights. At the next open, if **either** previous-close limit was breached, execute a causal rebalance even when the requested target has not changed. For a guard-only rebalance, scale current open positions proportionally by `min(1, 1.45/gross, 0.70/max_asset)`; do not rotate or add risk. Respect existing no-trade masks, fees and funding orders; impossible fills reject. Do not change any target, growth allocation, costs, market data, or selection threshold.

## Acceptance and anti-rescue

Source-free tests must prove: (1) per-asset-only close drift causes next-open remediation, (2) no previous breach means no gratuitous rebalance, (3) all pre-breach decisions remain identical under a future shock, (4) impossible locked remediation fails closed, (5) no asset or gross open-cap violation, (6) existing Clean-4 source-only path geometry remains unchanged because Phase618 found zero close asset breaches. Run both kernels' regressions and publish a reproducible delta. No historical PnL, promotion or benchmark comparison is authorized until official funding is independently attested and chronological gates pass.
