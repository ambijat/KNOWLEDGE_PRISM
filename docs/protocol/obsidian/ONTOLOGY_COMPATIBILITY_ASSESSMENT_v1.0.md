# Ontology Compatibility Assessment — Knowledge Prism → Obsidian Projection

> **Version:** 1.0 · **Owner:** Claude (backend) · **Status:** delivered
> **Purpose:** state, from the *real* database, what can and cannot be projected
> to Obsidian today, so Codex builds against fact rather than the brief's
> illustrative file-corpus.

## 1. What the corpus actually is

The Knowledge Prism corpus is the SQLite database `db/knowledge_prism.db`. The
brief's example paths (`canonical_records/<id>.json`, `corpus/references.jsonl`,
`sources/`, `graph/`, `exports/`) are **not present** in this repository and are
treated as illustrative only. The projection contract is defined against the
live tables below.

## 2. Live surfaces relevant to projection

| Backend surface | Rows | Projection role |
|---|---|---|
| `ontology_node` (`node_id, node_type, label, layer, weight, detail, provenance_status`) | 43 | concept/axis nodes |
| `ontology_edge` (`src, dst, rel, weight`) | 136 | typed relationships |
| `claim` (`claim_id, claim_text, scope, source_file, evidence_grade, …, initial_status`) | 32 | claims |
| `source_registry` (`source_file, sha256, n_rows, ingested_ts, target_table`) | 126 | provenance of ingested sources |
| `master_corpus` (`corpus_item_id, …, evidence_grade, verification_status, …`) | 35,861 | source documents |
| `block` (hash-chained ledger) | 29 | provenance / review authority |

## 3. Node-type reality vs. the brief's model

- **Live `node_type` values:** `Axis`, `Method/Theory`, `Empirical Object`.
- **Live `layer` values:** `A`, `B`, `meta`.
- **Live `provenance_status`:** `design_hypothesis` for **all 43 nodes**.

The brief's projection example assumes `record_type ∈ {concept, entity, source}`.
That mapping is **not** 1:1 with this ontology. The projection contract maps:

| Obsidian `record_type` | Backend origin |
|---|---|
| `concept` | `ontology_node` where `node_type ∈ {Axis, Method/Theory}` |
| `entity` | `ontology_node` where `node_type = Empirical Object` |
| `source` | `source_registry` row / `master_corpus` item |
| `claim` | `claim` row |
| `relationship` | `ontology_edge` row |

## 4. The canonical-status problem (decisive)

**No row in the corpus is canonical today.** Every `ontology_node` is
`design_hypothesis`; `concept_verified` and `ontology_core` tables are empty;
claims sit at `provisional` / intermediate grades. Consequently:

- A projection of *live* state would contain **zero** `status = canonical`
  records.
- Presenting a `design_hypothesis` node to Codex as canonical would violate the
  Charter's evidence discipline (metadata/design guesses are not evidence).

**Resolution:** the first milestone uses a **synthetic fixture** (permitted by
the brief) whose records are explicitly labelled with their status, so Codex can
build and test every status pathway (`canonical`, `reviewed`, `proposed`,
`researcher_synthesis`, `superseded`, `rejected`) without any live record being
mislabelled. When live records are later promoted through the existing
human-gated, ledger-sealed process, the same projection builder will emit them
with their true status.

## 5. Predicate reality

All 136 live edges use the single predicate `fuses_with`. The contract defines a
**controlled predicate vocabulary** (§6 of the projection contract) that is a
superset; `fuses_with` is included so live edges remain projectable. Codex must
treat the predicate list as closed — unknown predicates fail validation.

## 6. Status-vocabulary reconciliation

The integration-contract authority ladder
(`raw/extracted/proposed/reviewed/canonical/researcher_synthesis/rejected/superseded`)
is the **projection** vocabulary. It is distinct from, and must not overwrite,
the frozen five-value `scholar_input_status_taxonomy` and the evidence grades.
The mapping is given in the projection contract §5. No existing taxonomy is
modified by this assignment.

## 7. Conclusion

Projection is feasible **as a read-only, status-honest transform** of the DB.
The only backend addition required for the round-trip is a **file-based proposal
inbox** (no new canonical table). Everything else reuses existing surfaces and
the existing `export_frontend_data.py` DB-reading pattern.
