# Master Corpus Register Schema

## Purpose

The master corpus register is the audit table for the rebuilt corpus-ontology project. It consolidates path-based records from the SOLEMON crawl and Recoll manifest, while preserving Zotero as a separate bibliographic layer.

## Generated files

| File | Purpose |
|---|---|
| `MASTER_CORPUS_REGISTER_PRELIMINARY.csv` | Path-based document corpus from SOLEMON + Recoll |
| `ZOTERO_REGISTER_PRELIMINARY.csv` | Zotero bibliographic layer |
| `BRIDGE_CONCEPTS_VERIFICATION_QUEUE.csv` | Provisional concept claims requiring verification |
| `takeover_summary.json` | Counts and audit summary |

## `MASTER_CORPUS_REGISTER_PRELIMINARY.csv` schema

| Field | Type | Meaning |
|---|---|---|
| `corpus_item_id` | string | Stable generated ID for the path-level corpus item |
| `title_candidate` | string | Best available title from Recoll metadata or filename |
| `author_candidate` | string | Best available author from Recoll metadata, if any |
| `filename` | string | File basename |
| `path_norm` | string | Normalized absolute path from inherited artifacts |
| `ext` | string | File extension from direct crawl or inferred path |
| `mime_or_ext` | string | MIME type from Recoll when available, otherwise extension |
| `size_bytes` | integer | File size in bytes when available |
| `size_mb` | float | File size in MB when available |
| `topdir` | string | Top-level directory under the mounted drive, where inferable |
| `folder` | string | Immediate parent or thematic folder |
| `source_solemon_crawl` | boolean | Whether the row appears in the direct SOLEMON crawl |
| `source_recoll_manifest` | boolean | Whether the row appears in the Recoll manifest |
| `dedupe_key` | string | Preliminary dedupe key: lowercase filename + file size |
| `duplicate_group_size` | integer | Number of records sharing the dedupe key |
| `is_duplicate_candidate` | boolean | Whether the item appears to have duplicates |
| `corpus_class_preliminary` | enum | `Core`, `Peripheral`, `Noise`, or `Unknown` |
| `evidence_grade` | enum | Current evidence grade |
| `verification_status` | enum/string | Current verification state |
| `claim_use_allowed` | string | How the row may be used at this stage |
| `notes` | string | Audit notes |

## Classification rules used in the preliminary register

The first-pass classification is deliberately conservative.

| Class | Trigger logic | Caution |
|---|---|---|
| `Core` | Keywords in path/title/folder match IR, geopolitics, Afghanistan, Central Asia, Eurasia, security, systems theory, semiotics, network analysis, AI/IR, methods | Must still be verified against text |
| `Peripheral` | Adjacent but not directly matched to core or noise terms | May be upgraded after inspection |
| `Noise` | Clearly unrelated signals such as physics, chemistry, clinical, software/manual, household material | May still contain rare false negatives |
| `Unknown` | Broad personal-library folders where metadata is insufficient | High-priority triage category |

## Evidence-grade values

| Value | Meaning |
|---|---|
| `metadata_only` | Known only from path/title/folder/Zotero metadata |
| `metadata_manifest` | Known from structured Recoll or generated manifest metadata |
| `snippet_seen` | Snippet or preview inspected |
| `frontmatter_seen` | Front matter, abstract, TOC, introduction, or preface inspected |
| `chapter_sampled` | Substantive chapter or section sampled |
| `fulltext_readable` | Extracted text is readable enough for systematic analysis |
| `concept_verified` | Conceptual claim checked against actual text |

## Zotero layer schema

`ZOTERO_REGISTER_PRELIMINARY.csv` preserves the original Zotero fields:

| Field | Meaning |
|---|---|
| `first_author` | First author from Zotero export |
| `year` | Publication year where available |
| `title` | Zotero item title |
| `type` | Zotero item type |
| `collections` | Zotero collection membership |
| `tags` | Zotero tags |
| `zotero_item_id` | Generated local ID |
| `evidence_grade` | Initially `metadata_only` |
| `verification_status` | Initially `unverified` |
| `claim_use_allowed` | Bibliographic inventory only until verified |

## Bridge-concept verification schema

`BRIDGE_CONCEPTS_VERIFICATION_QUEUE.csv` preserves the inherited fields and adds controls:

| Field | Meaning |
|---|---|
| `folder` | Source folder from inherited bridge analysis |
| `file` | Filename |
| `title` | Interpreted title |
| `axis` | Inherited classification: theory, method, empirical, mixed |
| `thesis` | AI-generated thesis claim |
| `concepts` | AI-generated concept tags |
| `bridge_claim_status` | Initially `provisional_unverified` |
| `required_next_evidence` | Minimum evidence required for upgrade |
| `claim_use_allowed` | Hypothesis only until checked |

## Current takeover summary

The preliminary union generated from the inherited artifacts contains:

| Metric | Count |
|---|---:|
| Zotero rows | 1,841 |
| Recoll manifest rows | 12,594 |
| SOLEMON crawl rows | 35,178 |
| Path-union master document rows | 35,861 |
| Duplicate-candidate rows | 7,259 |
| Duplicate groups | 3,347 |
| Bridge-concept rows | 392 |
| Deep-read folder rows | 13 |
| Recoll subject-folder rows | 502 |

Preliminary class counts:

| Class | Count |
|---|---:|
| Unknown | 23,137 |
| Core | 11,453 |
| Peripheral | 839 |
| Noise | 432 |

These are triage categories, not final scholarly categories.
