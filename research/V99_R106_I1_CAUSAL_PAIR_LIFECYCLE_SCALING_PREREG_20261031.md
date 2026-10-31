# V99 I1 — causal held-option pair scan throughput invariant (2026-10-31)

**SOURCE-ONLY engineering prerequisite; NO economics, ROI, signal retune, promotion, orders or holdout access.**

## Existing bottleneck
In `research/tools/v99_r106_i1_lifecycle_daily_tape.py`, `causal_pairs` tests every pair of held symbols per (Monday, BTC/ETH, expiry) with nested loops. The independent lifecycle oracle repeats the same quadratic search. With 6,000 distinct strikes, one expiry alone can require up to 17,997,000 pair comparisons when no valid synchronized pair exists. This is a throughput blocker once the 661-day original licensed option tape is available, not a source-provenance fix.

## Fixed, testable change
Replace only the existence check for two distinct **numeric** strikes with a chronological arrival-time sweep. Keep the exact original eligibility, last-receipt revocation, per-contract pre-expiry continuity, <=1,000,000us absolute venue-clock and arrival-clock differences, Monday 00:00 strict predecision, 28–34 calendar-day expiry and source flags unchanged. For each (entry,asset,expiry), maintain a sliding <=1s arrival window and count prior venue timestamps in [current venue-1s,current venue+1s] minus the count of the current numeric strike. A strictly positive difference establishes a causal distinct-strike pair. Use a bounded sorted venue index with bisect, not a new dependency. The independent oracle must implement its own equivalent check, not import the primary helper. Include deterministic 6,000-strike no-match and positive controls, boundary exactly 1s, 1s+1us, equal-strike aliases, and differential comparisons to the original quadratic reference on small randomized inputs. No changes to reported metrics or decisions.

## Verification and hard limit
Run the existing lifecycle synthetic 661-day CI and independent oracle after the change. A green run proves only equivalent source-screen software and improved asymptotic pair comparisons; it cannot certify the 658 missing licensed days, 180 lifecycles, native fees, margins, funding, execution, settlement or any economic TRAIN. Frozen, paper, champion, validation and final holdout remain sealed.