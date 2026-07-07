# Revised Project Protocol for the Research-Corpus Ontology

## Status

This protocol supersedes the earlier Claude Science domain-mapping workflow. The earlier work is preserved as reconnaissance, not final ontology. Its useful artifacts remain part of the project base, but every interpretive claim must now be evidentially graded and reproducible.

## Inherited artifact base

The takeover preserves the following inherited artifacts:

| Artifact | Role in the rebuilt workflow | Status |
|---|---|---|
| `zotero_inventory.csv` | Bibliographic register from Zotero metadata | Preserved; metadata-only |
| `recoll_corpus_manifest.csv` | Recoll-indexed document manifest | Preserved; metadata/index-level |
| `recoll_subject_folders.csv` | Recoll folder summary | Preserved; folder-level clue only |
| `solemon_crawl.csv` | Direct filesystem crawl of SOLEMON | Preserved; strongest inventory source |
| `deepread_folders.csv` | Priority folders selected for close reading | Preserved; to be verified |
| `bridge_concepts.csv` | AI-generated provisional concepts for 392 items | Preserved; hypothesis-only until verified |
| `domain_map.png`, `corpus_domain_map.png` | Visual maps | Preserved; exploratory |
| `domain_definition.md` | Previous domain statement | Preserved; draft, not final |

## Takeover principle

The project is no longer an agent-led impressionistic map. It is now an auditable corpus-ontology project.

The governing rule is:

> No domain claim, conceptual claim, or bibliographic claim may be treated as scholarly evidence unless its evidence grade is explicit.

## Core objective

To construct a defensible research-corpus ontology for computational and interpretive mapping of geopolitical knowledge structures in International Relations, with Afghanistan-Central Asia/Eurasia as the empirical core and systems theory, semiotics, network analysis, and AI-assisted ontology-building as the methodological apparatus.

## Workflow phases

### Phase 1 — Corpus consolidation

Inputs:

- Zotero inventory
- Recoll manifest
- SOLEMON direct crawl
- bridge-concepts table
- deep-read folder table

Actions:

1. Merge all path-based document records from Recoll and SOLEMON.
2. Preserve Zotero as a separate bibliographic layer because Zotero entries do not always have accessible file paths.
3. Deduplicate path-based documents using normalized path, filename, and file size.
4. Assign preliminary corpus IDs.
5. Mark source provenance for every row.

Outputs:

- `MASTER_CORPUS_REGISTER_PRELIMINARY.csv`
- `ZOTERO_REGISTER_PRELIMINARY.csv`
- `takeover_summary.json`

### Phase 2 — Evidence grading

Each record must receive one evidence grade:

| Evidence grade | Meaning | Permitted use |
|---|---|---|
| `metadata_only` | File path, title, folder, extension, or Zotero metadata only | Inventory and search only |
| `metadata_manifest` | Recoll or structured manifest metadata available | Inventory and prioritisation only |
| `snippet_seen` | Search snippet/preview has been inspected | Weak relevance claim |
| `frontmatter_seen` | Title page, abstract, contents, introduction, or preface inspected | Medium relevance claim |
| `chapter_sampled` | At least one substantive chapter/section sampled | Stronger concept claim |
| `fulltext_readable` | Text extraction works at scale | Eligible for systematic analysis |
| `concept_verified` | Thesis/concepts checked against text sample | Usable as scholarly evidence |

### Phase 3 — Corpus classification

Every item is classified into one of four provisional classes:

| Class | Meaning |
|---|---|
| `Core` | Directly relevant to empirical or methodological domain |
| `Peripheral` | Adjacent but not central |
| `Noise` | Clearly outside domain or administrative/junk material |
| `Unknown` | Cannot be decided from metadata alone |

Folder names are clues, not ontology. A folder can nominate a classification, but cannot decide it.

### Phase 4 — Bridge-concept verification

The inherited `bridge_concepts.csv` is treated as a hypothesis table. It must be verified before use.

Verification steps:

1. Locate file path for each bridge concept item.
2. Extract or inspect front matter.
3. Sample at least one substantive section.
4. Confirm, modify, or reject the AI-generated thesis.
5. Confirm, modify, or reject concept tags.
6. Upgrade evidence grade to `concept_verified` only after textual support is recorded.

Output:

- `BRIDGE_CONCEPTS_VERIFIED.csv`

### Phase 5 — Ontology construction

The ontology will be built from verified evidence using controlled top-level classes:

| Ontology class | Examples |
|---|---|
| Empirical Region | Afghanistan, Central Asia, South Asia, Eurasia |
| Actor | state, Taliban, China, Russia, India, Pakistan, US, regional organisations |
| Process | securitisation, connectivity, intervention, state-building, energy politics |
| Theory | realism, constructivism, RSCT, critical geopolitics, English School |
| Method | systems theory, semiotics, network analysis, grounded theory, computational modelling |
| Knowledge Object | archive, map, corpus, ontology, discourse, concept cluster |
| Pedagogic Use | syllabus, lecture corpus, classroom protocol, research training material |

### Phase 6 — Gap analysis and external literature

External papers must not be pulled until the internal corpus has been stabilised. External literature is for gap filling, not for defining the domain.

External retrieval may begin only after:

1. the core corpus is identified,
2. bridge concepts are verified for a representative subset,
3. obsolete or duplicate material is isolated,
4. empirical gaps after 2021 are clearly identified,
5. method gaps are distinguished from empirical gaps.

## Immediate next work package

1. Review `MASTER_CORPUS_REGISTER_PRELIMINARY.csv`.
2. Manually inspect the top 100 `Core` items and top 100 `Unknown` items.
3. Choose a 30-50 item bridge-verification sample from `BRIDGE_CONCEPTS_VERIFICATION_QUEUE.csv`.
4. Upgrade those items from hypothesis-only to verified or rejected.
5. Produce `DOMAIN_BOUNDARY_V2_VERIFIED.md` after verification.

## Red-line rules

- Do not say the corpus has been read when it has only been mapped.
- Do not treat Recoll as full text.
- Do not treat folder names as final intellectual categories.
- Do not use `bridge_concepts.csv` as evidence without verification.
- Do not pull external papers until the internal core is known.
- Do not collapse empirical geopolitics and methodology into one vague mega-domain.
