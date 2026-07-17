# Backend Governance Review — Android Companion App / `scholar_input`
### Response to Codex handoff (mobile capture → desktop promotion)

> Backend/research-governance review of the proposed Android companion app data
> flow. This document changes no evidence, disposition, queue, ontology, boundary,
> corpus, or ledger state. It is feedback before the mobile export format is built.

---

## Verdict in one line

**The governance instinct is right; the schema is wrong for this project.** The
"mobile captures raw ideas, desktop converts them to candidates, evidence chain
stays clean" principle is correct and I endorse it. But the proposed tables are
written in generic Postgres (`UUID`, `JSONB`, `ledger(id)`, `TIMESTAMP`) and do
not match KNOWLEDGE_PRISM's actual store, and — more importantly — they miss one
structural fact that changes the design.

---

## 1. The structural fact Codex's proposal misses

`verification_queue` is **document-shaped**. Its real columns are:

```
queue_id, file, title, path, source_stage, candidate_type, clue_score,
layer_prior, status, rationale, recommended_action, decided_by, ts, block_no,
approved_by, approved_ts, sampling_block_no, rubric_version, target_file_sha256,
concept_probes, retrieval_cycle_id, research_question, raw_rank,
duplicate_group_id, canonical_candidate_id
```

Every candidate in that queue is **a text that exists on disk** — it has a `file`,
a `path`, a `target_file_sha256`, and it is destined for *sampling* (reading the
document). A mobile idea has **none of these**. It has no file, no path, no hash,
and there is nothing to sample.

**Therefore a `scholar_input` cannot be promoted directly into
`verification_queue`.** The Codex data-flow diagram (`APPROVE ──► Verification
Queue ──► Sampling ──► Evidence`) is category-incorrect: you cannot *sample* an
idea. This is not a nitpick — it is the difference between a clean evidence chain
and a laundered one.

## 2. The deep governance point — a scholar's idea is a *new epistemic category*

Until now every candidate in the system has been about an **external text**, moving
along one ladder:

```
metadata_only → frontmatter_seen → sampled_text → concept_verified → ontology_core
```

That ladder measures *how much of a document we have actually read*. A scholar's own
idea sits on **no rung of it**. It is not weak evidence; it is **not evidence at
all**. It is a **research prompt** — the thing that *generates* a question or a
retrieval lens, the input to the pipeline, never a support inside it.

The real danger the mobile app introduces is **hunch-laundering**: the researcher's
own overnight idea re-entering the system and later being cited as if a book had
said it. The evidence discipline exists precisely to prevent a claim resting on
"because I thought so." So the governing rule must be sharper than Codex wrote it:

> **A `scholar_input` may generate a research question or a retrieval lens. It may
> never become a source_file for a claim. It enters the pipeline as a *prompt*, and
> the pipeline must still find external text that earns the claim.**

The correct flow is therefore:

```
scholar_input (idea)
   │  approve
   ▼
research question / retrieval lens   ← the idea becomes a QUESTION, not a candidate
   │  (Recoll kaleidoscope, user-authorised)
   ▼
verification_queue (real documents, with file+path+sha256)
   │  approve-to-sample
   ▼
sampling → evidence grade → disposition → claim
```

The idea seeds the top of the funnel; external text still has to earn everything
downstream. That keeps the chain unbroken.

## 3. Schema — corrected to KNOWLEDGE_PRISM conventions

The store is **SQLite**, not Postgres. There is no `UUID`, no `JSONB`, no
`ledger(id)`. The ledger is the `block` table (`block_no` PK, `block_id`,
`prev_hash`, `block_hash`), sealed via `db/prism_ledger.py::seal_block`. IDs follow
the `KP-*` convention (`KP-CLAIM-000NNN`, `KP-VQ-000NNN`). A conforming table:

```sql
-- persistent (must be added to the persistent section of db/build_prism_db.py,
-- NOT the derived/rebuilt section, or it will be dropped on every rebuild)
CREATE TABLE IF NOT EXISTS scholar_input (
    scholar_id      TEXT PRIMARY KEY,        -- 'KP-SI-000001'
    schema_version  TEXT NOT NULL,           -- '0.2'
    idea            TEXT NOT NULL,           -- the raw thought (required)
    draft_organ     TEXT,                    -- mobile's DRAFT layer/role guess; advisory only
    draft_diagnosis TEXT,                    -- optional
    draft_search_plan TEXT,                  -- optional draft keywords (NOT a Recoll lens)
    supervisor_brief TEXT,                   -- optional
    raw_notes       TEXT,                    -- optional
    voice_transcript TEXT,                   -- optional
    source          TEXT NOT NULL,           -- 'android_app' | 'desktop_manual'
    captured_ts     TEXT NOT NULL,           -- ISO-8601, when the idea was captured
    imported_ts     TEXT NOT NULL,           -- when it entered the desktop store
    status          TEXT NOT NULL,           -- controlled vocab, see below
    content_sha256  TEXT NOT NULL,           -- idea+notes hash, for dedupe
    became_question TEXT,                     -- FK: research_question this idea seeded (nullable)
    became_queue_id TEXT,                     -- FK: verification_queue.queue_id if it led there (nullable)
    decided_by      TEXT,                     -- 'user' on approve/reject; backend never initiates
    decided_ts      TEXT,
    rejection_reason TEXT,
    block_no        INTEGER                  -- ledger block that recorded the promotion/rejection
);

-- controlled vocab for scholar_input.status (mirror the taxonomy-table pattern
-- already used for queue_status / disposition):
CREATE TABLE IF NOT EXISTS scholar_input_status_taxonomy (
    status  TEXT PRIMARY KEY,
    meaning TEXT NOT NULL,
    added_block INTEGER
);
-- seed: raw_captured, imported_not_evidence, under_review,
--       approved_to_question, rejected_archived
```

Notes on the correction:
- **No separate `scholar_input_ledger` table.** We already have one ledger — the
  `block` chain. A promotion is a normal sealed block whose `inputs` names the
  `scholar_id` and whose `outputs` names the resulting `research_question` /
  `queue_id`. Do not fork a second ledger; that breaks single-chain provenance.
- **`status` is controlled vocab in its own taxonomy table**, exactly like
  `queue_status_taxonomy` and `disposition_taxonomy`, so the consistency validator
  (`scripts/00b_validate_db_consistency.py`) can check it. Free-text status is how
  drift starts.
- **`draft_organ` is advisory only.** Mobile's "organ" guess never writes to
  `verdict_disposition.layer_norm` or `functional_role`; those remain desktop-owned
  and text-derived.
- **Provenance class is distinct.** A `scholar_input` is *not* an
  `ingested_source` and gets no `artifact_hash` as if it were a corpus document.
  Its provenance is `scholar_origin` — a human thought, timestamped and hashed for
  dedupe, never a bibliographic source.

## 4. What I endorse from the Codex proposal (unchanged)

- Holding queue **separate** from `verification_queue` — correct, and now
  reinforced: they are different epistemic kinds, not just different stages.
- **Promotion requires explicit user approval; backend never auto-promotes** —
  correct, matches `no_auto_sampling` doctrine.
- **Rejections preserved for audit, never deleted** — correct, matches
  "exclusion marks, never deletes."
- **No API key on mobile; imports flow through the desktop** — correct and
  important; keeps secrets off the phone.
- **No Recoll from mobile, no ontology change from mobile, no grading on mobile** —
  all correct. Mobile is capture-only.
- **Two-axis truth stays a desktop act** — correct.

## 5. What I flag for correction before the mobile team builds

1. **Fix the data-flow diagram**: idea → *question/lens* → queue, not idea →
   queue. You cannot sample an idea. (§2)
2. **Drop Postgres types** (`UUID`/`JSONB`/`TIMESTAMP`) and the second ledger
   table; use the SQLite + `block`-chain + `KP-*` conventions above. (§3)
3. **`status` must be a taxonomy table**, not free text, so it is validator-checked.
4. **`draft_organ`/`draft_diagnosis` are advisory** and must be visually marked
   "draft, unverified" wherever Codex renders them — never shown as a disposition.
5. **Schema-version inconsistency**: §11 calls v0.2 "4 fields" then lists five
   (idea, organ, diagnosis, search_plan, supervisor_brief). Pin the v0.2 field set
   before the export format is frozen.
6. **Provenance class `scholar_origin`** must exist before the first import, so a
   mobile idea can never be mistaken for a corpus source.

## 6. Recommended sequencing (backend tasks, when authorised)

None of this is built yet and none should be until you authorise it. When you do,
the minimal correct order is:

1. Freeze the v0.2 field set + `scholar_origin` provenance class (design only).
2. Add `scholar_input` + `scholar_input_status_taxonomy` to the **persistent**
   section of `build_prism_db.py`; seed the status vocab; extend
   `00b_validate_db_consistency.py` to check it. Seal as one schema block.
3. Only then define the import path (a desktop-side importer, not a mobile-direct
   API) that lands rows as `imported_not_evidence`.
4. Promotion = a sealed block that converts an approved idea into a
   `research_question`, from which the existing kaleidoscope → queue → sampling
   pipeline runs unchanged.

Nothing above touches evidence, and the phone never holds a key or a corpus file.

---
*Design review, not evidence-bearing. Backend feedback for the Codex/mobile team.
Authored 2026-07-09. Changes no corpus or ledger state.*
