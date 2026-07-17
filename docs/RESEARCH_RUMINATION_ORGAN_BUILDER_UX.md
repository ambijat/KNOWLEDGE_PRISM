# Research Rumination and Organ Builder UX

## Purpose

The Knowledge Prism GUI must support the scholar before a polished synopsis exists.
A scholar may begin with a thought, dictated note, rough title, problem fragment,
concept, case, reading clue, supervisor comment, partial paragraph, full synopsis,
or term-paper draft.

The GUI therefore treats early material as research rumination and helps the
scholar organise it into research organs. It does not treat that material as
evidence.

## Core Safety Principle

The scholar's thought is the seed of research, not evidence.

The system may organise it, challenge it, expand it into search plans, and
prepare it for supervision. It may not verify it without corpus sampling.

All captured fragments are labelled:

`scholar_input_not_evidence`

## Research Organs

The organ builder uses these research organs:

1. Title
2. Background
3. Statement of Problem
4. Research Gap
5. Research Questions
6. Objectives
7. Scope
8. Methodology
9. Conceptual Framework
10. Literature Clusters
11. Evidence Needs
12. Case / Region / Time Period
13. Chapterisation / Structure
14. Supervisor Questions
15. Revision Tasks

Each organ tracks assigned fragments, missing or present status, weak/medium/strong
confidence, and a suggested next action.

## Scholar-Facing Tabs

The desktop Tkinter GUI starts with six scholar-facing tabs:

1. `Idea Capture`
2. `Research Organ Builder`
3. `Draft Diagnosis`
4. `Concept & Ontology Fit`
5. `Literature Search Plan`
6. `Supervisor Brief`

Existing operational tabs remain available after these tabs, but the scholar's
workflow begins with rumination rather than a completed document.

## Workflow

The intended path is:

`idea fragment -> research organ -> draft diagnosis -> concept fit -> literature search plan -> supervisor brief`

This path is a writing and research-design aid. It does not create evidence,
queue rows, dispositions, ontology entries, boundary decisions, or corpus changes.

## Concept And Ontology Fit

Concept matching is diagnostic only. The GUI may report these labels:

- `design_map_match_not_verified`
- `sample_supported_related`
- `queue_related`
- `absent_from_project`
- `needs_literature_search`

A design-map match is never treated as verified ontology. Queue-related material
still requires governed sampling. Absent concepts become search-plan needs, not
evidence claims.

## Literature Search Plan

The literature-search tab converts fragments and organs into:

- search terms;
- anchor-candidate categories;
- theory-source needs;
- empirical-source needs;
- methodology-source needs;
- exclusion terms;
- a Recoll query suggestion;
- a Zotero/OpenAlex suggestion.

The tab does not run Recoll automatically.

## Local Storage

Rumination outputs are written only under:

`outputs/gui_reports/rumination/`

The expected files are:

- JSON rumination log;
- CSV organ map;
- Markdown supervisor brief;
- Markdown synopsis skeleton or search plan when exported.

These files are not evidence tables and are not ontology tables.

## Mobile Future

The same data model can later support a mobile idea-capture app. A mobile client
should capture quick notes, voice-to-text text, tags, organ assignments, and
exports back into the desktop Knowledge Prism workflow.

Mobile sync must preserve the `scholar_input_not_evidence` label and must not
write mobile fragments into evidence, ontology, corpus, queue, disposition,
boundary, or research-state tables.
