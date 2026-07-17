# Knowledge Prism Research Exoskeleton GUI

Local operational GUI for KNOWLEDGE_PRISM v0.3.

## Framework Choice

This implementation uses **Tkinter** because Streamlit and Gradio are not
installed in the current environment, while Tkinter is available in the Python
standard library.

## Run

From the project root:

```bash
python3 gui/knowledge_prism_app.py
```

## Scope

v0.3 is intentionally conservative:

- Loads project state from `db/knowledge_prism.db`.
- Adds a `Scholar Input Inbox` for frozen schema v0.2 JSON files.
- Lists multiple local scholar-input JSON records from
  `outputs/gui_reports/scholar_inputs/` with compact metadata and validation
  status.
- Validates scholar input records locally as `scholar_input_not_evidence`.
- Displays every scholar input with the `SCHOLAR INPUT — NOT EVIDENCE` banner.
- Previews research-question seeds without creating research-question IDs or
  backend rows.
- Exports validation reports, seed previews, and supervisor-note summaries under
  `outputs/gui_reports/scholar_inputs/`.
- Provides six scholar-facing rumination tabs plus the ten read-only operational tabs.
- Splits v0.2 scholar workflow logic into intake, diagnosis, concept-fit, and
  scholar-brief service modules.
- Captures scholar fragments as `scholar_input_not_evidence`.
- Accepts thoughts, dictated notes, rough titles, problem fragments, concepts,
  questions, objectives, methodology hunches, literature clues, supervisor
  comments, paragraphs, partial synopses, full synopses, and full drafts.
- Organises fragments into research organs before any draft or evidence workflow.
- Saves rumination logs, organ maps, search plans, synopsis skeletons, and
  supervisor briefs under `outputs/gui_reports/rumination/`.
- Saves draft research inputs under `outputs/gui_reports/drafts/`.
- Exports local Markdown, JSON, or CSV reports under `outputs/gui_reports/`.
- Displays verification queue and ontology status read-only.
- Shows disabled placeholders for Recoll, queue mutation, sampling, evidence
  verdicts, functional write actions, and ontology promotion.

## Safety

Default mode is read-only. Governed write mode can be toggled, but v0.3 still
keeps state-changing controls disabled. The GUI does not:

- run Recoll;
- sample PDFs;
- change queue status;
- alter evidence grades or dispositions;
- alter claims;
- promote concept-verified or ontology-core rows;
- adopt boundary proposals;
- delete corpus records.
- write scholar fragments into evidence, ontology, corpus, queue, disposition,
  boundary, or research-state tables.
- send scholar input directly to `verification_queue`.
- create research-question records from scholar input.

The GUI is local and may display local operational state. Public-facing exports
must still be separately checked before publication.

## Scholar Workflow

The first six tabs implement:

`idea capture -> organ builder -> draft diagnosis -> concept fit -> literature search plan -> supervisor brief`

This workflow supports research rumination and gradual organ-building. It can
help prepare a synopsis, search plan, or supervisor brief, but it does not verify
claims and does not promote any material into ontology.

## Scholar Input Inbox

The inbox implements the frozen scholar-input schema v0.2 as a local UI layer.
It loads JSON records, validates schema fields, displays warning labels for
draft organs/diagnoses/search terms, and previews a possible research-question
seed.

The inbox list shows filename, scholar id, schema version, source, captured
timestamp, status, draft organ, idea preview, and validation status. Selecting a
row loads the same not-evidence detail card; it does not import anything into
backend state.

Dropdown filters narrow the local list by status, source, and draft organ. The
Inbox shows a visible count such as `Showing 3 of 12 local scholar-input
records`, and `Reset Filters` returns all filters to `All`. The text search box
matches filename, scholar ID, idea text, tags, draft organ, source, status,
project title, and course/context; `Clear Search` restores the unsearched local
list while preserving the dropdown filter choices.

Correct flow:

`scholar_input -> approved_to_question -> research question / retrieval lens -> retrieval -> real documents -> verification_queue -> sampling -> evidence`

The Inbox never implements `scholar_input -> verification_queue`.
