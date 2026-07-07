# ROADMAP

## Phase 0 — Takeover scaffold

Status: **complete in this package**

- Preserve inherited artifacts.
- Establish folder structure.
- Add protocol, schema, and corrected domain boundary.
- Add validation and reporting scripts.

## Phase 1 — Corpus stabilisation

Goal: turn inherited artifacts into a reliable internal database.

Tasks:

1. Verify the master register can be regenerated from raw files.
2. Improve duplicate detection using title normalisation, size, extension, and path clusters.
3. Create `CORE_CORPUS_CANDIDATES.csv`.
4. Flag junk/noise with transparent rules.
5. Generate status reports after each run.

## Phase 2 — Text verification

Goal: move from metadata-level inference to textual evidence.

Tasks:

1. Select 50--100 high-value texts from `BRIDGE_CONCEPTS_VERIFICATION_QUEUE.csv`.
2. Extract first pages / TOC / abstract / preface where possible.
3. Assign evidence grades: `frontmatter_seen`, `chapter_sampled`, `concept_verified`.
4. Produce `BRIDGE_CONCEPTS_VERIFIED.csv`.

## Phase 3 — Ontology construction

Goal: build a proper ontology, not merely a folder map.

Top-level classes:

- Empirical Region
- Actor
- Process
- Theory
- Method
- Knowledge Object
- Pedagogic Use

## Phase 4 — Communicability package

Goal: prepare the project for presentation and Codex implementation.

Outputs:

- human-readable project brief
- workflow diagram
- corpus statistics dashboard
- Codex implementation prompt
- issue/task list

## Phase 5 — Visual Studio Codex handover

Goal: pass a mature, bounded software task to Codex.

Codex should only begin after Phase 1 stabilisation and at least a small Phase 2 verification sample.
