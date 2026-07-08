# HANDOVER — Recoll Kaleidoscope, Design Phase

**Session:** 7b564c3e-8699-4f40-98e6-07c5c35d7649 · **Date:** 2026-07-08
**Task:** design (only) the Recoll kaleidoscope retrieval cycle, per the approved next-safe-action.
**Deliverable:** `docs/protocol/RECOLL_KALEIDOSCOPE_PROTOCOL.md` (v1, design spec).

## What this phase is
A written retrieval protocol that obeys the Charter. It specifies how a scholar's research question becomes a governed cycle — lens → Recoll clues → clue-scored, intersected candidate pattern → logged selection into the verification queue — **without any candidate bypassing text sampling and without any retrieval result touching the evidence ladder or ontology.**

## What was NOT done (stop conditions honoured)
- **No Recoll query run.** No retrieval, no source fetch, no text sampling.
- **No change** to any `evidence_grade`, `verdict_disposition`, `functional_role`, `claim`, or ontology table.
- **No promotion**; nothing entered `concept_verified` or `ontology_core`.
- **No ledger block sealed** — design of an unrun protocol changes no project state; it is additive documentation. (A block will be appropriate when the protocol is *adopted* and/or first *run*.)

## Design decisions worth the reviewer's eye
1. **Clue vs evidence is the load-bearing rule** (protocol §3): Recoll relevance = lexical clue; evidence = text seen. A #1 hit is a candidate at `provisional_unverified`, never a verdict.
2. **Three declared clue components** (§6): Relevance (Recoll's score) · Novelty (join to what we already hold — surfaces the unseen) · Project-fit (a coarse, overridable Layer A/B prior — the Histology lesson encoded). Weights are written into each run record, never hidden.
3. **Intersection is what makes a *pattern*** (§6): every hit is joined to `master_corpus` (`path_norm`), `functional_role` (`file`), `verdict_disposition` (`file`) so each candidate carries "what we already know."
4. **Grey-zone logging** (§7): a separate retrieval-judgment JSONL (not the evidence ledger) records every reach-further/hold-back call. Never silent.
5. **Boundary kinematics** (§8): surprises are *tagged*, not acted on; boundaries move only on an accumulated pattern, by a separate sealed decision — never automatically, never on one book.
6. **The cycle adds a front door, not a bypass** (§9): its last legitimate step is *selection into the verification queue*; everything downstream is the existing unchanged pipeline.
7. **Output schema** (§11) is a self-describing, reproducible *proposal artifact* whose `changed_evidence_state` is always `false`.
8. **Dry-run** (§12) is explicitly fabricated to show record shape; no query produced it.

## Grounding (read-only, no retrieval)
Schema confirmed against the live DB so the protocol references real columns: `master_corpus.path_norm/evidence_grade`, `functional_role.file`, `verdict_disposition.file`, `recoll_subject_folders.domain/knowledge`. Recoll CLI availability was already established in a prior turn; it was **not** invoked here.

## State at end of phase
Chain at block 19, verified OK. Pilot unchanged: 11 at `sampled_text_supported_core_candidate`, 14 functional readings, 0 at `concept_verified`/`ontology_core`.

## Recommended next step (for the scholar to choose)
**Review the protocol and, if the design is sound, authorise a single supervised dry live-run** — one real Recoll query for one scholar-authored research question, producing one run record for inspection, still with **no** promotion and **no** evidence-state change. That first governed turn is where the Second- and Third-Law logging gets exercised on real hits. Do not batch or scale until that single run is reviewed.
