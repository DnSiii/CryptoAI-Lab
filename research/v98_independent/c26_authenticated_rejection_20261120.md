# C26 — authenticated training rejection (2026-11-20)

Source: GitHub Actions run https://github.com/DnSiii/CryptoAI-Lab/actions/runs/44690686823, commit a658caab79583d5bbf7b51a9b2a5baf760478d38, 27,048 hourly Clean-4 bars, native V98 funding, no holdout accessed.

The historical replay finished for all three cost scenarios and produced nonzero turnover, but the independent ledger audit failed `EXPOSURE_CAP_VIOLATION` in `v98_c21_ledger_audit.py` at the 90% aggregate / 40% single-asset exposure gate. The runner deliberately holds positions between weekly scheduled fills, permitting drift to exceed a cap before the next rebalance. This is a substantive invalidation of the preregistered C26 implementation; do not rescue C26 by changing its trading calendar or exposure rule after seeing the outcome.

Unvalidated runner summaries (NOT approved PnL): 1x final equity $15,508.24, max DD 13.44%; 2x $15,371.16, DD 13.50%; 4x $15,217.53, DD 13.60%, from $10,000 initial. The arithmetic independent audit did NOT complete, so these are diagnostics only, not evidence of economic superiority.

Decision: **REJECT C26; no champion, no validation, no benchmark, no paper promotion.** Preserve the old rejected variants and the Clean-4/holdout boundaries. A genuinely new preregistered complete-engine candidate must specify how its risk governor maintains intraperiod limits (including drift) without introducing hidden leverage or violating causal t-1 execution. Next work: quantify breach rows from the C26 archived ledger, implement a distinct architecture with continuous safety governor, run authenticated historical replay and independent economic gates.
