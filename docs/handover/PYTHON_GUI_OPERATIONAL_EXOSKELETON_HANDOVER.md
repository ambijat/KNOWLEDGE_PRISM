# Python GUI Operational Exoskeleton Handover

**Date:** 2026-07-09  
**Implementation:** v0.1 local Tkinter GUI  
**Entry point:** `gui/knowledge_prism_app.py`

## Purpose

The Python GUI is the local operational counterpart to the static public front
end. It helps the scholar move from research input toward governed outputs while
preserving the project rule that clues, queues, sampled support, design maps,
and verified ontology are distinct states.

## Framework Choice

Tkinter was selected because Streamlit and Gradio are not installed in the
current environment, while Tkinter is available in the Python standard library.

## Implemented Files

- `gui/knowledge_prism_app.py`
- `gui/services/db_access.py`
- `gui/services/project_state.py`
- `gui/services/query_lens.py`
- `gui/services/report_writer.py`
- `gui/services/safety.py`
- `gui/services/__init__.py`
- `gui/README.md`

## Implemented Tabs

1. Research Input
2. Query Lens
3. Retrieval Console
4. Verification Queue
5. Sampling Workbench
6. Evidence Review
7. Functional Interpretation
8. Ontology Status
9. Reports and Exports
10. Project State

## v0.1 Working Features

- Load current project state from SQLite.
- Show ledger/action-log verification status.
- Show read-only verification queue rows.
- Show read-only evidence rows and functional-role rows.
- Show design-map ontology status separately from verified ontology.
- Draft scholar research input.
- Generate a transparent query-lens preview.
- Export research input, query lens, queue snapshot, ontology status, and
  project state as Markdown, JSON, or CSV.
- Keep state-changing workflow controls disabled with explanatory messages.

## Safety Boundaries

The GUI does not run Recoll, sample texts, OCR files, approve sampling, create
evidence verdicts, alter queue status, promote evidence grades, change
dispositions, promote ontology, adopt boundary proposals, or modify corpus
records.

Governed write mode is visible as a future safety gate, but v0.1 keeps
state-changing buttons disabled even when it is toggled.

## Data Sources

The GUI reads these SQLite tables:

- `block`
- `master_corpus`
- `verification_queue`
- `boundary_proposal`
- `verdict_disposition`
- `functional_role`
- `ontology_node`
- `ontology_edge`
- `claim`

It also invokes existing verification commands:

- `python3 db/prism.py verify`
- `python3 scripts/04_log_agent_action.py verify`

## Exports

Local outputs are written under:

- `outputs/gui_reports/`
- `outputs/gui_reports/drafts/`

Draft research inputs are labelled `draft_only_not_evidence`. Query lenses are
labelled `planning_only_not_retrieval`.

## Next Safe Step

Add a governed write-mode implementation for one narrow action only:
`Export Queue` plus an action-log entry for the export, still without queue
mutation.
