# V99 R106 Phase195-S/T — corrected consensus ancestry and paper publication forensics (2026-10-08)

**Status: DATA_ONLY / HOLD; no champion promotion; no economic trials.** V16 Frozen, V99 Frozen, untouched holdout, causal t-1, chronological TRAIN-only selection, temporal folds, severe/supersevere costs, regime matrix and benchmark envelope remain unchanged.

## S: protocol correction before execution

The preregistered Phase195-S historical_summaries route was **wrong for the fixed Bellatrix slot 6173989**, which predates Capella. Per Ethereum consensus specs, Capella froze historical_roots and began historical_summaries for later slots. The correct pre-Capella ancestry path is:

1. Independently compute SSZ BeaconBlock hash_tree_root from the archived Bellatrix signed block (NOT execution block hash, raw SSZ SHA256, or provider assertion).
2. Merkle-include the beacon block root in the 8192-element block_roots vector at slot offset **5413** (13 siblings).
3. Hash HistoricalBatch(block_roots_root, state_roots_root); include in frozen historical_roots list at index **753** (24 siblings + SSZ list length mix-in; length **758** at Capella activation).
4. Include historical_roots list root at Capella BeaconState field index **7** (5 siblings) to reproduce the independently trusted BeaconState root.
5. **Separately authenticate** the checkpoint's finality/trust chain. A matching path to an operator-supplied state root is NOT authenticated consensus ancestry.

The Phase195-S tool implements only step 2-4 with strict fixed slot, Capella checkpoint slot range, branch lengths and hash checks; it intentionally reports **PROVISIONAL_MERKLE_PATH_MATCH_UNANCHORED** even if all supplied branches match. No real proof bytes or independently authenticated finalized checkpoint have been obtained; no proof success is claimed. This corrects the preregistration *before* seeing any economic outcome.

Source: Ethereum consensus specs Capella BeaconState and historical_roots replacement; see https://ethereum.github.io/consensus-specs/specs/capella/beacon-chain/ and https://eth2book.info/capella/annotated-spec/ .

## T: independent official paper publication failure attribution

Audited the **actual GitHub Actions failed-run artifact 11580900803** from run **37847351859**, not synthetic paper data. All **8 official ledgers** (V13/V14/V15/V16/V99 and core/opportunity/combined) fail the append-only guard at **exactly their final published hour 2026-10-01 16:00 UTC**; earlier prefix rows match. The replay extends to **2026-10-08 20:00 UTC**, but cannot be published without rewriting an immutable historical row.

In 7 ledgers with funding breakdown, the final published hour had **funding_result_brl = 0**, while replay supplies newly nonzero adverse funding (examples: V13 -0.47 BRL; V16 -0.36 BRL; core -0.42 BRL). The V99 ledger lacks per-hour funding decomposition; its final published capital changed from **R$ 9,263.27 to R$ 9,262.91**, consistent with the cross-track correction but **not independently attributable to funding from that ledger alone**. This is a late-arriving funding/backfill signature, not evidence that the strategy parameters changed. The publication guard correctly rejected it.

**Do not** weaken the append-only verifier, overwrite 2026-10-01, splice curves without accounting, or present uncommitted replay results as official forward paper. Safe recovery requires a separately tested, explicitly disclosed append-only *later-hour correction entry* or a forward replay pinned to immutable as-published data; either route must preserve published history, ledger accounting identities, and frozen candidate decisions. This document is diagnosis, not authorization to alter the paper strategy or main branch.

## Reproducibility and next gate

- Phase195-S deterministic synthetic Merkle/adversarial checks; no authenticated proof inputs.
- Phase195-T synthetic append-only controls and actual 8-ledger failed artifact classification.
- Next: acquire Bellatrix SSZ BeaconBlock root and independently authenticated Capella state checkpoint with complete proof siblings; independently validate full TRAIN coverage and latency. In parallel, design and test an append-only paper correction protocol **without changing any prior published byte**.
- Dashboard champions unchanged. Keep historical backtest, untouched holdout, unpromoted DATA_ONLY research, and official forward paper strictly separate.
