# Claude — Obsidian Backend Assignment

> **Document class:** Handover / active backend assignment
> **Owner:** Claude (backend / research-governance)
> **Counterpart:** `docs/handover/CODEX_OBSIDIAN_FRONTEND_ASSIGNMENT.md`
> **Governs:** the authoritative contract for the Knowledge Prism ↔ Obsidian
> vertical slice (projection out, proposals in).
> **Subordinate to:** `CHARTER.md`, `CLAUDE_BACKEND_IDENTITY.md`,
> `docs/protocol/KNOWLEDGE_PRISM_OBSIDIAN_INTEGRATION_CONTRACT_v0.1.md`.
> **Status:** ACTIVE — vertical-slice contract delivered; full corpus migration NOT authorised.

## Purpose

Define and deliver the *minimum* authoritative backend contract through which:

```text
Knowledge Prism canonical corpus → validated projection package → Obsidian workspace
Obsidian researcher proposal → controlled proposal inbox → KP validation → accept / revise / reject
```

Codex must never have to infer corpus semantics on its own. This assignment
produces the schemas, the synthetic fixture, and the validator that make the
contract executable and testable, without touching any research state.

## Governing finding (read before building)

The task brief's illustrative paths (`canonical_records/<id>.json`,
`corpus/references.jsonl`, `sources/`, `graph/`, `exports/`) **do not exist in
this repository.** The Knowledge Prism corpus is the SQLite database
`db/knowledge_prism.db`. The projection contract is therefore defined **against
the real database surfaces** (`ontology_node`, `ontology_edge`, `claim`,
`source_registry`, `master_corpus`, and the `block` ledger for provenance), not
against a hypothetical JSON file-corpus.

Two consequences fix the shape of this slice:

1. **Nothing is canonical yet.** All 43 `ontology_node` rows carry
   `provenance_status = design_hypothesis`; `concept_verified` and
   `ontology_core` are empty. There are zero text-verified concepts to project.
2. **Only one edge predicate exists in data** (`fuses_with`). The rich predicate
   set (`supports`, `contradicts`, `instrument_of`, …) is the *contract's*
   controlled vocabulary, not the live graph.

Therefore the first-milestone fixture is **synthetic** (explicitly permitted by
the brief), and the projection status mapping treats `design_hypothesis` as
**non-canonical**. No live design-hypothesis node is presented to Codex as
canonical.

## Deliverables (all delivered by the sealing block named in this file's footer)

| # | Deliverable | Path |
|---|---|---|
| 1 | Ontology compatibility assessment | `docs/protocol/obsidian/ONTOLOGY_COMPATIBILITY_ASSESSMENT_v1.0.md` |
| 2 | Versioned projection contract | `docs/protocol/obsidian/OBSIDIAN_PROJECTION_CONTRACT_v1.0.md` |
| 3 | Stable record-ID + filename policy | contract §4 |
| 4 | Canonical-status mapping | contract §5 |
| 5 | Projection schema (JSON Schema) | `docs/protocol/obsidian/schemas/projection.schema.json` |
| 6 | Export-manifest schema | `docs/protocol/obsidian/schemas/export_manifest.schema.json` |
| 7 | Proposal-ingestion schema | `docs/protocol/obsidian/schemas/proposal.schema.json` |
| 8 | Proposal review lifecycle | contract §7 + `decision_receipt.schema.json` |
| 9 | Protected-region merge rules | contract §8 |
| 10 | Synthetic test fixture | `docs/protocol/examples/obsidian_vertical_slice/` |
| 11 | Automated schema + merge validation | `scripts/08_validate_obsidian_projection.py` |
| 12 | Codex handoff instructions | `docs/handover/CODEX_OBSIDIAN_INTEGRATION_HANDOFF.md` |

## Hard lines for this assignment

- The proposal inbox is **file-based** (`proposals/inbox/*.json`) for the slice.
  No new canonical DB table is created; no Obsidian input writes to
  `ontology_node`, `ontology_edge`, `claim`, or any evidence table.
- Accepted proposals do **not** auto-canonicalise. Promotion into the DB remains
  a separate, human-gated, ledger-sealed act using the existing
  `register_claim` / ontology mechanisms — out of scope here.
- No full-corpus migration. No changes to importer, transition CLI, GUI,
  Noteman, or Research Graph Exporter.
- Existing exporter `scripts/export_frontend_data.py` is the reuse anchor for
  reading the DB into public-safe JSON; this contract's projection builder is
  specified to sit alongside it, not replace it.

## First permitted Codex step

Consume the frozen projection schema + synthetic fixture below and build the
Obsidian workspace generator against them (Codex assignment Task 1–2), using the
fixture's `export_manifest.json` as the index source of truth. Codex must not
set any proposal to `accepted`/`reviewed`/`canonical`.
