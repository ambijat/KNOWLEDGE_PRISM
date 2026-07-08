# Verification-Queue Schema Normalisation

**Block:** 24 — `block_0024_queue_schema_normalisation` (chain verifies OK; action log 25 records).
**Nature:** schema-governance only. No text sampled, no PDF opened, no evidence grade, disposition, ontology, or boundary status changed. Trenin remains `status=queued`.

---

## 1. Controlled vocabularies created

### `queue_candidate_type_taxonomy` (8 values)
`anchor_candidate` (synonyms note: `kaleidoscope_anchor_piece`), `ordinary_candidate` (synonyms: `normal_candidate|standard_candidate`), `surprise_candidate`, `resample_candidate`, `ocr_candidate`, `manual_nomination`, `openalex_candidate`, `recoll_candidate`.
`kaleidoscope_anchor_piece` is recorded as a **synonym** of `anchor_candidate` in the `synonyms` column — not a separate uncontrolled type. So anchors are countable by one value.

### `queue_status_taxonomy` (9 values)
`queued`, `approved_for_sampling`, `sampling_in_progress`, `sampled_pending_review`, `verified_sample_supported`, `rejected_after_sampling`, `deferred`, `duplicate`, `closed`. `is_terminal=1` for `rejected_after_sampling`, `duplicate`, `closed`.

### `layer_prior` normalised vocabulary
`A | B | AB | Peripheral | Out_of_domain | Ambiguous` (documented in the `verification_queue` schema comment; applied to future records; the one existing row corrected below).

## 2. Pre-sampling governance fields added to `verification_queue`
`approved_by`, `approved_ts`, `sampling_block_no`, `rubric_version`, `target_file_sha256`, `concept_probes`, `retrieval_cycle_id`, `research_question`, `raw_rank`, `duplicate_group_id`, `canonical_candidate_id`.
All left NULL except those already known without sampling: `retrieval_cycle_id=recoll_kaleidoscope_trial_001`, `raw_rank=5`, `research_question` (the Trial 001 RQ). Fields requiring actual sampling (`sampling_block_no`, `rubric_version`, `target_file_sha256`, `concept_probes`, `approved_by/ts`) remain NULL.

## 3. Trenin queue row (`KP-VQ-000001`) — metadata corrections only
- `layer_prior`: **A → AB**, with reason recorded in `rationale`: the work fuses empirical Eurasia / post-Soviet space (Layer A) with geopolitical imagination / theory (Layer B); AB is the correct provisional prior and matches `boundary_proposal KP-BP-000001`. This is a **queue-metadata correction**, not an evidence or ontology change.
- `candidate_type`: `anchor_candidate` (now a controlled value).
- `status`: **unchanged, `queued`.**

## 4. Duplicate handling
Trenin has two drive copies: `trenin_eurasia.pdf` (SOLEMON/Winstore/BASE_ONE/Mackinder) and `trenin.pdf` (SOLEMON/GHANA_B/BOOKS5).
- `duplicate_group_id = DUP-TRENIN-EOE` records them as related.
- `canonical_candidate_id = NULL`: **canonicalisation deferred** — choosing a canonical copy safely requires `target_file_sha256` comparison, and the PDFs were not opened. Recorded in `recommended_action`.

## 5. Persistence
`db/build_prism_db.py` updated so all of this survives a from-scratch rebuild:
- `verification_queue` CREATE now includes the 11 governance columns;
- `queue_candidate_type_taxonomy` and `queue_status_taxonomy` added under the PERSISTENT section with seed data (`INSERT OR IGNORE`);
- an idempotent ALTER backfill adds the 11 columns to any pre-existing `verification_queue`.
**Rebuild survival check: PASS** — after re-running the build script, all 11 fields present, both taxonomies (8 + 9 rows), the corrected Trenin row (`layer_prior=AB`, `status=queued`, `DUP-TRENIN-EOE`, canonical NULL), boundary status still `proposed_boundary_refinement`, and evidence invariants intact (11 promoted, 0 concept/ontology, 0 Trenin in `verdict_disposition`).

## 6. Not done (by instruction)
No Recoll run, no new candidates, no sampling, no PDF extraction, no evidence-grade / disposition / promotion change, no boundary adoption.
