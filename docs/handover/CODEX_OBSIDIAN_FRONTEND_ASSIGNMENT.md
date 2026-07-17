# Codex Frontend Assignment

## Objective

Build the minimum Obsidian-facing superstructure that allows a researcher to browse Knowledge Prism canonical records, visualise selected relationships and submit non-canonical proposals for backend review.

Do not redefine the corpus ontology or implement a competing backend.

Use the Claude backend integration contract and fixture as the source of truth.

## First action

Inspect only:

* the existing frontend or desktop application structure;
* current corpus-loading interfaces;
* Noteman integration points;
* Research Graph Exporter outputs;
* any existing file export controls;
* the backend-provided Obsidian contract, schemas and fixture.

Do not rescan the entire project if these components have already been mapped.

Before implementation, document how this work can coexist with the present Noteman and Research Graph Exporter workflows.

## Product principle

The frontend must visibly distinguish:

```text
Canonical Knowledge Prism content
from
Researcher-created interpretation
from
Pending proposal
```

A user must never mistake an Obsidian note or Canvas connection for a canonical corpus assertion merely because it is visually present.

## Task 1 — Obsidian workspace generator

Implement a generator that consumes the backend projection package and produces a valid Obsidian vault or Obsidian-compatible directory.

The initial logical structure should be:

```text
obsidian/
├── 00_dashboard/
├── 01_concepts/
├── 02_entities/
├── 03_sources/
├── 04_topics/
├── 05_projects/
├── 06_arguments/
├── 07_questions/
├── 08_canvases/
├── 09_synthesis/
├── 10_teaching/
├── proposals/
└── templates/
```

Adapt paths to the existing project conventions if required.

Do not install third-party plugins as part of the first milestone.

## Task 2 — Generated canonical notes

Generate concept, entity and source pages from backend projections.

Each generated note must show:

* title;
* Knowledge Prism stable ID;
* record type;
* status;
* canonical definition or summary;
* source references;
* typed relationships;
* last synchronisation information;
* clear indication that the section was generated.

Use protected regions:

```markdown
<!-- KP:GENERATED:START -->

[Generated canonical content]

<!-- KP:GENERATED:END -->

<!-- RESEARCHER:NOTES:START -->

## Researcher Notes

<!-- RESEARCHER:NOTES:END -->
```

Regeneration must preserve the researcher section.

## Task 3 — Visual status language

Use a restrained and consistent visual vocabulary in generated notes and any supporting application UI:

* Canonical
* Reviewed
* Proposed
* Researcher synthesis
* Rejected
* Superseded
* Synchronisation conflict

Do not rely only on colour. Include readable text labels.

## Task 4 — Dashboard

Create an Obsidian landing page showing:

* last export time;
* corpus or projection version;
* number of generated concepts;
* number of entities;
* number of sources;
* number of canonical relationships;
* number of pending proposals;
* synchronisation warnings;
* links to major indexes and canvases.

Use plain Markdown and standard Obsidian functionality for the first milestone.

Do not make Dataview a mandatory dependency.

## Task 5 — Index and navigation generation

Generate:

* concept index;
* entity index;
* source index;
* recent updates;
* canonical relationship summary;
* pending proposal index;
* synchronisation conflict index.

Indexes must be generated from the export manifest rather than inferred by scanning arbitrary researcher files.

## Task 6 — Canvas generation

Create one initial Obsidian Canvas from the backend fixture.

It must:

* contain nodes linked to real generated Markdown files;
* include at least one researcher synthesis note;
* distinguish canonical nodes from researcher-authored nodes;
* show labelled relationship edges;
* preserve Knowledge Prism IDs in node metadata or associated files;
* remain a visual projection rather than an executable workflow.

Moving a node must change only the Canvas layout. It must not alter backend relationships.

## Task 7 — Researcher synthesis note

Provide a template for researcher-authored synthesis:

```yaml
---
note_type: researcher_synthesis
status: researcher_synthesis
canonical: false
related_record_ids:
  - CON-000042
created_by: researcher
---
```

The template should include:

* research question;
* relevant canonical records;
* argument;
* counterargument;
* evidence needed;
* proposed connections;
* unresolved issues.

## Task 8 — Proposal authoring

Provide a controlled method to create backend-compatible proposals.

At the first milestone, this may be:

* a structured Markdown template plus exporter;
* a small form in the existing desktop frontend;
* or a simple local proposal editor.

The user should be able to prepare:

* relationship proposals;
* correction proposals;
* research questions;
* synthesis candidates.

The interface must state clearly:

> Submission creates a proposal for review. It does not alter the canonical Knowledge Prism corpus.

## Task 9 — Proposal export

Convert valid researcher proposals into the backend-defined JSON format and place them in the agreed proposal inbox.

Validate before export:

* required fields;
* stable source and target IDs;
* permitted predicate;
* non-empty rationale;
* valid proposal type;
* status fixed to `proposed`.

Do not permit the frontend to set a proposal to `canonical`, `accepted` or `reviewed`.

## Task 10 — Decision receipts

When the backend returns an accepted, revised or rejected proposal receipt, reflect it in Obsidian by:

* updating proposal status;
* linking to any resulting canonical record or relationship;
* preserving the original proposal;
* displaying the backend review message;
* recording synchronisation time.

Do not erase rejected proposals automatically.

## Task 11 — Synchronisation control

Expose a bounded synchronisation operation:

```text
Preview changes
→ show files to create, update, preserve or flag
→ apply changes
→ display manifest result
```

The preview should identify:

* new generated notes;
* changed generated sections;
* preserved researcher sections;
* title or path changes;
* superseded notes;
* malformed marker conflicts;
* files requiring manual review.

Do not silently overwrite conflict files.

## Task 12 — Coexistence with existing applications

Do not replace Noteman or Research Graph Exporter.

Document the intended separation:

* Noteman handles reviewed-corpus intake and note workflow already assigned to it.
* Research Graph Exporter handles graph-oriented export already assigned to it.
* Obsidian provides a human-readable, navigable and visual projection.
* The new work may consume their outputs or shared canonical exports but must not reproduce their full functionality.

Where existing components already generate Markdown, graph nodes or relationship files, reuse them.

## Task 13 — Controlled fixture implementation

Use only the backend-provided small fixture for the initial implementation.

Demonstrate:

1. generated canonical notes;
2. stable wikilinks;
3. one dashboard;
4. one Canvas;
5. preserved researcher notes after regeneration;
6. one relationship proposal;
7. one exported proposal JSON;
8. one backend decision receipt reflected in the vault;
9. one deliberately malformed file producing a safe conflict report.

## Restrictions

Do not:

* alter canonical JSON directly;
* invent backend statuses;
* redefine predicates;
* create a new corpus database;
* install unnecessary Obsidian plugins;
* turn Canvas into an executable workflow engine;
* undertake complete corpus migration;
* duplicate Noteman;
* duplicate Research Graph Exporter;
* perform unrelated redesign of the desktop application;
* overwrite user-authored material silently.

## Deliverables

Provide:

1. Obsidian workspace generator;
2. note templates;
3. generated fixture vault;
4. dashboard and indexes;
5. one working Canvas;
6. proposal-authoring mechanism;
7. proposal JSON exporter;
8. synchronisation preview and conflict handling;
9. decision-receipt rendering;
10. concise user instructions.

## Required report-back

Reply with a concise implementation report containing:

### Actions performed

Summarise the implemented frontend and Obsidian workflow.

### Files created

List each new file and its function.

### Files modified

List each modified file and the change made.

### User-visible outputs

Identify the generated vault, dashboard, Canvas, templates and proposal interface.

### Contract compliance

State which Claude schemas and fixture version were used.

### Validation performed

Provide commands, tests and results.

### Preservation test

Confirm whether researcher-authored sections survived regeneration.

### Proposal round-trip

Report proposal creation, export and backend decision receipt behaviour.

### Existing components reused

State which Noteman, graph-export or project components were reused.

### Actions deliberately omitted

State backend, migration, plugin, refactoring or prohibited work not undertaken.

### Risks or unresolved decisions

Limit this to concrete frontend integration issues.

### Handoff status

State whether the controlled vertical slice is ready for joint review.

### Next recommended step

Give one bounded next step only.
