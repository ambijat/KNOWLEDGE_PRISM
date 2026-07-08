# CLAUDE — RESEARCH SESSION ORIENTATION & JUDGMENT PLAN

**Role assumed:** research judgment · corpus interpretation · evidence discipline · boundary learning.
**Not my remit:** front-end productisation (Codex owns that).
**Charge:** keep KNOWLEDGE_PRISM intellectually alive as a social-science / IR research machine.
**Date:** 2026-07-08 · **Session:** 7b564c3e-8699-4f40-98e6-07c5c35d7649
**State at orientation:** chain OK to block 19 · action log OK (14 records) · nothing changed by this orientation.

---

## 1. WHAT WAS READ (in the charter's prescribed order)

1. **`CHARTER.md`** (sealed doctrine, block 19) — the beacon.
2. **`RESTORE.md`** (v2) — now points to the charter first.
3. **Ledger block 19** — `block_0019_founding_charter`, confirmed on chain.
4. **`FUNCTIONAL_IR_INTERPRETATION_PROTOCOL.md`** — anatomy/physiology/biomechanics; the 5+ question functional schema.
5. **`VERIFICATION_RUBRIC.md`** (v3) — bounded sampling protocol; two-axis §8.
6. **Disposition / evidence tables** — `verdict_disposition` (8 written rows), `disposition_taxonomy` (6 vocab values).
7. **Functional-role table** — `functional_role`, 14 rows.
8. **Handover docs** — SHIFT_HANDOVER + this note.

---

## 2. CHARTER READING — what the project IS, FORBIDS, and PERMITS

**What it is.** A *social-science exoskeleton*. It amplifies the scholar's invariant gestures — **reach, memory, endurance, integrity** — and never substitutes for them. The scholar is the source of meaning; the ledger is memory; the database is scaffolding; the front end is communication; the research question is central. The corpus is a **kaleidoscope**: it reconfigures around each research goal rather than sitting static. The project must live at the level of **biomechanics** (how concepts, actors, regions, theories interact to *explain*), not stall at anatomy (cataloguing what exists).

**What it forbids.** Treating the project as a cadaver lab of documents or a database fetish; letting a database *status* stand in for meaning; substituting the machine for the scholar's own acts (holding the question, judging meaning, maturing the idea, writing); **silent** judgment; treating metadata or search rank as evidence; frozen walls that cannot learn.

**What it permits through accountable discretion.** Judgment *inside the gray zone* — reaching past a strict gate, offering an interpretation that runs ahead of the evidence, holding an out-of-domain-but-live source — **provided every such call is logged with its reasoning** so it stays auditable and reversible. Judge freely; never silently. And boundaries are permitted — expected — to *move*: they learn from logged cases, shift when a case genuinely surprises the taxonomy, rest when confirmed, and resist overfitting to every shiny exception. The ledger is the training history of that movement.

---

## 3. CURRENT MACHINERY (scaffolding — subordinate to interpretation)

- **Database:** `db/knowledge_prism.db`, rebuilt reproducibly by `db/build_prism_db.py`. Derived tables are dropped+rebuilt; persistent tables survive.
- **Ledger:** `block` / `claim` / `claim_event`, hash-chained via `db/prism_ledger.py`; **19 blocks, chain verifies OK**. Action log `logs/agent_actions.jsonl` (14 records, OK) via `scripts/04_log_agent_action.py`; shift ritual `scripts/05_start_agent_shift.py`.
- **Evidence tables:** `verdict_disposition` (persistent; carries disposition, layer_tag, evidence_grade); ladder = `provisional_unverified → sampled_text_supported_core_candidate → concept_verified → ontology_core`.
- **Disposition taxonomy** (`disposition_taxonomy`, 6 values): `core_candidate`, `claim_supported_but_project_irrelevant`, `excluded_misfile_noise`, `excluded_unreadable`, `review_required` (all block 14), `Peripheral_context` (block 15).
- **Functional-role table** (`functional_role`, persistent, 14 rows): the interpretation layer — IR function, contribution type, interaction illuminated, substantive layer, explanatory contribution; evidence grade recorded only as an annotation *on* the reading.
- **Pilot state (verified live):** 18 rows → 11 `core_candidate` promoted to `sampled_text_supported_core_candidate`; 2 `review_required`; 1 `excluded_unreadable`; 1 `Peripheral_context`; 2 `claim_supported_but_project_irrelevant`; 1 `excluded_misfile_noise`. **0 at concept_verified, 0 at ontology_core.**

---

## 4. CURRENT INTELLECTUAL CENTRE

- **Functional IR Interpretation** — every live item read by *function*, not status. This is where meaning lives.
- **Boundary kinematics** — limits are learned from logged cases; move on surprise, rest on confirmation, avoid overfitting; the ledger is the training set.
- **The Recoll kaleidoscope** — named in the charter as the next likely amplification of the *reach/gathering* gesture: the corpus reconfiguring around a research question. Proven technically feasible (recoll CLI + live index queried successfully) but **not yet built or run** as a governed cycle.

---

## 5. COMPLETED SEALED WORK (this session, blocks 13–19)

| Block | Sealed work |
|---|---|
| 13 | Rubric v2 approved + 18-book pilot executed |
| 14 | Two-axis disposition model; persistent taxonomy tables; Exam + Histology dispositioned; KP-CLAIM-000021 |
| 15 | Six user-ruled dispositions; `Peripheral_context` + `layer_tag` |
| 16 | Sample-level promotion of 11 rows; KP-CLAIM-000022…000032; `evidence_grade` column |
| 17 | Shift-close handover |
| 18 | Functional-IR turn: protocol + `functional_role` table + 14 readings |
| 19 | **Founding Charter** (living doctrine, above the ledger) |

Evidence rubric ✓ · two-axis model ✓ · sample-level promotion ✓ · functional-role layer ✓ · charter/block 19 ✓.

---

## 6. OPEN RESEARCH WORK

1. **Ratzel and Demography** — deeper targeted re-sample; a *validated* argument quote required (prior quote failed verbatim check). Potentially a genealogy of political geography — territory, state expansion, demographic imagination, spatial power — but current evidence too weak to admit to the theory-method layer.
2. **Russia and the Mongols** — deeper re-sample; decide core (Eurasian historical depth) vs `Peripheral_context` vs background.
3. **abiword_job / Advaita Vedanta & IR** — OCR / manual inspection; unreadable ≠ irrelevant. Possibly a non-Western ontology contribution.
4. **Recoll kaleidoscope** — design, then (on approval) run the goal→rank→intersect→sealed-view cycle.
5. **OpenAlex enrichment** — Stage 7, later.
6. **Concept verification** — only after further evidence; nothing is a candidate for `concept_verified` yet.

---

## 7. PROHIBITED ACTIONS (this shift)

- **No scaling** to the remaining ~370 bridge rows.
- **No promotion** to `concept_verified` or `ontology_core`.
- **No front-end changes** (Codex's remit).
- **No silent boundary shifts; no hidden judgment** — every gray-zone call logged.
- **No overwriting** ledger blocks (append-only).
- **No treating metadata / search rank as scholarship** — clues, not evidence.

---

## 8. RECOMMENDED NEXT SAFE ACTION — *design the Recoll kaleidoscope cycle (without running it)*

**The action:** produce a written design spec for one governed kaleidoscope cycle — how a research goal becomes query terms; how recoll ranks the corpus; how the ranking is intersected with `master_corpus` and `functional_role`; how the resulting pattern is frozen as a named, dated, sealed view; and — critically — how the *reach-further-or-hold-back* judgment is logged as a boundary-learning event. No query is run; no evidence, disposition, or grade changes.

**Why this one, in charter terms:**
- It amplifies the gesture the scholar himself identified as under-powered — **gathering / reach** ("bring the relevant books to the table").
- It is **maximally safe and fully reversible**: designing is not retrieving. Nothing enters the evidence ladder, no boundary actually moves, nothing is sealed until the user approves the design.
- It is where **boundary kinematics become operational**: retrieval is the site of constant "is this relevant enough to surface?" judgment, so specifying the cycle forces us to make the Second- and Third-Law logging concrete *before* any live call — exactly the discipline the charter demands.
- It respects the cardinal rule by construction: the spec makes recoll *feed* the verification queue, never bypass it (rank = clue, text = evidence).

**Why not the alternatives now:** the three re-sample/OCR items (Ratzel, Russia/Mongols, abiword_job) each *do* touch evidence and would need a sealed block; they are better run *after* the kaleidoscope exists, because the kaleidoscope is what will select re-sampling targets in a principled way rather than by hand. Reviewing the 14 functional readings for quality is worthwhile but is interpretation QA I authored myself — better checked by the scholar (source of meaning) than re-marked by me.

**This is a proposal, not an action taken.** Per the stop condition, I await approval before designing or running anything.

---

## 9. BOUNDARY-MOVEMENT & INTEGRITY DECLARATION

- **Boundary movement this shift:** none. No disposition, grade, taxonomy value, or functional reading was added or altered.
- **Gray-zone judgments entered:** none requiring a log — this is orientation only.
- **Evidence / ontology status changed:** none. Still 11 at `sampled_text_supported_core_candidate`, 0 at `concept_verified`, 0 at `ontology_core`.
- **Ledger:** no new block sealed (orientation changes no doctrine/disposition/evidence/role/state; charter ritual does not require a block for pure orientation). Chain remains at 19, verified OK.
- **Reversible:** everything — this note is additive and describes state without mutating it.
