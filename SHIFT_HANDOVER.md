# SHIFT HANDOVER — KNOWLEDGE_PRISM

**Shift:** Claude, session `7b564c3e-8699-4f40-98e6-07c5c35d7649`
**Date:** 2026-07-07
**Stage:** Pipeline Stage 4 — Verification Queue (pilot complete, first promotion done)
**Chain state at close:** blocks 0–16 sealed · CHAIN INTEGRITY OK · ACTION LOG OK (9 records)

> Read this with `RESTORE.md` (boot ritual) and `PIPELINE.md` (8-stage map).
> The mandatory shift-start ritual is `scripts/05_start_agent_shift.py` (block 0012). Run it before touching anything.

---

## 1. WHAT THIS SHIFT DID (blocks 13–16)

| Block | block_id | What it recorded |
|------|----------|------------------|
| 13 | `block_rubric_v2_pilot_run` | Approved VERIFICATION_RUBRIC v2; executed the 18-book bridge pilot. Nothing promoted. |
| 14 | `block_disposition_taxonomy_two_axis` | Introduced the **two-axis disposition model** (Axis 1 = thesis accuracy, Axis 2 = corpus membership). Created persistent tables `verdict_disposition` + `disposition_taxonomy`. Dispositioned Exam form (#17 → `excluded_misfile_noise`) and Histology (#14 → `claim_supported_but_project_irrelevant`). Registered KP-CLAIM-000021. |
| 15 | `block_0015_six_row_dispositions` | Applied user-supervised dispositions to the 6 review rows (#5,#7,#12,#13,#16,#18). Added vocab value `Peripheral_context` + column `layer_tag`. Confirmed Histology as `decided_by=human`. |
| 16 | `block_0016_sample_level_promotion_11` | **Sample-level promotion** of the 11 clean `core_candidate` rows to evidence grade `sampled_text_supported_core_candidate`. Added column `evidence_grade`. Registered KP-CLAIM-000022…000032 (accepted). **NOT ontology-core. NOT scaled.** |

### Action-log records appended this session (`logs/agent_actions.jsonl`)
- `rubric-pilot-run` — inspect, then seal
- `disposition-taxonomy` — decide
- `six-row-dispositions` — seal
- `sample-level-promotion` — seal

---

## 2. THE DOCTRINE NOW IN FORCE (do not violate)

1. **Two-axis model is permanent.** A row can be textually SUPPORTED and still excluded if it fails the project-relevance test. Thesis accuracy ≠ corpus membership.
2. **Metadata are clues, not evidence.** A concept/claim is real only when seen in text (Cardinal rule, unchanged).
3. **Exclusion marks, never deletes.** Excluded rows keep their `master_corpus` record for provenance; only the disposition changes. Nothing leaves disk.
4. **Layer B is bounded.** Method/theory material relevant to IR, geopolitics, systems theory, semiotics, ontology, knowledge representation, network analysis, AI-assisted corpus methods, research methods, epistemology. Scholarly-but-out-of-domain (e.g. Histology, ICT-policy) → `claim_supported_but_project_irrelevant`.
5. **Journalism / policy docs are not core.** They may become `Peripheral_context` (empirical/reportage), never auto-promoted to core ontology unless a later primary-source/media-evidence layer is explicitly created.
6. **Evidence ladder — promotion is stepwise:**
   `provisional_unverified → sampled_text_supported_core_candidate → concept_verified → ontology_core`.
   This shift reached step 2 for 11 rows only. Steps 3–4 require separate sign-off.

### Controlled vocabulary (`disposition_taxonomy`, seeded reproducibly in `build_prism_db.py`)
| disposition | axis2 | added_block |
|---|---|---|
| core_candidate | core_candidate | 14 |
| claim_supported_but_project_irrelevant | excluded | 14 |
| excluded_misfile_noise | excluded | 14 |
| excluded_unreadable | excluded | 14 |
| review_required | review_required | 14 |
| Peripheral_context | peripheral | 15 |

---

## 3. PILOT OUTCOME — all 18 rows (final state at close)

**Promoted (11) → `sampled_text_supported_core_candidate`, claims KP-CLAIM-000022…000032:**
#1 Global Transformation · #2 Nations at War · #3 Ideology and IR · #4 Theory and Metatheory in IR · #5 Ethnofederalism (`layer_tag=Layer_B_method_theory_core`) · #6 Why Islamism Is Winning · #8 Semiotics of Maps · #9 Cultural Cartography · #10 Structural Realism · #11 Discourse Analysis · #15 To Lead the Free World

**Not promoted (7):**
| Row | Disposition | Next action |
|---|---|---|
| #7 Ratzel and Demography | review_required | deeper re-sample; **validated argument quote required** (quote failed verbatim check) |
| #13 Russia and the Mongols | review_required | deeper re-sample; decide core vs peripheral vs historical background |
| #18 Advaita Vedanta and IR (`abiword_job`) | excluded_unreadable | **OCR / manual inspection** (unreadable ≠ irrelevant) |
| #16 "We have to go" / Afghans flee | Peripheral_context | keep as contextual reportage; not core |
| #12 Regional Action Plan / Information Society | claim_supported_but_project_irrelevant | exclude from core (ICT-policy, out of domain) |
| #14 Histology: A Text and Atlas | claim_supported_but_project_irrelevant | exclude from core (out of domain) |
| #17 Practical Exam Format May 2020 | excluded_misfile_noise | exclude from core (misfile, not scholarship) |

**Ontology-core count: 0.** No item promoted to `concept_verified` or `ontology_core`.

---

## 4. SCRIPTS / SCHEMA TOUCHED THIS SHIFT

- **`db/build_prism_db.py`** — schema evolved (persistent across derived rebuilds, verified):
  - added persistent tables `verdict_disposition`, `disposition_taxonomy` (block 14)
  - added columns `layer_tag` (block 15) and `evidence_grade` (block 16) with idempotent `ALTER` backfill
  - seeded the full controlled vocabulary via `INSERT OR IGNORE` so a from-scratch build reproduces it
  - artifact re-saved as **v2** (version_id `d723806a-d996-4f62-ba46-cf5e516af59d`)
- **`VERIFICATION_RUBRIC.md`** — v3, added §8 (two-axis disposition model). Artifact v3 `9a8aefdc-9d95-4ceb-b6ec-861287e15487`.
- Unchanged core scripts (reference only): `db/prism_ledger.py`, `db/prism.py`, `scripts/04_log_agent_action.py`, `scripts/05_start_agent_shift.py`, `db/populate_ontology_and_ledger.py`.

**Persistence guarantee tested:** `verdict_disposition` (8 rows) and `disposition_taxonomy` (6 vocab values) and all 11 evidence grades survive a full `python3 db/build_prism_db.py` rebuild (which drops & rebuilds the derived tables). Chain re-verifies OK after rebuild.

---

## 5. ARTIFACTS PRODUCED THIS SHIFT (latest version_id)

| File | version_id | What it is |
|---|---|---|
| VERIFICATION_RUBRIC.md (v3) | 9a8aefdc-9d95-4ceb-b6ec-861287e15487 | Rubric + §8 two-axis model |
| build_prism_db.py (v2) | d723806a-d996-4f62-ba46-cf5e516af59d | Builder with persistent disposition schema |
| pilot_list_proposal.csv | 6940f75d-4d45-4a2b-a1d2-c244326c29eb | 18-book stratified pilot list |
| BRIDGE_PILOT_RESULTS.md | 130d6209-a282-428d-aee2-7cf0aa33d768 | Pilot narrative results |
| BRIDGE_PILOT_VERDICTS.csv | 7256ca05-b9c5-4f7a-81f9-7ad71c7210a6 | Raw 18-row verdicts (source of truth for rows) |
| DISPOSITIONS.csv | 491fbf85-ef0e-4d51-8739-cbf2600c4bba | First 2 dispositions (block 14) |
| PILOT_REVIEW_TABLE.csv | 98e5d8e9-54a3-4456-af83-d6ee413a06f1 | 16-row two-axis review table |
| PILOT_REVIEW_FINAL.csv | 5cdf3f2a-6888-4370-8553-56806295cb07 | Final disposition, all 18 rows |
| PROMOTED_11_sampled_text.csv | 0fcd359e-3be1-4cd1-869f-030771987f7a | The 11 promoted rows + grades |

---

## 6. WHERE THE NEXT SHIFT PICKS UP

Immediate queue (no scaling yet — user has NOT authorized the ~370-row scale-up):
1. **Re-sample #7 Ratzel** with a stronger targeted chapter/concept probe; require a verbatim-validated argument quote before any disposition change.
2. **Re-sample #13 Russia and the Mongols**; decide core vs `Peripheral_context` vs historical background.
3. **OCR / manual-inspect #18** (Advaita Vedanta & IR). If title holds, it may be Layer B / bridge material.
4. Await user sign-off before: (a) any `concept_verified` promotion of the 11; (b) scaling the sampler to the remaining ~370 bridge rows. **Recommended before scaling:** add an explicit project-relevance track to the sampler (the pilot showed relevance ≠ accuracy — Histology was SUPPORTED but out-of-domain).

Downstream stages unchanged: 5 Core Corpus triage → 6 ontology promotion from text → 7 OpenAlex reconciliation → 8 Codex handover.

**To resume:** run `scripts/05_start_agent_shift.py`, then `python3 db/prism.py verify` (expect CHAIN OK, 17 blocks) and `python3 scripts/04_log_agent_action.py verify`. State of record is `db/knowledge_prism.db` on the FIGHTER drive.
