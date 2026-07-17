# Scholar Input UI Handover

## Summary

v0.3 adds a Tkinter `Scholar Input Inbox` for the frozen
`scholar_input_not_evidence` schema v0.2.

This is a UI/display/report layer only. It validates local JSON, displays scholar
input cards, previews possible research-question seeds, and exports local
reports. It does not implement backend import or research-state mutation.

## Correct Flow

`scholar_input -> approved_to_question -> research question / retrieval lens -> retrieval -> verification_queue of real documents -> sampling -> evidence`

The UI must not create a shortcut from scholar input to `verification_queue`.

## Implemented UI

The new `Scholar Input Inbox` tab supports:

- `Load Scholar Input JSON`
- `Validate Against v0.2 Schema`
- `Preview Research Question Seed`
- `Export Scholar Input Summary`
- `Copy Supervisor Note`

The following buttons are explanatory-only placeholders:

- `Seed Research Question`
- `Reject and Archive`
- `Run Retrieval`
- `Send to Verification Queue`

The last action is explicitly blocked because only external retrieved documents
can enter `verification_queue`.

## Display Rules

Every loaded record displays:

`SCHOLAR INPUT — NOT EVIDENCE`

The card also shows:

- `DRAFT — unverified organ assignment`
- `DRAFT — unverified diagnosis`
- `Suggested keywords — not Recoll lens`
- `Not evidence`
- `Not in verification queue`
- `Not a claim`
- `Not ontology`

## Services

New services:

- `gui/services/scholar_input_schema.py`
- `gui/services/scholar_input_reports.py`

They perform local validation, seed-preview generation, sample-fixture creation,
and report export under `outputs/gui_reports/scholar_inputs/`.

## Validation Boundary

The UI validates:

- `schema_version == "0.2"`
- `record_type == "scholar_input_not_evidence"`
- non-empty `idea`
- allowed `source`
- allowed `status`
- ISO timestamp shape for `captured_ts` and optional `imported_ts`
- frozen `draft_organ` vocabulary
- `content_sha256` existence and, when feasible, a lightweight recompute

## Research-State Boundary

No database schema, evidence grade, disposition, queue status, ontology,
boundary, corpus, claim, research-state row, Recoll run, or sampling action is
changed by this UI.
