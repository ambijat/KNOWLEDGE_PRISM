# Handover to Codex — Android Scholar-Input Exchange Contract v0.1

**From:** Claude (backend / research-governance)
**Cycle:** Android exchange contract-freeze (bounded specification cycle)
**Date:** 2026-07-10

---

## Exact contract document

`docs/protocol/KNOWLEDGE_PRISM_ANDROID_SCHOLAR_INPUT_EXCHANGE_v0.1.md`

This is the single authoritative, versioned, normative (MUST/SHOULD/MAY)
document. It is frozen at `exchange_contract_version = 0.1` against
`scholar_input_schema_version = 0.2`.

## Exact fixture locations

`docs/protocol/examples/android_exchange_v0.1/`

    android_single_valid_v0.1.json          (input; validated ✓)
    android_batch_valid_v0.1.json           (input; validated ✓)
    android_invalid_forbidden_field_v0.1.json (input; refused as designed ✓)
    android_ack_imported_v0.1.json          (spec fixture)
    android_ack_duplicate_v0.1.json         (spec fixture)
    android_ack_invalid_v0.1.json           (spec fixture)

## Android-owned responsibilities

- Offline-first capture UI over the 16 frozen `draft_organ` tokens (labels in
  UI, canonical tokens in payload).
- Local `client_record_id` (UUID v4), created at first save, stable across
  edits/exports.
- Local validation of required capture fields before enabling export.
- Set the four fixed values on every record: `schema_version=0.2`,
  `record_type=scholar_input_not_evidence`, `source=android_app`,
  `status=raw_captured`.
- Serialise `tags` as a semicolon string; `confidence` from {low,medium,high}.
- ISO-8601 + timezone timestamps.
- Advisory local canonical-hash computation for duplicate warnings.
- JSON file export (transport A) — single object or array.
- Read the desktop acknowledgement and drive the local mobile-state model.
- Security/privacy controls (§13): private storage, explicit export, no
  content in logs, non-identifying `device_alias`, plaintext-export warning.

## Backend-owned responsibilities (do NOT reimplement on mobile)

- `KP-SI-######` id allocation; `imported_ts`; `content_sha256`;
  force-null of all six governance fields; force `status=imported_not_evidence`.
- The `raw_captured → imported_not_evidence` transition (importer).
- All governance beyond import: `under_review`, `approved_to_question`,
  `rejected_archived` via `scripts/07_transition_scholar_input.py` (desktop only).

## Prohibited Android behaviours (hard)

Approve/reject/question/queue/sample records; assign `KP-SI`; populate any
governance field; create research questions; touch `verification_queue`,
evidence, claims, dispositions, functional roles, ontology, boundaries, or the
ledger; export any status other than `raw_captured`; implement live
bidirectional sync; embed credentials; introduce cloud services.

## Confirmed blockers

**None.** Contract is frozen and Android coding may begin.

Both previously documented ack gaps are **CLOSED in v0.1.1** (acknowledgement
amendment; see the contract §9, §11, §14, §17 and
`docs/protocol/examples/android_exchange_v0.1.1/`):

1. Duplicate acknowledgement now **echoes the existing `KP-SI` id** for an exact
   content-hash duplicate of an already-committed row.
2. The importer now **emits a machine-readable acknowledgement**:
   `--output-format json` (JSON only on stdout) or `--ack-file <path>`. The
   default `--output-format text` report is unchanged and byte-identical to
   v0.1. Per-record entries use the `acks[]` array with fields
   `client_record_id, result, backend_scholar_id, content_sha256, message,
   error_code`; `result ∈ {eligible, imported, duplicate_skipped, invalid,
   batch_refused, transport_failed}`.

The scholar-input payload schema is **unchanged at 0.2**; existing v0.1 exports
remain accepted. Android acknowledgement ingestion may now target the emitted
v0.1.1 structure (still a later task — see below).

## First permitted Android implementation task

> **Build the offline capture + local-draft store + JSON file export**, producing
> a single-record `android_single_valid_v0.1.json`-shaped file (and the array
> form for batches) that passes `scripts/06_import_scholar_input.py --dry-run`
> unchanged. Scope this first task to: capture form over the 16 organs, local
> `client_record_id`, the four fixed values, local field validation, and file
> export. **Do not** build acknowledgement ingestion, HTTP transport, or any
> sync in this first task — those are separate later tasks.

Acknowledgement ingestion, the mobile-state model wiring, and transports B–D
are subsequent tasks, each separately scoped.

## Do not

Begin the Android project beyond the single first task above; modify the
backend schema, importer, transition CLI, validators, GUI, or research state.
