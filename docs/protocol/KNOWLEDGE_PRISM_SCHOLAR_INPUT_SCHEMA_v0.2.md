# KNOWLEDGE_PRISM — Scholar Input Schema v0.2
### Design-freeze specification · `scholar_input_not_evidence`

> **Status: FROZEN v0.2.** This is a design document only. No table is created, no
> database or ledger is modified, no code is written by this document. It defines
> the single authoritative format for mobile/desktop scholar inputs so that Codex
> UI work and Android export work can proceed against a fixed target.
> Authored 2026-07-09 by the backend/research-governance department.

---

## 0. Core principle (the one rule everything else serves)

**A scholar input is not evidence.**

A mobile or desktop idea may generate a research question, a retrieval lens, a
search plan, or a supervisor brief. It may **not**:

- become an evidence-bearing source;
- directly enter `verification_queue`;
- become a claim, disposition, functional role, concept verification, or
  ontology-core item.

An idea is a **research prompt** — the input that seeds the pipeline, never a
support inside it. The discipline exists to prevent *hunch-laundering*: the
researcher's own overnight thought re-entering the system and later being cited as
if a document had said it.

### Corrected data flow (authoritative)

```
scholar_input                      ← a captured idea (NOT evidence)
   ↓  approved_to_question         ← explicit user action, may be sealed as a block
research question / retrieval lens  ← the idea becomes a QUESTION, not a candidate
   ↓
Recoll / corpus retrieval           ← user-authorised; produces clues, not evidence
   ↓
verification_queue of real documents ← rows with file + path + target_file_sha256
   ↓  approved_to_sample
sampling                            ← bounded read of an actual text
   ↓
evidence review                     ← evidence_grade assigned
   ↓
functional interpretation           ← what the text DOES for the argument
   ↓
claim / ontology                    ← only if earned by external text
```

The idea seeds the top of the funnel. **External text still has to earn every
claim downstream.** That keeps the evidence chain unbroken.

---

## 1. Record identity

| Field | Type | Required | Meaning |
|---|---|---|---|
| `schema_version` | text | yes | Must be `"0.2"`. |
| `record_type` | text | yes | Must be `"scholar_input_not_evidence"`. The record announces its own non-evidential nature. |
| `scholar_id` | text | yes (assigned on import) | KP-style id, `KP-SI-000001`. Mobile may leave blank; desktop import assigns. |
| `source` | text | yes | One of `android_app`, `desktop_manual`, `desktop_import`. |
| `captured_ts` | text (ISO-8601) | yes | When the idea was captured on the originating device. |
| `imported_ts` | text (ISO-8601) | yes (on import) | When it entered the desktop store. Null until imported. |

## 2. Required content

| Field | Type | Required | Meaning |
|---|---|---|---|
| `idea` | text | **yes, non-empty** | The raw thought. This is the only obligatory content field. Everything else is advisory or governance. |

## 3. Optional advisory fields

All optional; may be empty strings. **Advisory only** — none of these ever writes to
an evidence, disposition, functional-role, or ontology table. They are drafts the
researcher jotted; the desktop pipeline re-derives the real values from text.

| Field | Type | Meaning |
|---|---|---|
| `draft_organ` | text | Researcher's guess at which research organ this idea serves (§6 vocab). Advisory. |
| `draft_diagnosis` | text | Researcher's own read of what the idea is about. Advisory. |
| `draft_search_plan` | text | Draft keywords the researcher would search. **Draft keywords, not a Recoll lens.** |
| `supervisor_brief` | text | A note to/from a supervisor. |
| `raw_notes` | text | Freeform notes. |
| `voice_transcript` | text | Native mobile speech-to-text output. |
| `tags` | text (comma-separated) | Free tags. Advisory; not corpus tags, not ontology terms. |
| `confidence` | text/number | Researcher's own subjective confidence in the idea. Never an evidence grade. |
| `project_title` | text | Which project/thesis the idea belongs to. |
| `course_or_context` | text | Course, seminar, or context of capture. |

## 4. Governance fields

| Field | Type | Meaning |
|---|---|---|
| `status` | text | Controlled vocab (§5). Lifecycle position of the input. |
| `content_sha256` | text | Hash of the canonical content (idea + notes), for dedupe and provenance. |
| `became_question` | text | Back-link: the research-question id this idea seeded, if approved. Null otherwise. |
| `became_queue_id` | text | Back-link: the `verification_queue.queue_id` this idea ultimately led to, if any. Null otherwise. |
| `decided_by` | text | `user` on approve/reject. **Backend never initiates a decision**, only records it. |
| `decided_ts` | text (ISO-8601) | When the decision was made. |
| `rejection_reason` | text | Optional reason if rejected. Preserved for audit. |
| `block_no` | integer | Ledger block that recorded the promotion or rejection, if a block was sealed. Null while merely stored. |

## 5. Controlled status vocabulary

`scholar_input.status` is drawn from exactly these five values (mirrors the
taxonomy-table pattern used for queue status and dispositions, so the consistency
validator can check it):

| Status | Meaning |
|---|---|
| `raw_captured` | Captured on the originating device (mobile/desktop), not yet imported to the desktop store. |
| `imported_not_evidence` | Landed in the desktop holding store. Present for review; **explicitly not evidence**; not in `verification_queue`. |
| `under_review` | The researcher is actively considering it. Still not evidence. |
| `approved_to_question` | User approved it to **seed a research question / retrieval lens**. This is the promotion — and it is a promotion *to a question*, never directly to the verification queue or to a claim. |
| `rejected_archived` | User rejected it. Preserved for audit, never deleted, never promoted. |

**Note the ceiling:** the highest status an idea can reach is `approved_to_question`.
There is no `approved_to_evidence`. An idea's journey ends by becoming a question;
from there the ordinary document pipeline takes over on real texts.

## 6. Valid draft organs

`draft_organ`, when present, must be one of the research-organ vocabulary below (or
null). **`draft_organ` is advisory only and never writes to `verdict_disposition`,
`functional_role`, or any ontology table.** It helps the researcher file a thought;
it does not classify evidence.

```
Title              Background            Statement_of_Problem   Research_Gap
Research_Questions Objectives            Scope                  Methodology
Conceptual_Framework  Literature_Clusters  Evidence_Needs       Case_Region_Time_Period
Chapterisation     Supervisor_Questions  Revision_Tasks         Unassigned
```

## 7. Validation rules

An import is **rejected before storage** unless all hold:

| Field | Rule | On failure |
|---|---|---|
| `schema_version` | equals `0.2` | reject; prompt for upgrade |
| `record_type` | equals `scholar_input_not_evidence` | reject; invalid record |
| `idea` | non-empty string | reject; idea required |
| `source` | one of `android_app`, `desktop_manual`, `desktop_import` | reject; unknown source |
| `captured_ts` | valid ISO-8601 | reject; parse error |
| `content_sha256` | matches recomputed content hash | reject; integrity failure |
| `draft_organ` | one of §6 organs, or null | reject; invalid organ |
| optional text fields | may be empty strings | accept |

Additional guards (from the mobile governance review): enforce a per-import size
limit; on a `content_sha256` collision with an existing row, warn the user of a
possible duplicate rather than silently importing.

## 8. Example records

### 8.1 Android voice/dictated idea

```json
{
  "record_type": "scholar_input_not_evidence",
  "_note": "This record is scholar input, not evidence.",
  "schema_version": "0.2",
  "scholar_id": null,
  "source": "android_app",
  "captured_ts": "2026-07-09T02:58:11+05:30",
  "imported_ts": null,
  "idea": "Maybe post-Soviet Central Asian security is better read as geopolitical imagination than as balance-of-power. Check whether Trenin frames Eurasia this way.",
  "draft_organ": "Conceptual_Framework",
  "draft_diagnosis": "constructivist / critical-geopolitics angle",
  "draft_search_plan": "eurasia, imagination, near abroad, regional order",
  "supervisor_brief": "",
  "raw_notes": "",
  "voice_transcript": "maybe post soviet central asian security is better read as geopolitical imagination than balance of power check whether trenin frames eurasia this way",
  "tags": "eurasia,imagination",
  "confidence": "hunch",
  "project_title": "Eurasian security imaginaries",
  "course_or_context": "PhD chapter 2",
  "status": "raw_captured",
  "content_sha256": "<computed on canonical content>",
  "became_question": null,
  "became_queue_id": null,
  "decided_by": null,
  "decided_ts": null,
  "rejection_reason": null,
  "block_no": null
}
```

### 8.2 Desktop manually entered synopsis fragment

```json
{
  "record_type": "scholar_input_not_evidence",
  "_note": "This record is scholar input, not evidence.",
  "schema_version": "0.2",
  "scholar_id": "KP-SI-000002",
  "source": "desktop_manual",
  "captured_ts": "2026-07-09T09:14:00+05:30",
  "imported_ts": "2026-07-09T09:14:00+05:30",
  "idea": "Chapter 3 needs a counter-case: a text that argues balance-of-power still explains Central Asian alignment. Find the strongest opposing account to sample as a foil.",
  "draft_organ": "Evidence_Needs",
  "draft_diagnosis": "",
  "draft_search_plan": "balance of power, central asia, alignment, hedging",
  "supervisor_brief": "Supervisor asked for a fair strongest-opponent.",
  "raw_notes": "keep it as a foil, not a strawman",
  "voice_transcript": "",
  "tags": "counter-case,foil",
  "confidence": "",
  "project_title": "Eurasian security imaginaries",
  "course_or_context": "PhD chapter 3",
  "status": "imported_not_evidence",
  "content_sha256": "<computed on canonical content>",
  "became_question": null,
  "became_queue_id": null,
  "decided_by": null,
  "decided_ts": null,
  "rejection_reason": null,
  "block_no": null
}
```

## 9. SQLite implementation note (NOT implemented here)

When implementation is authorised, the recommended structure — **SQLite types only,
KP-style ids, no Postgres `UUID`/`JSONB`, no second ledger** — is:

```sql
-- persistent section of db/build_prism_db.py (NOT the derived/rebuilt section)
CREATE TABLE IF NOT EXISTS scholar_input (
    scholar_id        TEXT PRIMARY KEY,     -- 'KP-SI-000001'
    schema_version    TEXT NOT NULL,        -- '0.2'
    record_type       TEXT NOT NULL,        -- 'scholar_input_not_evidence'
    source            TEXT NOT NULL,        -- android_app | desktop_manual | desktop_import
    captured_ts       TEXT NOT NULL,        -- ISO-8601
    imported_ts       TEXT,                 -- ISO-8601, null until imported
    idea              TEXT NOT NULL,        -- required content
    draft_organ       TEXT,                 -- advisory; one of §6 or null
    draft_diagnosis   TEXT,
    draft_search_plan TEXT,
    supervisor_brief  TEXT,
    raw_notes         TEXT,
    voice_transcript  TEXT,
    tags              TEXT,
    confidence        TEXT,
    project_title     TEXT,
    course_or_context TEXT,
    status            TEXT NOT NULL,        -- FK -> scholar_input_status_taxonomy.status
    content_sha256    TEXT NOT NULL,
    became_question   TEXT,                 -- research-question id, nullable
    became_queue_id   TEXT,                 -- verification_queue.queue_id, nullable
    decided_by        TEXT,                 -- 'user'
    decided_ts        TEXT,
    rejection_reason  TEXT,
    block_no          INTEGER               -- ledger block for a promotion/rejection
);

CREATE TABLE IF NOT EXISTS scholar_input_status_taxonomy (
    status      TEXT PRIMARY KEY,
    meaning     TEXT NOT NULL,
    added_block INTEGER
);
-- seed rows: raw_captured, imported_not_evidence, under_review,
--            approved_to_question, rejected_archived
```

Both tables belong in the **persistent** section of `build_prism_db.py` so they are
not dropped when the derived tables are rebuilt. The consistency validator
(`scripts/00b_validate_db_consistency.py`) should gain a check that every
`scholar_input.status` appears in `scholar_input_status_taxonomy`.

## 10. Ledger note

- **Imports may be stored without evidence promotion.** Landing a row as
  `imported_not_evidence` is not an evidence act and need not seal a block.
- **Approval to question may require a sealed block** — a state transition
  (`imported_not_evidence`/`under_review` → `approved_to_question`) that seeds a
  research question is a governed act and should be recorded.
- **Rejection may require a sealed block** — `rejected_archived` with its reason,
  for audit.
- **The ledger records the state transition, not the idea as evidence.** The block's
  `inputs` names the `scholar_id`; its `outputs` names the resulting research
  question or the archival decision. The raw idea lives in `scholar_input`, never in
  the block as a source.
- **No second ledger is created.** There is one hash-chained `block` table; scholar
  promotions and rejections are ordinary blocks on it.

## 11. Codex display rules

- Every scholar-input card must show the banner **`SCHOLAR INPUT — NOT EVIDENCE`**.
- `draft_organ` must be shown as **`DRAFT — unverified organ assignment`**.
- `draft_diagnosis` must be shown as **`DRAFT — unverified diagnosis`**.
- The approval action means **"seed research question,"** not "send directly to
  verification queue." The button label and confirmation copy must say so.
- Codex must **never** display a scholar input as evidence, and must never show a
  scholar input inside an evidence card, a claim, a disposition, or the ontology.

## 12. Android export rules (future app)

The mobile app is **capture-only**. It:

- captures ideas (typed or dictated) and exports them;
- exports **JSON or Markdown only**;
- runs **no Recoll**, holds **no corpus access**, does **no evidence grading**, takes
  **no ontology action**, has **no ledger access**;
- carries **no API key** and never talks to the backend directly — all imports pass
  through the desktop, which performs validation (§7).

Mobile `draft_organ`, `draft_search_plan`, and `draft_diagnosis` are drafts that
help the researcher think on the go; the desktop pipeline re-derives every real
value from text.

---
*Frozen design specification v0.2. Not evidence-bearing. Changes no corpus or
ledger state. Supersedes the schema sketch in SCHOLAR_INPUT_MOBILE_REVIEW.md §3.*
