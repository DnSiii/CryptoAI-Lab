# Phase195-AN — Native universe eligibility: static code audit

**DATA_ONLY/HOLD; no proof of an executed noncausal position yet.** `scripts/paper_once_v15.py` explicitly applies `apply_eligibility_boundaries` to the V15 raw opportunity targets, but returns the underlying historical `data` unchanged. In `scripts/paper_once_v99_research_variants.py`, F1 and F3 build native sleeves from that full `data` through `p1.fixed_sleeves(data)` and other native builders. The inspected native route does not apply the per-symbol `eligible_after_timestamp` gate to those native targets.

The paper also recomputes F1/F3 train-only routing on each run. Although TRAIN_END is fixed, dynamic historical membership can change the training input. This is a reproducibility and point-in-time **risk**, not proof of the exact cause of the observed rewrites.

Next: freeze original target matrices, discovery receipts, train-router decisions and data hashes; compare original vs new native targets before each symbol's eligibility time; run fixed-universe and fixed-market-data ablations. Reject any retroactive positions or changing train-selected router. Preserve causal t-1, folds, costs, benchmark envelope and untouched holdout. No promotion or paper rewrite.
