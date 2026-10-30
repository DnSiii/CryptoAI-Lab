# V98 Independent — Phase219 postmortem

Decision: **REJECT_FAMILY_NO_RESCUE**.

## Mechanical evidence
- Workflow run 37083365934 completed successfully.
- Training-only firewall `<2026-01-01` passed for prices and funding.
- Static preregistration/causality invariants passed.
- Two independent executions produced the same report SHA256: `1bf3e13e624b86a359eabb9d872e2d82e2d22ae81906c36365b289854e47b54b`.
- Exactly 8 preregistered specs were evaluated on chronological folds 2023, 2024, 2025.
- Mechanical gate: `training-fold coherent specs: []`. No spec had base return > 0 and PF > 1 in all three folds.
- Severe and supersevere return monotonicity assertions passed for every spec/fold.

## Failure-mechanism audit
A representative frozen spec (`fund_L270_Z15_hold4`) illustrates why the family is not robust. In 2023 base it returned +9.45% with PF 1.0266, MDD -38.68%, payoff 1.1381 and 25.21% positive days, but severe costs already turned it to -17.27% / PF 0.9807 / MDD -47.02%; supersevere reached -52.76% / PF 0.8983 / MDD -60.46%. The base result itself was regime-dependent: bear return -5.87% / PF 0.9554 versus bull +14.44% / PF 1.0732. This is cost-fragile, regime-fragile behavior rather than a durable edge.

The same representative spec already shows material asset dispersion (2023 base BNB -3.51% while SOL +7.17%), so aggregate profitability cannot be treated as broad cross-asset confirmation. Funding contribution is explicitly accounted for rather than ignored.

## Scientific decision
No threshold rescue, sign flip, asset deletion, regime filter, or hold-period retuning is permitted after observing Phase219. The family is rejected as preregistered. The 2026+ holdout remains unopened and must not be used to select the next hypothesis.

Champion status: unchanged.
