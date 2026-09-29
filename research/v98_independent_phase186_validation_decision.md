# V98 Independent — Phase186 untouched validation decision

Status: **REJECT_VALIDATION_NO_RESCUE / FINAL HOLDOUT REMAINS CLOSED**

## Confirmatory result

The preregistered Phase185 frozen WALCL 4-native-observation contraction 0.50 gate failed untouched validation over 2026-01-01 through 2026-07-31. No parameter, threshold, lookback, sign, multiplier, asset-specific setting, or rescue was searched after observing validation.

WALCL candidate base validation: total return **-9.0547%**, Profit Factor **0.85084**, max drawdown **-15.1058%**, payoff **0.90923**, win rate **48.34%**, 102 positive / 109 negative days. Severe return **-9.2756%** (PF 0.84723; MDD -15.2640%). Supersevere return **-9.6173%** (PF 0.84167; MDD -15.4931%). Mandatory failures were validation return <= 0, PF <= 1.02, severe return <= 0, and supersevere return <= 0.

## Independent failure audit

The failure is broad rather than a single-asset accident. Every asset contribution is negative: BTC -14.54%, ETH -17.78%, BNB -15.86%, XRP -27.27%, SOL -24.54% of aggregate negative contribution. Concentration is modest (mean top-1 weight share 21.22%, p95 22.24%; mean 5 active assets), so concentration does not explain the loss.

The regime decomposition identifies the main pathology: approximate return contribution is **+1.07% in bear**, **-0.38% in bull**, and **-9.55% in sideways**. The WALCL gate therefore did not generalize as a robust liquidity/risk-off overlay; most validation damage came from sideways conditions. Monthly results were negative in Jan (-1.69%), Feb (-3.95%), May (-0.37%), and especially Jun (-6.64%); Mar (+0.32%), Apr (+1.13%), and Jul (+1.77%) were positive but insufficient. Bottom-10 negative days account for 28.06% of negative mass and top-10 positive days for 33.42% of positive mass, not an isolated one-day failure.

The CONTROL was also negative (-9.0802%, PF 0.81294), while WALCL improved PF only modestly and did not create positive expectancy. This supports regime non-stationarity / insufficient independent edge rather than merely transaction-cost sensitivity; severe and supersevere costs worsen an already negative base result.

## Integrity and reproducibility

The workflow rebuilt canonical V98 validation-only data ending 2026-07-31 23:00 UTC and independently asserted all canonical timestamps were < 2026-08-01. The candidate used next-UTC-day WALCL availability, no same-day use, frozen Phase185 parameters, and no V16/V99 input. Two deterministic executions produced byte-identical report SHA256 `d6ee7d023f0495ef266298a8f30973afd71d15d01b21b9951ec617b2f2b4b7ad`; positions SHA256 for the WALCL variant was `ebb09df97c717371aa1ce5b616dd04395ffa789546d3ea8d9fc0677ac190e962`.

## Decision

**REJECT_VALIDATION_NO_RESCUE.** Phase185 is no longer eligible for promotion to final holdout. The final holdout beginning 2026-08-01 remains unopened. No final-holdout workflow should be created for this candidate.

The scientifically justified next step is a new training-only, orthogonal hypothesis family, preregistered before any new candidate evaluation. Validation observations above may be used only as failure diagnosis, not to tune a WALCL rescue or optimize specifically for 2026 validation regimes.