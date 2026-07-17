# Handover — Scholar Input Schema v0.2 Freeze

**Date:** 2026-07-09
**From:** Claude (backend / research-governance)
**To:** next shift + Codex front-end team
**Type:** design-freeze handover. No DB, ledger, or evidence state changed.

## What was frozen
`docs/protocol/KNOWLEDGE_PRISM_SCHOLAR_INPUT_SCHEMA_v0.2.md` — the definitive v0.2
schema for `scholar_input_not_evidence` records (mobile + desktop capture).

## The one principle
A scholar input is **not evidence**. It may seed a research question or retrieval
lens; it may never become a claim, disposition, functional role, concept
verification, ontology item, or a direct `verification_queue` entry. Corrected flow:
`scholar_input → approved_to_question → research question/lens → retrieval →
verification_queue (real documents) → sampling → evidence → claim/ontology if earned`.

## Frozen vocabularies
- **status (5):** raw_captured · imported_not_evidence · under_review ·
  approved_to_question · rejected_archived. Ceiling is `approved_to_question` — there
  is deliberately no `approved_to_evidence`.
- **source (3):** android_app · desktop_manual · desktop_import.
- **draft_organ (16):** Title, Background, Statement_of_Problem, Research_Gap,
  Research_Questions, Objectives, Scope, Methodology, Conceptual_Framework,
  Literature_Clusters, Evidence_Needs, Case_Region_Time_Period, Chapterisation,
  Supervisor_Questions, Revision_Tasks, Unassigned. **Advisory only.**

## What is NOT done (deliberately)
No `scholar_input` table created; `build_prism_db.py` untouched; validator untouched;
no block sealed; no code written. This is a freeze document to build against.

## Codex status
Codex may now **prepare UI mock-ups against the frozen fields and display rules**
(§11), but must build no evidence-path behaviour and must render every card as
`SCHOLAR INPUT — NOT EVIDENCE`. Approval means "seed research question," never
"send to verification queue."

## Next bounded step (needs user authorisation)
When the user authorises implementation: add `scholar_input` +
`scholar_input_status_taxonomy` to the **persistent** section of
`build_prism_db.py`, seed the status vocab, extend the consistency validator, and
seal one schema block. Not before.
