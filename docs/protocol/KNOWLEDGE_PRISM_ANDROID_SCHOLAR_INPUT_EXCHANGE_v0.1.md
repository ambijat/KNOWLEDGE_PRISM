# KNOWLEDGE_PRISM — Android ↔ Desktop Scholar-Input Exchange Contract

    exchange_contract_version   = 0.1   (this document)
    scholar_input_schema_version = 0.2  (frozen backend schema it targets)

**Status: FROZEN v0.1.** These are two independent version dimensions.
The exchange contract may evolve without changing the scholar-input schema,
and vice versa.

This document is **normative**. It uses **MUST / MUST NOT / SHOULD / MAY** in
the RFC-2119 sense. Sections marked *Implementation example* are illustrative
only and bind no one.

Authoritative surfaces this contract was validated against (2026-07-10):
`scripts/06_import_scholar_input.py` (278 lines), `gui/services/scholar_input_schema.py`,
the `scholar_input` table (schema v0.2, 26 columns) and
`scholar_input_status_taxonomy` (5 frozen statuses).

---

## 0. One-paragraph summary

The Android application is an **offline-first capture client**. It creates
scholar-input drafts, stores them privately on the device, and — only on
explicit user action — exports **schema-v0.2-conformant JSON** that the
existing desktop importer (`06_import_scholar_input.py`) already accepts
unchanged. Every exported record carries the fixed values
`schema_version=0.2`, `record_type=scholar_input_not_evidence`,
`source=android_app`, `status=raw_captured`. The desktop importer is the sole
authority that assigns `KP-SI-######` identifiers, computes `content_sha256`,
and lands the record at `imported_not_evidence`. Android performs **no**
governance act: it never approves, rejects, questions, queues, samples, or
touches evidence, ontology, or the ledger. The mobile ceiling is
`raw_captured`; everything above it is desktop-governed.

---

## 1. Governing boundary (normative)

The Android application **is** a capture client, **not** a research-governance
engine.

Android **MAY**:

- create scholar-input drafts;
- edit locally *unsubmitted* drafts;
- validate required capture fields before export;
- assign a local, non-authoritative `client_record_id`;
- store drafts in application-private offline storage;
- export or transmit schema-conformant scholar-input records;
- display import acknowledgements;
- display whether a record was `imported`, `duplicate_skipped`, or `invalid`.

Android **MUST NOT**:

- approve a record to a research question;
- reject or archive a persistent backend record;
- assign an authoritative `KP-SI-######` identifier;
- populate `became_question`, `became_queue_id`, `decided_by`, `decided_ts`,
  `rejection_reason`, or `block_no`;
- create research questions or retrieval lenses;
- contact `verification_queue`;
- create evidence, claims, dispositions, or functional roles;
- modify the ontology or any boundary;
- alter ledger state in any way.

Ceiling ladder (normative):

    Android ceiling      : raw_captured        (mobile-exported status)
    Desktop import lands  : imported_not_evidence
    Governed transitions  : under_review → approved_to_question | rejected_archived
                            (desktop only — scripts/07_transition_scholar_input.py)

A scholar input is **never** evidence and **MUST NEVER** be routed directly
into `verification_queue`.

---

## 2. Exchange model (normative)

The v0.1 exchange is:

    offline-first capture
      → explicit export/transfer (user-initiated)
      → desktop/backend import (06_import_scholar_input.py)
      → acknowledgement returned to the user

The client **MUST NOT** assume continuous cloud synchronisation. No live
bidirectional sync exists in v0.1. Approval outcomes (`approved_to_question`)
are **not** visible to Android in v0.1; they will surface only through a
future governed read channel (out of scope here).

### 2.1 Transport (normative)

**v0.1 supported transport: `A. JSON file export/import`.**

Rationale: the desktop importer already accepts a `.json` file (single object)
or a directory of `.json` files, and reads a `--input` path. A file export is
the smallest transport that requires **zero** backend change. The Android app
writes a `.json` file to shared/exportable storage (or offers it via the OS
share sheet as a file); the researcher moves it to the desktop; the importer
consumes it.

The following are **future extensions** and **MUST NOT** be assumed present in
v0.1:

- `B. Android share-sheet JSON export` — permitted as a convenience wrapper
  over transport A (it still produces the same JSON file), but not a distinct
  contract.
- `C. local-network HTTP transfer` — future; requires a backend HTTP receiver
  that does not yet exist.
- `D. USB/file-system transfer` — future; a manual variant of A.

Exactly **one** transport is mandatory for v0.1. Others are optional and
non-normative until separately frozen.

---

## 3. Normative Android record envelope

An exported payload is **either** a single JSON object (one record) **or** a
JSON array of such objects (a batch). See §10.

Each record object contains three field classes.

### 3.A Android-supplied capture fields

These map **1:1** onto the importer's accepted keys. Column semantics are
fixed by schema v0.2.

| Field | Req? | v0.1 rule |
|---|---|---|
| `schema_version` | MUST | fixed `"0.2"` (§6) |
| `record_type` | MUST | fixed `"scholar_input_not_evidence"` (§6) |
| `source` | MUST | fixed `"android_app"` (§6) |
| `status` | MUST | fixed `"raw_captured"` (§6) |
| `captured_ts` | MUST | ISO-8601 with timezone (§7) |
| `idea` | MUST | non-empty after trim; the only required content field |
| `draft_organ` | SHOULD | one of the 16 frozen tokens, or `null`/omitted → treated as unassigned (§7) |
| `draft_diagnosis` | MAY | free text or `""` |
| `draft_search_plan` | MAY | free text or `""` |
| `supervisor_brief` | MAY | free text or `""` |
| `raw_notes` | MAY | free text or `""` (hashed — §8) |
| `voice_transcript` | MAY | free text or `""` (hashed — §8) |
| `tags` | MAY | serialised string (§7.4) |
| `confidence` | MAY | free text; recommended vocabulary (§7.3) |
| `project_title` | MAY | free text or `""` |
| `course_or_context` | MAY | free text or `""` |

The importer requires, at minimum: correct `schema_version`, `record_type`,
`source`; a non-empty `idea`; a valid `captured_ts`; and — if present — a
`draft_organ` in the frozen vocabulary and a non-forbidden `status`.

### 3.B Mobile metadata fields (envelope-only)

**Contract design chosen (§9): a single flat JSON object per record that is
BOTH the schema-conformant scholar_input payload AND the carrier of
envelope-level mobile metadata as sibling keys.**

This is safe because the importer copies only a fixed allow-list of columns
(`COPY_FIELDS`) and **ignores every unknown key**. Validated 2026-07-10: a
single record carrying all seven metadata keys below imported cleanly, and
none of them reached the database.

| Envelope field | Purpose | Backend fate |
|---|---|---|
| `client_record_id` | local UUID, acknowledgement matching (§9) | ignored by importer |
| `client_generated_ts` | first-save time on device | ignored |
| `client_updated_ts` | last local edit time | ignored |
| `client_app_version` | mobile build | ignored |
| `client_platform` | e.g. `"android"` | ignored |
| `device_alias` | non-identifying label (§15) | ignored |
| `export_batch_id` | groups a batch export | ignored |
| `exchange_contract_version` | e.g. `"0.1"` (§16) | ignored |

Rules (normative):

- These fields **MUST** remain envelope-only. They **MUST NOT** be treated as
  authoritative database governance identifiers.
- They **are currently ignored** by the importer (they are neither copied nor
  rejected). This is the v0.1 behaviour and it is sufficient.
- The client **MUST NOT** overload `scholar_id`, `raw_notes`, `voice_transcript`,
  or any research-content field to carry transport metadata.
- Should a future backend release wish to persist any of these, that requires a
  frozen-schema extension — **not** permitted in this cycle.

### 3.C Backend-controlled fields — forbidden from Android

Android **MUST NOT** supply any of:

    scholar_id      imported_ts     content_sha256
    became_question became_queue_id decided_by
    decided_ts      rejection_reason block_no

Authoritative backend behaviour (from the importer, verified):

- `scholar_id` — allocated by the importer inside the commit transaction as
  gap-safe `KP-SI-{max+1:06d}`. Android-supplied value is not consulted.
- `imported_ts` — set by the importer at commit (`now_iso()`).
- `content_sha256` — computed by the importer (§8). Authoritative.
- `became_question`, `became_queue_id`, `decided_by`, `decided_ts`,
  `rejection_reason`, `block_no` — the six `GOVERNANCE_FIELDS`. The importer
  **rejects** any record where one of these is non-null/non-empty (validation
  error → record invalid → batch refused on commit), and additionally
  **force-nulls** all six on insert. So Android supplying one is a hard
  validation failure, by design.

---

## 4. Required fixed values (normative, frozen)

Every Android v0.1 export **MUST** set:

    schema_version = "0.2"
    record_type    = "scholar_input_not_evidence"
    source         = "android_app"
    status         = "raw_captured"

The desktop importer remains the sole authority for the transition
`raw_captured → imported_not_evidence`.

Android **MUST NOT** export any of:

    under_review   approved_to_question   rejected_archived   approved_to_evidence

`approved_to_evidence` is invalid **everywhere** in KNOWLEDGE_PRISM and does
not exist in the taxonomy.

> Note on importer tolerance: the importer's `ACCEPTABLE_SOURCE_STATUSES` also
> tolerates `imported_not_evidence`, `under_review`, `null`, and `""` as *input*
> (all forced to `imported_not_evidence` on write). Android narrows this: the
> **only** permitted exported `status` is `raw_captured`. The wider importer
> tolerance is a desktop-side convenience and **MUST NOT** be relied on by the
> mobile client.

---

## 5. Organ and vocabulary contract (normative)

The exported `draft_organ`, when present, **MUST** be exactly one of the 16
frozen canonical tokens (case-sensitive, underscores as shown):

    Title                  Background             Statement_of_Problem
    Research_Gap           Research_Questions     Objectives
    Scope                  Methodology            Conceptual_Framework
    Literature_Clusters    Evidence_Needs         Case_Region_Time_Period
    Chapterisation         Supervisor_Questions   Revision_Tasks
    Unassigned

Rules:

- `draft_organ` **MAY** be `null` or omitted. The importer treats
  `null`/`""`/absent identically (no organ assigned). The client **SHOULD**
  default to `Unassigned` for clarity, but `null` is accepted.
- The Android UI **SHOULD** present human-readable labels (e.g.
  "Statement of Problem") but **MUST** export the exact canonical token
  ("Statement_of_Problem"). Label↔token mapping lives entirely in the client.
- The client **MUST NOT** invent competing labels or tokens in the payload.

### 5.3 `confidence`

`confidence` is **free text** in the backend (no enum enforced). The Android
client **SHOULD** constrain the UI to a recommended vocabulary —
`low` / `medium` / `high` — and export the lowercase token. Free text is
accepted by the backend but discouraged for consistency.

### 5.4 `tags`

`tags` is a single **string** column. The client **MUST** serialise multiple
tags into one string using a **semicolon** separator, e.g. `"buffer-state;security;ontology"`.
No JSON array; no comma (commas appear inside tag phrases). Empty → `""`.

### 5.5 Timestamps

All timestamps (`captured_ts`, and the envelope `client_*_ts`) **MUST** be
ISO-8601 **with an explicit timezone offset** (e.g. `2026-07-10T09:15:00+00:00`
or a `Z` suffix, which the importer normalises). UTC is **RECOMMENDED**.
The importer parses `captured_ts` via `datetime.fromisoformat` after replacing
`Z`; a value without offset parses but is ambiguous and is **discouraged**.

---

## 6. Canonical content hash (normative, frozen)

The canonical content hash is frozen **identically** to the backend and GUI:

    content_sha256 = SHA-256(
        NFC( idea + "\n" + raw_notes + "\n" + voice_transcript )
    )   hex, lowercase

Rules:

- Fields hashed, in fixed order: `idea`, `raw_notes`, `voice_transcript`.
- Each absent-or-null field → **empty string** (absent and null are identical).
- Join with a **single** `"\n"` (U+000A line feed) between the three fields.
- **Unicode NFC**-normalise the joined string, encode **UTF-8**, take SHA-256,
  emit lowercase hex.
- Governance / db-generated fields (`scholar_id`, `imported_ts`,
  `content_sha256`, `status`, and the six governance fields) are **excluded**.

Client behaviour:

- The Android client **SHOULD** compute this hash locally to warn the user of
  an obvious local duplicate before export.
- Any Android-computed hash is **advisory only**. The client **MUST NOT** place
  it in `content_sha256` (a forbidden backend field, §3.C), and **MUST NOT**
  attempt to override the backend-generated value.
- The **desktop importer remains authoritative** for `content_sha256`.

---

## 7. Local Android identity (normative)

`client_record_id`:

- **MUST** be a UUID (RFC 4122, v4 RECOMMENDED) — globally unique enough for a
  single device/installation;
- **MUST** be created when the draft is first saved;
- **MUST** be stable across local edits and across re-exports of the same draft;
- **MUST NEVER** be treated as, or mapped to, `scholar_id`;
- **MUST NEVER** be used to infer approval or any governance state;
- **SHOULD** be used only for acknowledgement matching (§12).

Where it resides: as an **envelope-level sibling key** in the same JSON object
(§3.B). The current v0.2 importer does not reject unknown fields — it ignores
them — so `client_record_id` travels with the record and is simply not
persisted. **No backend schema change is made in this cycle to accommodate it.**

---

## 8. Batch format (normative)

v0.1 supports **both** a single-record payload (one JSON object) and a
multi-record batch (a JSON array of objects). Both are already accepted by the
importer (verified).

Frozen batch semantics:

- **batch schema version** — the batch inherits `exchange_contract_version=0.1`;
  there is no separate batch envelope object in v0.1 (the batch *is* the JSON
  array). A wrapping object **MAY** be added in a future version.
- **batch identifier** — carried per-record as the envelope field
  `export_batch_id` (ignored by the backend; used only for client-side and
  acknowledgement grouping).
- **record ordering** — the importer processes array elements in order and
  previews/assigns `KP-SI` ids in that order. Ordering is preserved but
  **MUST NOT** be relied on for meaning.
- **all-or-nothing validation** — **normative and enforced.** On `--commit`,
  if **any** record in the batch is invalid, the importer refuses the **entire**
  batch and writes nothing (`COMMIT REFUSED`, rc=2). Verified.
- **duplicate treatment** — duplicates (by content hash) are **skipped**, not
  errors; the rest of the batch may still commit. Intra-batch duplicates are
  also detected (second occurrence skipped).
- **mixed valid/invalid** — the presence of one invalid record blocks the whole
  commit. There is **no per-record quarantine.** The client **MUST NOT** promise
  the user that valid records in a mixed batch will land.
- **maximum recommended batch size** — **SHOULD NOT exceed 500 records** per
  export file in v0.1 (advisory; keeps a single transaction and one
  acknowledgement file manageable). No hard backend limit is imposed.

---

## 9. Duplicate semantics (normative)

The backend's **only** exact-duplicate rule is **canonical content hash**
(§6) equality against existing rows (and within the batch).

Four cases, frozen:

| Case | Backend view | Acknowledgement |
|---|---|---|
| same `client_record_id`, unchanged content | backend has no memory of `client_record_id`; decided purely by hash | `duplicate_skipped` if the hash already exists, else `imported` |
| same canonical content hash (any origin) | exact duplicate | `duplicate_skipped` |
| edited record, same `client_record_id`, **changed** content | new hash → not a duplicate | `imported` as a **new** record (see §12) |
| same content, **different** `client_record_id` | same hash → duplicate | `duplicate_skipped` |

Acknowledgement `result` values (frozen, §13):

    imported          duplicate_skipped   invalid
    batch_refused     transport_failed

Rules:

- The client **MUST NOT** interpret `duplicate_skipped` as meaning its local
  record received a new `KP-SI` identifier. It did not.
- Acknowledgements **SHOULD** report the already-existing backend `KP-SI`
  identifier for an exact duplicate so the client can reconcile.

> **BOUNDED CONTRACT GAP (§18, non-blocking):** the current importer's duplicate
> path prints only the content sha, **not** the existing `KP-SI-######`. So for
> `duplicate_skipped`, `backend_scholar_id` **will be null in v0.1**. This is a
> documented gap, not invented behaviour. A one-line importer enhancement
> (look up `scholar_id` by `content_sha256` and include it in the report) would
> close it; that enhancement is **out of scope** for this freeze cycle.

---

## 10. Edit and resubmission semantics (normative)

**Before first successful import:** the same `client_record_id` MAY be edited
locally and re-exported freely. Nothing is authoritative yet.

**After a successful import:** a changed canonical content hash **MUST NOT**
silently overwrite the existing backend record — and it **cannot**, because the
importer only ever INSERTs and never UPDATEs `scholar_input`.

**Chosen v0.1 behaviour: `A. create a new scholar-input submission`.**

When the user edits an already-imported draft and re-exports, the new content
hash differs, so the importer treats it as a **new** record and assigns a
**new** `KP-SI` id. The client **SHOULD** make this explicit in the UI ("this
will be submitted as a new record; the earlier submission is unchanged on the
desktop"). Provenance is preserved because both submissions persist
independently; neither mutates the other.

Options B (explicit "submit as revised record") and C (revision-link protocol)
are **future extensions** and are **NOT** part of v0.1. The backend performs
**no** mutation of imported scholar inputs in v0.1.

---

## 11. Acknowledgement envelope (specification)

> The importer does **not** yet emit a machine-readable acknowledgement file
> (it prints a human-readable report to stdout). The structure below is a
> **specification fixture** for the future desktop-side acknowledgement writer
> and the Android reader. It is frozen as a contract target; producing it is a
> future desktop task.

Acknowledgement object (batch-level with per-record entries):

    {
      "ack_schema_version": "0.1",
      "batch_id": "<export_batch_id or synthesised>",
      "processed_ts": "<ISO-8601 UTC>",
      "acks": [
        {
          "client_record_id": "<uuid from the submitted record>",
          "result": "imported | duplicate_skipped | invalid | batch_refused | transport_failed",
          "backend_scholar_id": "KP-SI-###### | null",
          "content_sha256": "<hex> | null",
          "message": "<short human-readable, no private content, no SQL, no paths>"
        }
      ]
    }

Field nullability & rules:

- `backend_scholar_id` — non-null only for `result=imported`; **null** for
  `duplicate_skipped` in v0.1 (§9 gap), `invalid`, `batch_refused`,
  `transport_failed`.
- `content_sha256` — present for `imported` and `duplicate_skipped`; null for
  `invalid`/`batch_refused`/`transport_failed`.
- Acknowledgements are **both** batch-level (the wrapper) **and** record-level
  (each `acks[]` entry). Android matches an entry to a local draft **only** via
  `client_record_id`.
- Android **MAY** mark a local draft "accepted by desktop" **only** upon
  receiving `result=imported` (or `duplicate_skipped`) for its
  `client_record_id`.
- "Accepted by desktop" **MUST NOT** be shown as "approved to question."
  `approved_to_question` is invisible to Android in v0.1 and reachable only
  through a future governed read channel.
- v0.1 has **no** live bidirectional sync.

---

## 12. Offline Android local-state model (normative)

Mobile-only UI states — **distinct** from backend governance statuses and
**never** exported as `status`:

    draft_local            (being written; not yet ready)
    ready_to_export        (validated locally, awaiting export)
    exported_unacknowledged(exported; no ack yet)
    imported_acknowledged  (ack result=imported received)
    duplicate_acknowledged (ack result=duplicate_skipped received)
    export_failed          (transport failed)
    invalid_local          (failed local validation, or ack result=invalid)

Mapping rule (normative):

    mobile UI state  ≠  backend governance status

The only backend `status` Android ever writes into a payload is
`raw_captured`. The mobile states above are a **local** lifecycle and MUST NOT
leak into the exported `status` field. Android MAY display a backend status
(e.g. `imported_not_evidence`) **only** if it has actually received an
acknowledgement carrying it.

---

## 13. Security and privacy (normative)

- Local drafts **MUST** be stored in application-private storage.
- Export **MUST** require an explicit user action (no background auto-export).
- `raw_notes` and `voice_transcript` are **sensitive**; the client **MUST NOT**
  write full record content to debug logs.
- No secrets/credentials **MUST** be embedded in the APK.
- Transport files **SHOULD** use predictable but non-sensitive names, e.g.
  `kp_scholar_export_<export_batch_id>.json`. File names **MUST NOT** contain
  record content.
- Temporary exports **SHOULD** be removable by the user.
- Acknowledgements **MUST NOT** reproduce full private content (a short
  `message` only).
- `device_alias` **MUST** be a user-set, non-identifying label. The client
  **MUST NOT** use IMEI, Android advertising ID, phone number, MAC, or any
  account identifier.
- **Encryption of the v0.1 file export is DEFERRED** with an explicit warning:
  the exported `.json` is **plaintext**. The UI **MUST** warn the user that the
  export file contains their notes in clear text and **SHOULD** advise deleting
  it after successful desktop import. Encrypted transport is a future extension.

---

## 14. Version negotiation (normative)

- **Supported schema version** (`0.2`): process normally.
- **Older schema version**: the Android client **MUST NOT** silently upgrade or
  transform. It **SHOULD** refuse to export under a schema it no longer supports
  and prompt the user to update the app.
- **Newer / unknown schema version**: the client **MUST NOT** silently
  downgrade or fabricate fields. The desktop importer remains authoritative and
  will reject a `schema_version != "0.2"` record outright (verified: validation
  error). The client **SHOULD** surface `INVALID_SCHEMA_VERSION` rather than
  attempt a transform.

Frozen:

    exchange_contract_version    = 0.1
    scholar_input_schema_version = 0.2   (these are independent dimensions)

---

## 15. Error contract (normative)

Stable machine-readable error codes → recommended user-facing Android message
(the message is advisory; the code is frozen):

| Code | Cause (backend/importer or transport) | User-facing message (SHOULD) |
|---|---|---|
| `INVALID_SCHEMA_VERSION` | `schema_version != "0.2"` | "This record uses an unsupported schema. Update the app." |
| `INVALID_RECORD_TYPE` | `record_type` wrong | "Internal record type error. Update the app." |
| `INVALID_SOURCE` | `source` not `android_app` | "Export source error." |
| `INVALID_STATUS` | `status` not `raw_captured` (or a forbidden governed status) | "Invalid capture status." |
| `EMPTY_IDEA` | `idea` empty/missing | "Please enter an idea before exporting." |
| `INVALID_DRAFT_ORGAN` | organ not in the 16-token vocab | "Choose a valid section (organ)." |
| `FORBIDDEN_GOVERNANCE_FIELD` | a governance field was supplied | "Internal error: governance field present. Report this." |
| `DUPLICATE_CONTENT` | content hash already present | "This note was already imported." |
| `BATCH_ATOMIC_REFUSAL` | one+ invalid records in a committed batch | "The batch had invalid records; nothing was imported. Fix and resend." |
| `TRANSPORT_FAILURE` | file could not be written/moved/read | "Export/transfer failed. Try again." |
| `ACKNOWLEDGEMENT_UNREADABLE` | ack file malformed/unparseable | "Couldn't read the desktop response." |

Errors **MUST NOT** expose stack traces, SQL, raw private filesystem paths, or
full record content.

---

## 16. Compatibility matrix

Legend — **AS** already supported by current backend · **SO** specification-only
(no backend code needed for v0.1) · **BG** backend gap · **AR** Android
responsibility.

| Contract requirement | AS | SO | BG | AR |
|---|:--:|:--:|:--:|:--:|
| JSON file import (single object) | ✅ | | | ✅ (write file) |
| JSON batch import (array) | ✅ | | | ✅ |
| Fixed values `0.2 / scholar_input_not_evidence / android_app / raw_captured` | ✅ | | | ✅ (set them) |
| Force status→`imported_not_evidence` on write | ✅ | | | |
| `KP-SI` id allocation (gap-safe max+1) | ✅ | | | |
| `content_sha256` computed by backend | ✅ | | | |
| Canonical hash parity (Android advisory copy) | ✅ | | | ✅ (compute locally) |
| Governance fields force-null + reject-if-supplied | ✅ | | | ✅ (never send) |
| 16-organ vocabulary enforcement | ✅ | | | ✅ (constrain UI) |
| Unknown envelope metadata ignored (`client_record_id`, …) | ✅ | | | ✅ (carry as siblings) |
| Batch all-or-nothing atomic refusal | ✅ | | | ✅ (warn user) |
| Duplicate skip by content hash | ✅ | | | |
| Duplicate ack echoes existing `KP-SI` id | | | ⚠️ | |
| Machine-readable acknowledgement file | | ✅ | ⚠️ | ✅ (read it) |
| `tags` semicolon serialisation | ✅ (free string) | ✅ (convention) | | ✅ |
| `confidence` recommended vocab | ✅ (free string) | ✅ (convention) | | ✅ |
| Local mobile-state model | | ✅ | | ✅ |
| Error-code taxonomy | | ✅ | | ✅ (map codes) |
| Version negotiation refusal | ✅ (rejects bad schema) | ✅ | | ✅ |
| Encryption of export file | | | | deferred (§13) |

Backend-gap classification:

- **Duplicate ack does not echo existing `KP-SI` id** — *non-blocking
  enhancement.* One-line importer change; not required for Android to begin.
- **No machine-readable acknowledgement file emitted** — *future
  synchronisation feature.* The importer's stdout report is sufficient for a
  first manual-file workflow; a structured ack writer is a desktop task, not an
  Android blocker.

**There are no blockers before Android coding.** Both gaps are enhancements
Android can code around (it can proceed on stdout/manual acknowledgement and
on hash-only duplicate detection).

---

## 17. Fixtures

Location: `docs/protocol/examples/android_exchange_v0.1/`

Input fixtures (validated against `scripts/06_import_scholar_input.py` on a
disposable DB copy, 2026-07-10):

| Fixture | Validation result |
|---|---|
| `android_single_valid_v0.1.json` | dry-run valid; commit → `KP-SI` assigned, status `imported_not_evidence`; envelope metadata ignored |
| `android_batch_valid_v0.1.json` | dry-run valid (2 records); commit → both imported atomically |
| `android_invalid_forbidden_field_v0.1.json` | invalid (`became_question` supplied); commit **REFUSED** rc=2 |

Acknowledgement fixtures (specification only — importer does not yet emit this
structure):

| Fixture | Note |
|---|---|
| `android_ack_imported_v0.1.json` | `result=imported`, backend id present |
| `android_ack_duplicate_v0.1.json` | `result=duplicate_skipped`, `backend_scholar_id=null` (documents the §9 gap) |
| `android_ack_invalid_v0.1.json` | `result=invalid`, `FORBIDDEN_GOVERNANCE_FIELD` |

Fixtures contain **no** real scholar content.

---

## 18. Android readiness

    contract frozen and Android coding may begin

The first permitted Android implementation task and the full Codex handover are
in `docs/handover/ANDROID_EXCHANGE_CONTRACT_HANDOVER.md`.

---

*Frozen under exchange_contract_version 0.1 against scholar_input schema v0.2.
Sealed in the KNOWLEDGE_PRISM ledger (see handover for block number).*
