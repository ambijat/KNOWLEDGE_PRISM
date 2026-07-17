# Obsidian Integration — Governance Rulings (Appendix A resolved)

> **Version:** 1.0 · **Author of rulings:** the researcher (Ambrish Dhaka)
> **Recorded by:** Claude (backend) · **Date:** 2026-07-16
> **Status:** AUTHORITATIVE. These rulings resolve the four matters parked in
> Appendix A of `KNOWLEDGE_PRISM_OBSIDIAN_INTEGRATION_CONTRACT_v0.1.md`.
> **Effect on v1.0:** the frozen Projection Contract v1.0, its four schemas,
> the validator, the fixture, and the Codex handoff are **unchanged** by these
> rulings — the rulings confirm and constrain the existing design; they do not
> reopen it.

This document is the decision record for the four governance questions. It is
read alongside `OBSIDIAN_PROJECTION_CONTRACT_v1.0.md`; where a ruling adds a
display obligation, it is noted as guidance for the *frontend* implementation,
not as a change to the frozen backend schema.

## Ruling 1 — Status-vocabulary reconciliation

The native Knowledge Prism backend status remains **authoritative**. For the
current ontology material the authoritative provenance status is
`design_hypothesis`. Obsidian may carry a projection/display status (e.g.
`extracted`), but it **must preserve and visibly expose** the original backend
provenance status. The projection status must never replace, conceal, or
upgrade the authoritative backend status.

Preferred display representation (frontend obligation):

```yaml
provenance_status: design_hypothesis
projection_status: extracted
canonical: false
```

**Consistency with v1.0:** the projection record already carries the
authoritative origin in `provenance.origin_table` / `provenance.reviewed`, and
the status map (§5) already caps `design_hypothesis` at projection status
`extracted` and never `canonical`. This ruling makes the *dual-visibility*
requirement explicit for the frontend. It is **not** a schema change; it is a
rendering obligation for Codex. If Codex finds the current `provenance` object
insufficient to render this triad, that is a concrete implementation question
to raise (see support boundary) — not licence to edit the frozen schema
unilaterally.

## Ruling 2 — ID-namespace authority

Existing stable backend identifiers are authoritative for live records. Obsidian
must not establish an independent identity namespace for live records.

- filenames are labels, not identities;
- title changes must not create new records;
- Obsidian links must resolve through stable backend IDs or a
  backend-maintained deterministic mapping;
- synthetic fixture identifiers may retain their current readable prefixes;
- any future live-export mapping must remain controlled by the backend contract.

**Consistency with v1.0:** matches contract §4 exactly (IDs authoritative,
filenames not; the `id_crosswalk` in the manifest is the single, backend-owned
place the two namespaces meet). The synthetic-fixture prefixes (`CON-`, `ENT-`,
…) are explicitly permitted to remain.

## Ruling 3 — Definition of canonical corpus

A record is canonical **only when** (1) it has passed the designated human
review and promotion procedure, **and** (2) that promotion has been recorded
through the appropriate ledger-sealed governance act.

None of the following make a record canonical: existence in SQLite; inclusion in
an ontology table; inclusion in a graph export; projection into Obsidian;
proposal acceptance; repeated researcher use; inclusion in a synthesis note.

Accordingly, the current **43 ontology nodes remain non-canonical
`design_hypothesis` records**. Proposal acceptance remains separate from
canonical promotion.

**Consistency with v1.0:** matches contract §5 and §7 (promotion is a separate,
human-gated, ledger-sealed act; acceptance never canonicalises).

## Ruling 4 — Proposal inbox persistence

The proposal inbox shall remain **file-based** for the controlled vertical
slice. Do not create a proposal database table at this stage. A database-backed
proposal workflow may be reconsidered only after the slice demonstrates a real
need for concurrent review, searchable workflow state, higher proposal volume,
migration controls, audit/retention rules, or ledger integration. Until such a
review occurs, the file-based inbox is authoritative.

**Consistency with v1.0:** matches contract §7 and §9 (inbox is files only; no
new canonical DB table).

## Frozen set (unchanged by these rulings)

Obsidian Projection Contract v1.0; the four JSON Schemas; protected-region merge
rules; closed predicate vocabulary; proposal lifecycle; decision-receipt format;
synthetic fixture; validator behaviour; Codex integration handoff.

v1.0 is **not** to be revised on stylistic preference or alternative
architecture — only on a concrete, implementation-blocking defect reported by
Codex.

## Guidance document (v0.1) — deliberately NOT sealed

The earlier v0.1 conceptual guidance document remains **unsealed** by ruling. It
stays unsealed until Codex completes the vertical slice and reports whether the
conceptual guidance is fully consistent with the implemented v1.0 contract.
After that review it may be revised and sealed through a separate governance act.
