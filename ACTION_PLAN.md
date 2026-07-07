# KNOWLEDGE PRISM ACTION PLAN

Date: 2026-07-07

## Control Assessment

The project is structurally healthy and ready for the next evidence-gated work
package.

Current verified state:

- Project validation passes with `python3 scripts/00_validate_project.py`.
- Status reporting runs with `python3 scripts/03_report_status.py`.
- The SQLite spine is present at `db/knowledge_prism.db`.
- The provenance chain verifies with `python3 db/prism.py verify`.
- The current database contains 35,861 master corpus rows, 392 bridge-concept
  rows, 86 Step-2 literature rows, 11 claims, and 16 claim events.
- The SOLEMON source mount is present at `SOURCE_ARCHIVE`.
- All 392 bridge-concept queue filenames have exact matches in the master corpus.

The project is not yet a verified ontology. It is an auditable corpus-ontology
system whose metadata, database, and provenance infrastructure are in place.
The next intellectual milestone is text-level verification.

## Putative Project Goals

I interpret the project's practical goals as follows:

1. Convert a dispersed scholarly archive into a reliable, queryable corpus.
2. Preserve every inference under explicit evidence grades.
3. Move from folder/title metadata to sampled textual evidence.
4. Identify a defensible core corpus for Afghanistan, Central Asia, Eurasia, IR
   theory, geopolitics, systems theory, semiotics, network analysis, grounded
   theory, and AI-assisted ontology building.
5. Build a verified ontology of empirical regions, actors, processes, theories,
   methods, knowledge objects, and pedagogic uses.
6. Reconcile the internal corpus with external bibliographic graphs such as
   OpenAlex only after the internal corpus is stable.
7. Produce a communicable package for academic, technical, and pedagogic use.
8. Leave the project in a state another Codex session can restore, verify, and
   continue without relying on chat memory.

## Governing Rule

No claim is promoted because it is plausible.

Folder names, titles, Zotero metadata, Recoll snippets, AI bridge concepts, and
computed eigenspace axes are clues. A scholarly claim becomes usable only when
the sampled text supports it and the ledger records the basis.

## Redundancy And Efficiency Vetting

The first version of this plan was deliberately expansive. The leaner execution
model should make a verification batch the central unit of work. One batch
should carry mapping, access status, sample status, verdict status, review
status, exports, reports, and provenance sealing.

Redundancies to remove:

1. `BRIDGE_TO_MASTER_REGISTER.csv`, `BRIDGE_QUEUE_ACCESS_REPORT.md`, and
   `BRIDGE_SAMPLE_MANIFEST.csv` should not be hand-built as unrelated outputs.
   They should be generated from one batch manifest.
2. A new pilot-selection script should not duplicate
   `scripts/02_generate_bridge_verification_sample.py`. Extend or replace that
   script so it selects balanced batches, joins them to the master corpus, and
   emits both machine-readable and human-readable outputs.
3. Do not create parallel sources of truth in CSV and SQLite. The database and
   append-only claim events are the source of truth; CSV and Markdown files are
   exports.
4. Do not seal a provenance block for every minor artifact. Seal one block per
   meaningful batch milestone: access-mapped pilot, sampled pilot, adjudicated
   pilot, then scaled verification batches.
5. Do not start a separate manual "top 100 Core" inspection before the bridge
   pilot. Use bridge-verification results to train the first positive signals
   for later core-corpus triage.
6. Do not build the communicability package before the verification pilot. The
   package should be generated from verified pilot/core-corpus facts, otherwise
   it repeats provisional language.
7. Keep OpenAlex work lightweight until the internal core is stable. Cheap DOI
   reconciliation can proceed, but new external expansion should wait.

Efficiency rules:

- Prefer one manifest row per bridge item with lifecycle columns:
  `batch_id`, `bridge_row_id`, `corpus_item_id`, `path_norm`, `access_status`,
  `sample_status`, `verdict_status`, `review_status`, `current_evidence_grade`,
  and `ledger_block_id`.
- Use content hashes for extracted samples so unchanged samples are not
  regenerated.
- Cache PDF extraction results by `corpus_item_id` and source-file hash.
- Use deterministic batch selection so a pilot can be reproduced.
- Keep human review queues as filtered views or exports from verdict data, not
  as a second manually maintained list.
- Update `db/prism.py boot` from the same verification tables instead of
  maintaining a separate status document by hand.

## Implementation Sequence

### Work Package 1: Prepare The Verification Batch Spine

Goal: make one reproducible batch layer that handles bridge-to-master mapping,
file access, sample manifests, verdict imports, review queues, and reports.

Tasks:

1. Add one batch manifest/export that maps every bridge-concept row to
   `corpus_item_id`, `path_norm`, duplicate group, access status, sample status,
   verdict status, review status, and current evidence grade.
2. Confirm that each mapped `path_norm` exists on disk under the mounted SOLEMON
   archive.
3. Add explicit statuses for missing, unreadable, encrypted, wrong-file, and
   sampled items.
4. Extend `scripts/02_generate_bridge_verification_sample.py` or replace it with
   a batch-oriented successor instead of creating multiple one-off scripts.
5. Generate both `data/verification/BRIDGE_BATCH_MANIFEST.csv` and
   `outputs/reports/BRIDGE_QUEUE_ACCESS_REPORT.md` from the same data.
6. Seal the access-mapped pilot as one provenance block only after the manifest
   and report are generated.

Acceptance gate:

- 392 bridge rows have path mappings.
- Missing/unreadable files are counted explicitly.
- No verification sampling starts from an unmapped file.

### Work Package 2: Build the Text Sampling Toolchain

Goal: create a reproducible way to sample front matter, introductions, concept
probes, and chapter windows.

Tasks:

1. Add a script that extracts bounded text samples from PDFs where possible,
   keyed by `corpus_item_id` and source-file hash.
2. Store samples under `data/verification/samples/` using stable IDs.
3. Record extraction metadata: source path, page range, character offsets,
   extractor used, extraction warnings, and text hash.
4. Detect scanned or unreadable PDFs and route them to human/OCR review.
5. Update the batch manifest with sample locations and extraction status instead
   of creating an unrelated sample register.

Acceptance gate:

- Pilot sample files can be regenerated from source paths.
- Every sample has locators sufficient for re-checking.
- Unreadable files are not silently treated as absent evidence.

### Work Package 3: Run a 15-20 Item Verification Pilot

Goal: test the rubric before scaling to all 392 bridge claims.

Pilot composition:

- 8-10 International Relations theory items.
- 3-4 systems theory or method items.
- 3-4 semiotics or knowledge-representation items.
- 2-3 empirical Afghanistan/Central Asia/Eurasia items.

Tasks:

1. Select a deterministic balanced pilot list from the bridge queue.
2. Extract front matter, introduction sample, concept probes, and one extra
   theory-heavy chapter window where applicable.
3. Apply the verdict taxonomy from `VERIFICATION_RUBRIC.md`:
   `SUPPORTED`, `PARTIAL`, `CONTRADICTED`, `ABSENT`, or `UNREADABLE`.
4. Record key-concept observations separately from thesis support.
5. Append claim events rather than overwriting existing claims.
6. Produce `BRIDGE_CLAIMS_PILOT_VERDICTS.csv` and
   `BRIDGE_CLAIMS_PILOT_REPORT.md` as exports from the batch/verdict data.

Acceptance gate:

- Every pilot verdict includes a basis, locator, confidence, and short evidence
  quote where promotion is attempted.
- Contradictions, low-confidence verdicts, unreadable files, and high-value
  absent cases are routed for human review.
- `concept_verified` is not assigned during this pilot; the pilot can promote
  only to sampled-text evidence.

### Work Package 4: Turn Verification Into A Ledgered Workflow

Goal: make text verification part of the project's persistent state.

Tasks:

1. Extend the database with a small verification schema if needed:
   `verification_batch`, `verification_item`, `verification_sample`,
   `bridge_claim_verdict`, and `concept_observation`.
2. Keep derived tables rebuildable while preserving claim events append-only.
3. Add CLI commands for:
   - preparing a batch,
   - extracting samples,
   - importing verdicts,
   - exporting the human review queue,
   - reporting stage progress.
4. Derive the human review queue from verdict status and confidence instead of
   maintaining it as a manually edited table.
5. Seal each completed verification batch as a ledger block.

Acceptance gate:

- `python3 db/prism.py boot` reports current verification progress.
- Every promoted claim has a readable provenance trail.
- Re-running build scripts does not erase claim history.

### Work Package 5: Scale Bridge Verification

Goal: move the 392 bridge-concept claims from hypothesis-only into sampled,
reviewed, or blocked states.

Tasks:

1. Review the pilot results and adjust thresholds only once.
2. Run verification in batches of 25-50 items.
3. Prioritize load-bearing theory and mixed-axis items first:
   - theory: 220 rows,
   - mixed: 70 rows,
   - empirical: 57 rows,
   - method: 45 rows.
4. Maintain a live review queue for contradictions, unreadables, and confidence
   below threshold.
5. Produce cumulative `BRIDGE_CONCEPTS_SAMPLED.csv` and Markdown reports as
   exports from the database.

Acceptance gate:

- At least 100 bridge claims have sampled-text verdicts before the ontology is
  promoted.
- All 392 rows are eventually one of: supported, partial, contradicted,
  insufficient, unreadable, or superseded.

### Work Package 6: Establish the Core Corpus

Goal: convert heuristic corpus classes into a defensible working set.

Tasks:

1. Use verified bridge results to define positive core signals.
2. Inspect duplicate groups before final count claims.
3. Build `CORE_CORPUS_CANDIDATES.csv`.
4. Separate:
   - confirmed core,
   - probable core,
   - peripheral,
   - noise,
   - unknown pending evidence.
5. Generate a corpus dashboard with counts, duplicate risk, evidence grades, and
   top folders.

Acceptance gate:

- Core corpus status is text-informed, not only metadata-inferred.
- Final counts distinguish physical files, duplicate groups, and intellectual
  works.

### Work Package 7: Promote the Ontology From Provisional to Verified

Goal: build the ontology from observed textual evidence.

Tasks:

1. Treat the current 5-axis eigenspace as a provisional analytical scaffold.
2. Promote ontology nodes only when supported by sampled text.
3. Add evidence-backed edges between empirical objects and methods/theories.
4. Preserve rejected or modified bridge concepts as negative evidence.
5. Produce `DOMAIN_BOUNDARY_V2_VERIFIED.md` and an ontology export.

Acceptance gate:

- Every promoted ontology node or edge links to at least one sampled claim or
  accepted analysis claim.
- The ontology can explain what is verified, what is analytical, and what
  remains provisional.

### Work Package 8: Reconcile With External Literature

Goal: use OpenAlex/arXiv enrichment to fill gaps, not to replace corpus evidence.

Tasks:

1. Cross-reference the 86 Step-2 papers with Zotero and the master corpus.
2. Mark which external works are already owned, missing, duplicate, or only
   bibliographic.
3. Add DOI/OpenAlex IDs where possible.
4. Run a targeted post-2021 refresh for Afghanistan/Taliban, BRI, energy
   corridors, and China-Central Asia/Eurasia.
5. Keep external additions separately graded until their texts are available.

Acceptance gate:

- External literature is tied to a specific internal gap.
- The project can distinguish owned corpus items from recommended acquisitions.

### Work Package 9: Communicability Package

Goal: make the project understandable to academic, technical, and pedagogic
audiences.

Deliverables:

1. `PROJECT_BRIEF_FOR_ACADEMICS.md`
2. `TECHNICAL_PIPELINE.md`
3. `CLASSROOM_PROTOCOL.md`
4. `outputs/maps/` visual ontology maps
5. `outputs/reports/CORPUS_DASHBOARD.md`
6. `docs/handover/CODEX_IMPLEMENTATION_BRIEF.md`

Acceptance gate:

- Academic version explains the research method.
- Technical version explains reproducibility.
- Pedagogic version explains how the archive becomes a researchable domain.

### Work Package 10: Codex Handover and Automation

Goal: leave an executable, restorable implementation path.

Tasks:

1. Document the session boot ritual:
   `python3 db/prism.py boot`.
2. Document validation and regeneration commands.
3. Add tests around bridge mapping, extraction manifests, and ledger integrity.
4. Create a concise issue list for the next coding session.
5. Package the mature pipeline only after verification and core corpus stages
   have real evidence behind them.

Acceptance gate:

- A fresh session can restore state, verify integrity, and know the next action
  without reading chat history.

## Immediate Lean Actions

1. Replace or extend `scripts/02_generate_bridge_verification_sample.py` into a
   batch-preparation command that performs bridge-to-master joining, access
   checks, deterministic pilot selection, and report generation.
2. Generate `data/verification/BRIDGE_BATCH_MANIFEST.csv` and
   `outputs/reports/BRIDGE_QUEUE_ACCESS_REPORT.md` from that one command.
3. Add cached PDF sample extraction keyed by `corpus_item_id` and source-file
   hash.
4. Generate sample files for the deterministic 15-20 item pilot.
5. Add a verdict import path that appends claim events and exports the human
   review queue.
6. Update `db/prism.py boot` to summarize verification batch progress.
7. Seal the access-mapped/sampled/adjudicated pilot as batch-level provenance
   blocks, then scale to 25-50 item batches.

## Risks To Control

- Treating titles and folders as evidence.
- Promoting AI-generated bridge theses without textual support.
- Losing duplicate distinctions between file copies and intellectual works.
- Treating unreadable PDFs as absent concepts.
- Letting external literature redefine the domain before the internal corpus is
  stabilized.
- Mixing accepted claims, provisional claims, and analytical scaffolds in the
  same output without visible grade labels.

## Definition Of Done For The Next Milestone

The next milestone is not a finished ontology. It is a verified pilot that proves
the project can move from hypothesis-only bridge concepts to sampled-text claim
events without breaking provenance.

The milestone is done when:

- 15-20 bridge claims have sampled evidence.
- every pilot item has a mapped source file and sample manifest row.
- verdicts are append-only and visible in the database.
- validation and chain verification still pass.
- a human review queue exists for hard cases.
- the project can honestly say: the verification workflow works.
