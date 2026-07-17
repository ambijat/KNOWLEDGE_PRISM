# Research Rumination and Organ Builder Handover

## Summary

v0.2 of the scholar-facing GUI has been revised from a narrow draft-intake model into a
Research Rumination and Organ Builder. It supports early research gestures before
a formal synopsis exists and keeps every epistemic escalation gated.

## Implemented Model

The GUI now supports this sequence:

`idea capture -> organ assignment -> draft diagnosis -> concept fit -> literature search plan -> supervisor brief`

The sequence is deliberately non-promotional. It helps the scholar organise,
diagnose, and prepare research material, but it does not verify claims or alter
the project ontology.

## Safety Contract

Every captured fragment is labelled:

`scholar_input_not_evidence`

Scholar fragments are seed material only. They may be organised, drafted,
diagnosed, mapped, and converted into search strategy. They may not become
evidence without corpus sampling.

The implementation does not write fragments into:

- evidence tables;
- ontology tables;
- queue tables;
- disposition tables;
- corpus tables;
- boundary tables;
- research-state tables.

## Scholar-Facing Tabs

### Idea Capture

Captures thoughts, dictated notes, rough titles, problem fragments, research
questions, objectives, concepts, cases or regions, time periods, theory hunches,
methodology hunches, literature clues, evidence needs, supervisor comments,
paragraphs, partial synopses, full synopses, and full drafts.

Supports `.txt`, `.md`, and `.docx` import into the text box before capture.

### Research Organ Builder

Organises fragments into these research organs:

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

Each organ shows status, confidence, fragment count, and a suggested next action.
Exported organ maps are CSV files under `outputs/gui_reports/rumination/`.

### Draft Diagnosis

Accepts generated organ text, pasted synopsis text, term-paper draft text,
chapter draft text, or literature review draft text. It detects present organs,
missing organs, weak organs, repeated lines, unclear research questions,
unsupported claim-like statements, methodology gaps, literature gaps, missing
scope, and weak chapterisation.

### Concept & Ontology Fit

Maps scholar concepts against Knowledge Prism without overclaiming. It uses
diagnostic labels only:

- `design_map_match_not_verified`
- `sample_supported_related`
- `queue_related`
- `absent_from_project`
- `needs_literature_search`

### Literature Search Plan

Converts fragments and organs into search terms, anchor-candidate categories,
theory-source needs, empirical-source needs, methodology-source needs, exclusion
terms, a Recoll query suggestion, and a Zotero/OpenAlex suggestion. It does not
run Recoll.

### Supervisor Brief

Generates a Markdown brief containing working title, problem, research question,
objectives, methodology hunch, concepts, case/region/time period, literature
clusters, evidence gaps, weak or missing organs, questions for supervisor, next
revision tasks, and a search-plan snapshot.

Every brief includes this provenance note:

`This brief is generated from scholar input and Knowledge Prism diagnostic logic. It is not evidence verification and does not promote any claim into the ontology.`

## Files

Main implementation files:

- `gui/knowledge_prism_app.py`
- `gui/services/draft_intake.py`
- `gui/services/draft_diagnosis.py`
- `gui/services/concept_fit.py`
- `gui/services/scholar_brief.py`
- `gui/services/rumination.py`

Documentation files:

- `docs/RESEARCH_RUMINATION_ORGAN_BUILDER_UX.md`
- `docs/handover/RESEARCH_RUMINATION_ORGAN_BUILDER_HANDOVER.md`

Local output directory:

- `outputs/gui_reports/rumination/`

## Mobile Future

The `ResearchFragment` and organ-map data model can be reused by a future mobile
app for quick note capture, voice-to-text import, tagging, organ assignment, and
sync/export into desktop Knowledge Prism.

The mobile path must preserve the same non-promotion rule: mobile fragments are
not evidence, not ontology, and not corpus rows.
