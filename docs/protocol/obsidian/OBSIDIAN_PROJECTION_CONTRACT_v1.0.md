# Obsidian Projection Contract

> **Version:** 1.0 · **Owner:** Claude (backend) · **Status:** FROZEN for the vertical slice
> **Authority:** subordinate to `CHARTER.md` and
> `docs/protocol/KNOWLEDGE_PRISM_OBSIDIAN_INTEGRATION_CONTRACT_v0.1.md`.
> **Companion schemas:** `schemas/projection.schema.json`,
> `schemas/export_manifest.schema.json`, `schemas/proposal.schema.json`,
> `schemas/decision_receipt.schema.json`.
> **Validator:** `scripts/08_validate_obsidian_projection.py`.
> **Fixture:** `docs/protocol/examples/obsidian_vertical_slice/`.

This contract defines the frontend-neutral data exchanged between Knowledge
Prism (authoritative) and the Obsidian workspace (projection + proposal
surface). It is the single source of truth Codex builds against. Knowledge Prism
is the system of record; Obsidian never writes canonical state.

## 1. Scope and direction

**Outbound (authoritative → projection):** KP emits a *projection package* — a
set of projection records plus one export manifest. Obsidian renders these.

**Inbound (proposal → review):** Obsidian writes *proposal* JSON files into the
proposal inbox. KP validates, a human decides, and KP emits a *decision
receipt*. Acceptance never mutates canonical state automatically.

```text
DB (authoritative)
  → 08_build (future) → projection package (records + manifest)   [OUT]
  → Obsidian renders

Obsidian → proposal JSON → proposals/inbox/                        [IN]
  → 08_validate → human decision → decision receipt → proposals/receipts/
```

## 2. Package layout

```text
<package>/
├── export_manifest.json          # index + counts + versions (authority for indexes)
├── records/
│   ├── CON-000001.json           # one projection record per file
│   ├── ENT-000001.json
│   ├── SRC-000001.json
│   └── CLM-000001.json
├── proposals/
│   ├── inbox/                    # Obsidian writes here
│   ├── accepted/  revised/  rejected/
│   └── receipts/                 # KP writes decision receipts here
└── README.md
```

Indexes (concept/entity/source/proposal) are generated **from
`export_manifest.json`**, never by scanning arbitrary researcher files.

## 3. Projection record

Every record conforms to `schemas/projection.schema.json`. Required fields:

- `projection_version` (`"1.0"`)
- `record_id` — stable KP ID (see §4)
- `record_type` — one of `concept | entity | source | claim`
- `title`
- `status` — one of the authority levels (§5)
- `source_ids` — array of `SRC-*` (may be empty for a source record itself)
- `relationships` — array of relationship objects (§6); may be empty
- `provenance` — object: `{reviewed: bool, review_date: str|null, block_no: int|null, origin_table: str}`
- `sync` — object: `{projection_built_ts: str, projection_version: "1.0"}`

Optional: `definition`, `summary`, `detail`, `layer`, `evidence_grade`.

A projection record **must not** contain researcher-authored prose — that lives
only in the Obsidian `RESEARCHER:NOTES` region, never in the package.

## 4. Stable record-ID and filename policy

- IDs are authoritative; **filenames are not**. A note's filename may change; its
  embedded `record_id` must not.
- Projection ID families (frontend-facing):
  `SRC-###### · PAS-###### · CON-###### · ENT-###### · CLM-###### · REL-###### · PROP-######`
  (6-digit zero-padded).
- These map to backend-native IDs via the manifest's `id_crosswalk` (e.g.
  `CLM-000001 ↔ KP-CLAIM-000001`, `CON-000001 ↔ axis1`). The crosswalk is the
  **only** place the two namespaces meet; neither renames the other.
- Filename convention for generated notes: `<record_id> <slug>.md` (ID first so
  the stable key survives a title change). The `record_id` is also written into
  the note's YAML front-matter and inside the generated region.
- Proposals: `PROP-######`. Receipts reference the same `PROP-` id.

## 5. Canonical-status mapping

Projection authority levels and their backend meaning:

| Projection `status` | Backend condition | Canonical? |
|---|---|---|
| `raw` | captured, unprocessed | no |
| `extracted` | machine-extracted, unreviewed | no |
| `proposed` | in a proposal, awaiting review | no |
| `reviewed` | human-reviewed, not yet promoted | no |
| `canonical` | promoted via ledger-sealed act (`concept_verified`/`ontology_core`/accepted claim) | **yes** |
| `researcher_synthesis` | researcher-authored interpretation | no |
| `rejected` | reviewed and declined | no |
| `superseded` | replaced by a newer canonical record | no |

Backend `provenance_status = design_hypothesis` → projection `status` is **at
most** `extracted` (never `canonical`). Scholar-input taxonomy and evidence
grades are **not** overwritten by this mapping; the mapping is read-only and
one-directional (DB → projection).

## 6. Controlled predicate vocabulary (closed set)

`supports · contradicts · defines · mentions · causes · enables · constrains ·
located_in · part_of · instrument_of · associated_with · precedes · responds_to ·
fuses_with`

`fuses_with` is included because it is the only predicate present in the live
`ontology_edge` table. Any predicate outside this set **fails validation**. Each
relationship object: `{relationship_id: "REL-######", predicate, target_id,
target_title, status}` where `status` follows §5.

## 7. Proposal ingestion + review lifecycle

Proposal types (closed set): `relationship_proposal · correction_proposal ·
research_question · synthesis_candidate`. Schema: `schemas/proposal.schema.json`.

**Invariants enforced by the validator (proposal is REJECTED if violated):**

1. `status` **must** equal `proposed`. A proposal may never declare itself
   `canonical`, `accepted`, or `reviewed`.
2. `record_id` matches `^PROP-\d{6}$`.
3. `proposal_type` in the closed set.
4. For `relationship_proposal`: `source_id` and `target_id` must be
   syntactically valid KP IDs and `predicate` in the closed vocabulary (§6).
5. `rationale` non-empty.
6. No field may name or mutate a canonical table/row directly.

**Lifecycle:**

```text
proposed → (human review) → accepted | revised | rejected
```

Each terminal decision emits a `decision_receipt`
(`schemas/decision_receipt.schema.json`): `{receipt_version, proposal_id,
decision ∈ {accepted,revised,rejected}, decided_by, decided_ts, review_message,
resulting_record_id?}`. The original proposal file is **preserved** (moved to
`accepted/`|`revised/`|`rejected/`, never deleted). **Acceptance does not
canonicalise** — turning an accepted proposal into a canonical DB row is a
separate, human-gated, ledger-sealed backend act, out of scope for this slice.

## 8. Protected-region merge rules

Generated notes carry two regions:

```markdown
<!-- KP:GENERATED:START -->
…canonical generated content…
<!-- KP:GENERATED:END -->

<!-- RESEARCHER:NOTES:START -->
…researcher-authored content…
<!-- RESEARCHER:NOTES:END -->
```

Merge algorithm on regeneration (implemented + tested by
`08_validate_obsidian_projection.py`'s `merge` mode):

1. Parse the existing note into (generated, researcher) spans by marker.
2. Produce the merged note = **new** generated span + **existing** researcher span.
3. The researcher span is copied byte-for-byte; regeneration never edits it.
4. **Conflict conditions → no write, log a conflict instead of overwriting:**
   - missing either marker pair;
   - duplicated marker pair;
   - markers interleaved / out of order;
   - `END` before `START`.
5. A conflict yields a `*.conflict.md` report and leaves the original file
   untouched. Destructive overwrite is never performed.

## 9. What this contract deliberately does not do

- No new canonical DB table; the proposal inbox is files only.
- No auto-promotion of accepted proposals.
- No full-corpus migration; live projection of real records is a later,
  separately-authorised step.
- No changes to importer, transition CLI, GUI, Noteman, Research Graph Exporter,
  or ledger controls.
