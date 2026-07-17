<!-- KP GOVERNANCE HEADER — added when this contract was placed into guidance -->

> **Document class:** Guidance / architecture contract (governing)
> **Contract:** Knowledge Prism ↔ Obsidian Integration
> **Version:** v0.1
> **Status:** ADOPTED AS GUIDANCE (architecture principle set; not yet sealed in the ledger)
> **Owners:** Claude (backend / corpus semantics, schemas, validation, canonical status,
> export + proposal-ingestion contracts, synchronisation rules, provenance) ·
> Codex (Obsidian-facing files/views, dashboard, navigation, generated Markdown/Canvas
> presentation, proposal-authoring UI, sync controls)
> **Relationship to existing governance:** subordinate to `CHARTER.md`; does not alter the
> frozen scholar-input schema v0.2, the importer, the transition CLI, or the Android
> exchange contract v0.1 (block 29). Knowledge Prism remains the authoritative system of
> record; Obsidian is a projection + proposal surface only.
> **Not sealed:** this document has been recorded as guidance only. It has NOT been sealed
> into the hash-chained ledger and creates no ledger block. Seal as a bounded governance
> block when the architecture is ratified for build.

---

# Knowledge Prism–Obsidian Integration Contract

## Architectural principle

Knowledge Prism is the authoritative system of record.

Obsidian is a human-facing research, navigation, visualisation and synthesis workspace generated from, and linked to, the Knowledge Prism canonical corpus.

Obsidian must not become an independent or competing corpus.

## Base structure

The Knowledge Prism base structure contains:

* source registration;
* source and passage identifiers;
* extraction outputs;
* draft structured records;
* validation states;
* canonical records;
* concepts, entities, claims and relationships;
* typed graph edges;
* provenance;
* contradiction records;
* version and processing logs.

The base structure determines:

* what is known;
* where the knowledge came from;
* whether it has been reviewed;
* whether it is draft, proposed, reviewed or canonical;
* what evidence supports each claim or relationship.

## Superstructure

The Obsidian superstructure contains:

* generated concept pages;
* generated entity pages;
* source-reference pages;
* topic indexes;
* Obsidian Canvas maps;
* research questions;
* researcher annotations;
* argument notes;
* synthesis notes;
* chapter-planning notes;
* teaching notes.

The superstructure supports interpretation but does not silently alter canonical knowledge.

## Direction of authority

The authoritative flow is:

```text
Sources
→ Knowledge Prism extraction
→ draft records
→ human review
→ canonical corpus
→ Obsidian projection
```

The reverse flow is proposal-only:

```text
Obsidian annotation or proposed connection
→ proposal inbox
→ Knowledge Prism validation
→ accept, revise or reject
→ canonical corpus update
```

No Obsidian edit, link or Canvas movement may directly modify the canonical corpus.

## Two classes of Obsidian notes

### Generated corpus projections

These are produced from canonical Knowledge Prism records.

They must contain:

* stable Knowledge Prism record ID;
* record type;
* canonical status;
* source IDs;
* last synchronisation date;
* provenance;
* typed canonical relationships;
* a clear generated-content marker.

Generated sections must not be treated as manually authored notes.

### Researcher workspace notes

These are created or edited by the researcher.

They may include:

* interpretations;
* arguments;
* comparisons;
* research questions;
* tentative links;
* synthesis;
* teaching applications.

They must be marked as non-canonical unless subsequently accepted through Knowledge Prism review.

## Protected-note model

Where a generated note also allows researcher annotations, use protected regions:

```markdown
<!-- KP:GENERATED:START -->
Generated canonical content
<!-- KP:GENERATED:END -->

<!-- RESEARCHER:NOTES:START -->
Researcher-authored content
<!-- RESEARCHER:NOTES:END -->
```

Synchronisation may replace only the generated region. It must preserve the researcher region.

## Authority levels

Use the following common status vocabulary:

* `raw`
* `extracted`
* `proposed`
* `reviewed`
* `canonical`
* `researcher_synthesis`
* `rejected`
* `superseded`

A synthesis may be analytically sophisticated while remaining non-canonical.

## Stable identifiers

Do not use filenames as the only identifiers.

Records should retain stable IDs such as:

```text
SRC-000001
PAS-000001
CON-000001
ENT-000001
CLM-000001
REL-000001
PROP-000001
```

File names may change; stable IDs must not.

## Typed relationships

Do not reduce all relationships to generic Obsidian links.

Knowledge Prism relationships should retain predicates such as:

* `supports`
* `contradicts`
* `defines`
* `mentions`
* `causes`
* `enables`
* `constrains`
* `located_in`
* `part_of`
* `instrument_of`
* `associated_with`
* `precedes`
* `responds_to`

Obsidian may display these relationships, but the canonical predicate remains defined by Knowledge Prism.

## Initial repository arrangement

Use the existing project structure wherever possible. Do not reorganise the entire repository merely to imitate this example.

The target logical components are:

```text
protocol/
sources/
processing/
corpus/
graph/
obsidian/
exports/
logs/
```

These may map onto existing directories rather than requiring new top-level folders.

## Integration boundary

Claude owns:

* corpus ontology;
* schemas;
* validation;
* canonical status;
* export contract;
* proposal-ingestion contract;
* synchronisation rules;
* provenance safeguards.

Codex owns:

* Obsidian-facing files and views;
* dashboard;
* vault navigation;
* generated Markdown presentation;
* Canvas presentation;
* proposal-authoring interface;
* synchronisation controls and status display.

Codex must not redefine corpus semantics.

Claude must not redesign the GUI or duplicate frontend implementation.

## Non-goals for the first implementation

Do not initially attempt:

* autonomous canonisation of Obsidian notes;
* executable Canvas workflows;
* rewiring backend processes by moving Canvas nodes;
* unrestricted two-way synchronisation;
* installation of unnecessary Obsidian plugins;
* mass conversion of the entire corpus before the contract is tested;
* replacement of Noteman or Research Graph Exporter;
* replacement of the existing Knowledge Prism workflow.

## Required first milestone

Prove the architecture on a small, controlled fixture containing approximately:

* two sources;
* three concepts;
* three entities;
* four claims;
* five typed relationships;
* one researcher synthesis;
* one proposed relationship;
* one Obsidian Canvas.

The milestone is successful only when:

1. canonical records generate correct Obsidian notes;
2. provenance remains visible;
3. researcher annotations survive regeneration;
4. a proposed Obsidian relationship enters a review inbox;
5. the proposal does not become canonical automatically;
6. accepted or rejected proposal status is reflected back in Obsidian;
7. the Canvas links to actual generated and researcher-authored files.

## Efficiency and project discipline

* Inspect only the files needed to understand the relevant pipeline.
* Do not repeatedly scan the full repository.
* Reuse existing schemas, validators, exporters and GUI patterns.
* Do not build duplicate pipelines.
* Preserve backward compatibility unless a change is explicitly justified.
* Prefer an incremental vertical slice over a large speculative implementation.
* Record assumptions and unresolved contract questions.

---

## Appendix A — Open contract questions (Claude, recorded, not resolved)

These are flagged for the researcher's decision before any Obsidian build begins.
They do **not** modify existing backend state; they are notes on where this new
contract meets the frozen system.

1. **Status-vocabulary reconciliation.** This contract's authority levels
   (`raw`/`extracted`/`proposed`/`reviewed`/`canonical`/`researcher_synthesis`/
   `rejected`/`superseded`) are a *new* eight-value vocabulary. The existing
   scholar-input taxonomy is a *five*-value frozen set
   (`raw_captured`/`imported_not_evidence`/`under_review`/`approved_to_question`/
   `rejected_archived`), and evidence carries its own grades. A mapping table
   between the two must be defined before projection — the two vocabularies are
   not interchangeable and neither should silently absorb the other.
2. **Stable-ID namespaces.** The `SRC-/PAS-/CON-/ENT-/CLM-/REL-/PROP-` families
   are new. The backend already mints `KP-SI-`, `KP-RQ-`, `KP-VQ-`, `KP-BP-`,
   `KP-CLAIM-`. Whether the Obsidian IDs are new columns, an ID-crosswalk table,
   or a rename of existing families is an unresolved schema question — and any
   schema change is out of scope until explicitly authorised.
3. **Canonical corpus definition.** "Canonical corpus" here must be tied to a
   concrete backend surface (which tables/statuses constitute "canonical").
   Today nothing is in `concept_verified`/`ontology_core`; the projection has no
   canonical concept rows to render yet. The first milestone fixture is therefore
   a *synthetic* fixture, not a projection of live canonical state.
4. **Proposal inbox.** No `proposal` table exists in the backend today. The
   reverse (Obsidian → proposal → validation) flow requires a new proposal-inbox
   surface owned by Claude. This is the first genuine backend addition the
   contract implies; it should be designed and sealed as its own bounded block
   when authorised.
