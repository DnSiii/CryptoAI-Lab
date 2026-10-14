# V98 Independent Phase259 — Network-Security Expansion Sleeve

Status: **PREREGISTERED BEFORE PHASE259 PNL**.

## Architecture role

Phase259 tests a new exogenous **Network-Security Expansion Sleeve** on top of the frozen Phase252 partial V98 engine.

Frozen baseline is unchanged:
- Growth Core primitive: +0.25 BTC/ETH/BNB/SOL continuously.
- Phase252 Opportunity Sleeve: +0.0625 each when the frozen 168h mean funding condition is <= 0.
- baseline gross = 1.00 or 1.25.

Phase259 uses only the Phase258 PASS_DATA_ONLY Bitcoin hashrate series. It does not modify the Phase252 rule.

## Frozen economic hypothesis

Sustained expansion in Bitcoin network hashing power reflects increasing committed infrastructure/security and can mark a constructive crypto risk environment. The signal is intentionally slow and uses only completed prior-day network data.

At each 23:00 UTC decision on trading day t:

1. Let D = calendar day t-1, the latest fully completed UTC day.
2. Deterministically forward-fill only the Phase258 missing dates, with a maximum allowed gap of 3 days. No interpolation.
3. recent_hashrate = simple mean of the 30 completed daily observations ending at D.
4. prior_hashrate = simple mean of the preceding 30 completed daily observations.
5. NETWORK_EXPANSION is ON iff recent_hashrate > prior_hashrate.
6. If ON, add +0.0625 to each Clean-4 asset = +0.25 gross.
7. If OFF or fewer than 60 completed daily observations exist, the sleeve is flat.
8. Add the sleeve to frozen Phase252 without changing Phase252 positions.
9. Decision after 23:00 close executes at next 00:00 open and persists until the next daily decision.

Integrated gross cap = 1.50.

## Frozen constants

- source = exact Phase258 normalized hashrate CSV
- recent window = 30 completed days
- prior window = immediately preceding 30 completed days
- threshold = recent mean > prior mean (zero growth boundary)
- sleeve = +0.0625 per asset / +0.25 total gross
- decision hour = 23:00 UTC
- no alternate smoothing, window, threshold, direction, asset subset, sleeve size, price confirmation, funding interaction, regime condition or post-result rescue

## Frozen comparator

Exact frozen Phase252 architecture on identical Clean-4 price/funding data and execution.

## Promotion gate

Phase259 becomes **NETWORK_SECURITY_EXPANSION_CANDIDATE** only if all are true:

1. BASE integrated return > Phase252 BASE return by >=5% relative.
2. BASE CAGR > Phase252 CAGR.
3. BASE daily PF >= Phase252 PF.
4. BASE max DD is not worse than Phase252 by >5 percentage points.
5. BASE worst day >= -20%.
6. marginal calendar return versus Phase252 positive in at least 2/3 folds.
7. no calendar fold underperforms Phase252 by >10 percentage points.
8. SEVERE integrated return > Phase252 SEVERE return.
9. SUPERSEVERE integrated return > Phase252 SUPERSEVERE return.
10. at least 100 active decision-days in training.
11. no ruin.
12. max open gross <=1.500000001.
13. max absolute asset contribution share <=70%.
14. top-10 absolute daily-return concentration <=45%.
15. deterministic rerun produces byte-identical result.

Failure => **REJECT_NETWORK_SECURITY_EXPANSION_NO_RESCUE** for this exact 30d-vs-prior30d / +0.25 gross rule. No window/threshold/sign/gross rescue.

Validation/holdout remain locked. V14/V15/V99 remain unused.
