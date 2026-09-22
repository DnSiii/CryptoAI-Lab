# V99 R106 — independent train-only failure-mechanism audit, Phases100–110

Audit performed while Phase111 is still running. This document uses **only already-persisted train-only reports** from Phases100–110. No holdout data, holdout metrics, or downstream outcomes are read or inferred.

## Purpose
Determine whether recent failures look like isolated tail/pathology events worth a narrowly justified repair, or a broad family-level lack of 1h severe-cost edge that should force research toward a genuinely orthogonal source.

## Evidence table

| Phase | Mechanism | Train ROI | PF | Healthy folds |
|---|---|---:|---:|---:|
| 100 | taker-flow 24h impulse | -98.62% | 0.0381 | 0/4 |
| 101 | flow absorption | -98.56% | 0.0939 | 0/4 |
| 102 | OI impulse | -65.63% | 0.5439 | 0/4 |
| 103 | OI acceleration | -70.28% | 0.4982 | 0/4 |
| 104 | OI dispersion | -86.95% | 0.3737 | 0/4 |
| 105 | top-trader divergence | -26.60% | 0.7087 | 0/4 |
| 106 | top-trader size divergence | -19.97% | 0.7859 | 0/4 |
| 107 | top-trader conviction | -11.82% | 0.8587 | 0/4 |
| 108 | global crowding contrarian | -23.80% | 0.8505 | 0/4 |
| 109 | top-trader account-count crowding contrarian | -19.31% | 0.7926 | 0/4 |
| 110 | top-trader position-vs-count disagreement | -29.94% | 0.7013 | 0/4 |

## Fold/pathology check
Phase107 is the least-negative recent positioning candidate and therefore the strongest test of whether aggregate failure is merely tail-driven. Its four chronological folds were all negative:
- fold 1: ROI -0.75%, PF 0.9395, robust mean without top 1% = -1.876e-05;
- fold 2: ROI -0.59%, PF 0.8938, robust mean without top 1% = -2.550e-05;
- fold 3: ROI -5.54%, PF 0.8386, robust mean without top 1% = -1.977e-05;
- fold 4: ROI -5.40%, PF 0.8452, robust mean without top 1% = -1.893e-05.

Phase110 is likewise negative in all four folds and has a negative robust mean without the top 1% in every fold. Therefore the Phase100–110 pattern is not explained by one exceptional loss cluster or one temporal fold.

## Scientific decision
1. **No rescue/retuning** of Phases100–110. No threshold search, parameter grid, sign flip, selective fold exclusion, or lower-cost reinterpretation is justified.
2. The repeated failure across flow, OI and long/short-positioning transformations at the fixed 1h severe-cost gate is treated as evidence to reduce further search density inside the same metrics family.
3. Phase111 remains independent and must finish under its preregistered consensus specification; this audit does not alter it.
4. Phase112 deliberately changes the information source to official USD-M `premiumIndexKlines` and is **data/integrity only**. It cannot inspect return relationships or create a candidate.
5. Any Phase113 alpha may be specified only after Phase112 evidence is harvested, and must be preregistered before any candidate PnL.

## Integrity
- Selection evidence: train only.
- Holdout: untouched/not parsed for this audit.
- V16 Frozen: immutable.
- V99 Frozen: immutable.
- This audit changes no gate and promotes no candidate.
