# Bridge Verification — Pilot Results (rubric v2)

**Status: PROVISIONAL. Nothing promoted. For supervisor review.**

Model: reasoning (claude-sonnet-5). Object under test = the AI *claim* about each book,
judged only against a bounded sampled slice (front-matter + TOC + intro; theory/mixed also got a ~2,000-word chapter sample;
plus per-concept first-occurrence probes). Every argument/term quote was programmatically re-checked against the slice text;
quotes not found verbatim are flagged, not trusted.

## Outcome distribution

| verdict_status | n |
|---|---|
| claim_sampled_supported | 14 |
| claim_sampled_partial | 2 |
| flagged_contradicted | 1 |
| blocked_unreadable | 1 |

Confidence gate = 0.75. Rows below the gate, plus any CONTRADICTED, route to human review (never auto-promote).

## Per-book verdicts

| # | axis | book | pages | thesis verdict | conf | concepts seen | arg-quote | route |
|---|---|---|---|---|---|---|---|---|
| 1 | mixed | The Global Transformation: History, Modernit | 417 | SUPPORTED | 0.93 | 5/6 | verified | provisional accept |
| 2 | empirical | Nations at War: A Scientific Study of Intern | 260 | SUPPORTED | 0.9 | 6/6 | verified | provisional accept |
| 3 | theory | Ideology and International Relations in the  | 317 | SUPPORTED | 0.9 | 5/6 | verified | provisional accept |
| 4 | method | Theory and Metatheory in International Relat | 234 | SUPPORTED | 0.9 | 4/5 | verified | provisional accept |
| 5 | empirical | Does ethnofederalism explain the success of  | 25 | SUPPORTED | 0.78 | 6/6 | verified | provisional accept |
| 6 | theory | Why Islamism Is Winning | 3 | SUPPORTED | 0.8 | 5/5 | verified | provisional accept |
| 7 | mixed | Ratzel and Demography | 13 | PARTIAL | 0.55 | 4/5 | ⚠ NOT in slice | HUMAN REVIEW (<0.75) |
| 8 | method | Overview of the Semiotics of Maps | 12 | SUPPORTED | 0.95 | 4/5 | verified | provisional accept |
| 9 | mixed | Cultural Cartography: Maps and Mapping in Cu | 21 | SUPPORTED | 0.95 | 2/6 | verified | provisional accept |
| 10 | theory | Structural Realism: Structure, Object, and C | 226 | SUPPORTED | 0.9 | 5/6 | verified | provisional accept |
| 11 | method | Discourse Analysis as Theory and Method | 240 | SUPPORTED | 0.97 | 5/6 | verified | provisional accept |
| 12 | empirical | Regional Action Plan towards the Information | 147 | SUPPORTED | 0.85 | 5/5 | verified | provisional accept |
| 13 | mixed | Russia and the Mongols: Slavs and the Steppe | 349 | PARTIAL | 0.55 | 3/7 | verified | HUMAN REVIEW (<0.75) |
| 14 | method | Histology: A Text and Atlas with Correlated  | 1002 | SUPPORTED | 0.75 | 2/5 | verified | provisional accept |
| 15 | mixed | To Lead the Free World: American Nationalism | 270 | SUPPORTED | 0.88 | 5/5 | verified | provisional accept |
| 16 | empirical | We have to go: Afghans ready to flee country | 2 | SUPPORTED | 0.75 | 3/5 | verified | provisional accept |
| 17 | empirical | Practical Exam Format May 2020 | 1 | CONTRADICTED | 0.95 | 0/0 | — | HUMAN REVIEW (contradiction) |
| 18 | mixed | Advaita Vedanta and International Relations | 8 | UNREADABLE | 0.0 | 0/5 | — | unreadable |

## Notable cases (with verbatim evidence)

### The Global Transformation: History, Modernity and the Making of Intern
- **SUPPORTED** (conf 0.93). Clean SUPPORTED — real argument sentence present.
- argument_quote: "Global modernity reconstituted the mode of power that underpinned international order and opened a power gap between those who harnessed the revolutions of modernity and those who were denied access to them." — verified in slice

### Practical Exam Format May 2020
- **CONTRADICTED** (conf 0.95). Planted stress-test: a 1-page exam form, not a book. Correctly CONTRADICTED.

### Advaita Vedanta and International Relations
- **UNREADABLE** (conf 0.0). Planted stress-test: OCR/scan artifact, 0/5 concept probes. Correctly UNREADABLE.

### Histology: A Text and Atlas with Correlated Cell and Molecular Biology
- **SUPPORTED** (conf 0.75). Thesis accurately describes a histology atlas → SUPPORTED. But the book has no IR relevance and sits in a methods folder. Exposes a rubric gap: it tests thesis *accuracy*, not project *relevance*.
- argument_quote: "Histology A TEXT AND ATLAS With Correlated Cell and Molecular Biology" — verified in slice

### Ratzel and Demography
- **PARTIAL** (conf 0.55). PARTIAL, but the argument_quote did NOT validate verbatim against the slice — flagged. Shows the quote-checker catches paraphrase/hallucinated quotes.
- argument_quote: "Ethnography does not recognize nonreligious peoples, but only different evolutionary stages of religious ideas, which in some peoples are described as that of the chrysalis, small and hidden, while others have created nu" — ⚠ NOT found verbatim

## Method findings (what the pilot taught us)

1. **Pipeline bug caught & fixed mid-pilot.** The first run fed a *blank* thesis (the proposal CSV lacked the `thesis` column) → 14 spurious ABSENT verdicts. Re-run after backfilling `bridge_concepts.thesis`. Lesson: the sampler must read the thesis from the DB, not the pilot CSV.
2. **Both planted misfiles were caught** — the exam form (CONTRADICTED) and the OCR artifact (UNREADABLE). The rubric detects genre/format mismatch.
3. **Relevance ≠ accuracy gap.** The Histology atlas passed on thesis accuracy yet is irrelevant to IR. Recommend adding a **project-relevance track** (does the book touch Layer A or Layer B?) separate from thesis verification.
4. **Quote validation works.** One argument quote (ratzel) failed verbatim re-check and was flagged automatically — the 'no quote, no promotion' rule is enforceable in code.
5. **Token budget.** Long theory books need ≥3,000 output tokens or JSON truncates; batch runs should set this.
6. **Confidence gate at 0.75** routed 3 rows to human review — a workable review volume for 18 books (~17%).

## What was NOT done (by instruction)

- No claim status changed in the DB. No ontology promotion. No block sealed yet.
- These verdicts are proposals. On your sign-off, supported rows advance to `sampled_text`/`concept_verified`, the contradicted row goes to human-review disposition, and the run is sealed as a provenance block.