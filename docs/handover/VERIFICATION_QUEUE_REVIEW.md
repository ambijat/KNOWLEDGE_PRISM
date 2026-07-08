# Verification-Queue Review Note

**Status:** read-only review of the new queue mechanism. No text sampled, no evidence/disposition/ontology/boundary status changed. No block sealed by this review.
**Scope:** the two persistent tables introduced by block 22 — `verification_queue` and `boundary_proposal`.
**Reviewer:** claude (research judgment / evidence discipline).

---

## 1. Table schemas

### `verification_queue`
Auditable retrieval-stage queue. A retrieval clue (e.g. a Recoll Kaleidoscope hit) is recorded here **before** any sampling, so the queueing act is visible and the kaleidoscope never behaves as an automatic research agent.

| column | type | meaning |
|---|---|---|
| `queue_id` | TEXT | stable id, `KP-VQ-000001` … |
| `file` | TEXT | source basename |
| `title` | TEXT | display title |
| `path` | TEXT | disk path of the surfaced copy |
| `source_stage` | TEXT | how it entered the queue (e.g. `recoll_kaleidoscope_trial_001`) |
| `candidate_type` | TEXT | `normal_candidate` \| `anchor_candidate` \| `kaleidoscope_anchor_piece` |
| `clue_score` | REAL | retrieval clue score at queueing time — **NOT evidence** |
| `layer_prior` | TEXT | provisional layer prior (clue, overridable): A \| B \| AB \| Ambiguous \| Out-of-domain |
| `status` | TEXT | `queued` \| `approved_for_sampling` \| `sampled` \| `declined` |
| `rationale` | TEXT | why queued |
| `recommended_action` | TEXT | next governed step |
| `decided_by` | TEXT | claude \| codex \| user |
| `ts` | TEXT | ISO-8601 UTC |
| `block_no` | INTEGER | sealing block |

### `boundary_proposal`
Boundary-kinematics ledger. A surprise during retrieval/verification may suggest moving a Layer boundary. Such a move is **proposed** here, never enacted silently.

| column | type | meaning |
|---|---|---|
| `proposal_id` | TEXT | stable id, `KP-BP-000001` … |
| `scope` | TEXT | which boundary (e.g. `layer_A_AB`) |
| `observation` | TEXT | the surprise that triggered it |
| `proposed_change` | TEXT | the refinement proposed |
| `status` | TEXT | `proposed_boundary_refinement` \| `adopted` \| `rejected` |
| `triggered_by` | TEXT | source_stage / event |
| `decided_by` | TEXT | claude \| codex \| user |
| `ts` | TEXT | ISO-8601 UTC |
| `block_no` | INTEGER | sealing block |

Both are declared in `db/build_prism_db.py` under the **PERSISTENT (never dropped)** section with `CREATE TABLE IF NOT EXISTS`, so a from-scratch rebuild reconstructs the schema and live rows are preserved.

## 2. Current rows
- `verification_queue`: **1 row** — `KP-VQ-000001`, `trenin_eurasia.pdf`, `candidate_type=anchor_candidate`, `status=queued`, `clue_score=0.833`, `layer_prior=A`, `source_stage=recoll_kaleidoscope_trial_001`, `block_no=22`.
- `boundary_proposal`: **1 row** — `KP-BP-000001`, `scope=layer_A_AB`, `status=proposed_boundary_refinement`, `triggered_by=recoll_kaleidoscope_trial_001`, `block_no=22`.

## 3. Rows survive rebuild
**Yes.** After running `db/build_prism_db.py` (which drops+rebuilds all DERIVED tables), both tables retained exactly 1 row each. They are on the persistent side of the build script, alongside `block`, `claim`, `verdict_disposition`, `functional_role`, `disposition_taxonomy`.

## 4. How Trenin is represented
Trenin exists **only as a queue entry** (`KP-VQ-000001`, status `queued`) plus prose in the Trial 001 report and a `notes=anchor_candidate=yes` mark in the trial CSV. Explicit limits carried in the row's `rationale` and `recommended_action`: retrieval clue only — not verified, not promoted, not ontology-core; sampling must be rubric-governed with a validated argument quote and is **not** to be done automatically by the kaleidoscope.

## 5. How the boundary proposal is represented
As `boundary_proposal` row `KP-BP-000001` with `status=proposed_boundary_refinement`. It records the observation (dense Russia/Eurasia/post-Soviet-order cluster in the first cycle) and the proposed change (recognise Eurasian security imaginaries + post-Soviet spatial order as central to Layer A/AB). It is **proposed, not adopted** — no Layer definition, domain doc, or ontology has been altered.

## 6. Separation from evidence / disposition / ontology state
**Clean.** Trenin appears in **0** rows of `verdict_disposition`, `functional_role`, `claim`, and `ontology_node`. It appears in `master_corpus` (4 copies across drives) — but that table is raw corpus **inventory/provenance**, exactly where a retrieval clue should sit, and carries no evidence grade for Trenin. The queue is structurally distinct: separate table, separate id namespace (`KP-VQ-*` vs `KP-CLAIM-*`), and no foreign-key path from a queue row into an evidence grade without an explicit later sampling event.

## 7. Fields needed before sampling
The queue is sufficient to *hold* a candidate, but a governed sampling step will need these — most can be added to `verification_queue` as sampling progresses, or captured on the eventual `verdict_disposition`/`claim` row:
- `approved_by` + `approved_ts` — who authorised the move `queued → approved_for_sampling` (currently `decided_by`/`ts` describe the queueing act, not the approval).
- `sampling_block_no` — the block under which sampling occurs (distinct from the queueing `block_no`).
- `rubric_version` — which VERIFICATION_RUBRIC version governs the sample.
- `sha256` of the target file — bind the verdict to the exact bytes sampled (guards against a different drive-copy being read).
- `concept_probes` — the hypothesised concept terms to probe (Russia / post-Soviet order / Central Asia / security imaginary for Trenin).
- link field (`queue_id`) echoed onto the resulting `verdict_disposition` row so the clue→evidence lineage is queryable both directions.

## 8. Schema sufficiency for future Recoll candidates
**Largely yes.** `queue_id`, `source_stage`, `candidate_type`, `clue_score`, `layer_prior`, `status`, `rationale` generalise to any Recoll cycle and to non-Recoll sources. Gaps to close before volume:
- No `retrieval_cycle_id` / `research_question` field — future candidates should record *which* kaleidoscope cycle and *which* research question surfaced them (a candidate can recur across cycles).
- No `rank` field — `clue_score` is kept but the raw Recoll rank that produced it is not, weakening reproducibility.
- No uniqueness constraint — nothing stops the same `file` being queued twice from two cycles; dedup is currently by convention only.
- `duplicate_of` / canonical-file handling — Trenin surfaced as two drive copies (`trenin_eurasia.pdf`, `trenin.pdf`); the queue holds one, but there is no explicit field recording the alternates.

## 9. Field-name / status normalisation before more candidates enter
Recommended normalisations (cheap now, costly after volume):
- **`candidate_type` controlled vocab.** Fix to `{normal_candidate, anchor_candidate}` and treat `kaleidoscope_anchor_piece` as a synonym of `anchor_candidate` (or a `source`-scoped label), so anchors are countable by one value.
- **`status` controlled vocab + a taxonomy table.** Mirror the `disposition_taxonomy` pattern with a small `queue_status_taxonomy` so `{queued, approved_for_sampling, sampled, declined}` is enforced and documented, not free text.
- **`layer_prior` shared vocab.** Align exactly with the layer vocabulary used in `functional_role.layer_substantive` (`A|B|AB`) plus retrieval-only extras (`Ambiguous|Out-of-domain`), so a prior and a substantive verdict are comparable.
- **id zero-padding** already consistent (`KP-VQ-000001`, `KP-BP-000001`) — keep the 6-digit width.

None of these block current operation; they are hygiene to apply before batch candidates arrive.

---

## Confirmation
This review sampled no text, extracted no PDF, changed no evidence grade, created/changed no disposition, promoted nothing, and did **not** adopt the boundary proposal. `verification_queue` = 1 row (`queued`), `boundary_proposal` = 1 row (`proposed_boundary_refinement`), both unchanged by this review.
