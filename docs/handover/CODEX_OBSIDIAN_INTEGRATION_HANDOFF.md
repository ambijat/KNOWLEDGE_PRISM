# Codex Handoff — Obsidian Integration (backend deliverables ready)

> **From:** Claude (backend) · **To:** Codex (frontend/GUI/Obsidian views)
> **Date:** 2026-07-16 · **Status:** contract + schemas + validator + fixture frozen at v1.0
> **Read first:** `CHARTER.md`, then
> `docs/protocol/KNOWLEDGE_PRISM_OBSIDIAN_INTEGRATION_CONTRACT_v0.1.md` (guidance),
> then `docs/protocol/obsidian/OBSIDIAN_PROJECTION_CONTRACT_v1.0.md` (the build target).

## What is ready for you

| # | Deliverable | Path |
|---|---|---|
| 1 | Ontology compatibility assessment | `docs/protocol/obsidian/ONTOLOGY_COMPATIBILITY_ASSESSMENT_v1.0.md` |
| 2 | Projection contract (ID policy §4, status map §5, predicates §6, lifecycle §7, merge §8) | `docs/protocol/obsidian/OBSIDIAN_PROJECTION_CONTRACT_v1.0.md` |
| 3 | Projection JSON Schema | `docs/protocol/obsidian/schemas/projection.schema.json` |
| 4 | Export-manifest schema | `docs/protocol/obsidian/schemas/export_manifest.schema.json` |
| 5 | Proposal schema | `docs/protocol/obsidian/schemas/proposal.schema.json` |
| 6 | Decision-receipt schema | `docs/protocol/obsidian/schemas/decision_receipt.schema.json` |
| 7 | Validator (schema + merge) | `scripts/08_validate_obsidian_projection.py` |
| 8 | Synthetic vertical-slice fixture | `docs/protocol/examples/obsidian_vertical_slice/` |

## The contract in one paragraph

Knowledge Prism is authoritative. It emits a **projection package** (records +
one `export_manifest.json`) that Obsidian renders. Obsidian writes **proposals**
into a file-based inbox; a human decides; KP emits a **decision receipt**.
Acceptance never mutates canonical state — promotion to a canonical DB row is a
separate, human-gated, ledger-sealed backend act, out of scope here. IDs are
authoritative and stable; filenames are not. The two ID namespaces (frontend
`CON-######`… vs backend `axis1`/`KP-CLAIM-######`) meet **only** in the
manifest's `id_crosswalk`.

## What you build

1. **Exporter (frontend side of it):** consume the projection package and render
   one Obsidian note per record. Note layout is fixed by §8 — a `KP:GENERATED`
   region (you regenerate) and a `RESEARCHER:NOTES` region (you must preserve
   byte-for-byte). Reuse the `export_frontend_data.py` pattern; do **not** invent
   a new DB read path.
2. **Regeneration/merge:** on re-sync, replace only the generated region. Use the
   exact conflict rules in §8. The reference implementation + tests live in
   `08_validate_obsidian_projection.py merge`; match its behaviour.
3. **Proposal capture:** an Obsidian-side action that writes a
   `proposal.schema.json`-valid file into `proposals/inbox/`. `status` must be
   `proposed`; never write anything that claims to be canonical.
4. **Review reflection:** render inbox proposals and their decision receipts so
   accept/revise/reject status is visible in the vault.
5. **Canvas:** see `vertical_slice.canvas` for the shape — file nodes + edges
   labelled by predicate, pointing at real note files.

## What you must NOT do (charter-enforced)

- No writes to `ontology_node`, `ontology_edge`, `claim`, `verdict_disposition`,
  `functional_role`, `concept_verified`, `ontology_core`, or any evidence table.
- No new canonical DB table for proposals — the inbox is files only.
- No auto-canonicalisation of accepted proposals.
- No predicate outside the closed set in §6 (`fuses_with` included because it is
  the only predicate in the live edge table).
- No status of `canonical` for anything whose backend row is
  `provenance_status = design_hypothesis` (today that is all 43 ontology nodes).

## How to validate your output

```
python scripts/08_validate_obsidian_projection.py all <your_package_dir>
python scripts/08_validate_obsidian_projection.py merge <a_generated_note.md> --apply-to-tmp
```

The fixture already passes `all` (14 files schema-clean, 13 notes merge-clean)
and the validator has been proven to **reject** bad status, bad IDs, bad
predicates, proposals claiming canonical, and malformed marker regions. Build
until your package passes the same checks.

## Milestone success criteria (from the assignment)

1. Canonical records → correct notes.
2. Provenance visible in every note.
3. Researcher annotations survive regeneration.
4. Proposed relationship enters the review inbox.
5. Proposal is not auto-canonical.
6. Accept/reject status reflected back.
7. Canvas links to real files.

All seven are demonstrated against the synthetic fixture. When you wire the real
projection builder (a later, separately-authorised backend step), the same
contract and validator apply unchanged.

## Governance rulings (Appendix A — RESOLVED 2026-07-16)

The four Appendix A questions have been ruled on by the researcher and recorded
in `docs/protocol/obsidian/OBSIDIAN_GOVERNANCE_RULINGS_v1.0.md`. Summary of what
binds your frontend build:

1. **Status vocabulary.** Backend provenance status is authoritative. You must
   display both, and never conceal or upgrade the backend status — render the
   triad `provenance_status: design_hypothesis / projection_status: extracted /
   canonical: false`. Projection status never replaces backend status.
2. **ID namespace.** Backend IDs are authoritative for live records; filenames
   are labels; title changes must not mint records; links resolve through stable
   backend IDs or the backend-maintained `id_crosswalk`. Fixture prefixes may
   stay. (= contract §4.)
3. **Canonical corpus.** Canonical = passed human review/promotion **and**
   recorded via a ledger-sealed act. SQLite existence, ontology membership,
   graph export, projection, proposal acceptance, repeated use, or synthesis
   inclusion do **not** confer canonical status. The 43 nodes stay
   non-canonical `design_hypothesis`. (= contract §5/§7.)
4. **Proposal inbox.** Stays file-based for the slice; no proposal DB table.
   (= contract §7/§9.)

The v1.0 contract, schemas, merge rules, predicate vocabulary, lifecycle,
decision-receipt format, fixture and validator are **frozen**. Do not reopen on
stylistic or architectural preference — only on a concrete implementation-
blocking defect. The v0.1 guidance doc remains unsealed pending your slice
report.
