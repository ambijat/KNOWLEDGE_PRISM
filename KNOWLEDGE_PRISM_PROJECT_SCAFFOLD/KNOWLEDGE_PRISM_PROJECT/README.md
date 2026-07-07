# KNOWLEDGE PRISM

**Project status:** post-Claude takeover scaffold  
**Created:** 2026-07-06 13:03:30  
**Working location:** repository root

## Purpose

KNOWLEDGE PRISM is an auditable corpus-ontology project for converting a dispersed scholarly archive into a researchable map of International Relations knowledge structures.

The corrected domain is:

> Computational and interpretive mapping of geopolitical knowledge structures in International Relations, using Afghanistan--Central Asia/Eurasia as the empirical core and systems theory, semiotics, network analysis, grounded theory, and AI-assisted ontology-building as the methodological apparatus.

## Takeover rule

This project preserves Claude's useful reconnaissance but does **not** accept Claude's domain definition as final. Every claim must carry an evidence grade.

## Main directories

```text
KNOWLEDGE_PRISM/
├── README.md
├── PROJECT_STATUS.md
├── ROADMAP.md
├── INSTALL_IN_TARGET_FOLDER.sh
├── data/
│   ├── raw/                 # inherited Zotero, Recoll, SOLEMON, Claude artifacts
│   ├── processed/           # master corpus register and cleaned outputs
│   └── verification/        # bridge-concept verification queues
├── docs/
│   ├── protocol/            # governing protocol and schema
│   ├── domain/              # corrected domain boundary
│   ├── handover/            # Codex handover documents
│   └── audit/               # provenance and takeover audit
├── outputs/
│   ├── maps/                # domain visualisations
│   └── reports/             # generated status reports
├── scripts/                 # reproducible project utilities
├── logs/                    # run logs
└── codex/                   # prompt and task files for Visual Studio Codex
```

## First commands after installing

```bash
cd KNOWLEDGE_PRISM
python3 scripts/00_validate_project.py
python3 scripts/03_report_status.py
```

## Golden principle

Do not use this corpus as if it has been fully read. At present it has been **mapped**, **triaged**, and **partly concept-indexed**. Full textual claims require verification.
