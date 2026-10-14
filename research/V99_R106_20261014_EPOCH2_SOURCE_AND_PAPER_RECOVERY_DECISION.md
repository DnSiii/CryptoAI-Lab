# V99 R106 — Five-variant paper recovery and new-versioned-epoch decision

Date: 2026-10-14 (UTC). Research branch: `research/v99-r106-native-all-regime-engine`.

**Research verdict: DATA_ONLY/HOLD. No economic alpha trial, no champion promotion, no holdout usage, no real orders, no Frozen modification.**

## What really broke the old paper

The durable public ledger remains **byte-identical** to its archived Git blob `97ce6ea8e9b58a9616892d915c86d96ae3c54225` on `paper-results`, through **2026-10-10 05:00 UTC**. Its raw SHA-256 is `f188c4d95761c4ddf4719f4d86bfab0faa54a65f79d576f42ce3cc4f09e17089`.

Actual GitHub Actions run `38617716407`, **attempt 2**, re-ran the real R106 five-variant generator from the corrected research branch. The prior `NameError: p1 is not defined` was fixed by accessing the pre-imported, frozen `base.p1.TRAIN_END`. This time, the runner completed the computational replay and **the historical publication guard rejected it**, as intended:

| Track | Changed old paper hours | Irremovable legacy problems |
| --- | ---: | --- |
| R98 | 0 | 25 forward rows in old historical reference |
| R106 F1 | **568** | old operations capped at 1,500, 25 forward rows in old reference |
| R106 F3 | **452** | old operations capped at 1,500, 25 forward rows in old reference |
| R106 F7/F9 | 0 | 25 forward rows in old historical reference |
| R106 F12 | 0 | 25 forward rows in old historical reference |

All five newly corrected historical references would differ from the old polluted reference (also containing 998 post-TRAIN observations). Updating the old backtest reference in place is **not allowed** because it changes a published artifact. Altering old equity hours or silently filling missing operations is equally forbidden.

Read-only formal proof: `research/tools/v99_r106_legacy_epoch_feasibility.py`. Even the most favorable candidate **identical to the old published ledger** fails the current publication guard because the guard checks the immutable old capped operations and its old backtest/paper overlap. That is a **candidate-independent impossibility**, not an unlucky market run. GitHub CI `38624548245` independently executed the proof against the actual `paper-results` file and returned `NEW_VERSIONED_EPOCH_REQUIRED`.

## Concrete code repaired

- `scripts/paper_once_v99_research_variants_v2.py`: correct `base.p1.TRAIN_END` import path, uncapped operations in research candidate, strict TRAIN-only historical curve. Not a legitimate way to backfill or change the old published paper.
- `research/tests/test_v99_r106_runner_integration.py`: four integration tests execute the **real** `main()` with synthetic five-track data and a mocked refusal-producing publication firewall. They verify no writes occur before approval.
- `research/tools/v99_r106_legacy_epoch_feasibility.py` and tests: prove the old epoch cannot accept any new candidate without weakening the guard.
- `research/tools/v99_r106_epoch2_quarantine.py` and tests: implement a **new versioned forward-epoch contract**, anchored to the unchanged SHA-256 of the old public ledger:
  - new UTC boundary strictly after the old published last hour;
  - no inherited old ROI or capital; each of five tracks starts with BRL 10,000 and **zero new-epoch PnL**;
  - conservative source-reception `t−1`: first eligible decision at `floor(received_utc, 1h)+2h`;
  - exact untruncated operation journal, no duplicate symbol/hour events;
  - exact **gross − fees + funding + transfer = net** each hour, **previous capital + net = next capital**, and continuous hourly timestamps;
  - raw first-party `exchangeInfo` payload hash, Binance reported serverTime and explicitly recorded receipt timestamp required;
  - even a schema PASS is **QUARANTINE_PENDING_VERIFIED_SOURCE**, never auto-authorized publication or promotion. No new epoch was actually launched.

## CI and live source audit

GitHub Actions `38625267947` passed **105 tests**: 17 helper/operations + 4 true main() integration + 20 publication firewall + 27 old-epoch quarantine + 19 fresh-epoch contract + 9 old-epoch feasibility + 9 published-epoch witness. This is software integrity, **not an economic backtest**.

`research/tools/v99_r106_live_first_party_receipt.py` was implemented to capture contemporary raw Binance USD-M exchangeInfo, server time and five recent hourly closed-bar receipts over HTTPS with SHA-256 and conservative decision eligibility. Its **18 synthetic tests passed** in run `38624009496`, but the first **live GitHub Actions request to `https://fapi.binance.com/fapi/v1/time` returned HTTP 451**. Thus **no first-party live payload or authenticated new source receipt** was obtained, and the new epoch remains closed. Do not hide 451, spoof source time, backdate discovery, or substitute retrospective `onboardDate` as a receipt. Alternative approved source access or provider authorization is required.

The old main workflow `.github/workflows/v99-research-paper.yml` was improved with a read-only fail-fast check **before expensive market replay**. Run `38625564290` confirmed the blocked result in seconds after setup, exiting code 2 with an explicit annotation. The research automations are separate and remain enabled; this check does not disable research or alter the historical paper. Future clean epoch activation requires a distinct workflow with verified provenance and complete independent accounting, not reopening this unsatisfiable legacy guard.

### Artifacts and protected assets

- V16 Frozen and V99 Frozen: untouched.
- Final holdout: not accessed for optimization.
- `paper-results` five-variant ledger: unchanged Git blob `97ce6ea8e9b58a9616892d915c86d96ae3c54225` after these changes.
- Existing historical research champion: **R106 F7/F9 Core**, no successor validated.
- F1/F3 published ROI claims remain uncertified due to source and completeness deficiencies.
- Zero new live trades, zero real orders, zero legitimate new forward results.

## Next shortest route to a real improvement

1. Obtain **lawfully accessible**, first-party or independently evidenced point-in-time market/universe receipts; the current GitHub runner is blocked by HTTP 451. No geographic bypass or unverified source substitution.
2. Attach those receipts to the already-tested clean epoch-2 journal; begin only **after** observed source-time and full t−1 closure, with zero inherited PnL and immutable old-epoch archive.
3. Reconcile full five-variant hourly accounting, operations and exposures to the new versioned paper without selecting a winner on the paper period.
4. Separately, use a genuinely orthogonal, PIT-verified **TRAIN-only** source for any R106 challenger, with severe/supersevere costs, folds, benchmark envelope, tails/regimes and reproducibility. Never tune on 2026 paper or the final holdout.

The immediate block is **authenticated data access and the absence of a valid new forward epoch**, not a need to loosen drawdown gates or invent new high-ROI candidates.
