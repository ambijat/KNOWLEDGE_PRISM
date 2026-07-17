# KNOWLEDGE_PRISM — Full Project Audit

**Date:** 2026-07-08 · **Auditor:** Claude (research-judgment track) · **Mode:** read-only, no state changed.
**Ledger head at audit:** block 24 (`block_0024_queue_schema_normalisation`). **Stage:** 4 of 8 (Verification Queue).

This audit inspects ledger integrity, evidence state, corpus tables, the ontology, the retrieval/queue governance, and the document/artifact inventory. It changes nothing. One material interpretive risk is flagged (§4); everything else is healthy or cosmetic.

---

## 1. Ledger & chain integrity — PASS
- `verify_chain()` = **True**, zero broken links.
- **25 blocks, numbered 0–24, no gaps, no duplicate block numbers.**
- Dual-track authorship confirmed: **13 blocks Codex, 12 blocks Claude** — the two-agent governance model is operating as designed (Codex = front-end/index; Claude = research judgment).
- Action log verifies OK (25 records at last check).
- `artifact_hash` integrity table: 134 file-hash rows; `retrievable` registry: 32 rows; `source_registry`: 117 ingested-source hashes. Provenance spine intact.

**Cosmetic issue (not a defect):** block **23** carries the label `block_0022_codex_index_development_update` — a Codex label typo (block_no 23, label says 0022). The hash chain keys on `block_no`, so integrity is unaffected; the human-readable label is simply misnumbered. Recommend Codex correct the label convention on its next block; do not rewrite block 23 (that would break the chain).

## 2. Evidence state — consistent with Stage 4
- `verdict_disposition`: **18 rows** = the pilot set. Breakdown: 11 `core_candidate`, 2 `review_required`, 2 `claim_supported_but_project_irrelevant`, 1 `excluded_unreadable`, 1 `excluded_misfile_noise`, 1 `Peripheral_context`. Sums to 18. ✓
- Evidence grade: **11 at `sampled_text_supported_core_candidate`**, 7 null (the excluded/review rows, correctly ungraded).
- **0 at `concept_verified`, 0 at `ontology_core`.** Correct — no over-promotion; the "concept is real only when seen in text, and only at the top of the ladder" discipline is being held.
- `functional_role`: **14 rows** (11 promoted + the 3 unresolved: #7 Ratzel, #13 Russia/Mongols, #18 Advaita/OCR). Every graded or flagged item has a functional-IR reading. ✓
- `claim`: **32 total** — 27 accepted, 5 provisional. The 5 provisional are correctly *not* accepted: they sit at reconnaissance / metadata_only / hypothesis_only / analysis grades (domain_definition, master-register, bridge-queue, methodology) — i.e. design-stage assertions, not text-verified claims. Claims KP-CLAIM-000022–000032 (block 16) are the 11 promoted books.

## 3. Corpus scale — stable
| Table | Rows |
|---|---|
| master_corpus | 35,861 |
| solemon_crawl | 35,178 |
| zotero_register | 1,841 |
| recoll_subject_folders | 502 |
| bridge_concepts | 392 |
| intersection_seam / ontology_edge | 136 / 136 |
| source_registry | 117 |
| step2_corpus | 86 |
| pub_eigenspace | 47 |

**Coverage reality-check:** of 392 bridge concepts, **18 (4.6%) have been dispositioned and 11 (2.8%) promoted** to the intermediate grade. This is exactly the expected footprint for Stage 4 with no scaling authorized — but it is worth stating plainly: the verified core is a *pilot-sized* seed, not yet a representative sample of the 392-row bridge, and nowhere near the 35,861-row master corpus. No scaling should be read into the current numbers.

## 4. Ontology — MATERIAL INTERPRETIVE RISK (flag, do not "fix" silently)
`ontology_node` holds **43 nodes** (5 `Axis` meta-nodes, 18 `Empirical Object`, 20 `Method/Theory`) and `ontology_edge` holds **136 edges**. These are the **design-time domain map** built in Stage 1 from the domain definition and the eigenspace/NMF analysis (e.g. nodes "Afghanistan", "Heartland", "Russia"; the 5 latent axes). **None of these nodes carries an evidence grade, a source file, or a block number.**

The risk: a reader (or the Codex front-end) can see "43-node, 136-edge ontology" and present it as *the verified concept ontology of the project*. It is not. It is an a-priori hypothesis scaffold. The evidence pipeline has correctly promoted **0** items to `ontology_core` — meaning the design ontology and the verified ontology are, at this stage, **two different things that share one table shape.**

**Recommendation (proposal only — not enacted):** distinguish the design/hypothesis ontology from the text-verified ontology, either with a `provenance`/`status` column on `ontology_node` (`design_hypothesis` vs `text_verified`) or a separate view. Until then, any surface that displays the ontology should label it "design map (hypothesis), not yet text-verified." This is a boundary/interpretation matter for the user to rule on, consistent with "judge freely, but never silently."

## 5. Retrieval & queue governance — healthy
- `verification_queue`: 1 row — Trenin (`KP-VQ-000001`), `candidate_type=anchor_candidate`, `status=queued`, `layer_prior=AB`, `duplicate_group_id=DUP-TRENIN-EOE`, canonical NULL. **Not sampled.** ✓
- Controlled vocabularies now in place: `queue_candidate_type_taxonomy` (8), `queue_status_taxonomy` (9). `kaleidoscope_anchor_piece` recorded as a synonym, not a rogue type.
- `boundary_proposal`: 1 row (`KP-BP-000001`, layer_A_AB) at `proposed_boundary_refinement` — awaiting user ratification, correctly not adopted.
- Separation verified: Trenin appears in the queue and in `master_corpus` (raw provenance, 4 drive copies) but in **0** rows of `verdict_disposition`, `functional_role`, `claim`, or `ontology_node`. The retrieval clue has not leaked into evidence state.

## 6. Documents & artifacts — well-populated
- **43 artifacts** in project scope (17 .md, 16 .csv, 4 .py, 4 .png, 1 .json, 1 .pdf).
- Governance beacons all present and current: CHARTER.md (15.3 KB), RESTORE.md, VERIFICATION_RUBRIC.md, PIPELINE.md, plus 21 docs under `docs/` (domain, protocol, handover, audit, reports).
- Some overlap/redundancy in top-level status docs (ACTION_PLAN, PROJECT_STATUS, ROADMAP, PREAMBLE, README, SHIFT_HANDOVER all co-exist) — not a defect, but a consolidation pass would reduce the chance of a future shift reading a stale one. Low priority.

## 7. Summary scorecard
| Dimension | State |
|---|---|
| Hash chain | ✅ verifies, 0–24 contiguous |
| Evidence discipline (no over-promotion) | ✅ 0 at concept_verified/ontology_core |
| Pilot evidence (11 core candidates) | ✅ graded + functionally read |
| Queue governance | ✅ normalised, Trenin queued, not sampled |
| Boundary discipline | ✅ proposal not adopted |
| Corpus provenance | ✅ hashes + source registry intact |
| Ontology labelling | ⚠️ design-map vs verified not distinguished (§4) |
| Ledger label hygiene | ⚠️ block 23 mislabelled 0022 (cosmetic) |
| Doc redundancy | ⚠️ several overlapping status docs (low priority) |

## 8. Recommended next steps (all await user ruling — nothing enacted)
1. **Ontology labelling (§4)** — add a provenance/status distinction so the 43-node design map is never mistaken for a verified ontology. Highest-value fix.
2. **Codex label correction** — align block-label numbering going forward; leave block 23 as-is.
3. **Standing evidence queue** — re-sample #7 Ratzel (validated quote required) and #13 Russia/Mongols; reOCR #18 Advaita. Unchanged since block 15.
4. **Then, and only on authorization:** either approve Trenin `queued → approved_for_sampling`, or run a second Recoll cycle (candidates now enter under controlled vocabularies), or begin governed scaling beyond the 18-book pilot.

**No evidence grade, disposition, ontology status, boundary status, claim, or block was created or modified by this audit.**
